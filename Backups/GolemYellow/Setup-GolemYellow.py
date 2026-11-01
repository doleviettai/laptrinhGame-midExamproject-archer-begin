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
BLUE_GRAPH = ROOT / 'Assets/Script/GolemBlueCombat.asset'
YELLOW_GRAPH = ROOT / 'Assets/Script/GolemYellowCombat.asset'
BLUE_CONTROLLER = ROOT / 'Assets/Animation/Enemy/Golem/Golem_blue.controller'
YELLOW_CONTROLLER = ROOT / 'Assets/Animation/Enemy/Golem/Golem_yellow.controller'


def read(path):
    return path.read_text(encoding='utf-8')


def embedded(text):
    match = re.search(r"    _json: '(.*?)'\n    _objectReferences:", text, re.S)
    assert match, 'Missing Visual Scripting JSON'
    raw = re.sub(r'\n[ ]+', ' ', match[1]).replace("''", "'")
    return match, json.loads(raw)


def replace_json(text, match, payload):
    serialized = json.dumps(payload, ensure_ascii=True, separators=(',', ':')).replace("'", "''")
    return text[:match.start(1)] + serialized + text[match.end(1):]


def block(text, file_id):
    match = re.search(r'^--- !u!(\d+) &' + str(file_id) + r'\n.*?(?=^--- !u!|\Z)', text, re.M | re.S)
    assert match, f'Missing YAML object {file_id}'
    return match[0]


def replace_block(text, file_id, replacement):
    return text.replace(block(text, file_id), replacement, 1)


def meta_guid(path):
    return re.search(r'^guid: (\w+)$', read(Path(str(path) + '.meta')), re.M)[1]


def remap_component(text, new_id, new_object):
    text = re.sub(r'^(--- !u!\d+ &)-?\d+', lambda m: m[1] + str(new_id), text, count=1)
    return re.sub(r'  m_GameObject: \{fileID: -?\d+\}', f'  m_GameObject: {{fileID: {new_object}}}', text, count=1)


original = {p: read(p) for p in [SCENE, BLUE_GRAPH, BLUE_CONTROLLER, YELLOW_CONTROLLER]}
hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in original}
assert not YELLOW_GRAPH.exists(), 'Yellow combat graph already exists; inspect it before updating.'

# The copied graph remains separate so Blue and Yellow keep individual starting HP.
blue_match, blue_payload = embedded(original[BLUE_GRAPH])
initial_payload = copy.deepcopy(blue_payload)
nodes = {e['$id']: e for e in blue_payload['graph']['elements'] if '$id' in e}
health_initializers = []
for node in nodes.values():
    if node['$type'] != 'Unity.VisualScripting.SetVariable' or node['defaultValues']['name']['$content'] != 'health':
        continue
    for edge in blue_payload['graph']['elements']:
        if edge['$type'] == 'Unity.VisualScripting.ValueConnection' and edge['destinationUnit'].get('$ref') == node['$id'] and edge['destinationKey'] == 'input':
            source = nodes[edge['sourceUnit']['$ref']]
            if source['$type'] == 'Unity.VisualScripting.Literal' and source['type'] == 'System.Int32':
                health_initializers.append(source)
assert len(health_initializers) == 1
hp_literal = health_initializers[0]
old_blue_hp = hp_literal['value']['$content']
hp_literal['value']['$content'] = 9
for element in blue_payload['graph']['elements']:
    if element['$type'] == 'Unity.VisualScripting.GraphGroup' and element['label'].startswith('01 |'):
        element['comment'] = element['comment'].replace(f'health = {old_blue_hp}', 'health = 9')
new_blue_graph = replace_json(original[BLUE_GRAPH], blue_match, blue_payload)

yellow_payload = copy.deepcopy(blue_payload)
for element in yellow_payload['graph']['elements']:
    if element.get('$id') == hp_literal['$id']:
        element['value']['$content'] = 3
    if element['$type'] == 'Unity.VisualScripting.GraphGroup':
        element['comment'] = element['comment'].replace('Golem Blue', 'Golem Yellow').replace('health = 9', 'health = 3')
    if element.get('member', {}).get('name') == 'Destroy' and element['defaultValues'].get('%t', {}).get('$content') == 0.85:
        element['defaultValues']['%t']['$content'] = 0.6
