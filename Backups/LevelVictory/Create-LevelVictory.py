from pathlib import Path
import copy
import datetime
import json
import re
import shutil
import uuid
from PIL import Image, ImageDraw

ROOT = Path(r'D:\GamePrograms\MidTestExam')
SCENE = ROOT / 'Assets/Scenes/SampleScene.unity'
UI = ROOT / 'Assets/Script/GameUIManager.asset'
BUILD = ROOT / 'ProjectSettings/EditorBuildSettings.asset'
scene = SCENE.read_text(encoding='utf-8')
health_text = (ROOT / 'Assets/Script/PlayerHealth.asset').read_text(encoding='utf-8')
ui_text = UI.read_text(encoding='utf-8')
assert 'm_Name: FinishPoint\n' not in scene
assert not (ROOT / 'Assets/Scenes/Level2.unity').exists()
backup = ROOT / 'Backups/LevelVictory' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup.mkdir(parents=True)
for source in [SCENE, UI, BUILD]:
    shutil.copy2(source, backup / source.name)


def uid():
    return str(uuid.uuid4())


def typed(value, kind='System.Single'):
    return {'$content': value, '$type': kind}


def parse_blocks(text):
    return {int(m[2]): m[0] for m in re.finditer(r'^--- !u!(\d+) &(\d+)\n.*?(?=^--- !u!|\Z)', text, re.M | re.S)}


def block(file_id):
    return parse_blocks(scene)[int(file_id)]


def field(text, key, value):
    if key == 'm_text':
        text, count = re.subn(r'^  m_text:.*?(?=^  m_isRightToLeft:)', lambda m:'  m_text: '+str(value)+'\n',text,count=1,flags=re.M|re.S)
        assert count, key
        return text
    text, count = re.subn(r'^  '+re.escape(key)+r':[^\n]*', lambda m:'  '+key+': '+str(value), text, count=1, flags=re.M)
    assert count, key
    return text


def edit(file_id, replacement):
    global scene
    scene = scene.replace(block(file_id), replacement, 1)


def read_data(text):
    match = re.search(r"    _json: '(.*?)'\n    _objectReferences:", text, re.S)
    assert match
    return json.loads(re.sub(r'\n +',' ',match[1]).replace("''","'"))


def replace_data(text, value):
    match = re.search(r"    _json: '(.*?)'\n    _objectReferences:",text,re.S)
    payload = json.dumps(value,ensure_ascii=True,separators=(',',':')).replace("'","''")
    return text[:match.start(1)]+payload+text[match.end(1):]


source = (ROOT / 'Backups/GameUI/Create-GameUI.py').read_text(encoding='utf-8')
exec(source[source.index('class Graph:'):source.index("g = Graph('Game UI")])

# Copy the simple Game Over card to a separate Victory Canvas.
blocks = parse_blocks(scene)
next_id = 590000000000000000


def new_id():
    global next_id
    next_id += 1
    assert next_id not in blocks
    return next_id


cloned = []


def collect(gameobject):
    cloned.append(gameobject)
    components = [int(x) for x in re.findall(r'component: \{fileID: (\d+)\}', blocks[gameobject])]
    cloned.extend(components)
    transform = next(i for i in components if blocks[i].startswith(('--- !u!224','--- !u!4 &')))
    child_section = re.search(r'  m_Children:(.*?)(?=  m_Father:)',blocks[transform],re.S)[1]
    for child in re.findall(r'fileID: (\d+)',child_section):
        child_object = int(re.search(r'm_GameObject: \{fileID: (\d+)\}',blocks[int(child)])[1])
        collect(child_object)


collect(490000000000000010)
mapping = {old:new_id() for old in cloned}
new_blocks = []
for old in cloned:
    text = blocks[old]
    text = re.sub(r'^(--- !u!\d+ &)\d+',lambda m:m[1]+str(mapping[old]),text,count=1)
    text = re.sub(r'fileID: (\d+)',lambda m:'fileID: '+str(mapping.get(int(m[1]),int(m[1]))),text)
    if old == 490000000000000010:
        text = field(text,'m_Name','VictoryCanvas')
        text = field(text,'m_IsActive',0)
    if text.startswith('--- !u!223'):
        text = field(text,'m_SortingOrder',40)
    new_blocks.append(text)
