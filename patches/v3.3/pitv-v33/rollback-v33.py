#!/usr/bin/env python3
"""Roll back the PiTV 3.3 D-pad patch only when its installed files still match."""
from pathlib import Path
import argparse, hashlib, json, os, stat, sys

def sha(b:bytes):return hashlib.sha256(b).hexdigest()

def write(path:Path, data:bytes, mode:int):
    tmp=path.with_name('.'+path.name+'.pitv33-restore')
    try:
        tmp.write_bytes(data);tmp.chmod(mode);os.replace(tmp,path)
    finally:tmp.unlink(missing_ok=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('backup',type=Path)
    parser.add_argument('--extension-dir',type=Path,default=Path.home()/'pi-tv/dpad-extension')
    parser.add_argument('--backup-root',type=Path,default=Path.home()/'pi-tv-v33-backups')
    a=parser.parse_args()
    backup=a.backup.expanduser().resolve();root=a.backup_root.expanduser().resolve()
    if backup.parent!=root or not backup.name.startswith('backup-') or not (backup/'installed').is_file():
        raise RuntimeError('Backup-sökvägen är inte en giltig installerad PiTV V3.3-backup.')
    ext=a.extension_dir.expanduser().resolve()
    record=json.loads((backup/'record.json').read_text(encoding='utf-8'))
    for name,expected in record['new'].items():
        target=ext/name
        if not target.is_file() or sha(target.read_bytes())!=expected:
            raise RuntimeError(f'{name} har ändrats sedan V3.3. Återställning stoppad, inget överskrivet.')
    for name,expected in record['old'].items():
        data=(backup/name).read_bytes()
        if sha(data)!=expected:raise RuntimeError('Skadad backup: '+name)
    for name in ('manifest.json','navigation.js'):
        target=ext/name;mode=stat.S_IMODE(target.stat().st_mode)
        write(target,(backup/name).read_bytes(),mode)
    (ext/'navigation-core.js').unlink()
    (backup/'installed').unlink()
    print('PiTV V3.3 återställd till V3.2 – starta om: sudo reboot')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('AVBRÖT: '+str(exc),file=sys.stderr);sys.exit(1)
