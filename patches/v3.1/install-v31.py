#!/usr/bin/env python3
"""PiTV V3.1: safe, reversible Back/navigation and Chromium kiosk improvement.

Never touches Chromium profile, Widevine, tokens/certificates, Android APK.
Copies known files first; aborts on unexpected versions instead of guessing.
"""
from __future__ import annotations
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

HOME=Path.home()
SERVER=HOME/'pi-tv-v3/server.py'
START=HOME/'pi-tv/start.sh'
EXT=HOME/'pi-tv/dpad-extension'
MANIFEST=EXT/'manifest.json'
BG=EXT/'pitv-background.js'
SENTINEL='PiTV V3.1: Chrome extension navigation via chrome.tabs.goBack'
OLD_BACK="run('wtype','-M','alt','-k','Left','-m','alt')"
NEW_BACK="run('wtype','-M','ctrl','-M','shift','-k','y','-m','shift','-m','ctrl')"
BACKGROUND='''// PiTV V3.1: Browser-history Back; never synthesizes Left in Netflix.\nchrome.commands.onCommand.addListener((command) => {\n  if (command !== 'pitv-browser-back') return;\n  chrome.tabs.query({active: true, currentWindow: true})\n    .then((tabs) => {\n      const tab = tabs[0];\n      if (!tab || typeof tab.id !== 'number') return;\n      return chrome.tabs.goBack(tab.id);\n    })\n    .catch((error) => console.warn('PiTV Back:', error.message));\n});\n'''

def sha(data:bytes)->str: return hashlib.sha256(data).hexdigest()
def fail(msg:str): raise RuntimeError(msg)
def main():
    if os.geteuid()==0: fail('Kör som användaren pi, INTE sudo.')
    for path in (SERVER,START,MANIFEST):
        if not path.is_file(): fail(f'Kan inte hitta {path}. Inga ändringar gjorda.')
    if BG.exists(): fail(f'{BG.name} finns redan. Avbryter för att undvika konflikt.')

    server_src=SERVER.read_text(encoding='utf-8')
    start_src=START.read_text(encoding='utf-8')
    manifest_src=MANIFEST.read_text(encoding='utf-8')
    if server_src.count(OLD_BACK)!=1: fail('Känner inte igen Back-kommandot i V3-servern. Ingen ändring gjord.')
    if start_src.count('--start-fullscreen')!=1: fail('Känner inte igen start.sh:s fullscreen-flagga. Ingen ändring gjord.')
    if '--kiosk' in start_src: fail('Kiosk-läge verkar redan vara konfigurerat. Avbryter.')
    manifest=json.loads(manifest_src)
    if manifest.get('manifest_version') != 3: fail('Tillägget är inte Manifest V3. Avbryter.')
    if 'commands' in manifest or 'background' in manifest: fail('Tillägget har redan shortcuts/bakgrundsprocess. Avbryter.')
    if not (EXT/'navigation.js').exists(): fail('navigation.js saknas. Ingen ändring gjord.')
    if 'dpad-extension' not in start_src: fail('start.sh verkar inte ladda PiTV-tillägget. Avbryter.')

    new_server=server_src.replace(OLD_BACK,NEW_BACK,1)
    new_server=new_server.replace("elif action == 'back':\n", f"elif action == 'back':\n        # {SENTINEL}\n",1)
    new_start=start_src.replace('--start-fullscreen', '--kiosk --start-maximized',1)
    manifest['background']={'service_worker':BG.name}
    manifest['commands']={'pitv-browser-back':{'suggested_key':{'default':'Ctrl+Shift+Y'},
                       'description':'PiTV: tillbaka en sida i webbläsarhistoriken'}}
    manifest['version']='2.1.0'
    new_manifest=json.dumps(manifest,indent=2,ensure_ascii=False)+'\n'
    ast.parse(new_server,filename=str(SERVER))
    json.loads(new_manifest)
    # Optional syntax validation before touching user files
    if shutil.which('node'):
        cp=subprocess.run(['node','--check','-'],input=BACKGROUND,text=True,capture_output=True)
        if cp.returncode!=0: fail(f'JavaScript syntaxfel: {cp.stderr[:200]}')

    backups_root=HOME/'pi-tv-v31-backups'
    backups_root.mkdir(mode=0o700,exist_ok=True)
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    backup=backups_root/f'backup-{stamp}-{os.getpid()}'
    backup.mkdir(mode=0o700)
    originals={'server.py':SERVER,'start.sh':START,'manifest.json':MANIFEST}
    for name,path in originals.items(): shutil.copy2(path,backup/name)
    (backup/'checksums-before.txt').write_text(''.join(f'{name}  {sha((backup/name).read_bytes())}\n' for name in originals),encoding='utf-8')

    replacements=[(SERVER,new_server),(START,new_start),(MANIFEST,new_manifest),(BG,BACKGROUND)]
    created=[]
    try:
        for path,data in replacements:
            had=path.exists()
            mode=stat.S_IMODE(path.stat().st_mode) if had else 0o644
            tmp=path.with_name('.'+path.name+'.pitv31-tmp')
            with tmp.open('w',encoding='utf-8',newline='\n') as out: out.write(data)
            tmp.chmod(mode)
            os.replace(tmp,path)
            if not had: created.append(path)
        subprocess.run(['bash','-n',str(START)],check=True,capture_output=True)
        ast.parse(SERVER.read_text(encoding='utf-8'))
        assert json.loads(MANIFEST.read_text(encoding='utf-8'))['commands']['pitv-browser-back']
    except BaseException:
        for name,path in originals.items(): shutil.copy2(backup/name,path)
        for path in created: path.unlink(missing_ok=True)
        raise

    print('\nPiTV V3.1 installerad. Inga hemligheter eller Chromium-profiler ändrade.')
    print(f'Säkerhetskopia: {backup}')
    print('Nu: sudo reboot')
    print('Återställning vid problem:')
    print(f'  bash ~/rollback-v31.sh "{backup}"')

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('AVBRÖT: '+str(exc),file=sys.stderr)
        sys.exit(1)
