from pathlib import Path
import json
import re
import uuid

root = Path(r'D:\GamePrograms\MidTestExam')
scene_path = root/'Assets/Scenes/_GolemCameraVerification.unity'
graph_path = root/'Assets/Script/_GolemCameraProbe.asset'
scene = scene_path.read_text(encoding='utf-8')
assert 'm_Name: CameraVerificationProbe\n' not in scene
nodes, edges = [], []
sequence = 10


def typed(value, kind='System.Single'):
    return {'$content': value, '$type': kind}


def node(unit_kind, **extra):
    global sequence
    i=str(sequence);sequence+=1
    nodes.append({**extra,'defaultValues':extra.get('defaultValues',{}),'position':{'x':sequence*100,'y':0},
                  'guid':str(uuid.uuid4()),'$version':'A','$type':'Unity.VisualScripting.'+unit_kind,'$id':i})
    return i


def edge(kind, a, ak, b, bk):
    edges.append({'sourceUnit':{'$ref':a},'sourceKey':ak,'destinationUnit':{'$ref':b},'destinationKey':bk,
                  'guid':str(uuid.uuid4()),'$type':'Unity.VisualScripting.'+kind+'Connection'})


def flow(a, ak, b, bk='enter'):
    edge('Control',a,ak,b,bk)


def data(a, ak, b, bk):
    edge('Value',a,ak,b,bk)


def literal(value):
    return node('Literal',type='System.String',value=typed(value,'System.String'))


def variable(name, target=None):
    i=node('GetVariable',kind='Object',specifyFallback=False,defaultValues={'object':None,'name':typed(name,'System.String')})
    if target:data(target,'value',i,'object')
    return i


def log_value(source, key):
    i=node('InvokeMember',chainable=False,parameterNames=['message'],
           member={'name':'Log','parameterTypes':['System.Object'],'targetType':'UnityEngine.Debug','targetTypeName':'UnityEngine.Debug','$version':'A'})
    data(source,key,i,'%message')
    return i


def snapshot(previous, previous_port, label):
    marker=log_value(literal('GOLEM_CAMERA_PROBE_'+label),'output')
    blue=log_value(variable('isAwake',variable('Blue')),'value')
    yellow=log_value(variable('isAwake',variable('Yellow')),'value')
    flow(previous,previous_port,marker)
    flow(marker,'exit',blue)
    flow(blue,'exit',yellow)
    return yellow


def timer(duration):
    return node('Timer',defaultValues={'duration':typed(duration),'unscaledTime':typed(False,'System.Boolean')})


def move_camera(x):
    i=node('SetMember',chainable=False,
           member={'name':'position','parameterTypes':None,'targetType':'UnityEngine.Transform','targetTypeName':'UnityEngine.Transform','$version':'A'},
           defaultValues={'target':None,'input':{'x':x,'y':0.83,'z':-10.0,'$type':'UnityEngine.Vector3'}})
    data(variable('MainCamera'),'value',i,'target')
    return i


start=node('Start',coroutine=False)
wait=timer(.5);flow(start,'trigger',wait,'start')
before=snapshot(wait,'completed','OUTSIDE_BEFORE')
camera=move_camera(11.0);flow(before,'exit',camera,'assign')
wait_visible=timer(.25);flow(camera,'assigned',wait_visible,'start')
after=snapshot(wait_visible,'completed','INSIDE_AFTER')
camera_away=move_camera(-25.0);flow(after,'exit',camera_away,'assign')
wait_away=timer(.25);flow(camera_away,'assigned',wait_away,'start')
latched=snapshot(wait_away,'completed','LATCHED_AFTER_EXIT')
done=log_value(literal('GOLEM_CAMERA_PROBE_DONE'),'output');flow(latched,'exit',done)

graph={'variables':{'Kind':'Flow','collection':{'$content':[],'$version':'A'},'$version':'A'},
       'controlInputDefinitions':[],'controlOutputDefinitions':[],'valueInputDefinitions':[],'valueOutputDefinitions':[],
       'title':'Temporary camera verification','summary':None,'pan':{'x':0,'y':0},'zoom':.1,'elements':nodes+edges,'$version':'A'}
template=(root/'Assets/Script/GolemBlueCombat.asset').read_text(encoding='utf-8').split('  _data:\n')[0]
text=template.replace('m_Name: GolemBlueCombat','m_Name: _GolemCameraProbe')+"  _data:\n    _json: '"+json.dumps({'graph':graph},separators=(',',':'))+"'\n    _objectReferences: []\n"
probe_guid=uuid.uuid4().hex
graph_path.write_text(text,encoding='utf-8')
Path(str(graph_path)+'.meta').write_text('fileFormatVersion: 2\nguid: '+probe_guid+'\nNativeFormatImporter:\n  externalObjects: {}\n  mainObjectFileID: 11400000\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n',encoding='utf-8')

# Fix the Player for this temporary test; physics and health remain present.
match=re.search(r'^--- !u!114 &1381974997\n.*?(?=^--- !u!|\Z)',scene,re.M|re.S)
assert match
scene=scene.replace(match[0],match[0].replace('  m_Enabled: 1','  m_Enabled: 0',1),1)
go,tr,machine,variables=[str(uuid.uuid4().int%(2**62)) for _ in range(4)]
component_template=re.search(r'^--- !u!114 &738191898\n.*?(?=^--- !u!|\Z)',scene,re.M|re.S)[0]
component=re.sub(r'^(--- !u!114 &)-?\d+',lambda m:m[1]+machine,component_template,count=1)
component=component.replace('m_GameObject: {fileID: 738191892}','m_GameObject: {fileID: '+go+'}')
component=re.sub(r'guid: e1cf3f5f69f186a40ac91d61232c8031', 'guid: '+probe_guid,component)
declarations=[]
for index,name in enumerate(['MainCamera','Blue','Yellow']):
    declarations.append({'name':name,'value':typed(index,'UnityEngine.Object'),
                         'typeHandle':{'Identification':'UnityEngine.GameObject, UnityEngine.CoreModule, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null','$version':'A'},'$version':'A'})
variables_data=json.dumps({'declarations':{'Kind':'Object','collection':{'$content':declarations,'$version':'A'},'$version':'A'}},separators=(',',':'))
new=f'''--- !u!1 &{go}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {tr}}}
  - component: {{fileID: {variables}}}
  - component: {{fileID: {machine}}}
  m_Layer: 0
  m_Name: CameraVerificationProbe
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &{tr}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 0}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!114 &{variables}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {go}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: e741851cba3ad425c91ecf922cc6b379, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: Unity.VisualScripting.Core::Unity.VisualScripting.Variables
  _data:
    _json: '{variables_data}'
    _objectReferences:
    - {{fileID: 519420028}}
    - {{fileID: 738191892}}
    - {{fileID: 752946046}}
'''+component
scene=scene.replace('--- !u!1660057539 &9223372036854775807',new+'--- !u!1660057539 &9223372036854775807',1)
scene=scene.rstrip()+'\n  - {fileID: '+tr+'}\n'
scene_path.write_text(scene,encoding='utf-8')
print('Temporary Visual Scripting probe prepared; shipping graphs and SampleScene unchanged.')