for element in yellow_payload['graph']['elements']:
    if element['$type'] == 'Unity.VisualScripting.GraphGroup' and element['label'].startswith('12 |'):
        element['comment'] = element['comment'].replace('0.85', '0.6')
yellow_graph_text = replace_json(original[BLUE_GRAPH], blue_match, yellow_payload)
yellow_graph_text = yellow_graph_text.replace('  m_Name: GolemBlueCombat\n', '  m_Name: GolemYellowCombat\n', 1)
yellow_graph_guid = uuid.uuid4().hex
yellow_graph_meta = f'''fileFormatVersion: 2
guid: {yellow_graph_guid}
NativeFormatImporter:
  externalObjects: {{}}
  mainObjectFileID: 11400000
  userData: 
  assetBundleName: 
  assetBundleVariant: 
'''

# Reuse the tested transition topology with the Yellow controller's own state IDs
# and its actual yellow/orange animation clips.
state_mapping = {
    '-1350208438603190586': '-1690879407289893053',
    '-6001154423380425270': '643756393317116415',
    '49540323481982045': '5756257963356906672',
    '2169784751130767256': '-1469138759174189173',
    '-3640981601880222573': '1595753559444445346',
    '-5408812948437196602': '3174132927118267823',
}
clip_mapping = {
    'Golem_blue.anim': 'Golem_yl_idel.anim',
    'Golem_blue_walking.anim': 'Golem_yl_walking.anim',
    'Golem_blue_attack.anim': 'Golem_yl_attack.anim',
    'Golem_blue_eat_hit.anim': 'Golem_yl_eat_hit.anim',
    'Golem_blue_die.anim': 'Golem_yl_die.anim',
}
controller = original[BLUE_CONTROLLER]
for old_name, new_name in clip_mapping.items():
    directory = BLUE_CONTROLLER.parent
    controller = controller.replace(meta_guid(directory / old_name), meta_guid(directory / new_name))
for old_id, new_id in state_mapping.items():
    controller = re.sub(r'(?m)(^--- !u!\d+ &)' + re.escape(old_id) + r'$', lambda m: m[1] + new_id, controller)
    controller = controller.replace(f'fileID: {old_id}}}', f'fileID: {new_id}}}')
for old_name, new_name in {
    'Golem_blue_eat_hit': 'Golem_yl_eat_hit',
    'Golem_blue_attack': 'Golem_yl_attack',
    'Golem_blue_die': 'Golem_yl_die',
    'Golem_walking': 'Golem_yl_walking',
}.items():
    controller = controller.replace(f'  m_Name: {old_name}\n', f'  m_Name: {new_name}\n')
idle = block(controller, '-1690879407289893053').replace('  m_Name: Golem_blue\n', '  m_Name: Golem_yl_idel\n')
controller = replace_block(controller, '-1690879407289893053', idle)
controller_root = block(controller, 9100000).replace('  m_Name: Golem_blue\n', '  m_Name: Golem_yellow\n')
controller = replace_block(controller, 9100000, controller_root)

# Scene objects stay in their saved positions. Yellow receives the same collider
# and rigidbody settings that the user fitted and tested on the Blue sprite.
scene = original[SCENE]
all_ids = set(re.findall(r'^--- !u!\d+ &(-?\d+)', scene, re.M))


def new_id():
    while True:
        result = str(uuid.uuid4().int % (2**62))
        if result not in all_ids:
            all_ids.add(result)
            return result


blue_vars_text = block(scene, 738191899)
variables_match, blue_variables = embedded(blue_vars_text)
initial_variables = copy.deepcopy(blue_variables)
blue_declarations = blue_variables['declarations']['collection']['$content']
health_declaration = next(d for d in blue_declarations if d['name'] == 'health')
health_declaration['value']['$content'] = 9
blue_vars_updated = replace_json(blue_vars_text, variables_match, blue_variables)
scene = replace_block(scene, 738191899, blue_vars_updated)