victory_canvas = mapping[490000000000000010]
victory_transform = mapping[490000000000000006]


def clone_find_name(name):
    old = next(i for i,b in blocks.items() if re.search(r'^  m_Name: '+re.escape(name)+r'$',b,re.M))
    return mapping[old]


def update_new(ident, function):
    for i,text in enumerate(new_blocks):
        if re.match(r'^--- !u!\d+ &'+str(ident)+r'\n',text):
            new_blocks[i] = function(text)
            return
    raise AssertionError(ident)


def change_label(name, content, size=None):
    old_go = next(i for i,b in blocks.items() if re.search(r'^  m_Name: '+re.escape(name)+r'$',b,re.M))
    text_id = next(int(i) for i in re.findall(r'component: \{fileID: (\d+)\}',blocks[old_go]) if 'TMPro.TextMeshProUGUI' in blocks[int(i)])
    def change(text):
        text = field(text,'m_text',json.dumps(content,ensure_ascii=True))
        if size:
            text=field(text,'m_fontSize',size)
            text=field(text,'m_fontSizeBase',size)
        return text
    update_new(mapping[text_id],change)
    return mapping[text_id]


win_title_id=change_label('GameOverTitle','CHIẾN THẮNG!',76)
win_message_id=change_label('GameOverMessage','Bạn đã đến cuối khu rừng. Sẵn sàng cho màn tiếp theo!',29)
win_button_label_id=change_label('PlayAgainButton_Label','QUA MÀN MỚI')
win_note_id=change_label('RestartNote','Màn 2: Khu rừng chiều muộn',25)
next_button=clone_find_name('PlayAgainButton')
update_new(next_button,lambda t:field(t,'m_Name','NextLevelButton'))
update_new(clone_find_name('GameOverPanel'),lambda t:field(t,'m_Name','VictoryPanel'))
win_sprite_button = next(int(i)for i in re.findall(r'component: \{fileID: (\d+)\}',blocks[490000000000000095]) if 'UnityEngine.UI.Image' in blocks[int(i)])
update_new(mapping[win_sprite_button],lambda t:field(t,'m_Color','{r: 0.18, g: 0.4, b: 0.28, a: 1}'))

# Add the finish flag sprite. This is a small pixel drawing, not game logic.
flag_path = ROOT / 'Assets/Asset/FinishFlag.png'
assert not flag_path.exists()
flag_guid=uuid.uuid4().hex
flag=Image.new('RGBA',(32,64),(0,0,0,0));draw=ImageDraw.Draw(flag)
draw.rectangle((6,5,8,61),fill=(49,42,35,255));draw.rectangle((9,5,10,61),fill=(191,159,92,255))
draw.rectangle((4,1,12,7),fill=(61,49,33,255));draw.rectangle((6,2,10,5),fill=(245,215,113,255))
draw.polygon([(11,7),(29,7),(24,16),(29,25),(11,25)],fill=(35,60,43,255))
draw.polygon([(12,8),(27,8),(22,16),(27,23),(12,23)],fill=(71,171,99,255))
draw.line((13,9,13,22),fill=(153,218,123,255),width=2)
draw.rectangle((3,61,13,63),fill=(70,65,51,255));flag.save(flag_path)
meta=(ROOT/'Assets/Asset/GandalfHardcore Archer/GandalfHardcore Archer/arrow.png.meta').read_text(encoding='utf-8')
meta=re.sub(r'^guid: .*', 'guid: '+flag_guid,meta,count=1,flags=re.M)
meta=re.sub(r'  internalIDToNameTable:.*?(?=  externalObjects:)', '  internalIDToNameTable: []\n',meta,flags=re.S)
meta=meta.replace('  spriteMode: 2','  spriteMode: 1').replace('  alignment: 0','  alignment: 9',1).replace('  spritePivot: {x: 0.5, y: 0.5}','  spritePivot: {x: 0.21875, y: 0}')
meta=re.sub(r'  spriteSheet:.*?(?=  mipmapLimitGroupName:)', '''  spriteSheet:
    serializedVersion: 2
    sprites: []
    outline: []
    customData: 
    physicsShape: []
    bones: []
    spriteID: 
    internalID: 0
    vertices: []
    indices: 
    edges: []
    weights: []
    secondaryTextures: []
    spriteCustomMetadata:
      entries: []
    nameFileIdTable: {}
''',meta,flags=re.S)
Path(str(flag_path)+'.meta').write_text(meta,encoding='utf-8')

