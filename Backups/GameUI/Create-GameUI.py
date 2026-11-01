from pathlib import Path
import copy
import datetime
import json
import re
import shutil
import tarfile
import uuid

ROOT = Path(r'D:\GamePrograms\MidTestExam')
SCENE = ROOT / 'Assets/Scenes/SampleScene.unity'
HEALTH = ROOT / 'Assets/Script/PlayerHealth.asset'
scene = SCENE.read_text(encoding='utf-8')
health_text = HEALTH.read_text(encoding='utf-8')
assert 'm_Name: GameUIManager\n' not in scene
backup = ROOT / 'Backups/GameUI' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup.mkdir(parents=True)
for path in [SCENE, HEALTH]:
    shutil.copy2(path, backup / path.name)


def uid():
    return str(uuid.uuid4())


def block(file_id):
    match = re.search(r'^--- !u!\d+ &' + str(file_id) + r'\n.*?(?=^--- !u!|\Z)', scene, re.M | re.S)
    assert match, file_id
    return match[0]


def edit(file_id, text):
    global scene
    scene = scene.replace(block(file_id), text, 1)


def field(text, key, value):
    text, count = re.subn(r'^  ' + re.escape(key) + r':[^\n]*', lambda m: '  ' + key + ': ' + str(value), text, count=1, flags=re.M)
    assert count, key
    return text


def read_data(text):
    match = re.search(r"    _json: '(.*?)'\n    _objectReferences:", text, re.S)
    return json.loads(re.sub(r'\n +', ' ', match[1]).replace("''", "'"))


def replace_data(text, data):
    match = re.search(r"    _json: '(.*?)'\n    _objectReferences:", text, re.S)
    payload = json.dumps(data, ensure_ascii=True, separators=(',', ':')).replace("'", "''")
    return text[:match.start(1)] + payload + text[match.end(1):]


def typed(value, kind='System.Single'):
    return {'$content': value, '$type': kind}


# TextMeshPro's bundled essentials: fonts, materials, settings and shaders.
# Preserve the package GUIDs; never replace resources the user already imported.
archive = next((ROOT / 'Library/PackageCache').glob('com.unity.ugui@*/Package Resources/TMP Essential Resources.unitypackage'))
imported = []
with tarfile.open(archive, 'r:gz') as tar:
    members = {m.name: m for m in tar.getmembers()}
    for member in members.values():
        if not member.name.endswith('/pathname'):
            continue
        relative = tar.extractfile(member).read().decode('utf-8').strip()
        destination = ROOT / relative
        assert destination.resolve().is_relative_to((ROOT / 'Assets').resolve())
        stem = member.name.rsplit('/', 1)[0]
        asset_member = members.get(stem + '/asset')
        if asset_member:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_bytes(tar.extractfile(asset_member).read())
                imported.append(relative)
        else:
            destination.mkdir(parents=True, exist_ok=True)
        meta = Path(str(destination) + '.meta')
        meta_member = members.get(stem + '/asset.meta')
        if meta_member and not meta.exists():
            meta.write_bytes(tar.extractfile(meta_member).read())

FONT = '8f586378b4e144a9851e7b34d9b748ee'
TMP_GUID = 'f4688fdb7df04437aeb418b961361dc5'
BUTTON_GUID = '4e29b1a8efbd4b44bb3f3716e73f07ff'
MACHINE_GUID = 'd2fe5546f775c47d2820aa5e8a715f53'
VARIABLES_GUID = 'e741851cba3ad425c91ecf922cc6b379'
font_asset = ROOT / 'Assets/TextMesh Pro/Resources/Fonts & Materials/LiberationSans SDF.asset'
font_text = font_asset.read_text(encoding='utf-8-sig')
assert '2e498d1c8094910479dc3e1b768306a4' in font_text, 'Vietnamese dynamic fallback must be present.'

sequence = 490000000000000000


def new_id():
    global sequence
    sequence += 1
    assert not re.search(r'^--- !u!\d+ &' + str(sequence) + '$', scene, re.M)
    return sequence


new_blocks = []
children = {}


def go(name, components, active=True, layer=5):
    ident = new_id()
    new_blocks.append(f'''--- !u!1 &{ident}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
''' + ''.join(f'  - component: {{fileID: {i}}}\n' for i in components) + f'''  m_Layer: {layer}
  m_Name: {name}
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: {int(active)}
''')
    return ident


