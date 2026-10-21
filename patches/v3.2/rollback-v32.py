#!/usr/bin/env python3
"""Rollback only PiTV 3.2 files when checksums match; never changes Chromium profile."""
from pathlib import Path
import hashlib
import sys
import os
import json
import subprocess

ROOT=Path.home()/'pi-tv'/'dpad-extension'
MANIFEST=ROOT/'manifest.json'
MODULE=ROOT/'pitv-auto-fullscreen.js'
POLICY=Path('/etc/chromium/policies/managed/pitv-automatic-fullscreen.json')
def sha(data): return hashlib.sha256(data).hexdigest()
def main():
    if os.geteuid()==0: raise RuntimeError('Kör inte som sudo.')
    if len(sys.argv)!=2: raise RuntimeError('Använd: python3 ~/rollback-v32.py BACKUP-KATALOG')
    backup=Path(sys.argv[1]).expanduser().resolve()
    base=(Path.home()/'pi-tv-v32-backups').resolve()
    if backup.parent!=base or not (backup/'installed').is_file():
        raise RuntimeError('Ogiltig backup-katalog.')
    if sha(MANIFEST.read_bytes())!=(backup/'new-manifest-sha256').read_text().strip():
        raise RuntimeError('Manifestet är ändrat efter V3.2; avbryter för att inte skriva över nyare ändringar.')
    if not MODULE.is_file():raise RuntimeError('Videomodulen saknas; avbryter.')
    if not POLICY.is_file() or sha(POLICY.read_bytes())!=(backup/'policy-sha256').read_text().strip():
        raise RuntimeError('Policy saknas eller har ändrats; avbryter för säkerhet.')
    subprocess.run(['sudo','-v'],check=True)
    subprocess.run(['sudo','rm','--',str(POLICY)],check=True)
    MANIFEST.write_bytes((backup/'manifest.json').read_bytes())
    MODULE.unlink()
    (backup/'installed').unlink()
    print('V3.2 återställd. Starta om: sudo reboot')
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('AVBRÖT:',str(exc),file=sys.stderr);sys.exit(1)
