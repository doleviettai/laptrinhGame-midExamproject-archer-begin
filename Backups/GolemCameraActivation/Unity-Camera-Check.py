from pathlib import Path

# Reuse the local Unity Editor test helper; save this task's captures separately.
source = Path(r'D:\GamePrograms\MidTestExam\Backups\GolemYellow\Unity-Check.py').read_text(encoding='utf-8')
source = source.replace(r'Backups\GolemYellow\TestEvidence', r'Backups\GolemCameraActivation\TestEvidence')
source = source.replace("'yellow_%03d.jpg'", "'camera_%03d.jpg'")
source = source.replace('shot_number = 10', 'shot_number = 0')
exec(compile(source, '<Unity camera verification helper>', 'exec'))