def rect(ident, gameobject, parent=0, x=0, y=0, w=100, h=100, anchor=(.5, .5), stretch=False):
    children.setdefault(ident, [])
    if parent:
        children.setdefault(parent, []).append(ident)
    new_blocks.append(f'''--- !u!224 &{ident}
RectTransform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {gameobject}}}
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: @CHILDREN_{ident}@
  m_Father: {{fileID: {parent}}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
  m_AnchorMin: {{x: {0 if stretch else anchor[0]}, y: {0 if stretch else anchor[1]}}}
  m_AnchorMax: {{x: {1 if stretch else anchor[0]}, y: {1 if stretch else anchor[1]}}}
  m_AnchoredPosition: {{x: {x}, y: {y}}}
  m_SizeDelta: {{x: {0 if stretch else w}, y: {0 if stretch else h}}}
  m_Pivot: {{x: 0.5, y: 0.5}}
''')


def copy_component(source, ident, gameobject):
    text = block(source)
    text = re.sub(r'^(--- !u!\d+ &)-?\d+', lambda m: m[1] + str(ident), text, count=1)
    return field(text, 'm_GameObject', '{fileID: ' + str(gameobject) + '}')


def image(name, parent, x=0, y=0, w=100, h=100, color=(1, 1, 1, 1), stretch=False, raycast=True):
    tr, cr, im = new_id(), new_id(), new_id()
    obj = go(name, [tr, cr, im])
    rect(tr, obj, parent, x, y, w, h, stretch=stretch)
    new_blocks.append(copy_component(1823533, cr, obj))
    text = copy_component(1823532, im, obj)
    text = field(text, 'm_Color', '{r: %s, g: %s, b: %s, a: %s}' % color)
    text = field(text, 'm_RaycastTarget', int(raycast))
    new_blocks.append(text)
    return obj, tr, im


def tmp_component(ident, obj, content, size=36, color=(.15, .12, .09, 1), align=2, bold=False):
    text = copy_component(439694000, ident, obj)
    settings = {
        'm_text': json.dumps(content, ensure_ascii=True),
        'm_fontAsset': '{fileID: 11400000, guid: ' + FONT + ', type: 2}',
        'm_sharedMaterial': '{fileID: 2180264, guid: ' + FONT + ', type: 2}',
        'm_fontSize': size, 'm_fontSizeBase': size, 'm_fontSizeMin': size, 'm_fontSizeMax': size,
        'm_fontColor': '{r: %s, g: %s, b: %s, a: %s}' % color,
        'm_HorizontalAlignment': align, 'm_VerticalAlignment': 512,
        'm_fontStyle': 1 if bold else 0, 'm_RaycastTarget': 0,
        'm_TextWrappingMode': 1, 'm_lineSpacing': 4,
    }
    for key, value in settings.items():
        text = field(text, key, value)
    return text


def label(name, parent, content, x=0, y=0, w=600, h=60, size=36, color=(.15, .12, .09, 1), align=2, bold=False, anchor=(.5, .5)):
    tr, cr, txt = new_id(), new_id(), new_id()
    obj = go(name, [tr, cr, txt])
    rect(tr, obj, parent, x, y, w, h, anchor=anchor)
    new_blocks.append(copy_component(1823533, cr, obj))
    new_blocks.append(tmp_component(txt, obj, content, size, color, align, bold))
    return obj, tr


