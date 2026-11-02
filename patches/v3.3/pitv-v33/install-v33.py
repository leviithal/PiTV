#!/usr/bin/env python3
"""PiTV 3.3: fail-closed, reversible Chromium D-pad upgrade.

Never changes the PiTV API, Android APK, Chromium profile, Widevine, V3.1 Back,
or V3.2 automatic video fullscreen. No sudo or network access required.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from datetime import datetime

VERSION='2.3.0'

def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

def assert_js(path: Path):
    if shutil.which('node'):
        p=subprocess.run(['node','--check',str(path)], capture_output=True,text=True)
        if p.returncode: raise RuntimeError(f'JavaScript syntaxfel i {path.name}: {p.stderr.strip()}')

def prepare(ext: Path, source: Path):
    manifest_file=ext/'manifest.json'; nav_file=ext/'navigation.js'; core_file=ext/'navigation-core.js'
    bg_file=ext/'pitv-background.js'; video_file=ext/'pitv-auto-fullscreen.js'
    required=[manifest_file,nav_file,bg_file,video_file]
    for path in required:
        if not path.is_file():raise RuntimeError(f'Filen saknas: {path}. Avbryter utan ändringar.')
    if core_file.exists():raise RuntimeError('navigation-core.js finns redan. V3.3 kan redan vara installerad. Ingen ändring.')
    old_manifest=manifest_file.read_bytes(); old_nav=nav_file.read_bytes()
    manifest=json.loads(old_manifest)
    if manifest.get('manifest_version')!=3 or manifest.get('version')!='2.2.0':
        raise RuntimeError('Förväntade tilläggsversion 2.2.0 från V3.2; fick %s. Avbryter.'%manifest.get('version'))
    if manifest.get('background',{}).get('service_worker')!='pitv-background.js':
        raise RuntimeError('V3.1:s Bakåt-funktion saknas i manifestet. Avbryter.')
    if 'pitv-browser-back' not in manifest.get('commands',{}):
        raise RuntimeError('Bakåt-genvägen saknas. Avbryter.')
    scripts=manifest.get('content_scripts',[])
    navs=[s for s in scripts if 'navigation.js' in s.get('js',[])]
    films=[s for s in scripts if 'pitv-auto-fullscreen.js' in s.get('js',[])]
    if len(navs)!=1 or len(films)!=1 or navs[0].get('js')!=['navigation.js']:
        raise RuntimeError('V3.2:s script-order matchar inte förväntat format. Avbryter.')
    if b'PiTV D-pad' not in old_nav: raise RuntimeError('Okänd äldre navigation.js. Avbryter.')
    navs[0]['js']=['navigation-core.js','navigation.js']
    navs[0]['matches']=[m for m in navs[0].get('matches',[]) if 'youtube.com' not in m.lower()]
    if not navs[0]['matches']:raise RuntimeError('Netflix/Disney+ URL-mönster saknas.')
    manifest['version']=VERSION
    manifest['description']='Directional navigation for Netflix and Disney+ in PiTV.'
    new_manifest=(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
    new_nav=(source/'navigation.js').read_bytes()
    new_core=(source/'navigation-core.js').read_bytes()
    if len(new_nav)<3000 or len(new_core)<400:raise RuntimeError('Uppdateringsfilerna verkar ofullständiga.')
    for p in (source/'navigation.js',source/'navigation-core.js'):assert_js(p)
    return {'manifest.json':old_manifest,'navigation.js':old_nav}, \
           {'manifest.json':new_manifest,'navigation.js':new_nav,'navigation-core.js':new_core}

def replace_file(path: Path, data: bytes, mode: int):
    temp=path.with_name('.'+path.name+'.pitv33-write')
    try:
        with temp.open('wb') as f:f.write(data)
        temp.chmod(mode)
        os.replace(temp,path)
    finally:temp.unlink(missing_ok=True)

def main():
    parser=argparse.ArgumentParser(description='PiTV V3.3 D-pad – säker uppgradering')
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check',action='store_true',help='Skrivskyddad kontroll')
    group.add_argument('--install',action='store_true',help='Installera efter lyckad kontroll')
    parser.add_argument('--extension-dir',type=Path,default=Path.home()/'pi-tv/dpad-extension')
    parser.add_argument('--backup-root',type=Path,default=Path.home()/'pi-tv-v33-backups')
    a=parser.parse_args()
    if hasattr(os,'geteuid') and os.geteuid()==0 and a.extension_dir==Path.home()/'pi-tv/dpad-extension':
        raise RuntimeError('Kör som vanlig Pi-användare – aldrig sudo.')
    ext=a.extension_dir.expanduser().resolve()
    source=Path(__file__).resolve().parent
    originals,updates=prepare(ext,source)
    print('PiTV V3.3 förkontroll OK. Befintliga V3.1 Bakåt och V3.2 filmhelskärm finns kvar.')
    print('Ändrar endast tillägget: navigation.js, manifest.json och ny navigation-core.js.')
    if a.check:
        print('SKRIVSKYDDAT TEST: inga filer ändrade. Kör därefter --install.');return
    backups=a.backup_root.expanduser().resolve()
    backups.mkdir(mode=0o700,parents=True,exist_ok=True)
    backup=backups/('backup-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+str(os.getpid()))
    backup.mkdir(mode=0o700)
    for name,data in originals.items():
        dest=backup/name;dest.write_bytes(data);dest.chmod(0o600)
    record={'format':1,'old':{k:sha(v) for k,v in originals.items()},
            'new':{k:sha(v) for k,v in updates.items()},'files':['manifest.json','navigation.js','navigation-core.js']}
    (backup/'record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    try:
        for name,data in updates.items():
            path=ext/name
            oldmode=stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
            replace_file(path,data,oldmode)
        assert json.loads((ext/'manifest.json').read_text())['version']==VERSION
        assert all(sha((ext/k).read_bytes())==sha(v) for k,v in updates.items())
        (backup/'installed').write_text('success\n',encoding='ascii')
    except BaseException:
        for name,data in originals.items():
            try:replace_file(ext/name,data,0o644)
            except Exception:pass
        (ext/'navigation-core.js').unlink(missing_ok=True)
        raise
    print('\nPiTV V3.3 installerad. Backup:',backup)
    print('Starta om Pi:n med: sudo reboot')
    print('Återställning vid problem:')
    print('  python3 ~/pitv-v33/rollback-v33.py "'+str(backup)+'"')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('AVBRÖT utan avsiktliga ändringar: '+str(exc),file=sys.stderr)
        sys.exit(1)