finish_transform,finish_collider,finish_renderer,finish_machine,finish_vars,finish_go=[new_id()for _ in range(6)]
new_blocks.append(f'''--- !u!1 &{finish_go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {finish_transform}}}
  - component: {{fileID: {finish_collider}}}
  - component: {{fileID: {finish_renderer}}}
  - component: {{fileID: {finish_vars}}}
  - component: {{fileID: {finish_machine}}}
  m_Layer: 0
  m_Name: FinishPoint
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
''')


def copy_component(source,ident,obj):
    text=block(source)
    text=re.sub(r'^(--- !u!\d+ &)\d+',lambda m:m[1]+str(ident),text,count=1)
    return field(text,'m_GameObject','{fileID: '+str(obj)+'}')


transform=copy_component(1788435026,finish_transform,finish_go)
transform=field(transform,'m_LocalPosition','{x: 108.5, y: -6.24, z: 0}')
new_blocks.append(transform)
collider=copy_component(738191896,finish_collider,finish_go)
collider=field(collider,'m_IsTrigger',1)
collider=field(collider,'m_Offset','{x: 0, y: 2.5}')
collider=field(collider,'m_Size','{x: 1.8, y: 6}')
new_blocks.append(collider)
renderer=copy_component(1381974993,finish_renderer,finish_go)
renderer=field(renderer,'m_Sprite','{fileID: 21300000, guid: '+flag_guid+', type: 3}')
renderer=field(renderer,'m_SortingOrder',8)
renderer=field(renderer,'m_Color','{r: 1, g: 1, b: 1, a: 1}')
new_blocks.append(renderer)

f=Graph('Diem dich - chi nhan Player')
enter=f.node('OnTriggerEnter2D',0,0,coroutine=False,defaultValues={'target':None})
other=f.node('GetMember',320,250,member={'name':'gameObject','parameterTypes':None,'targetType':'UnityEngine.Component','targetTypeName':'UnityEngine.Component','$version':'A'},defaultValues={'target':None})
compare=f.node('InvokeMember',650,250,chainable=False,parameterNames=['tag'],member={'name':'CompareTag','parameterTypes':['System.String'],'targetType':'UnityEngine.GameObject','targetTypeName':'UnityEngine.GameObject','$version':'A'},defaultValues={'target':None,'%tag':typed('Player','System.String')})
is_player=f.node('If',1000,0)
ui_ref=f.get('GameUIManager',1050,300)
completed=f.node('TriggerCustomEvent',1400,0,argumentCount=0,defaultValues={'target':None,'name':typed('LevelCompleted','System.String')})
f.data(enter,'collider',other,'target');f.data(other,'value',compare,'target');f.data(compare,'result',is_player,'condition')
f.flow(enter,'trigger',is_player);f.flow(is_player,'ifTrue',completed);f.data(ui_ref,'value',completed,'target')
f.group('01 | PLAYER CHAM CO DICH',-70,-80,1950,800,'On Trigger Enter 2D -> Compare Tag Player -> If True -> gui LevelCompleted den GameUIManager.')
finish_guid=f.save('FinishPoint')
machine=copy_component(490000000000000107,finish_machine,finish_go).replace('9508e12a031a4b989a7e7bb9570e0635',finish_guid)
new_blocks.append(machine)
variables=copy_component(490000000000000106,finish_vars,finish_go)
vd=read_data(variables);vd['declarations']['collection']['$content']=[{'name':'GameUIManager','value':typed(0,'UnityEngine.Object'),'typeHandle':{'Identification':'UnityEngine.GameObject, UnityEngine.CoreModule, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null','$version':'A'},'$version':'A'}]
variables=replace_data(variables,vd).split('    _objectReferences:')[0]+'    _objectReferences:\n    - {fileID: 490000000000000108}\n'
new_blocks.append(variables)