def button(name, parent, content, y, color=(.16, .29, .24, 1), width=340):
    obj, tr, im = image(name, parent, y=y, w=width, h=80, color=color)
    ident = new_id()
    # Add Button to the GameObject just created.
    for i, text in enumerate(new_blocks):
        if text.startswith('--- !u!1 &' + str(obj) + '\n'):
            new_blocks[i] = text.replace('  m_Layer:', f'  - component: {{fileID: {ident}}}\n  m_Layer:', 1)
            break
    new_blocks.append(f'''--- !u!114 &{ident}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {obj}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {BUTTON_GUID}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: UnityEngine.UI::UnityEngine.UI.Button
  m_Navigation:
    m_Mode: 0
    m_WrapAround: 0
    m_SelectOnUp: {{fileID: 0}}
    m_SelectOnDown: {{fileID: 0}}
    m_SelectOnLeft: {{fileID: 0}}
    m_SelectOnRight: {{fileID: 0}}
  m_Transition: 1
  m_Colors:
    m_NormalColor: {{r: 1, g: 1, b: 1, a: 1}}
    m_HighlightedColor: {{r: 1.22, g: 1.22, b: 1.22, a: 1}}
    m_PressedColor: {{r: 0.75, g: 0.75, b: 0.75, a: 1}}
    m_SelectedColor: {{r: 1, g: 1, b: 1, a: 1}}
    m_DisabledColor: {{r: 0.5, g: 0.5, b: 0.5, a: 0.5}}
    m_ColorMultiplier: 1
    m_FadeDuration: 0.1
  m_SpriteState:
    m_HighlightedSprite: {{fileID: 0}}
    m_PressedSprite: {{fileID: 0}}
    m_SelectedSprite: {{fileID: 0}}
    m_DisabledSprite: {{fileID: 0}}
  m_AnimationTriggers:
    m_NormalTrigger: Normal
    m_HighlightedTrigger: Highlighted
    m_PressedTrigger: Pressed
    m_SelectedTrigger: Selected
    m_DisabledTrigger: Disabled
  m_Interactable: 1
  m_TargetGraphic: {{fileID: {im}}}
  m_OnClick:
    m_PersistentCalls:
      m_Calls: []
''')
    label(name + '_Label', tr, content, w=width-20, h=68, size=32, color=(.97, .94, .85, 1), bold=True)
    return obj


def canvas(name, order):
    tr, ca, sc, ray = new_id(), new_id(), new_id(), new_id()
    obj = go(name, [tr, ca, sc, ray], active=False)
    rect(tr, obj, w=0, h=0, anchor=(0, 0))
    for source, ident in [(237565379, ca), (237565378, sc), (237565377, ray)]:
        text = copy_component(source, ident, obj)
        if source == 237565379:
            text = field(text, 'm_SortingOrder', order)
        if source == 237565378:
            text = field(text, 'm_MatchWidthOrHeight', .5)
        new_blocks.append(text)
    return obj, tr


help_canvas, help_tr = canvas('InstructionsCanvas', 20)
over_canvas, over_tr = canvas('GameOverCanvas', 30)

# Move the user's Introduce hierarchy into the separate instructions Canvas.
info = block(1823531).replace('  - {fileID: 1137695676}\n', '')
edit(1823531, info)
intro = field(block(1137695676), 'm_Father', '{fileID: ' + str(help_tr) + '}')
for key, value in [('m_AnchorMin', '{x: 0, y: 0}'), ('m_AnchorMax', '{x: 1, y: 1}'),
                   ('m_AnchoredPosition', '{x: 0, y: 0}'), ('m_SizeDelta', '{x: 0, y: 0}')]:
    intro = field(intro, key, value)
edit(1137695676, intro)
children[help_tr].append(1137695676)
dim = field(block(1137695677), 'm_Color', '{r: 0.035, g: 0.055, b: 0.05, a: 0.82}')
edit(1137695677, dim)

# Keep the user's parchment sprite; render it first behind all text.
paper_rect = block(348978918)
paper_rect = field(paper_rect, 'm_AnchoredPosition', '{x: 0, y: 0}')
paper_rect = field(paper_rect, 'm_SizeDelta', '{x: 1250, y: 800}')
edit(348978918, paper_rect)
edit(348978919, field(block(348978919), 'm_RaycastTarget', 0))
background = field(block(156328693), 'm_SizeDelta', '{x: 1100, y: 720}')
background = background.replace('  - {fileID: 439693999}\n  - {fileID: 348978918}', '  - {fileID: 348978918}\n  - {fileID: 439693999}')
edit(156328693, background)
title_rect = field(block(439693999), 'm_AnchoredPosition', '{x: 0, y: 270}')
title_rect = field(title_rect, 'm_SizeDelta', '{x: 1000, y: 80}')
edit(439693999, title_rect)
edit(439694000, tmp_component(439694000, 439693998, 'HƯỚNG DẪN CHƠI', size=54, bold=True))
label('Introduction', 156328693, 'ARCHER SURVIVAL\nSống sót trong khu rừng. Dùng cung để hạ kẻ địch!', y=180, w=1000, h=100, size=29)
for y, key, description in [(65, 'A / D', 'Di chuyển sang trái / phải'), (-15, 'SPACE', 'Nhảy qua địa hình'), (-95, 'J', 'Kéo cung và bắn mũi tên')]:
    _, keytr, _ = image('Key_' + key.replace(' / ', '_'), 156328693, x=-330, y=y, w=180, h=60, color=(.18, .22, .17, 1), raycast=False)
    label('KeyLabel', keytr, key, w=175, h=54, size=28, color=(1, .95, .8, 1), bold=True)
    label('Action_' + key.replace(' / ', '_'), 156328693, description, x=150, y=y, w=650, h=64, size=31, align=1)