yellow_id = '752946046'
new_rigidbody, new_box, new_variables, new_machine = [new_id() for _ in range(4)]
yellow_go = block(scene, yellow_id)
assert len(re.findall(r'component: \{fileID:', yellow_go)) == 3, 'Yellow components changed; inspect first.'
yellow_go = yellow_go.replace('  m_Layer:', ''.join(f'  - component: {{fileID: {fid}}}\n' for fid in [new_box, new_rigidbody, new_variables, new_machine]) + '  m_Layer:', 1)
yellow_go = yellow_go.replace('  m_TagString: Untagged\n', '  m_TagString: Enemy\n', 1)
scene = replace_block(scene, yellow_id, yellow_go)
yellow_rigidbody = remap_component(block(scene, 738191897), new_rigidbody, yellow_id)
yellow_box = remap_component(block(scene, 738191896), new_box, yellow_id)
yellow_variables = copy.deepcopy(blue_variables)
for declaration in yellow_variables['declarations']['collection']['$content']:
    if declaration['name'] == 'health':
        declaration['value']['$content'] = 3
    elif declaration['name'] in ['isAwake', 'isAttacking', 'isHurt']:
        declaration['value']['$content'] = False
yellow_vars_text = remap_component(blue_vars_updated, new_variables, yellow_id)
yellow_vars_match, _ = embedded(yellow_vars_text)
yellow_vars_text = replace_json(yellow_vars_text, yellow_vars_match, yellow_variables)
assert '    - {fileID: 1381974991}' in yellow_vars_text, 'Player reference missing'
yellow_machine = remap_component(block(scene, 738191898), new_machine, yellow_id)
yellow_machine = yellow_machine.replace(meta_guid(BLUE_GRAPH), yellow_graph_guid)
scene = scene.replace('--- !u!1660057539 &9223372036854775807', yellow_box + yellow_rigidbody + yellow_vars_text + yellow_machine + '--- !u!1660057539 &9223372036854775807', 1)

# Verify serialized definitions before references (Full Serializer requirement).
def validate_graph(text):
    _, payload = embedded(text)
    seen = set()
    references = []

    def walk(value):
        if isinstance(value, dict):
            if '$id' in value:
                assert value['$id'] not in seen, 'Duplicate node ID'
                seen.add(value['$id'])
            if '$ref' in value:
                assert value['$ref'] in seen, f'Forward reference: {value["$ref"]}'
                references.append(value['$ref'])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    elements = payload['graph']['elements']
    assert len(set(e['guid'] for e in elements)) == len(elements)
    return payload


assert validate_graph(new_blue_graph) == blue_payload
assert validate_graph(yellow_graph_text) == yellow_payload
assert len(blue_payload['graph']['elements']) == len(initial_payload['graph']['elements'])
for old, new in zip(initial_payload['graph']['elements'], blue_payload['graph']['elements']):
    expected = copy.deepcopy(old)
    if expected.get('$id') == hp_literal['$id']:
        expected['value']['$content'] = 9
    if expected['$type'] == 'Unity.VisualScripting.GraphGroup' and expected['label'].startswith('01 |'):
        expected['comment'] = expected['comment'].replace(f'health = {old_blue_hp}', 'health = 9')
    assert expected == new, f'Unexpected Blue graph change: {old["guid"]}'
assert initial_variables['declarations']['collection']['$content'][1:] == blue_declarations[1:]
new_scene_blocks = {m[2]: (int(m[1]), m[0]) for m in re.finditer(r'^--- !u!(\d+) &(-?\d+)\n.*?(?=^--- !u!|\Z)', scene, re.M | re.S)}
for fid in [yellow_id, '738191892']:
    go_text = new_scene_blocks[fid][1]
    for cid in re.findall(r'component: \{fileID: (-?\d+)\}', go_text):
        assert cid in new_scene_blocks, cid
        assert f'm_GameObject: {{fileID: {fid}}}' in new_scene_blocks[cid][1]
original_blocks = {m[2]: m[0] for m in re.finditer(r'^--- !u!(\d+) &(-?\d+)\n.*?(?=^--- !u!|\Z)', original[SCENE], re.M | re.S)}
for fid, content in original_blocks.items():
    if fid not in [yellow_id, '738191899']:
        assert new_scene_blocks[fid][1] == content, f'Unrelated scene object changed: {fid}'
