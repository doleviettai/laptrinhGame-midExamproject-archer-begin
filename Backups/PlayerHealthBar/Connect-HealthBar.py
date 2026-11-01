from pathlib import Path
import copy
import datetime
import json
import re
import shutil
import uuid

ROOT = Path(r'D:\GamePrograms\MidTestExam')
SCENE = ROOT / 'Assets/Scenes/SampleScene.unity'
GRAPH = ROOT / 'Assets/Script/PlayerHealth.asset'


def read_data(text):
    match = re.search(r"    _json: '(.*?)'\n    _objectReferences:", text, re.S)
    assert match
    return json.loads(re.sub(r'\n +', ' ', match[1]).replace("''", "'"))


def replace_data(text, data):
    match = re.search(r"    _json: '(.*?)'\n    _objectReferences:", text, re.S)
    payload = json.dumps(data, ensure_ascii=True, separators=(',', ':')).replace("'", "''")
    return text[:match.start(1)] + payload + text[match.end(1):]


def block(text, file_id):
    match = re.search(r'^--- !u!\d+ &' + str(file_id) + r'\n.*?(?=^--- !u!|\Z)', text, re.M | re.S)
    assert match, file_id
    return match[0]


def typed(value, kind):
    return {'$content': value, '$type': kind}


scene_text = SCENE.read_text(encoding='utf-8')
graph_text = GRAPH.read_text(encoding='utf-8')
original = read_data(graph_text)
data = copy.deepcopy(original)
elements = data['graph']['elements']
assert not any(e.get('member', {}).get('name') == 'fillAmount' for e in elements)
initializer = next(e for e in elements if e.get('guid') == '73ef811e-36d1-44fa-b7ed-0f1764514461')
initializer_id = initializer['$id']
initializer.update({'kind': 'Object', 'specifyFallback': False,
                    'defaultValues': {'name': typed('maxHealth', 'System.String'), 'object': None},
                    '$type': 'Unity.VisualScripting.GetVariable'})
initializer.pop('type', None)
initializer.pop('value', None)
for e in elements:
    if e.get('sourceUnit', {}).get('$ref') == initializer_id:
        assert e['sourceKey'] == 'output'
        e['sourceKey'] = 'value'
    if e.get('$type') == 'Unity.VisualScripting.GraphGroup' and 'Start with 15 HP' in e.get('label', ''):
        e['label'] = 'Player - Khoi tao mau tu maxHealth (20 HP)'
        e['comment'] = 'On Start: PlayerHealth = maxHealth; isDead = False. maxHealth la Object Variable tren Player.'

next_id = max(int(e.get('$id', 0)) for e in elements) + 1
nodes, edges = [], []


def node(unit_kind, x, y, **extra):
    global next_id
    unit_id = str(next_id)
    next_id += 1
    nodes.append({**extra, 'defaultValues': extra.get('defaultValues', {}),
                  'position': {'x': x, 'y': y}, 'guid': str(uuid.uuid4()),
                  '$version': 'A', '$type': 'Unity.VisualScripting.' + unit_kind, '$id': unit_id})
    return unit_id


def edge(kind, a, ak, b, bk):
    edges.append({'sourceUnit': {'$ref': a}, 'sourceKey': ak,
                  'destinationUnit': {'$ref': b}, 'destinationKey': bk,
                  'guid': str(uuid.uuid4()), '$type': 'Unity.VisualScripting.' + kind + 'Connection'})


def variable(name, x, y):
    result = node('GetVariable', x, y, kind='Object', specifyFallback=False,
                  defaultValues={'name': typed(name, 'System.String'), 'object': None})
    edge('Value', local_this, 'self', result, 'object')
    return result


local_this = node('This', 0, 3150)
current_hp = variable('PlayerHealth', 300, 3000)
max_hp = variable('maxHealth', 300, 3250)
fill_image = variable('HealthBarFill', 700, 3450)
divide = node('ScalarDivide', 750, 3140)
update = node('Update', 1150, 3000, coroutine=False)
set_fill = node('SetMember', 1450, 3180, chainable=False,
                member={'name': 'fillAmount', 'parameterTypes': None,
                        'targetType': 'UnityEngine.UI.Image', 'targetTypeName': 'UnityEngine.UI.Image', '$version': 'A'},
                defaultValues={'target': None})
