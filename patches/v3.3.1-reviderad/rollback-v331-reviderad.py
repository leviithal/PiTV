#!/usr/bin/env python3
"""Revert PiTV V3.3.1 Reviderad directly to backed-up V3.2.

Checksum-verifies the installed patched files and every original backup before
writing. --recover-incomplete is only for interrupted installs and still checks
that each current file equals either old or expected new contents.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


def digest(b):
    return hashlib.sha256(b).hexdigest()


def atomic(path, payload, mode):
    tmp = path.with_name('.' + path.name + '.v331r-restore-' + str(os.getpid()))
    try:
        with tmp.open('wb') as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        tmp.chmod(mode)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description='Återställ PiTV V3.3.1 Reviderad till V3.2')
    ap.add_argument('backup', type=Path)
    ap.add_argument('--extension-dir', type=Path, default=Path.home() / 'pi-tv/dpad-extension')
    ap.add_argument('--start-file', type=Path, default=Path.home() / 'pi-tv/start.sh')
    ap.add_argument('--backup-root', type=Path, default=Path.home() / 'pi-tv-v331-reviderad-backups')
    ap.add_argument('--recover-incomplete', action='store_true', help='Endast efter avbruten installation')
    a = ap.parse_args()
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        raise RuntimeError('Kör som vanlig användare, inte sudo.')
    backup = a.backup.expanduser().resolve()
    root = a.backup_root.expanduser().resolve()
    if backup.parent != root or not backup.name.startswith('backup-') or not (backup/'record.json').is_file():
        raise RuntimeError('Ogiltig backup-sökväg.')
    record = json.loads((backup/'record.json').read_text(encoding='utf-8'))
    if record.get('release') != 'PiTV V3.3.1 Reviderad' or record.get('format') != 2:
        raise RuntimeError('Backupen är inte skapad av den REVIDERADE installeraren.')
    if not a.recover_incomplete and not (backup/'installed').is_file():
        raise RuntimeError('Installation ej verifierad. Endast --recover-incomplete kan användas efter avbrott.')
    paths = {
        'manifest.json': a.extension_dir.expanduser().resolve()/'manifest.json',
        'navigation.js': a.extension_dir.expanduser().resolve()/'navigation.js',
        'start.sh': a.start_file.expanduser().resolve(),
        'navigation-core.js': a.extension_dir.expanduser().resolve()/'navigation-core.js',
    }
    old = {}
    for name, expected in record['old_sha256'].items():
        data = (backup/name).read_bytes()
        if digest(data) != expected:
            raise RuntimeError('Skadad originalbackup: ' + name)
        old[name] = data
    for name, new_hash in record['new_sha256'].items():
        path = paths[name]
        if not path.exists():
            if a.recover_incomplete and name == 'navigation-core.js':
                continue
            raise RuntimeError('Installerad fil saknas: '+name)
        present = digest(path.read_bytes())
        accepted = {new_hash}
        if a.recover_incomplete and name in record['old_sha256']:
            accepted.add(record['old_sha256'][name])
        if present not in accepted:
            raise RuntimeError('Filen har ändrats sedan installationen. Ingen rollback: ' + name)
    for name, data in old.items():
        atomic(paths[name], data, record['old_modes'][name])
    paths['navigation-core.js'].unlink(missing_ok=True)
    (backup/'installed').unlink(missing_ok=True)
    (backup/'in-progress').unlink(missing_ok=True)
    (backup/'restored').write_text('Restored V3.2\n', encoding='ascii')
    print('PiTV V3.2 återställd. Starta om med sudo reboot.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('AVBRÖT: ' + str(exc), file=sys.stderr)
        sys.exit(1)
