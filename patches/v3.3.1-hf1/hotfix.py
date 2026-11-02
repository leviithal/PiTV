#!/usr/bin/env python3
"""PiTV V3.3.1 Reviderad HF1: scoped update on top of installed reviderad.

Only changes D-pad navigation.js and a dedicated managed policy. Does not touch
Widevine, profile, certificates, V3 server, screen settings, or Android APK.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

BASE_SHA = '00eeddf6406d76782b44cba395b94945f5f5d3d9d65524592abaf328d4c08dab'
POLICY = b'{"TranslateEnabled": false}\n'

def digest(b): return hashlib.sha256(b).hexdigest()
def assert_ok(cond, msg):
    if not cond: raise RuntimeError(msg)

def is_system_path(path):
    return path == Path('/etc/chromium/policies/managed/pitv-translate-disabled.json')

def policy_write(target, payload):
    if is_system_path(target):
        with tempfile.NamedTemporaryFile(mode='wb',delete=False) as t:
            t.write(payload);temp=t.name
        try:
            subprocess.run(['sudo','install','-D','-m','0644',temp,str(target)],check=True)
        finally:
            Path(temp).unlink(missing_ok=True)
    else:
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(payload)
        target.chmod(0o644)

def policy_remove(target):
    if is_system_path(target): subprocess.run(['sudo','rm','--',str(target)],check=True)
    else: target.unlink()

def nav_write(target, payload, mode):
    dest=target.with_name('.'+target.name+'.pitv-hf1-'+str(os.getpid()))
    try:
        dest.write_bytes(payload);dest.chmod(mode)
        os.replace(dest,target)
    finally:dest.unlink(missing_ok=True)

def main():
    aparser=argparse.ArgumentParser()
    group=aparser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check',action='store_true')
    group.add_argument('--install',action='store_true')
    group.add_argument('--rollback',type=Path,metavar='BACKUP_FOLDER')
    aparser.add_argument('--ext-dir',type=Path,default=Path.home()/'pi-tv/dpad-extension')
    aparser.add_argument('--policy-file',type=Path,default=Path('/etc/chromium/policies/managed/pitv-translate-disabled.json'))
    aparser.add_argument('--backup-root',type=Path,default=Path.home()/'pi-tv-v331-hf1-backups')
    a=aparser.parse_args()
    assert_ok(os.geteuid()!=0,'Kör som vanlig användare (utan sudo).')
    ext=a.ext_dir.expanduser().resolve()
    policy=a.policy_file.expanduser().absolute()
    backup_root=a.backup_root.expanduser().resolve()
    nav=ext/'navigation.js'
    manifest=ext/'manifest.json'
    patched=Path(__file__).resolve().parent/'navigation.js'
    assert_ok(manifest.is_file() and nav.is_file(),'PiTV tillägg saknas.')
    version=json.loads(manifest.read_text(encoding='utf-8')).get('version')
    assert_ok(version=='2.3.1','Kräver redan installerad V3.3.1 Reviderad (manifest 2.3.1); hittade '+str(version))
    assert_ok(patched.is_file(),'Paketet saknar navigation.js')
    newbytes=patched.read_bytes()
    assert_ok(b'PiTV 3.3.1 Reviderad HF1' in newbytes,'Fel navigationskälla')
    if shutil.which('node'):
        subprocess.run(['node','--check',str(patched)],check=True)

    if a.rollback:
        b=a.rollback.expanduser().resolve()
        assert_ok(b.parent==backup_root and b.name.startswith('backup-'),'Fel backupkatalog')
        assert_ok((b/'record.json').is_file(),'Backupmetadata saknas')
        r=json.loads((b/'record.json').read_text(encoding='utf-8'))
        assert_ok(r.get('release')=='v3.3.1-reviderad-hf1','Fel backupversion')
        old=(b/'navigation.js').read_bytes()
        assert_ok(digest(old)==r['old_sha'],'Originalbackup har ändrats')
        assert_ok(digest(nav.read_bytes())==r['new_sha'],'Installerad navigationsfil har ändrats, avbryter')
        assert_ok(policy.is_file() and policy.read_bytes()==POLICY,'Policy har ändrats/saknas, avbryter')
        nav_write(nav,old,r['old_mode'])
        policy_remove(policy)
        (b/'restored').write_text('Restored reviderad RC1\n',encoding='utf-8')
        print('Återställd till V3.3.1 Reviderad (inte V3.2). Kör sudo reboot.')
        return

    old=nav.read_bytes()
    assert_ok(digest(old)==BASE_SHA,'navigation.js matchar inte original V3.3.1 Reviderad. Inga ändringar.')
    assert_ok(not policy.exists(),f'Policyfilen finns redan: {policy}. Gör ingen automatisk överskrivning.')
    print('OK: V3.3.1 Reviderad igenkänd, navigation.js verifierad.')
    print('Ändringar: navigation.js + systempolicy för Chromium Translate.')
    print('Obs: Netflix automatisk Play är best-effort; reserv: fokusera Play och tryck OK igen.')
    if a.check:
        print('Förkontroll klar, ingenting ändrat.')
        return

    backup_root.mkdir(parents=True,exist_ok=True,mode=0o700)
    b=backup_root/('backup-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+str(os.getpid()))
    b.mkdir(mode=0o700)
    (b/'navigation.js').write_bytes(old)
    old_mode=stat.S_IMODE(nav.stat().st_mode)
    rec={'release':'v3.3.1-reviderad-hf1','old_sha':digest(old),'new_sha':digest(newbytes),
        'old_mode':old_mode, 'policy_path':str(policy)}
    (b/'record.json').write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8')
    policy_created=False
    try:
        policy_write(policy,POLICY)
        policy_created=True
        assert_ok(policy.read_bytes()==POLICY,'Policy kunde inte verifieras efter skrivning')
        nav_write(nav,newbytes,old_mode)
        assert_ok(digest(nav.read_bytes())==digest(newbytes),'Navigation ändrades inte som tänkt')
    except BaseException:
        try:nav_write(nav,old,old_mode)
        finally:
            if policy_created and policy.exists() and policy.read_bytes()==POLICY:
                policy_remove(policy)
        raise
    print('KLART. Backup:',b)
    print('Starta om: sudo reboot')
    print('Verifiera i Chromium: chrome://policy -> TranslateEnabled = false')
    print('Återställ hotfix till 3.3.1 Reviderad:')
    print('python3 ~/pitv-v331-hf1/hotfix.py --rollback "'+str(b)+'"')

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('AVBRÖT:',e,file=sys.stderr)
        sys.exit(1)
