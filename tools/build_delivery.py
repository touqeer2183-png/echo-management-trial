"""Build a clean installation ZIP without accounts, patient data or backups."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build():
    target = ROOT / 'dist' / 'AFZAL_HEART_CENTRE_MEDITECH_REVIEWED.zip'
    target.parent.mkdir(exist_ok=True)
    files = [ROOT / name for name in (
        'server.py', 'START ECHO.bat', 'README.md', 'UPGRADE.md',
        'requirements.txt', '_HANDOVER.md')]
    for folder in ('backend', 'public', 'tests'):
        files.extend(p for p in (ROOT / folder).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts
                     and p.suffix not in ('.pyc', '.pyo'))
    files.append(Path(__file__).resolve())
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('AFZAL_HEART_CENTRE_ECHO_SYSTEM/data/', '')
        for path in sorted(files):
            archive.write(path, 'AFZAL_HEART_CENTRE_ECHO_SYSTEM/' + path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert not any(name.endswith(('.sqlite3', '.sqlite3-wal', '.sqlite3-shm')) for name in names)
        assert not any('/backups/' in name or '/artifacts/' in name for name in names)
    print(target)
    return target


if __name__ == '__main__':
    build()