controller_ids = set(re.findall(r'^--- !u!\d+ &(-?\d+)', controller, re.M))
for cid in re.findall(r'\{fileID: (-?\d+)\}', controller):
    assert cid == '0' or cid in controller_ids, f'Controller local reference not found: {cid}'
assert all(f'm_Name: {name}\n' in controller for name in ['isWalk', 'doAttack', 'gotHit', 'doDie'])
assert all('guid: ' + meta_guid(BLUE_CONTROLLER.parent / target) in controller for target in clip_mapping.values())
assert 'Golem_blue' not in controller
for name in ['Golem_yl_attack.anim', 'Golem_yl_eat_hit.anim', 'Golem_yl_die.anim']:
    assert 'm_LoopTime: 0' in read(BLUE_CONTROLLER.parent / name)
assert 'm_GravityScale: 3' in yellow_rigidbody and 'm_Constraints: 4' in yellow_rigidbody
assert 'm_IsTrigger: 0' in yellow_box

guide = '''# Golem Yellow và Golem Blue

## Máu và sát thương

| Đối tượng | Máu khởi tạo | Sát thương mỗi đòn trúng |
|---|---:|---:|
| Player | 15 | Mỗi Arrow trúng gây 1 sát thương |
| Golem Blue — quái đặc biệt | 9 | 1 |
| Golem Yellow — quái thường | 3 | 1 |

Blue được đặt `health = 9` ở Object Variables trên scene và Integer Literal trong On Start của GolemBlueCombat.
Yellow dùng graph riêng GolemYellowCombat; On Start đặt health = 3.
Mỗi con giữ máu riêng; không chia sẻ biến App/Scene để lưu máu quái.

## Mở trong Unity

- Chọn Enemy → Golem_yellow → Script Machine → Edit Graph để xem GolemYellowCombat.
- Graph có 12 khung màu giống Golem Blue, mỗi khung có Comment giải thích.
- Animator dùng Golem_yellow.controller; toàn bộ Motion là clip màu vàng Golem_yl_*.

## Component của Golem Yellow

- Rigidbody 2D: Dynamic, Gravity Scale 3, Freeze Rotation Z.
- Box Collider 2D: Is Trigger tắt; Size (1.5632668, 1.4789243), Offset (-0.07003021, -0.9337318), khớp cùng loại sprite Golem Blue.
- Variables: health (Integer 3), Player (GameObject Player), moveSpeed (Float 2), isAwake (Boolean false), attackRange (Float 2), isAttacking (Boolean false), attackDelay (Float 0.4), attackRecovery (Float 0.8), isHurt (Boolean false).
- Script Machine: GolemYellowCombat. Tag Enemy.

## Luồng hành vi và nhận sát thương

1. On Start → health = 3, isAttacking = false, isHurt = false.
2. On Became Visible → isAwake = true. Sự kiện này cũng tính camera Scene view khi kiểm thử trong Editor.
3. On Update → nếu đã thức và không Hurt: ngoài tầm thì chọn hướng, Set Linear Velocity X, Flip X và isWalk=true.
4. Đủ gần: dừng X, isWalk=false, kiểm tra isAttacking để chỉ bắt đầu một đòn.
5. isAttacking=true → Animator Trigger doAttack → Timer attackDelay=0.4.
6. Timer Completed → kiểm tra lại tầm ngang → nếu trúng gửi Custom Event PlayerTakeDamage tới Player.
7. Trúng hay hụt đều qua Timer attackRecovery=0.8 → isAttacking=false.
8. On Trigger Enter 2D → collider → Get Game Object → Compare Tag PlayerArrow → If health > 0.
9. Destroy Arrow ngay → Subtract Integer 1 → Set Object health → kiểm tra Value mới > 0.
10. Còn máu: isHurt=true → Trigger gotHit → Timer 0.36 → isHurt=false; On Update dừng X và isWalk trong lúc Hurt.
11. Hết máu: Trigger doDie → velocity=(0,0) → gravityScale=0 → BoxCollider2D disabled → Destroy This sau 0.6 giây → ScriptMachine disabled.

Animation Die màu vàng dài khoảng 0.517 giây, nên thời gian hủy 0.6 giây cho clip phát xong.
Arrow giữ cách bắn sang phải như trước.

## Animator

Parameter: isWalk là Bool; doAttack, gotHit, doDie là Trigger.

| Chuyển state | Điều kiện |
|---|---|
| Golem_yl_idel → Golem_yl_walking | isWalk=true |
| Golem_yl_walking → Golem_yl_idel | isWalk=false |
| Any State → Golem_yl_attack | doAttack |
| Any State → Golem_yl_eat_hit | gotHit |
| Any State → Golem_yl_die | doDie |
| Attack/Hurt → Idle | Has Exit Time, Exit Time=1, Duration=0 |

Giữ nguyên tên clip/state có sẵn, kể cả tên `Golem_yl_idel`.
Attack/Hurt/Die không lặp; Idle và Walking lặp.

## Kiến thức bổ sung

Các phần đã học thêm cùng Golem Blue: Mathf Abs, đọc Transform.position và Vector3.x,
Set Linear Velocity X, Custom Event/Trigger Custom Event, và This.
Không tạo C#; game dùng component có sẵn và Script Graph.

## Kiểm tra

1. Thoát Play, tải lại SampleScene nếu Unity hỏi Reload.
2. Trong Play, chọn từng con và xem Object health: Blue bắt đầu 9, Yellow bắt đầu 3.
3. Tiến tới Yellow trên cùng mặt đất: Walking, quay mặt, đuổi; đến gần thì đánh và làm Player mất 1 máu mỗi đòn trúng.
4. Bắn Yellow: health 3 → 2 → 1 → 0. Arrow trúng biến mất; còn máu phát Hurt; hết máu phát Die và biến mất.
5. Bắn Blue cần 9 phát trúng để hết 9 máu.
6. Thoát Play, chạy lại: máu khởi tạo không bị giữ từ lượt trước.

Các Golem đuổi ngang, không có hệ thống tìm đường hoặc tự nhảy qua hố. Trong Editor, Scene camera cũng có thể làm On Became Visible kích hoạt.
'''
writes = {
    SCENE: scene,
    BLUE_GRAPH: new_blue_graph,
    YELLOW_GRAPH: yellow_graph_text,
    Path(str(YELLOW_GRAPH) + '.meta'): yellow_graph_meta,
    YELLOW_CONTROLLER: controller,
    ROOT / 'GolemYellow_LuongHoatDong.md': guide,
}
blue_guide = ROOT / 'GolemBlue_LuongHoatDong.md'
if blue_guide.exists():
    text = read(blue_guide).replace('health = 7', 'health = 9').replace('đặt 7 máu', 'đặt 9 máu').replace('Khởi tạo 7 máu', 'Khởi tạo 9 máu').replace('7 máu;', '9 máu;')
    writes[blue_guide] = text
