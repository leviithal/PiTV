"""Isolated dry-run using real OpenSSL and fake sudo/systemd: no changes to host /etc."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

FILE=Path(__file__).resolve().parents[1]/'installer/install-v331-stable.py'
spec=importlib.util.spec_from_file_location('pitv_v331_installer',FILE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        h=Path(self.tmp.name)
        self.patches=[]
        for attr,val in {
            'HOME':h,'PI':h/'pi-tv','API':h/'pi-tv-v3',
            'AUTOSTART':h/'.config/labwc/autostart',
            'SERVICE':h/'.config/systemd/user/pitv-v3.service',
            'POLICY':h/'etc/chromium/policies/managed/pitv-v331-stable.json',
            'BACKUPS':h/'PiTV-backups',
        }.items():
            p=patch.object(mod,attr,val);p.start();self.patches.append(p)
        for target, ret in [(mod.os,'geteuid'),(mod.platform,'machine'),(mod.shutil,'which')]:
            pass
        p=patch.object(mod.os,'geteuid',return_value=1000);p.start();self.patches.append(p)
        p=patch.object(mod.platform,'machine',return_value='aarch64');p.start();self.patches.append(p)
        p=patch.object(mod.shutil,'which',side_effect=lambda c:'/usr/bin/'+c);p.start();self.patches.append(p)
        p=patch.object(mod,'local_ip',return_value='192.168.1.99');p.start();self.patches.append(p)
        self.autostart=mod.AUTOSTART
        self.autostart.parent.mkdir(parents=True)
        self.autostart.write_text('# preexisting personal autostart\n')
        self.old=self.autostart.read_bytes()
        self.backups=[]
        def fake_run(*args,**kwargs):
            if args[0]=='sudo':
                if args[1]=='-v':return subprocess.CompletedProcess(args,0)
                if args[1]=='install':
                    dst=Path(args[-1]);dst.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(args[-2],dst)
                    return subprocess.CompletedProcess(args,0)
                if args[1]=='rm':
                    Path(args[-1]).unlink(missing_ok=True)
                    return subprocess.CompletedProcess(args,0)
            if args[0]=='systemctl':return subprocess.CompletedProcess(args,0)
            if args[0]=='hostname':return subprocess.CompletedProcess(args,0,stdout='192.168.1.99')
            return subprocess.run(args,check=True,**kwargs)
        p=patch.object(mod,'run',side_effect=fake_run);p.start();self.patches.append(p)
        p=patch.object(mod.subprocess,'run',side_effect=self.safe_subprocess);p.start();self.patches.append(p)
        # The fake subprocess uses original subprocess module call stored below.
        self.system=None
    def safe_subprocess(self,args,*a,**k):
        # This path only handles best-effort sudo raspi-config and systemctl service stop.
        if args[0]=='sudo' and len(args)>1 and args[1]=='rm':
            Path(args[-1]).unlink(missing_ok=True)
            return subprocess.CompletedProcess(args,0)
        if args[0] in ('sudo','systemctl'):return subprocess.CompletedProcess(args,0)
        return REAL_RUN(args,*a,**k)
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()
    def test_install_and_rollback(self):
        self.assertEqual(mod.preflight(),'192.168.1.99')
        with patch('builtins.input',return_value='INSTALL'):
            mod.install()
        self.assertTrue((mod.PI/'dpad-extension/navigation-core.js').exists())
        self.assertTrue((mod.API/'api-token').exists())
        self.assertEqual((mod.API/'api-token').stat().st_mode & 0o777,0o600)
        self.assertTrue((mod.API/'tls-cert.pem').exists())
        self.assertTrue(mod.POLICY.exists())
        self.assertIn('TranslateEnabled',mod.POLICY.read_text())
        self.assertTrue(mod.SERVICE.exists())
        self.assertIn(mod.BEGIN,mod.AUTOSTART.read_text())
        self.assertTrue((mod.API/'server.py').read_text().find("'ctrl','-M','shift'")>=0)
        backups=list(mod.BACKUPS.iterdir())
        self.assertEqual(len(backups),1)
        with self.assertRaises(RuntimeError):mod.preflight()  # cannot overwrite
        with patch('builtins.input',return_value='ROLLBACK'):
            mod.rollback(backups[0])
        self.assertEqual(self.autostart.read_bytes(),self.old)
        self.assertFalse(mod.SERVICE.exists())
        self.assertFalse(mod.POLICY.exists())
        self.assertTrue((backups[0]/'pi-tv-v3-retained/api-token').exists())
        self.assertFalse(mod.PI.exists())
    def test_readonly_and_fail_closed(self):
        self.assertEqual(mod.preflight(),'192.168.1.99')
        self.assertFalse(mod.PI.exists())
        mod.PI.mkdir()
        with self.assertRaises(RuntimeError):mod.preflight()

REAL_RUN=subprocess.run
if __name__=='__main__':unittest.main()