label('HelpTip', 156328693, 'Bạn có 20 máu. Tránh đòn đánh và giữ khoảng cách với enemy.', y=-185, w=1020, h=65, size=26)
close_button = button('CloseHelpButton', 156328693, 'ĐÓNG  [ K ]', -280)

# Add a compact reminder to the existing HUD.
label('HelpHint_K', 237565380, '[ K ]  Hướng dẫn', x=-220, y=-48, w=390, h=60, size=29,
      color=(.08, .18, .17, 1), bold=True, anchor=(1, 1))

_, shade_tr, _ = image('DimBackground', over_tr, color=(.025, .045, .04, .86), stretch=True)
_, card_tr, _ = image('GameOverPanel', shade_tr, w=960, h=580, color=(.075, .12, .11, 1))
image('TopAccent', card_tr, y=289, w=960, h=5, color=(.75, .42, .28, 1), raycast=False)
label('GameName', card_tr, 'ARCHER SURVIVAL', y=196, size=29, color=(.75, .81, .65, 1), bold=True)
label('GameOverTitle', card_tr, 'GAME OVER', y=80, w=850, h=125, size=98, color=(.98, .87, .64, 1), bold=True)
label('GameOverMessage', card_tr, 'Bạn đã hết máu. Hãy thử lại một lần nữa!', y=-26, w=850, h=75, size=32, color=(.84, .88, .82, 1))
restart_button = button('PlayAgainButton', card_tr, 'CHƠI LẠI', -153, color=(.52, .27, .17, 1), width=390)
label('RestartNote', card_tr, 'Bắt đầu lại với 20 máu', y=-230, size=25, color=(.65, .73, .67, 1))

# An always-active manager receives keyboard/button/death events.
manager_tr, manager_vars, manager_machine = new_id(), new_id(), new_id()
manager = go('GameUIManager', [manager_tr, manager_vars, manager_machine], layer=0)
transform = copy_component(1788435026, manager_tr, manager)
new_blocks.append(transform)


