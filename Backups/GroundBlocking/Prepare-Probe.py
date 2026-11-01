from pathlib import Path
import json
import re
import uuid

ROOT = Path(r'D:\GamePrograms\MidTestExam')
source = (ROOT/'Backups/GameUI/Create-GameUI.py').read_text(encoding='utf-8')
health_text = (ROOT/'Assets/Script/PlayerHealth.asset').read_text(encoding='utf-8')


def uid():
    return str(uuid.uuid4())


def typed(v, kind='System.Single'):
    return {'$content':v,'$type':kind}


exec(source[source.index('class Graph:'):source.index("g = Graph('Game UI")])
g=Graph('Temporary ground obstruction probe - no C#')


def log(value, key):
    n=g.node('InvokeMember',0,0,chainable=False,parameterNames=['message'],member={'name':'Log','parameterTypes':['System.Object'],'targetType':'UnityEngine.Debug','targetTypeName':'UnityEngine.Debug','$version':'A'})
    g.data(value,key,n,'%message')
    return n


def message(text):
    n=g.node('Literal',0,0,type='System.String',value=typed(text,'System.String'))
    return log(n,'output')


def set_running(value):
    n=g.node('SetVariable',0,0,kind='Object',defaultValues={'object':None,'name':typed('probeRunning','System.String')})
    v=g.node('Literal',0,0,type='System.Boolean',value=typed(value,'System.Boolean'))
    g.data(v,'output',n,'input')
    return n


def snapshot(previous, port, label):
    marker=message('GROUND_BLOCK_'+label)
    position=g.node('GetMember',0,0,member={'name':'position','parameterTypes':None,'targetType':'UnityEngine.Transform','targetTypeName':'UnityEngine.Transform','$version':'A'},defaultValues={'target':None})
    output=log(position,'value')
    g.flow(previous,port,marker);g.flow(marker,'exit',output)
    return output


start=g.node('Start',0,0,coroutine=False)
initial=set_running(False);g.flow(start,'trigger',initial,'assign')
settle=g.node('Timer',0,0,defaultValues={'duration':typed(.5),'unscaledTime':typed(False,'System.Boolean')});g.flow(initial,'assigned',settle,'start')
first=snapshot(settle,'completed','START')
run=set_running(True);g.flow(first,'exit',run,'assign')
last,port=run,'assigned'
for idx,duration in enumerate([.75,.75,1.0]):
    timer=g.node('Timer',0,0,defaultValues={'duration':typed(duration),'unscaledTime':typed(False,'System.Boolean')})
    g.flow(last,port,timer,'start')
    last=snapshot(timer,'completed','SAMPLE_'+str(idx+1));port='exit'
stop=set_running(False);g.flow(last,port,stop,'assign')
stop_v=g.node('SetMember',0,0,chainable=False,member={'name':'linearVelocityX','parameterTypes':None,'targetType':'UnityEngine.Rigidbody2D','targetTypeName':'UnityEngine.Rigidbody2D','$version':'A'},defaultValues={'target':None,'input':typed(0.0)})
g.flow(stop,'assigned',stop_v,'assign')
update=g.node('Update',0,0,coroutine=False);active=g.get('probeRunning',0,0);check=g.node('If',0,0)
drive=g.node('SetMember',0,0,chainable=False,member={'name':'linearVelocityX','parameterTypes':None,'targetType':'UnityEngine.Rigidbody2D','targetTypeName':'UnityEngine.Rigidbody2D','$version':'A'},defaultValues={'target':None,'input':typed(7.0)})
g.data(active,'value',check,'condition');g.flow(update,'trigger',check);g.flow(check,'ifTrue',drive,'assign')
collision=g.node('OnCollisionEnter2D',0,0,coroutine=False,defaultValues={'target':None})
name=g.node('GetMember',0,0,member={'name':'name','parameterTypes':None,'targetType':'UnityEngine.Object','targetTypeName':'UnityEngine.Object','$version':'A'},defaultValues={'target':None})
g.data(collision,'collider',name,'target')
hit=message('GROUND_BLOCK_COLLISION');name_log=log(name,'value');g.flow(collision,'trigger',hit);g.flow(hit,'exit',name_log)
guid=g.save('_GroundBlockingProbe')

scene=(ROOT/'Assets/Scenes/SampleScene.unity').read_text(encoding='utf-8')


def edit(ident,fn):
    global scene
    m=re.search(r'^--- !u!\d+ &'+str(ident)+r'\n.*?(?=^--- !u!|\Z)',scene,re.M|re.S)
    assert m
    scene=scene[:m.start()]+fn(m[0])+scene[m.end():]


edit(1381974994,lambda b:re.sub(r'^  m_LocalPosition:.*','  m_LocalPosition: {x: 83.2, y: -1.0, z: 0}',b,count=1,flags=re.M))
edit(1060966857,lambda b:b.replace('  m_IsActive: 1','  m_IsActive: 0',1))
edit(1381974997,lambda b:b.replace('  m_Enabled: 1','  m_Enabled: 0',1))
probe_machine=690000000000000001
edit(1381974991,lambda b:b.replace('  m_Layer:',f'  - component: {{fileID: {probe_machine}}}\n  m_Layer:',1))
m=re.search(r'^--- !u!114 &1852861732462757729\n.*?(?=^--- !u!|\Z)',scene,re.M|re.S)
component=m[0].replace('&1852861732462757729','&'+str(probe_machine),1).replace('45e090cf799c44aba44412cffda06037',guid)
scene=scene.replace('--- !u!1660057539 &9223372036854775807',component+'--- !u!1660057539 &9223372036854775807',1)
target=ROOT/'Assets/Scenes/_GroundBlockingVerification.unity';assert not target.exists()
target.write_text(scene,encoding='utf-8')
Path(str(target)+'.meta').write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\nDefaultImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n',encoding='utf-8')
print('Prepared temporary Visual Scripting physics probe at X=83.2. Enemies disabled only in temporary scene.')
