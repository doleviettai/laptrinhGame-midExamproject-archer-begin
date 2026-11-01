from pathlib import Path
import re

root = Path(r'D:\GamePrograms\MidTestExam')
source = root / 'Assets/Scenes/SampleScene.unity'
target = root / 'Assets/Scenes/_GolemCameraVerification.unity'
assert not target.exists(), 'Verification scene already exists; inspect first.'
scene = source.read_text(encoding='utf-8')


def edit_block(file_id, fn):
    global scene
    match = re.search(r'^--- !u!\d+ &' + str(file_id) + r'\n.*?(?=^--- !u!|\Z)', scene, re.M | re.S)
    assert match
    scene = scene[:match.start()] + fn(match[0]) + scene[match.end():]


# Both Golems start beyond the Player camera's right edge (about X=8.9).
# Place them on the same existing raised ground, using the original Enemy parent.
for file_id, x in [('738191893', 15 - 8.82743), ('752946047', 18 - 8.82743)]:
    edit_block(file_id, lambda block, x=x: re.sub(r'  m_LocalPosition: [^\n]+', f'  m_LocalPosition: {{x: {x:.5f}, y: 1.1081, z: 0}}', block))
for file_id in ['1348700410', '126313114']:
    edit_block(file_id, lambda block: block.replace('  m_IsActive: 1', '  m_IsActive: 0'))
target.write_text(scene, encoding='utf-8')
print('Created temporary camera-verification scene; SampleScene was not edited.')