class Graph:
    def __init__(self, title):
        self.title, self.nodes, self.edges, self.groups = title, [], [], []
        self.index = 10

    def node(self, unit_kind, x, y, **extra):
        i = str(self.index)
        self.index += 1
        self.nodes.append({**extra, 'defaultValues': extra.get('defaultValues', {}),
                           'position': {'x': x, 'y': y}, 'guid': uid(), '$version': 'A',
                           '$type': 'Unity.VisualScripting.' + unit_kind, '$id': i})
        return i

    def edge(self, kind, a, ak, b, bk):
        self.edges.append({'sourceUnit': {'$ref': a}, 'sourceKey': ak, 'destinationUnit': {'$ref': b},
                           'destinationKey': bk, 'guid': uid(), '$type': 'Unity.VisualScripting.' + kind + 'Connection'})

    def flow(self, a, ak, b, bk='enter'):
        self.edge('Control', a, ak, b, bk)

    def data(self, a, ak, b, bk):
        self.edge('Value', a, ak, b, bk)

    def get(self, name, x, y, target=None):
        i = self.node('GetVariable', x, y, kind='Object', specifyFallback=False,
                      defaultValues={'name': typed(name, 'System.String'), 'object': None})
        if target:
            self.data(target, 'value', i, 'object')
        return i

    def active(self, name, value, x, y):
        target = self.get(name, x, y+200)
        n = self.node('InvokeMember', x+300, y, chainable=False, parameterNames=['value'],
                      member={'name': 'SetActive', 'parameterTypes': ['System.Boolean'], 'targetType': 'UnityEngine.GameObject', 'targetTypeName': 'UnityEngine.GameObject', '$version': 'A'},
                      defaultValues={'target': None, **({'%value': typed(value, 'System.Boolean')} if value is not None else {})})
        self.data(target, 'value', n, 'target')
        return n

    def timescale(self, value, x, y):
        return self.node('SetMember', x, y, chainable=False,
                         member={'name': 'timeScale', 'parameterTypes': None, 'targetType': 'UnityEngine.Time', 'targetTypeName': 'UnityEngine.Time', '$version': 'A'},
                         defaultValues={'input': typed(value)})

    def group(self, name, x, y, w, h, comment, color=(.13, .22, .21)):
        self.groups.append({'position': {'xMin': x, 'yMin': y, 'xMax': x+w, 'yMax': y+h},
                            'label': name, 'comment': comment, 'color': dict(zip(['r','g','b','a'], [*color,1])),
                            'guid': uid(), '$version': 'A', '$type': 'Unity.VisualScripting.GraphGroup'})

    def save(self, name):
        graph = {'variables': {'Kind': 'Flow', 'collection': {'$content': [], '$version': 'A'}, '$version': 'A'},
                 'controlInputDefinitions': [], 'controlOutputDefinitions': [], 'valueInputDefinitions': [], 'valueOutputDefinitions': [],
                 'title': self.title, 'summary': None, 'pan': {'x': 150, 'y': 150}, 'zoom': .35,
                 'elements': self.nodes+self.edges+self.groups, '$version': 'A'}
        text = health_text.split('  _data:\n')[0].replace('m_Name: PlayerHealth', 'm_Name: '+name)
        text += "  _data:\n    _json: '" + json.dumps({'graph': graph}, ensure_ascii=True, separators=(',', ':')).replace("'", "''") + "'\n    _objectReferences: []\n"
        path = ROOT / ('Assets/Script/'+name+'.asset')
        assert not path.exists()
        path.write_text(text, encoding='utf-8')
        guid = uuid.uuid4().hex
        Path(str(path)+'.meta').write_text('fileFormatVersion: 2\nguid: '+guid+'\nNativeFormatImporter:\n  externalObjects: {}\n  mainObjectFileID: 11400000\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n', encoding='utf-8')
        return guid


g = Graph('Game UI - Game Over, Play Again, Huong dan K')
start = g.node('Start', 0, 0, coroutine=False)
reset_time = g.timescale(1.0, 320, 0)
hide_help = g.active('HelpCanvas', False, 650, 0)
hide_over = g.active('GameOverCanvas', False, 1300, 0)
g.flow(start, 'trigger', reset_time, 'assign'); g.flow(reset_time, 'assigned', hide_help); g.flow(hide_help, 'exit', hide_over)
g.group('01 | BAT DAU - AN HAI CANVAS', -70, -80, 2050, 650, 'On Start: timeScale = 1; HelpCanvas va GameOverCanvas SetActive False.')

update = g.node('Update', 0, 950, coroutine=False)
key = g.node('InvokeMember', 0, 1200, chainable=False, parameterNames=['key'],
             member={'name': 'GetKeyDown', 'parameterTypes': ['UnityEngine.KeyCode'], 'targetType': 'UnityEngine.Input', 'targetTypeName': 'UnityEngine.Input', '$version': 'A'},
             defaultValues={'%key': typed('K', 'UnityEngine.KeyCode')})
key_if = g.node('If', 350, 950)
player = g.get('Player', 350, 1300)
dead = g.get('isDead', 650, 1300, player)
dead_if = g.node('If', 700, 950)
help_ref = g.get('HelpCanvas', 1000, 1400)
active = g.node('GetMember', 1300, 1400,
                member={'name': 'activeSelf', 'parameterTypes': None, 'targetType': 'UnityEngine.GameObject', 'targetTypeName': 'UnityEngine.GameObject', '$version': 'A'}, defaultValues={'target': None})
