import importlib.util
import json
import os
import ssl
import subprocess
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pitv_server',HERE/'src/pi/v3.0/server.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PiTVTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        root=Path(cls.tmp.name)
        cls.token='a'*43
        (root/'api-token').write_text(cls.token+'\n')
        mod.ROOT=root
        cls.cert=root/'cert.pem';key=root/'key.pem'
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','3','-sha256',
                        '-keyout',str(key),'-out',str(cls.cert),'-subj','/CN=PiTV test',
                        '-addext','subjectAltName=IP:127.0.0.1'],
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
        cls.server=mod.Server(('127.0.0.1',0),mod.Handler)
        ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(str(cls.cert),str(key))
        cls.server.socket=ctx.wrap_socket(cls.server.socket,server_side=True)
        cls.port=cls.server.server_address[1]
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.ctx=ssl.create_default_context(cafile=str(cls.cert))
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2);cls.tmp.cleanup()
    def request(self,path,action=None,token=None):
        headers={}
        if token is not None:headers['Authorization']='Bearer '+token
        body=None
        if action is not None:
            body=json.dumps(action).encode();headers['Content-Type']='application/json'
        req=urllib.request.Request(f'https://127.0.0.1:{self.port}{path}',data=body,headers=headers,
                                   method='POST' if action is not None else 'GET')
        try:
            with urllib.request.urlopen(req,context=self.ctx,timeout=5) as r:
                return r.status,json.load(r)
        except urllib.error.HTTPError as err:
            return err.code,json.load(err)
    def test_unauthorized(self):
        self.assertEqual(self.request('/api/status')[0],401)
        self.assertEqual(self.request('/api/status',token='wrong')[0],401)
    def test_authorized_status(self):
        code,result=self.request('/api/status',token=self.token)
        self.assertEqual(code,200);self.assertEqual(result['server'],'online')
        self.assertFalse(result['playback_verified'])
    def test_commands_without_real_pitv(self):
        with patch.object(mod,'run') as runner,patch.object(mod,'focus_browser',return_value=True):
            for action,expected in [('up',('wtype','-k','Up')),
                                    ('ok',('wtype','-k','Return')),
                                    ('back',('wtype','-M','alt','-k','Left','-m','alt')),
                                    ('volumeup',('wpctl','set-volume','-l','1.0','@DEFAULT_AUDIO_SINK@','5%+'))]:
                code,result=self.request('/api/action',{'action':action},token=self.token)
                self.assertEqual(code,200);self.assertTrue(result['ok'])
                self.assertFalse(result['screen_confirmed'])
                self.assertEqual(runner.call_args.args,expected)
    def test_invalid_commands(self):
        for bad in [{'action':'shell','command':'rm -rf /'},
                    {'action':'type','value':''},
                    {'action':'type','value':'\u0000'},
                    {'action':'move','dx':'not integer'}]:
            self.assertEqual(self.request('/api/action',bad,token=self.token)[0],400)
    def test_status_does_not_leak_token(self):
        status,body=self.request('/api/status',token=self.token)
        self.assertEqual(status,200)
        self.assertNotIn(self.token,json.dumps(body))

if __name__=='__main__': unittest.main()
