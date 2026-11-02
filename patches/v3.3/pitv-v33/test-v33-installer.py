#!/usr/bin/env python3
"""Local-only regression test. No access to actual Raspberry Pi settings."""
import json, subprocess, sys, tempfile
from pathlib import Path

base=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    ext=tmp/'ext';ext.mkdir();bk=tmp/'backups'
    v32={'manifest_version':3,'name':'PiTV D-pad Navigation','version':'2.2.0',
         'description':'PiTV D-pad',
         'content_scripts':[{'matches':['https://www.netflix.com/*','https://www.youtube.com/*','https://www.disneyplus.com/*'],
                             'js':['navigation.js'],'run_at':'document_idle','all_frames':False},
                            {'matches':['https://www.netflix.com/*','https://www.disneyplus.com/*'],
                             'js':['pitv-auto-fullscreen.js'],'run_at':'document_idle','all_frames':False}],
         'background':{'service_worker':'pitv-background.js'},
         'commands':{'pitv-browser-back':{'suggested_key':{'default':'Ctrl+Shift+Y'},'description':'PiTV back'}}}
    (ext/'manifest.json').write_text(json.dumps(v32))
    (ext/'navigation.js').write_text('/* PiTV D-pad old navigation */\n')
    (ext/'pitv-background.js').write_text('/* back */\n')
    (ext/'pitv-auto-fullscreen.js').write_text('/* movie */\n')
    original={p.name:p.read_bytes() for p in ext.iterdir()}
    cmd=[sys.executable,str(base/'install-v33.py'),'--extension-dir',str(ext),'--backup-root',str(bk)]
    pre=subprocess.run(cmd+['--check'],capture_output=True,text=True)
    assert pre.returncode==0,pre.stderr
    assert {p.name:p.read_bytes() for p in ext.iterdir()}==original,'check unexpectedly changed files'
    install=subprocess.run(cmd+['--install'],capture_output=True,text=True)
    assert install.returncode==0,install.stderr
    manifest=json.loads((ext/'manifest.json').read_text())
    assert manifest['version']=='2.3.0'
    assert manifest['content_scripts'][0]['js']==['navigation-core.js','navigation.js']
    assert 'youtube' not in str(manifest['content_scripts'][0]['matches'])
    assert manifest['content_scripts'][1]==v32['content_scripts'][1]
    assert (ext/'pitv-background.js').read_bytes()==original['pitv-background.js']
    assert (ext/'pitv-auto-fullscreen.js').read_bytes()==original['pitv-auto-fullscreen.js']
    assert subprocess.run(cmd+['--install'],capture_output=True).returncode!=0,'repeat install must fail closed'
    backup=next(bk.glob('backup-*'))
    rollback=subprocess.run([sys.executable,str(base/'rollback-v33.py'),str(backup),'--extension-dir',str(ext),'--backup-root',str(bk)],capture_output=True,text=True)
    assert rollback.returncode==0,rollback.stderr
    assert {p.name:p.read_bytes() for p in ext.iterdir()}==original,'rollback differs from original'
    print('OK – installer/check/rollback/fail-closed: 11 kontroller')
