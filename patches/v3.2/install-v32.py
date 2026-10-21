#!/usr/bin/env python3
"""PiTV 3.2 experimental automatic video fullscreen; reversible; never touches Widevine."""
from __future__ import annotations
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path.home() / 'pi-tv' / 'dpad-extension'
MANIFEST = ROOT / 'manifest.json'
TARGET = ROOT / 'pitv-auto-fullscreen.js'
POLICY = Path('/etc/chromium/policies/managed/pitv-automatic-fullscreen.json')
POLICY_DATA = {
    'AutomaticFullscreenAllowedForUrls': [
        'https://www.netflix.com',
        'https://www.disneyplus.com',
    ]
}
FILENAME = 'pitv-auto-fullscreen.js'


def run(args):
    subprocess.run(args, check=True)


def main():
    if os.geteuid() == 0: raise RuntimeError('Kör med vanlig användare (inte sudo).')
    source = Path(__file__).resolve().with_name(FILENAME)
    if not MANIFEST.is_file() or not source.is_file():
        raise RuntimeError('Hittar inte V3.1-tillägget eller videomodulen.')
    if TARGET.exists() or POLICY.exists():
        raise RuntimeError('V3.2 verkar redan finnas. Avbryter så inget skrivs över.')
    if not (Path.home() / 'pi-tv' / 'dpad-extension' / 'pitv-background.js').is_file():
        raise RuntimeError('PiTV V3.1-tilläggets bakgrundsfil saknas. Avbryter.')
    original = MANIFEST.read_bytes()
    manifest = json.loads(original)
    if manifest.get('manifest_version') != 3 or 'pitv-browser-back' not in manifest.get('commands',{}):
        raise RuntimeError('V3.1:s Bakåt-funktion känns inte igen. Ingen ändring.')
    cs = manifest.get('content_scripts')
    if not isinstance(cs,list) or not any('navigation.js' in x.get('js',[]) for x in cs):
        raise RuntimeError('PiTV D-pad-skriptet saknas i manifestet. Ingen ändring.')
    cs.append({'matches': ['https://www.netflix.com/*', 'https://www.disneyplus.com/*'],
               'js':[FILENAME], 'run_at':'document_idle', 'all_frames':False})
    manifest['version'] = '2.2.0'
    patched = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    check = subprocess.run(['node','--check',str(source)], capture_output=True, text=True) if shutil.which('node') else None
    if check is not None and check.returncode: raise RuntimeError('JavaScript-syntaxfel: ' + check.stderr)
    print('V3.2 ger endast Netflix och Disney+ möjlighet att öppna film i helskärm automatiskt.')
    print('Detta är en experimentell funktion som kan behöva återställas om undertexter/spelargränssnitt påverkas.')
    print('Lokal Chrome-policy kommer att kräva sudo för installation. Inga API-nycklar ändras.')
    # Request permission early, before mutating any files.
    run(['sudo','-v'])
    backup_root = Path.home() / 'pi-tv-v32-backups'
    backup_root.mkdir(mode=0o700,exist_ok=True)
    backup = backup_root / ('backup-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + str(os.getpid()))
    backup.mkdir(mode=0o700)
    (backup / 'manifest.json').write_bytes(original)
    (backup / 'new-manifest-sha256').write_text(hashlib.sha256(patched).hexdigest() + '\n', encoding='ascii')
    (backup / 'policy-sha256').write_text(
        hashlib.sha256((json.dumps(POLICY_DATA,sort_keys=True,indent=2)+'\n').encode()).hexdigest()+'\n',encoding='ascii')
    policy_bytes = (json.dumps(POLICY_DATA,sort_keys=True,indent=2)+'\n').encode('utf-8')
    created = False
    try:
        shutil.copy2(source,TARGET)
        TARGET.chmod(0o644)
        temp = MANIFEST.with_name('.manifest-pitv32-temp.json')
        temp.write_bytes(patched)
        os.replace(temp,MANIFEST)
        # Managed policy lives under /etc, root-owned, not writable by pi.
        with tempfile.NamedTemporaryFile('wb',delete=False,prefix='pitv-v32-policy-') as fp:
            fp.write(policy_bytes)
            policy_tmp=fp.name
        try:
            run(['sudo','install','-d','-m','0755',str(POLICY.parent)])
            run(['sudo','install','-m','0644',policy_tmp,str(POLICY)])
            created=True
        finally:
            Path(policy_tmp).unlink(missing_ok=True)
    except BaseException:
        MANIFEST.write_bytes(original)
        TARGET.unlink(missing_ok=True)
        if created: subprocess.run(['sudo','rm','-f',str(POLICY)], check=False)
        raise
    (backup/'installed').write_text('installed\n',encoding='ascii')
    print('\nPiTV 3.2 installerad (experimentell). Säkerhetskopia:',backup)
    print('Starta om Raspberry Pi: sudo reboot')
    print('Kontrollera chrome://policy -> AutomaticFullscreenAllowedForUrls')
    print('Återställ: python3 ~/rollback-v32.py ' + str(backup))

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('AVBRÖT: '+str(exc),file=sys.stderr)
        sys.exit(1)