report = {
    'blueHP': 9, 'yellowHP': 3, 'damagePerHit': 1,
    'yellowGraphNodes': len(nodes),
    'yellowGraphConnections': sum(e['$type'].endswith('Connection') for e in yellow_payload['graph']['elements']),
    'yellowGroups': sum(e['$type'] == 'Unity.VisualScripting.GraphGroup' for e in yellow_payload['graph']['elements']),
    'yellowGraphGUID': yellow_graph_guid,
    'yellowComponents': {'rigidbody': new_rigidbody, 'collider': new_box, 'variables': new_variables, 'machine': new_machine},
    'originalScenePositionsPreserved': True,
    'blueOnlyHealthChanged': True,
    'graphReferenceOrderValidated': True,
    'controllerReferencesValidated': True,
    'files': len(writes),
}
print(json.dumps(report, ensure_ascii=True))
if '--apply' not in sys.argv:
    print('DRY RUN PASSED; no files changed.')
else:
    for path, digest in hashes.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, f'File changed during setup: {path}'
    backup = ROOT / 'Backups/GolemYellow' / datetime.now().strftime('%Y%m%d_%H%M%S')
    backup.mkdir(parents=True, exist_ok=False)
    for path in writes:
        if path.exists():
            destination = backup / path.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(path.read_bytes())
    for path, text in writes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    (backup / 'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('APPLIED. Backup: ' + str(backup))