negate = g.node('Negate', 1600, 1400)
toggle = g.active('HelpCanvas', None, 1050, 950)
opened_if = g.node('If', 1750, 950)
pause = g.timescale(0.0, 2100, 950)
resume = g.timescale(1.0, 2100, 1250)
g.data(key, 'result', key_if, 'condition');g.data(dead, 'value', dead_if, 'condition')
g.flow(update, 'trigger', key_if);g.flow(key_if, 'ifTrue', dead_if);g.flow(dead_if, 'ifFalse', toggle)
g.data(help_ref,'value',active,'target');g.data(active,'value',negate,'input');g.data(negate,'output',toggle,'%value')
g.flow(toggle,'exit',opened_if);g.data(active,'value',opened_if,'condition')
g.flow(opened_if,'ifTrue',pause,'assign');g.flow(opened_if,'ifFalse',resume,'assign')
g.group('02 | PHIM K - BAT / TAT HUONG DAN', -70, 850, 2550, 1000, 'Chi cho phep khi Player.isDead=False. SetActive = NOT activeSelf. Mo thi timeScale=0; dong thi timeScale=1.')

close_ref = g.get('CloseHelpButton', 0, 2250)
close = g.node('OnButtonClick', 350, 2050, coroutine=False, defaultValues={'target': None})
close_help = g.active('HelpCanvas', False, 700, 2050)
close_resume = g.timescale(1.0, 1400, 2050)
g.data(close_ref,'value',close,'target');g.flow(close,'trigger',close_help);g.flow(close_help,'exit',close_resume,'assign')
g.group('03 | BUTTON DONG HUONG DAN', -70, 1950, 2050, 650, 'On Button Click (CloseHelpButton) -> an HelpCanvas -> timeScale=1.')

death = g.node('CustomEvent', 0, 2900, argumentCount=0, coroutine=False, defaultValues={'target':None,'name':typed('PlayerDied','System.String')})
death_hide = g.active('HelpCanvas', False, 350, 2900)
death_show = g.active('GameOverCanvas', True, 1050, 2900)
death_pause = g.timescale(0.0, 1750, 2900)
g.flow(death,'trigger',death_hide);g.flow(death_hide,'exit',death_show);g.flow(death_show,'exit',death_pause,'assign')
g.group('04 | PLAYER CHET - HIEN GAME OVER', -70, 2800, 2300, 650, 'Nhan PlayerDied tu PlayerHealth: dong huong dan, hien GameOverCanvas, tam dung game.', (.3,.14,.12))

restart_ref = g.get('RestartButton', 0, 3900)
restart = g.node('OnButtonClick', 350, 3650, coroutine=False, defaultValues={'target':None})
restart_resume = g.timescale(1.0, 750, 3650)
load = g.node('InvokeMember', 1150, 3650, chainable=False, parameterNames=['sceneName'],
              member={'name':'LoadScene','parameterTypes':['System.String'],'targetType':'UnityEngine.SceneManagement.SceneManager','targetTypeName':'UnityEngine.SceneManagement.SceneManager','$version':'A'},
              defaultValues={'%sceneName':typed('SampleScene','System.String')})
g.data(restart_ref,'value',restart,'target');g.flow(restart,'trigger',restart_resume,'assign');g.flow(restart_resume,'assigned',load)
g.group('05 | BUTTON CHOI LAI - LOAD SAMPLESCENE', -70, 3550, 2050, 650, 'Tra timeScale=1 truoc khi LoadScene SampleScene. PlayerHealth On Start dat lai mau = maxHealth (20).', (.19,.2,.32))
ui_guid = g.save('GameUIManager')

manager_component = copy_component(1852861732462757729, manager_machine, manager)
manager_component = manager_component.replace('45e090cf799c44aba44412cffda06037', ui_guid)
new_blocks.append(manager_component)
manager_data = read_data(block(1381974998))
refs = [('Player',1381974991),('HelpCanvas',help_canvas),('GameOverCanvas',over_canvas),('RestartButton',restart_button),('CloseHelpButton',close_button)]
manager_data['declarations']['collection']['$content'] = [
    {'name':name,'value':typed(i,'UnityEngine.Object'),
     'typeHandle':{'Identification':'UnityEngine.GameObject, UnityEngine.CoreModule, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null','$version':'A'},'$version':'A'}
    for i,(name,_) in enumerate(refs)]
