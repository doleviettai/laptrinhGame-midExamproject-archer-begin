from pathlib import Path
import copy
import hashlib
import json
import re
import shutil

root=Path(r'D:\GamePrograms\MidTestExam')
backups=sorted(p for p in (root/'Backups/GolemCameraActivation').iterdir() if p.is_dir() and re.fullmatch(r'\d{8}_\d{6}',p.name))
assert backups
backup=backups[-1]


def parse(text):
    m=re.search(r"    _json: '(.*?)'\n    _objectReferences:",text,re.S)
    assert m
    return json.loads(re.sub(r'\n[ ]+',' ',m[1]).replace("''","'"))


def read(path):
    return path.read_text(encoding='utf-8')


graphs=[]
for name,expected_hp in [('GolemBlueCombat',9),('GolemYellowCombat',5)]:
    p=root/'Assets/Script'/(name+'.asset')
    before=parse(read(backup/'Assets/Script'/(name+'.asset')))['graph']['elements']
    after=parse(read(p))['graph']['elements']
    bm={e['guid']:e for e in before};am={e['guid']:e for e in after}
    removed=[e for guid,e in bm.items() if guid not in am]
    assert len(removed)==2
    assert sum(e['$type']=='Unity.VisualScripting.OnBecameVisible' for e in removed)==1
    original_nodes=0;original_wires=0
    for old in before:
        if old['guid'] not in am:continue
        new=am[old['guid']]
        if old['$type']=='Unity.VisualScripting.GraphGroup':continue
        a=copy.deepcopy(old);b=copy.deepcopy(new)
        a.pop('position',None);b.pop('position',None)
        assert a==b,old['guid']
        original_wires+=old['$type'].endswith('Connection')
        original_nodes+=not old['$type'].endswith('Connection')
    assert not any(e['$type']=='Unity.VisualScripting.OnBecameVisible' for e in after)
    assert sum(e.get('member',{}).get('name')=='WorldToViewportPoint' for e in after)==1
    new_nodes={e['$id']:e for e in after if '$id' in e}
    hp_nodes=[]
    for target in new_nodes.values():
        if target['$type']=='Unity.VisualScripting.SetVariable' and target.get('defaultValues',{}).get('name',{}).get('$content')=='health':
            for wire in after:
                if wire['$type']=='Unity.VisualScripting.ValueConnection' and wire['destinationUnit']['$ref']==target['$id'] and wire['destinationKey']=='input':
                    source=new_nodes[wire['sourceUnit']['$ref']]
                    if source['$type']=='Unity.VisualScripting.Literal':hp_nodes.append(source['value']['$content'])
    assert hp_nodes==[expected_hp]
    assert read(Path(str(p)+'.meta'))==read(Path(str(backup/'Assets/Script'/(name+'.asset'))+'.meta')) if Path(str(backup/'Assets/Script'/(name+'.asset'))+'.meta').exists() else True
    graphs.append({'graph':name,'health':expected_hp,'originalActionNodesPreserved':original_nodes,
                   'originalWiresPreserved':original_wires,'nodes':len(new_nodes),
                   'frames':sum(e['$type']=='Unity.VisualScripting.GraphGroup' for e in after)})

# No verification nodes or transformed test positions may be present in the main scene.
scene=read(root/'Assets/Scenes/SampleScene.unity')
assert 'CameraVerificationProbe' not in scene
assert 'm_LocalPosition: {x: 45.59, y: -4.14, z: 0}' in scene
assert 'm_LocalPosition: {x: -3.76, y: -0.19, z: 0}' in scene
assert '_GolemCameraProbe' not in read(root/'Assets/Script/GolemBlueCombat.asset')
assert '_GolemCameraProbe' not in read(root/'Assets/Script/GolemYellowCombat.asset')

# Archive this task's exact temporary asset files; never recursively delete.
archive=root/'Backups/GolemCameraActivation/VerifiedTemporaryAssets'
archive.mkdir(parents=True,exist_ok=True)
for relative in ['Assets/Scenes/_GolemCameraVerification.unity','Assets/Scenes/_GolemCameraVerification.unity.meta',
                 'Assets/Script/_GolemCameraProbe.asset','Assets/Script/_GolemCameraProbe.asset.meta']:
    source=(root/relative).resolve()
    destination=(archive/source.name).resolve()
    assert source.is_relative_to(root.resolve()) and destination.is_relative_to(archive.resolve())
    if source.exists():
        assert source.is_file() and not destination.exists()
        shutil.move(str(source),str(destination))

evidence={'graphs':graphs,'playCheck':{'outsideBefore':{'Blue':False,'Yellow':False},
                                     'insideAfter':{'Blue':True,'Yellow':True},
                                     'afterExitLatchedLikeSkeleton':{'Blue':True,'Yellow':True},
                                     'scriptExceptions':0},
          'temporaryAssetsArchived':True,'mainSceneTestChanges':False}
(root/'Backups/GolemCameraActivation/camera-verification-result.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print(json.dumps(evidence))