# Extend the shared UI graph; preserve existing nodes and connections.
ui=read_data(ui_text);elements=ui['graph']['elements']
all_nodes={e['$id']:e for e in elements if '$id'in e}
by_guid={e.get('guid'):e for e in elements}
g=Graph('unused');g.index=max(map(int,all_nodes))+1

# Start: hide the third Canvas and reset Object hasWon.
start_tail=next(e for e in elements if e.get('guid')=='925550d8-f49a-40e5-8082-f9f1b9633f17')
start_tail['label']='01 | BAT DAU - AN CAC CANVAS'
start_tail['comment']='timeScale=1; an huong dan, Game Over va Chien thang; hasWon=False.'
hide_win=g.active('VictoryCanvas',False,2200,0)
false_literal=g.node('Literal',2850,250,type='System.Boolean',value=typed(False,'System.Boolean'))
reset_win=g.node('SetVariable',2850,0,kind='Object',defaultValues={'name':typed('hasWon','System.String'),'object':None})
g.data(false_literal,'output',reset_win,'input')
g.flow('15','exit',hide_win);g.flow(hide_win,'exit',reset_win,'assign')
start_tail['position']['xMax']=3400

# K remains disabled after winning, so closing help cannot resume a completed game.
won_check=g.get('hasWon',2800,1350)
won_if=g.node('If',2800,950)
old_help_edge=next(e for e in elements if e.get('$type','').endswith('ControlConnection')and e['sourceUnit']=={'$ref':'21'}and e['sourceKey']=='ifFalse')
old_help_edge['destinationUnit']={'$ref':won_if}
g.data(won_check,'value',won_if,'condition');g.flow(won_if,'ifFalse','26')
help_group=next(e for e in elements if e.get('guid')=='69fade09-fcd2-4d31-b9ae-472cce4d4295')
help_group['position']['xMax']=3300
help_group['comment']='Chi nhan K khi Player.isDead=False va hasWon=False. Mo/An HelpCanvas va tam dung/tiep tuc.'

# Retry the active scene, including Level2.
active_scene=g.node('InvokeMember',700,4300,chainable=False,parameterNames=[],member={'name':'GetActiveScene','parameterTypes':[],'targetType':'UnityEngine.SceneManagement.SceneManager','targetTypeName':'UnityEngine.SceneManagement.SceneManager','$version':'A'})
scene_name=g.node('GetMember',1100,4300,member={'name':'name','parameterTypes':None,'targetType':'UnityEngine.SceneManagement.Scene','targetTypeName':'UnityEngine.SceneManagement.Scene','$version':'A'})
g.data(active_scene,'result',scene_name,'target');g.data(scene_name,'value','44','%sceneName')
retry=next(e for e in elements if e.get('guid')=='d11f44ef-8c12-4de2-addc-96fb9f801a01')
retry['position']['yMax']=4650;retry['label']='05 | CHOI LAI - LOAD SCENE HIEN TAI'
retry['comment']='timeScale=1 -> LoadScene(GetActiveScene.name). Man 2 chet thi choi lai dung man 2.'

