#!/usr/bin/env python3
"""Build an installable LoxBerry ZIP without local config or test files."""
import configparser
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('bin', 'config', 'icons', 'templates', 'webfrontend')
FILES = ('plugin.cfg', 'preinstall.sh', 'preupgrade.sh', 'postinstall.sh', 'README.md', 'CLI.md')


def build(destination=None):
    cfg = configparser.ConfigParser()
    cfg.read(ROOT / 'plugin.cfg')
    version = cfg['PLUGIN']['VERSION']
    target = Path(destination) if destination else ROOT / 'dist' / ('EvaStream-' + version + '.zip')
    target.parent.mkdir(parents=True, exist_ok=True)
    paths = [ROOT / f for f in FILES]
    for folder in DIRECTORIES:
        paths.extend(p for p in (ROOT / folder).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix != '.pyc'
                     and p.name != 'settings.json')
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            name = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(name, (2026, 9, 10, 0, 0, 0))
            info.create_system = 3
            mode = 0o755 if path.suffix in ('.sh', '.py') else 0o644
            info.external_attr = (0o100000 | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    print(target)
    return target


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else None)
