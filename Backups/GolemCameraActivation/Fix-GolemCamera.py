from pathlib import Path
from datetime import datetime
import copy
import hashlib
import json
import re
import sys
import uuid

ROOT = Path(r'D:\GamePrograms\MidTestExam')
SCENE = ROOT / 'Assets/Scenes/SampleScene.unity'
GRAPH_PATHS = [ROOT / 'Assets/Script/GolemBlueCombat.asset', ROOT / 'Assets/Script/GolemYellowCombat.asset']


def read(path):
    return path.read_text(encoding='utf-8')


def parse(text):
    match = re.search(r"    _json: '(.*?)'\n    _objectReferences:", text, re.S)
    assert match, 'Embedded JSON is missing'
    return match, json.loads(re.sub(r'\n[ ]+', ' ', match[1]).replace("''", "'"))


def write_json(text, match, payload):
    packed = json.dumps(payload, ensure_ascii=True, separators=(',', ':')).replace("'", "''")
    return text[:match.start(1)] + packed + text[match.end(1):]


def block(text, file_id):
    match = re.search(r'^--- !u!(\d+) &' + str(file_id) + r'\n.*?(?=^--- !u!|\Z)', text, re.M | re.S)
    assert match, f'Missing YAML block {file_id}'
    return match[0]


def typed(value, kind='System.Single'):
    return {'$content': value, '$type': kind}


def member(kind, name, parameters=None):
    return {'name': name, 'parameterTypes': parameters, 'targetType': kind, 'targetTypeName': kind, '$version': 'A'}


def verify_references(payload):
    seen = set()

    def visit(value):
        if isinstance(value, dict):
            if '$id' in value:
                assert value['$id'] not in seen, f'Duplicate ID: {value["$id"]}'
                seen.add(value['$id'])
            if '$ref' in value:
                assert value['$ref'] in seen, f'Forward reference: {value["$ref"]}'
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)


class AddNodes:
    def __init__(self, elements):
        self.next_id = max(int(e['$id']) for e in elements if '$id' in e) + 10
        self.nodes = []
        self.edges = []

    def node(self, unit_kind, x, y, **extra):
        node_id = str(self.next_id)
        self.next_id += 1
        node = {**extra, 'defaultValues': extra.get('defaultValues', {}), 'position': {'x': x, 'y': y},
                'guid': str(uuid.uuid4()), '$version': 'A', '$type': 'Unity.VisualScripting.' + unit_kind, '$id': node_id}
        self.nodes.append(node)
        return node_id

    def edge(self, kind, source, source_key, target, target_key):
        edge = {'sourceUnit': {'$ref': source}, 'sourceKey': source_key, 'destinationUnit': {'$ref': target},
                'destinationKey': target_key, 'guid': str(uuid.uuid4()), '$type': 'Unity.VisualScripting.' + kind + 'Connection'}
        self.edges.append(edge)
        return edge

    def data(self, source, source_key, target, target_key):
        return self.edge('Value', source, source_key, target, target_key)

    def flow(self, source, source_key, target, target_key):
        return self.edge('Control', source, source_key, target, target_key)

    def get(self, kind, name, x, y, self_target=False):
        return self.node('GetMember', x, y, member=member(kind, name), defaultValues={'target': None} if self_target else {})


def initial_health(payload):
    elements = payload['graph']['elements']
    nodes = {e['$id']: e for e in elements if '$id' in e}
    values = []
    for target in nodes.values():
        if target['$type'] == 'Unity.VisualScripting.SetVariable' and target['defaultValues']['name']['$content'] == 'health':
            for edge in elements:
                if edge['$type'] == 'Unity.VisualScripting.ValueConnection' and edge['destinationUnit'].get('$ref') == target['$id'] and edge['destinationKey'] == 'input':
                    source = nodes[edge['sourceUnit']['$ref']]
                    if source['$type'] == 'Unity.VisualScripting.Literal':
                        values.append(source['value']['$content'])
    assert len(values) == 1
    return values[0]