win_event=g.node('CustomEvent',0,5000,argumentCount=0,coroutine=False,defaultValues={'target':None,'name':typed('LevelCompleted','System.String')})
player=g.get('Player',0,5450)
dead=g.get('isDead',350,5450,player)
dead_if=g.node('If',400,5000)
won=g.get('hasWon',700,5450)
won_if2=g.node('If',800,5000)
true_literal=g.node('Literal',1100,5450,type='System.Boolean',value=typed(True,'System.Boolean'))
set_won=g.node('SetVariable',1200,5000,kind='Object',defaultValues={'name':typed('hasWon','System.String'),'object':None})
g.data(true_literal,'output',set_won,'input')
win_help=g.active('HelpCanvas',False,1550,5000)
win_over=g.active('GameOverCanvas',False,2250,5000)
win_show=g.active('VictoryCanvas',True,2950,5000)
controls=g.get('PlayerControls',0,6050,player)
disable_controls=g.node('SetMember',400,5800,chainable=False,member={'name':'enabled','parameterTypes':None,'targetType':'Unity.VisualScripting.ScriptMachine','targetTypeName':'Unity.VisualScripting.ScriptMachine','$version':'A'},defaultValues={'target':None,'input':typed(False,'System.Boolean')})
velocity=g.node('SetMember',800,5800,chainable=False,member={'name':'linearVelocity','parameterTypes':None,'targetType':'UnityEngine.Rigidbody2D','targetTypeName':'UnityEngine.Rigidbody2D','$version':'A'},defaultValues={'target':None,'input':{'x':0,'y':0,'$type':'UnityEngine.Vector2'}})
pause=g.timescale(0.0,1200,5800)
g.flow(win_event,'trigger',dead_if);g.data(dead,'value',dead_if,'condition');g.flow(dead_if,'ifFalse',won_if2)
g.data(won,'value',won_if2,'condition');g.flow(won_if2,'ifFalse',set_won,'assign')
g.flow(set_won,'assigned',win_help);g.flow(win_help,'exit',win_over);g.flow(win_over,'exit',win_show)
g.flow(win_show,'exit',disable_controls,'assign');g.data(controls,'value',disable_controls,'target')
g.flow(disable_controls,'assigned',velocity,'assign');g.data(player,'value',velocity,'target');g.flow(velocity,'assigned',pause,'assign')
g.group('06 | DEN DICH - CHIEN THANG',-70,4900,3700,1550,'LevelCompleted -> neu con song va chua thang -> hasWon=True -> hien VictoryCanvas -> dung Player va timeScale=0.',(.16,.3,.19))

next_ref=g.get('NextLevelButton',0,7000)
next_click=g.node('OnButtonClick',350,6750,coroutine=False,defaultValues={'target':None})
next_resume=g.timescale(1.0,750,6750)
next_name=g.get('NextScene',1000,7100)
next_load=g.node('InvokeMember',1150,6750,chainable=False,parameterNames=['sceneName'],member={'name':'LoadScene','parameterTypes':['System.String'],'targetType':'UnityEngine.SceneManagement.SceneManager','targetTypeName':'UnityEngine.SceneManagement.SceneManager','$version':'A'},defaultValues={'%sceneName':typed('Level2','System.String')})
g.data(next_ref,'value',next_click,'target');g.flow(next_click,'trigger',next_resume,'assign');g.flow(next_resume,'assigned',next_load)
g.data(next_name,'value',next_load,'%sceneName')
g.group('07 | BUTTON QUA MAN MOI',-70,6650,2100,850,'On Button Click NextLevelButton -> timeScale=1 -> LoadScene(Object NextScene).',(.17,.25,.32))
first_edge=next(i for i,e in enumerate(elements)if e.get('$type','').endswith('Connection'))
elements[first_edge:first_edge]=g.nodes;elements.extend(g.edges+g.groups)
UI.write_text(replace_data(ui_text,ui),encoding='utf-8')

# Scene-specific links for the shared UI graph.
manager_id=490000000000000106
manager_vars=read_data(block(manager_id));decls=manager_vars['declarations']['collection']['$content']
old_vars=block(manager_id);refs=re.findall(r'^    - (\{fileID: [^\n]+\})$',old_vars,re.M)
for name,obj in [('VictoryCanvas',victory_canvas),('NextLevelButton',next_button)]:
    index=len(refs);refs.append('{fileID: '+str(obj)+'}')
    decls.append({'name':name,'value':typed(index,'UnityEngine.Object'),'typeHandle':{'Identification':'UnityEngine.GameObject, UnityEngine.CoreModule, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null','$version':'A'},'$version':'A'})
for name,value,kind in [('hasWon',False,'System.Boolean'),('NextScene','Level2','System.String')]:
    decls.append({'name':name,'value':typed(value,kind),'typeHandle':{'Identification':kind+', mscorlib, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089','$version':'A'},'$version':'A'})
new_vars=replace_data(old_vars,manager_vars).split('    _objectReferences:')[0]+'    _objectReferences:\n'+''.join('    - '+r+'\n'for r in refs)
edit(manager_id,new_vars)
scene=scene.replace('--- !u!1660057539 &9223372036854775807',''.join(new_blocks)+'--- !u!1660057539 &9223372036854775807',1)
scene=scene.rstrip()+'\n  - {fileID: '+str(victory_transform)+'}\n  - {fileID: '+str(finish_transform)+'}\n'