var_text = copy_component(1381974998, manager_vars, manager)
var_text = replace_data(var_text, manager_data)
var_text = var_text.split('    _objectReferences:')[0]+'    _objectReferences:\n'+''.join('    - {fileID: '+str(obj)+'}\n'for _,obj in refs)
new_blocks.append(var_text)

# Tell the active UI manager after PlayerHealth completes its death sequence.
health = read_data(health_text)
elements = health['graph']['elements']
next_graph_id = max(int(e.get('$id',0)) for e in elements)+1
death_tail = next(e for e in elements if e.get('guid')=='4ffb931d-d5ad-4094-a63c-da330fac5e8c')['$id']
bridge = Graph('unused')
bridge.index = next_graph_id
self_ref = bridge.node('This', 0, 4100)
ui_ref = bridge.get('GameUIManager', 350, 4100)
notify = bridge.node('TriggerCustomEvent', 750, 4100, argumentCount=0,
                     defaultValues={'target':None,'name':typed('PlayerDied','System.String')})
bridge.data(self_ref,'self',ui_ref,'object');bridge.data(ui_ref,'value',notify,'target')
bridge.flow(death_tail,'assigned',notify)
bridge.group('05 | BAO UI HIEN GAME OVER', -70, 3970, 1500, 650, 'Sau khi het mau va tat dieu khien, gui PlayerDied den GameUIManager.', (.3,.14,.12))
first_edge = next(i for i,e in enumerate(elements)if e.get('$type','').endswith('Connection'))
elements[first_edge:first_edge]=bridge.nodes
elements.extend(bridge.edges+bridge.groups)
HEALTH.write_text(replace_data(health_text, health), encoding='utf-8')
player_vars = read_data(block(1381974998))
player_declarations = player_vars['declarations']['collection']['$content']
assert not any(v['name']=='GameUIManager'for v in player_declarations)
old_vars = block(1381974998)
player_refs = re.findall(r'^    - \{fileID: [^\n]+\}$',old_vars,re.M)
player_declarations.append({'name':'GameUIManager','value':typed(len(player_refs),'UnityEngine.Object'),
                            'typeHandle':{'Identification':'UnityEngine.GameObject, UnityEngine.CoreModule, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null','$version':'A'},'$version':'A'})
new_vars=replace_data(old_vars,player_vars).rstrip()+'\n    - {fileID: '+str(manager)+'}\n\n'
edit(1381974998,new_vars)

# Resolve new RectTransform child lists and append child references to existing parents.
for parent, values in children.items():
    marker = '@CHILDREN_'+str(parent)+'@'
    replacement = ('\n'+''.join('  - {fileID: '+str(v)+'}\n' for v in values).rstrip()) if values else '[]'
    if any(marker in b for b in new_blocks):
        new_blocks = [b.replace(marker,replacement) for b in new_blocks]
    elif values:
        old = block(parent)
        match=re.search(r'  m_Children:(.*?)(?=  m_Father:)',old,re.S)
        existing=match[0].replace('m_Children: []','m_Children:')
        edit(parent,old[:match.start()]+existing+''.join('  - {fileID: '+str(v)+'}\n' for v in values)+old[match.end():])

scene = scene.replace('--- !u!1660057539 &9223372036854775807', ''.join(new_blocks)+'--- !u!1660057539 &9223372036854775807',1)
scene=scene.rstrip()+'\n'+''.join('  - {fileID: '+str(i)+'}\n'for i in [help_tr,over_tr,manager_tr])
assert '@CHILDREN_' not in scene
SCENE.write_text(scene,encoding='utf-8')
manifest={'backup':str(backup),'helpCanvas':help_canvas,'helpTransform':help_tr,'gameOverCanvas':over_canvas,'gameOverTransform':over_tr,
          'manager':manager,'managerVariables':manager_vars,'managerMachine':manager_machine,'managerGraphGuid':ui_guid,
          'closeButton':close_button,'restartButton':restart_button,'importedTMPResources':imported,
          'managerNodes':len(g.nodes),'managerConnections':len(g.edges)}
(ROOT/'Backups/GameUI/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in manifest.items()if k!='importedTMPResources'},indent=2))
