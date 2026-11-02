#!/usr/bin/env python3
"""End-to-end local preflight/install/revert regression tests (simulated PiTV V3.2)."""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile

SRC = Path(__file__).resolve().parent.parent
INSTALL = SRC/'install-v331-reviderad.py'
ROLLBACK = SRC/'rollback-v331-reviderad.py'

def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def fixture(base):
    ext=base/'dpad-extension';ext.mkdir()
    manifest={
      'manifest_version':3,'name':'PiTV D-pad Navigation','version':'2.2.0',
      'description':'PiTV D-pad Navigation',
      'content_scripts':[
        {'matches':['https://www.netflix.com/*','https://*.netflix.com/*',
                    'https://www.disneyplus.com/*','https://*.disneyplus.com/*','https://www.youtube.com/*'],
         'js':['navigation.js'],'run_at':'document_idle','all_frames':False},
        {'matches':['https://www.netflix.com/*','https://www.disneyplus.com/*'],
         'js':['pitv-auto-fullscreen.js'],'run_at':'document_idle','all_frames':False}
      ],
      'background':{'service_worker':'pitv-background.js'},
      'commands':{'pitv-browser-back':{'suggested_key':{'default':'Ctrl+Shift+Y'},'description':'PiTV back'}}
    }
    (ext/'manifest.json').write_text(json.dumps(manifest))
    (ext/'navigation.js').write_text('/* PiTV D-pad 2.2.0 */\n')
    (ext/'pitv-auto-fullscreen.js').write_text('/* automatic fullscreen from V3.2 */\n')
    (ext/'pitv-background.js').write_text('/* back from V3.1 */\n')
    start=base/'start.sh'
    start.write_text('#!/usr/bin/env bash\nchromium --load-extension="$HOME/pi-tv/dpad-extension" --kiosk --start-maximized --password-store=basic "http://localhost"\n')
    start.chmod(0o755)
    return ext,start


def invoke(script,extra,ext,start,backups):
    return subprocess.run([sys.executable,str(script),*extra,'--extension-dir',str(ext),
                           '--start-file',str(start),'--backup-root',str(backups)],
                          capture_output=True,text=True)

with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    ext,start=fixture(root)
    backups=root/'backups'
    baseline={p.name:h(p) for p in [*ext.iterdir(),start]}
    pre=invoke(INSTALL,['--check'],ext,start,backups)
    assert pre.returncode==0,pre.stderr
    assert not backups.exists(), 'read-only check must not create backups'
    assert baseline=={p.name:h(p) for p in [*ext.iterdir(),start]}, 'check modified files'
    print('PASS 1: V3.2 preflight read-only')

    install=invoke(INSTALL,['--install'],ext,start,backups)
    assert install.returncode==0,(install.stdout,install.stderr)
    record_dirs=list(backups.glob('backup-*'))
    assert len(record_dirs)==1
    backup=record_dirs[0]
    manifest=json.loads((ext/'manifest.json').read_text())
    assert manifest['version']=='2.3.1'
    assert manifest['content_scripts'][0]['js']==['navigation-core.js','navigation.js']
    assert not any('youtube' in m for m in manifest['content_scripts'][0]['matches'])
    assert manifest['content_scripts'][1]['js']==['pitv-auto-fullscreen.js']
    assert h(ext/'pitv-background.js')==baseline['pitv-background.js']
    assert h(ext/'pitv-auto-fullscreen.js')==baseline['pitv-auto-fullscreen.js']
    assert (ext/'navigation-core.js').is_file()
    assert '--disable-features=Translate --kiosk --start-maximized' in start.read_text()
    assert start.stat().st_mode & 0o111, 'start.sh must retain executable mode'
    assert (backup/'installed').exists()
    print('PASS 2: direct V3.2 -> V3.3.1 Reviderad; untouched Back/video files')

    repeat=invoke(INSTALL,['--install'],ext,start,backups)
    assert repeat.returncode!=0
    assert len(list(backups.glob('backup-*')))==1
    print('PASS 3: repeat install refused')

    # If user edits files, rollback must fail without erasing their edits.
    (ext/'navigation.js').write_text('user changed this file')
    blocked=invoke(ROLLBACK,[str(backup)],ext,start,backups)
    assert blocked.returncode!=0
    assert (ext/'navigation.js').read_text()=='user changed this file'
    print('PASS 4: altered file blocks rollback')

    # Restore deployed bytes, then rollback fully.
    (ext/'navigation.js').write_bytes((SRC/'navigation.js').read_bytes())
    rb=invoke(ROLLBACK,[str(backup)],ext,start,backups)
    assert rb.returncode==0,(rb.stdout,rb.stderr)
    assert not (ext/'navigation-core.js').exists()
    assert baseline=={p.name:h(p) for p in [*ext.iterdir(),start]}
    print('PASS 5: exact original V3.2 bytes/mode restored')

    # Unsupported 3.3 version must abort without modifications.
    manifest=json.loads((ext/'manifest.json').read_text());manifest['version']='2.3.0'
    (ext/'manifest.json').write_text(json.dumps(manifest))
    after=h(ext/'manifest.json')
    bad=invoke(INSTALL,['--check'],ext,start,backups)
    assert bad.returncode!=0 and h(ext/'manifest.json')==after
    print('PASS 6: rejects unsupported V3.3 baseline without mutation')

# interrupted transaction: only some new files updated; --recover-incomplete
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp);ext,start=fixture(root);backups=root/'backups'
    base={p.name:h(p) for p in [*ext.iterdir(),start]}
    assert invoke(INSTALL,['--install'],ext,start,backups).returncode==0
    backup=next(backups.glob('backup-*'))
    (backup/'installed').unlink()
    (backup/'in-progress').write_text('interrupted')
    (ext/'navigation.js').write_bytes((backup/'navigation.js').read_bytes())
    (ext/'navigation-core.js').unlink()
    failed=invoke(ROLLBACK,[str(backup)],ext,start,backups)
    assert failed.returncode!=0
    recovery=invoke(ROLLBACK,[str(backup),'--recover-incomplete'],ext,start,backups)
    assert recovery.returncode==0,(recovery.stdout,recovery.stderr)
    assert base=={p.name:h(p) for p in [*ext.iterdir(),start]}
    print('PASS 7: safe recovery after partial installation')
print('All 7 PiTV V3.3.1 Reviderad regression suites passed.')