# Keep a small stage label next to the K reminder.
scene_blocks=parse_blocks(scene)
hint_go=next(i for i,b in scene_blocks.items()if 'm_Name: HelpHint_K\n'in b)
hint_text=next(int(i)for i in re.findall(r'component: \{fileID: (\d+)\}',scene_blocks[hint_go])if'TMPro.TextMeshProUGUI'in scene_blocks[int(i)])
old_hint=block(hint_text)
edit(hint_text,field(old_hint,'m_text',json.dumps('MÀN 1  |  [ K ] Hướng dẫn',ensure_ascii=True)))
SCENE.write_text(scene,encoding='utf-8')

# A playable second scene using the same terrain, different enemy placement and atmosphere.
level2=scene


def level2_edit(ident,fn):
    global level2
    b=parse_blocks(level2)[ident];level2=level2.replace(b,fn(b),1)


def nextscene_value(text):
    d=read_data(text)
    next(v for v in d['declarations']['collection']['$content']if v['name']=='NextScene')['value']=typed('SampleScene','System.String')
    return replace_data(text,d)


level2_edit(manager_id,nextscene_value)
level2_edit(hint_text,lambda b:field(b,'m_text',json.dumps('MÀN 2  |  [ K ] Hướng dẫn',ensure_ascii=True)))
for ident,content in [(win_title_id,'HOÀN THÀNH!'),(win_message_id,'Bạn đã vượt qua cả hai màn của Archer Survival.'),(win_button_label_id,'VỀ MÀN 1'),(win_note_id,'Cảm ơn bạn đã chơi!')]:
    level2_edit(ident,lambda b,content=content:field(b,'m_text',json.dumps(content,ensure_ascii=True)))
ground_block=parse_blocks(scene)[1439194137]
ground_cells=[tuple(map(int,c))for c in re.findall(r'- first: \{x: (-?\d+), y: (-?\d+), z: (-?\d+)\}',ground_block)]
for ident,world_x in [(1348700411,26),(752946047,72),(738191893,93)]:
    tile_x=int(world_x-.06)
    top=max(y for x,y,z in ground_cells if x==tile_x)+1-.24
    local_x=world_x-8.82743
    local_y=top+3+.9081
    position='{x: %.5f, y: %.5f, z: 0}'%(local_x,local_y)
    level2_edit(ident,lambda b,position=position:field(b,'m_LocalPosition',position))
for ident,color in [(1325086281,'{r: 0.78, g: 0.82, b: 0.94, a: 1}'),(769330803,'{r: 0.86, g: 0.9, b: 1, a: 1}'),(1506077063,'{r: 0.8, g: 0.85, b: 0.97, a: 1}')]:
    level2_edit(ident,lambda b,color=color:field(b,'m_Color',color))
level2_guid=uuid.uuid4().hex
(ROOT/'Assets/Scenes/Level2.unity').write_text(level2,encoding='utf-8')
(ROOT/'Assets/Scenes/Level2.unity.meta').write_text('fileFormatVersion: 2\nguid: '+level2_guid+'\nDefaultImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n',encoding='utf-8')
build=BUILD.read_text(encoding='utf-8')
assert 'Assets/Scenes/Level2.unity'not in build
build=build.replace('  m_configObjects:', '  - enabled: 1\n    path: Assets/Scenes/Level2.unity\n    guid: '+level2_guid+'\n  m_configObjects:',1)
BUILD.write_text(build,encoding='utf-8')
manifest={'backup':str(backup),'finishPoint':finish_go,'finishTransform':finish_transform,'finishCollider':finish_collider,'finishGraphGuid':finish_guid,
          'victoryCanvas':victory_canvas,'victoryTransform':victory_transform,'nextButton':next_button,'level2Guid':level2_guid,
          'flagGuid':flag_guid,'finishPosition':[108.5,-6.24,0],'nextSceneLevel1':'Level2','nextSceneLevel2':'SampleScene'}
(ROOT/'Backups/LevelVictory/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest,indent=2))