original = {path: read(path) for path in GRAPH_PATHS + [SCENE]}
digests = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in original}
writes = {}
reports = []
for path in GRAPH_PATHS:
    match, payload = parse(original[path])
    prior_payload = copy.deepcopy(payload)
    graph = payload['graph']
    elements = graph['elements']
    nodes = {e['$id']: e for e in elements if '$id' in e}
    by_guid = {e['guid']: e for e in elements}
    assert not any(e.get('member', {}).get('name') == 'WorldToViewportPoint' for e in elements), 'Camera patch already present'
    visible_event = by_guid['3edf6ff5-07b2-4e56-a811-88bfc992c83d']
    assert visible_event['$type'] == 'Unity.VisualScripting.OnBecameVisible'
    awake_set = by_guid['8d6c03b6-450a-495a-9e47-4c5c9ec5b5c1']
    awake_get = by_guid['e1464591-7e1e-46c6-8760-70d3c1b3dbe8']
    hurt_gate = by_guid['572055e3-3a8e-4972-b506-7aac81e3c419']
    start_hurt_set = by_guid['5573a4be-6b8f-406c-a46b-28c9a6cb200a']
    awake_gate_wire = next(e for e in elements if e['$type'] == 'Unity.VisualScripting.ValueConnection' and
                           e['sourceUnit'].get('$ref') == awake_get['$id'] and e['destinationKey'] == 'condition')
    awake_gate = nodes[awake_gate_wire['destinationUnit']['$ref']]
    assert awake_gate['$type'] == 'Unity.VisualScripting.If'
    assert not any(e['$type'] == 'Unity.VisualScripting.ControlConnection' and e['sourceUnit'].get('$ref') == awake_gate['$id'] and e['sourceKey'] == 'ifFalse' for e in elements)
    old_event_edges = [e for e in elements if e['$type'].endswith('Connection') and
                       (e['sourceUnit'].get('$ref') == visible_event['$id'] or e['destinationUnit'].get('$ref') == visible_event['$id'])]
    assert len(old_event_edges) == 1 and old_event_edges[0]['destinationUnit']['$ref'] == awake_set['$id']
    removed_guids = {visible_event['guid'], old_event_edges[0]['guid']}
    existing_false = next(e for e in elements if e['$type'] == 'Unity.VisualScripting.ValueConnection' and
                          e['destinationUnit'].get('$ref') == start_hurt_set['$id'] and e['destinationKey'] == 'input')
    false_literal = nodes[existing_false['sourceUnit']['$ref']]
    assert false_literal['value']['$content'] is False
    assert not any(e['$type'] == 'Unity.VisualScripting.ControlConnection' and e['sourceUnit'].get('$ref') == start_hurt_set['$id'] for e in elements)

    add = AddNodes(elements)
    reset = add.node('SetVariable', 730, 700, kind='Object',
                     defaultValues={'name': typed('isAwake', 'System.String'), 'object': None})
    add.data(false_literal['$id'], 'output', reset, 'input')
    add.flow(start_hurt_set['$id'], 'assigned', reset, 'assign')

    # Each new camera frame owns its own This source; no new shared long This wires.
    own = add.node('This', 6570, 760)
    camera = add.node('GetVariable', 6570, 180, kind='Object', specifyFallback=False,
                      defaultValues={'name': typed('MainCamera', 'System.String'), 'object': None})
    position = add.get('UnityEngine.Transform', 'position', 6570, 470, self_target=True)
    add.data(own, 'self', position, 'target')
    view = add.node('InvokeMember', 6920, 180, chainable=False, parameterNames=['position'],
                    member=member('UnityEngine.Camera', 'WorldToViewportPoint', ['UnityEngine.Vector3']),
                    defaultValues={'target': None, '%position': {'x': 0.0, 'y': 0.0, 'z': 0.0, '$type': 'UnityEngine.Vector3'}})
    add.data(camera, 'value', view, 'target')
    add.data(position, 'value', view, '%position')
    coords = []
    for axis, y in [('x', 180), ('y', 500), ('z', 820)]:
        component = add.get('UnityEngine.Vector3', axis, 7340, y)
        add.data(view, 'result', component, 'target')
        coords.append(component)
    compares = []
    for component, op, threshold, x, y in [
        (coords[0], 'Greater', 0.0, 7700, 180),
        (coords[0], 'Less', 1.0, 8100, 180),
        (coords[1], 'Greater', 0.0, 7700, 500),
        (coords[1], 'Less', 1.0, 8100, 500),
        (coords[2], 'Greater', 0.0, 7700, 820),
    ]:
        comp = add.node(op, x, y, numeric=True, defaultValues={'b': typed(threshold)})
        add.data(component, 'value', comp, 'a')
        compares.append((comp, 'comparison'))
    result = compares[0]
    for index, condition in enumerate(compares[1:]):
        combine = add.node('And', 8500 + (index % 2) * 350, 180 + (index // 2) * 320)
        add.data(result[0], result[1], combine, 'a')
        add.data(condition[0], condition[1], combine, 'b')
        result = combine, 'result'
    check_camera = add.node('If', 8850, 820)
    add.data(result[0], result[1], check_camera, 'condition')
    add.flow(awake_gate['$id'], 'ifFalse', check_camera, 'enter')
    add.flow(check_camera, 'ifTrue', awake_set['$id'], 'assign')
    add.flow(awake_set['$id'], 'assigned', hurt_gate['$id'], 'enter')
    # Explicit idle output while never detected; the first encounter still latches True like Skeleton.
    idle_speed = add.node('SetMember', 9280, 820, chainable=False,
                          member=member('UnityEngine.Rigidbody2D', 'linearVelocityX'),
                          defaultValues={'target': None, 'input': typed(0.0)})
    idle_walk = add.node('InvokeMember', 9650, 820, chainable=False, parameterNames=['name', 'value'],
                         member=member('UnityEngine.Animator', 'SetBool', ['System.String', 'System.Boolean']),
                         defaultValues={'target': None, '%name': typed('isWalk', 'System.String'), '%value': typed(False, 'System.Boolean')})
    add.data(own, 'self', idle_speed, 'target')
    add.data(own, 'self', idle_walk, 'target')
    add.flow(check_camera, 'ifFalse', idle_speed, 'assign')
    add.flow(idle_speed, 'assigned', idle_walk, 'enter')

    awake_true_wire = next(e for e in elements if e['$type'] == 'Unity.VisualScripting.ValueConnection' and
                          e['destinationUnit'].get('$ref') == awake_set['$id'] and e['destinationKey'] == 'input')
    awake_true = nodes[awake_true_wire['sourceUnit']['$ref']]
    assert awake_true['value']['$content'] is True
    awake_set['position'] = {'x': 9280, 'y': 180}
    awake_true['position'] = {'x': 9280, 'y': 500}
    init_frame = next(e for e in elements if e['$type'] == 'Unity.VisualScripting.GraphGroup' and e['label'].startswith('01 |'))
    camera_frame = next(e for e in elements if e['$type'] == 'Unity.VisualScripting.GraphGroup' and e['label'].startswith('02 |'))
    init_frame['position']['yMax'] = 1000
    init_frame['comment'] += ' Cuối On Start đặt isAwake=False để mỗi lượt phải được camera Player nhìn thấy mới thức.'
    camera_frame['position'] = {'xMin': 6500, 'yMin': 0, 'xMax': 10100, 'yMax': 1200}
    camera_frame['label'] = '02 | CAMERA PLAYER PHÁT HIỆN'
    camera_frame['comment'] = ('If isAwake=False → World To Viewport Point bằng Object MainCamera. '
                               'Kiểm tra 0<X<1, 0<Y<1, Z>0. Có trong camera Player → isAwake=True rồi đuổi/đánh; '
                               'chưa thấy → vận tốc X=0, isWalk=False. Scene view không kích hoạt. '
                               'Sau khi thức thì tiếp tục đuổi giống Skeleton. This chỉ dùng trong khung này.')
    graph['elements'] = add.nodes + [e for e in elements if e['guid'] not in removed_guids] + add.edges
    graph['pan'] = {'x': 5050.0, 'y': 2550.0}
    graph['zoom'] = 0.1

    # None of the existing attack, hit, death, or health nodes may change semantics.
    prior_by_guid = {e['guid']: e for e in prior_payload['graph']['elements']}
    for element in graph['elements']:
        if element['guid'] not in prior_by_guid:
            continue
        expected = copy.deepcopy(prior_by_guid[element['guid']])
        actual = copy.deepcopy(element)
        if element['$type'] == 'Unity.VisualScripting.GraphGroup':
            assert element['guid'] in [init_frame['guid'], camera_frame['guid']] or actual == expected
            continue
        expected.pop('position', None)
        actual.pop('position', None)
        assert expected == actual, f'Unexpected original graph change: {element["guid"]}'
    assert initial_health(payload) == initial_health(prior_payload)
    assert not any(e['$type'] == 'Unity.VisualScripting.OnBecameVisible' for e in graph['elements'])
    verify_references(payload)
    text = write_json(original[path], match, payload)
    assert parse(text)[1] == payload
    writes[path] = text
    reports.append({'graph': path.stem, 'healthPreserved': initial_health(payload),
                    'removedOnBecameVisible': True, 'resetOnStart': True, 'mainCameraReference': 'MainCamera',
                    'cameraMethodMatchesSkeleton': True, 'awakeGateToCameraIf': True,
                    'newNodes': len(add.nodes), 'newWires': len(add.edges),
                    'viewportNodeID': view, 'visibleIfID': check_camera})

# Append a local camera reference to both Golems' Object Variables, preserving their latest HP and Player.
scene = original[SCENE]
scene_records = []
for go_id in ['738191892', '752946046']:
    go = block(scene, go_id)
    name = re.search(r'^  m_Name: (.*)', go, re.M)[1]
    components = re.findall(r'component: \{fileID: (-?\d+)\}', go)
    variables_id = next(cid for cid in components if 'Unity.VisualScripting.Core::Unity.VisualScripting.Variables' in block(scene, cid))
    vars_text = block(scene, variables_id)
    vm, vp = parse(vars_text)
    original_vars = copy.deepcopy(vp)
    declarations = vp['declarations']['collection']['$content']
    assert not any(d['name'] == 'MainCamera' for d in declarations)
    references_match = re.search(r'    _objectReferences:(.*)', vars_text, re.S)
    reference_index = len(re.findall(r'^    - \{fileID:', references_match[1], re.M))
    declarations.append({'name': 'MainCamera', 'value': typed(reference_index, 'UnityEngine.Object'),
                         'typeHandle': {'Identification': 'UnityEngine.GameObject, UnityEngine.CoreModule, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null', '$version': 'A'}, '$version': 'A'})
    assert declarations[:-1] == original_vars['declarations']['collection']['$content']
    replacement = write_json(vars_text, vm, vp).rstrip() + '\n    - {fileID: 519420028}\n'
    scene = scene.replace(vars_text, replacement, 1)
    scene_records.append({'object': name, 'variablesID': variables_id,
                          'health': next(d['value']['$content'] for d in declarations if d['name'] == 'health'),
                          'cameraReferenceIndex': reference_index})
writes[SCENE] = scene

camera_doc = '''# Golem chỉ thức khi vào camera Player

Áp dụng cho cả GolemBlueCombat và GolemYellowCombat.

**Nguyên nhân cũ:** On Became Visible có thể bị camera Scene view kích hoạt khi Game camera còn ở xa.
**Cách mới:** dùng Camera.WorldToViewportPoint với GameObject Main Camera bên trong Player, giống SkeletonCombat.

## Biến Object

- MainCamera: GameObject = Player/Main Camera, đã gán trên cả hai Golem.
- isAwake: Boolean = False; On Start cũng đặt lại False.
- Máu giữ theo bản người dùng vừa lưu: Blue 9, Yellow 5.

## Nhóm 02 — Camera Player phát hiện

Data: MainCamera → Camera World To Viewport Point, Target.
This → Transform Get Position → World To Viewport Point, Position.
Kết quả Vector3 được tách X, Y, Z; kiểm tra X>0, X<1, Y>0, Y<1, Z>0 rồi ghép And.

Flow: On Update → If isAwake.
- True → hành vi đuổi/đánh hiện có.
- False → If điều kiện viewport. True → Set Object isAwake=True → hành vi hiện có.
- Nếu viewport False: Set Linear Velocity X=0 → Animator Set Bool isWalk=False.

Khung 02 dùng một This riêng. Các khung xử lý đánh, Hurt, trừ máu và Die giữ nguyên.

Sau lần đầu vào camera, isAwake giữ True và Golem tiếp tục đuổi, cùng cách Skeleton hoạt động.
Đây là điều kiện bắt đầu đuổi, không phải tự quên Player mỗi lần rời màn hình.

## Kiến thức bổ sung

Camera.WorldToViewportPoint, Vector3 Get X/Y/Z và And.
Chỉ dùng Unity API node và Visual Scripting, không có C#.

## Kiểm tra trong Unity

1. Trước Play, đặt Player xa Golem; vẫn có thể nhìn Golem trong Scene view.
2. Play: Golem ngoài camera Game phải đứng Idle, isAwake=False, vận tốc X=0.
3. Đưa Player đến để Golem vào camera Game: isAwake=True, Golem mới chạy đến và đánh.
4. Thoát Play rồi chạy lại: isAwake đặt lại False.
5. Arrow/Hurt/Die và máu Blue 9 / Yellow 5 giữ nguyên.
'''
writes[ROOT / 'Golem_CameraPlayer.md'] = camera_doc
for name in ['GolemBlue_LuongHoatDong.md', 'GolemYellow_LuongHoatDong.md']:
    path = ROOT / name
    if not path.exists():
        continue
    text = read(path)
    if name.startswith('GolemBlue'):
        text = text.replace('On Became Visible đặt isAwake bằng True. Camera Scene view cũng có thể kích hoạt sự kiện này trong Editor.',
                            'WorldToViewportPoint bằng camera Player; chỉ vào viewport mới đặt isAwake=True. On Start đặt lại False.')
        text = text.replace('VISIBLE[02 · Xuất hiện trong tầm nhìn]', 'VISIBLE[02 · Vào camera Game của Player]')
        text = text.replace('Các biến health, Player, moveSpeed, attackRange, isAwake, isAttacking, isHurt thuộc **Object**.',
                            'Các biến health, Player, MainCamera, moveSpeed, attackRange, isAwake, isAttacking, isHurt thuộc **Object**.')
        text = text.replace('Set Linear Velocity X, Custom Event/Trigger Custom Event, và This.',
                            'Set Linear Velocity X, Custom Event/Trigger Custom Event, This và Camera.WorldToViewportPoint.')
    else:
        text = text.replace('| Golem Yellow — quái thường | 3 | 1 |', '| Golem Yellow — quái thường | 5 | 1 |')
        text = text.replace('On Start đặt health = 3.', 'On Start đặt health = 5.')
        text = text.replace('health (Integer 3)', 'health (Integer 5)')
        text = text.replace('1. On Start → health = 3, isAttacking = false, isHurt = false.',
                            '1. On Start → health = 5, isAttacking = false, isHurt = false, isAwake = false.')
        text = text.replace('2. On Became Visible → isAwake = true. Sự kiện này cũng tính camera Scene view khi kiểm thử trong Editor.',
                            '2. Kiểm tra WorldToViewportPoint bằng Object MainCamera → chỉ khi vào camera Game của Player mới đặt isAwake = true, giống Skeleton.')
        text = text.replace('Blue bắt đầu 9, Yellow bắt đầu 3.', 'Blue bắt đầu 9, Yellow bắt đầu 5.')
        text = text.replace('health 3 → 2 → 1 → 0.', 'health 5 → 4 → 3 → 2 → 1 → 0.')
        text = text.replace('Trong Editor, Scene camera cũng có thể làm On Became Visible kích hoạt.',
                            'Phát hiện dùng camera Game của Player; Scene camera không kích hoạt đuổi sớm.')
    text += '\n\nCập nhật phát hiện camera: xem [Golem_CameraPlayer.md](Golem_CameraPlayer.md).\n'
    writes[path] = text

print(json.dumps({'graphs': reports, 'sceneReferences': scene_records, 'files': len(writes)}, ensure_ascii=True))
if '--apply' not in sys.argv:
    print('DRY RUN PASSED; no files changed.')
else:
    for path, digest in digests.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, f'File changed during preparation: {path}'
    backup = ROOT / 'Backups/GolemCameraActivation' / datetime.now().strftime('%Y%m%d_%H%M%S')
    backup.mkdir(parents=True)
    for path in writes:
        if path.exists():
            target = backup / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    for path, text in writes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    (backup / 'verification.json').write_text(json.dumps({'graphs': reports, 'sceneReferences': scene_records}, indent=2), encoding='utf-8')
    print('APPLIED BACKUP: ' + str(backup))