edge('Value', current_hp, 'value', divide, 'dividend')
edge('Value', max_hp, 'value', divide, 'divisor')
edge('Value', divide, 'quotient', set_fill, 'input')
edge('Value', fill_image, 'value', set_fill, 'target')
edge('Control', update, 'trigger', set_fill, 'assign')
frame = {'position': {'xMin': -70, 'yMin': 2920, 'xMax': 2050, 'yMax': 3770},
         'label': '04 | THANH MAU DO - PlayerHealth / maxHealth',
         'comment': 'Player > Script Machine PlayerHealth. Object HealthBarFill tham chieu Canvas/Info/HealthBar/Fill (Image). Divide Math/Scalar dung so thuc: 19/20 = 0.95. Moi On Update cap nhat Image Set Fill Amount, ke ca khi Player da chet.',
         'color': {'r': 0.38, 'g': 0.13, 'b': 0.15, 'a': 1.0},
         'guid': str(uuid.uuid4()), '$version': 'A', '$type': 'Unity.VisualScripting.GraphGroup'}
first_connection = next(i for i, e in enumerate(elements) if e.get('$type', '').endswith('Connection'))
elements[first_connection:first_connection] = nodes
elements.extend(edges + [frame])

# Keep all serialized references after their definitions.
seen = set()


def validate_refs(value):
    if isinstance(value, dict):
        if '$ref' in value:
            assert value['$ref'] in seen, value
        if '$id' in value:
            assert value['$id'] not in seen, value['$id']
            seen.add(value['$id'])
        for item in value.values():
            validate_refs(item)
    elif isinstance(value, list):
        for item in value:
            validate_refs(item)


validate_refs(data)
new_graph_text = replace_data(graph_text, data)
assert read_data(new_graph_text) == data

variables_block = block(scene_text, 1381974998)
variables = read_data(variables_block)
declarations = variables['declarations']['collection']['$content']
for name in ['PlayerHealth', 'maxHealth']:
    declaration = next(v for v in declarations if v['name'] == name)
    declaration['value'] = typed(20, 'System.Int32')
assert not any(v['name'] == 'HealthBarFill' for v in declarations)
references = re.findall(r'^    - (\{fileID: [^\n]+\})$', variables_block, re.M)
assert len(references) == 4
declarations.append({'name': 'HealthBarFill', 'value': typed(len(references), 'UnityEngine.Object'),
                     'typeHandle': {'Identification': 'UnityEngine.UI.Image, UnityEngine.UI, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null', '$version': 'A'}, '$version': 'A'})
new_variables_block = replace_data(variables_block, variables)
new_variables_block = new_variables_block.rstrip() + '\n    - {fileID: 1443194428}\n\n'
new_scene_text = scene_text.replace(variables_block, new_variables_block, 1)

fill_block = block(new_scene_text, 1443194428)
assert 'm_GameObject: {fileID: 1443194426}' in fill_block
for expected in ['m_Type: 3', 'm_FillMethod: 0', 'm_FillOrigin: 0', 'm_FillAmount: 1']:
    assert expected in fill_block, expected
for file_id, health in [(738191899, 9), (3171497350686431758, 5)]:
    enemy_block = block(new_scene_text, file_id)
    assert enemy_block == block(scene_text, file_id)
    enemy_vars = read_data(enemy_block)['declarations']['collection']['$content']
    assert next(v for v in enemy_vars if v['name'] == 'health')['value']['$content'] == health

backup = ROOT / 'Backups/PlayerHealthBar' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup.mkdir(parents=True, exist_ok=False)
for source in [SCENE, GRAPH, Path(str(GRAPH) + '.meta')]:
    shutil.copy2(source, backup / source.name)
SCENE.write_text(new_scene_text, encoding='utf-8')
GRAPH.write_text(new_graph_text, encoding='utf-8')
print(json.dumps({'backup': str(backup), 'addedNodes': len(nodes), 'addedConnections': len(edges),
                  'maxPlayerHealth': 20, 'golemYellowHealth': 5, 'golemBlueHealth': 9,
                  'fillImage': 'Canvas/Info/HealthBar/Fill', 'fillImageComponent': 1443194428,
                  'healthInitializer': 'Get Object maxHealth -> Set Object PlayerHealth'}, ensure_ascii=False))
