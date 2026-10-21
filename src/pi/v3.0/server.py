#!/usr/bin/env python3
"""PiTV V3: independent, authenticated HTTPS remote for a trusted home LAN.

No secret appears in request URLs, arguments or routine logs. Do not expose 8766 to WAN.
"""
import hmac
import json
import logging
import os
import re
import ssl
import subprocess
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path.home() / 'pi-tv-v3'
PORT = int(os.environ.get('PITV_PORT', '8766'))
BIND = os.environ.get('PITV_BIND', '0.0.0.0')
LOCK = threading.Lock()
LIMIT_LOCK = threading.Lock()
REQUESTS = defaultdict(deque)
KEYS = {'up':'Up','down':'Down','left':'Left','right':'Right','ok':'Return',
        'esc':'Escape','space':'space','focus':'F9'}
ACTIONS = set(KEYS) | {'back','volumeup','volumedown','mute','move','click',
                        'scrollup','scrolldown','type'}

def run(*argv):
    try:
        proc = subprocess.run(argv, timeout=4, check=False,
                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.TimeoutExpired:
        raise RuntimeError('Kommandot tog för lång tid') from None
    except OSError:
        raise RuntimeError('Saknar kommando eller åtkomst') from None
    if proc.returncode != 0:
        # Never echo arguments or raw stderr into API/logs.
        raise RuntimeError('Kommando misslyckades (exit %d)' % proc.returncode)

def focus_browser():
    # Best effort; all key commands attempt focus. Window focus is not UI acknowledgment.
    for target in ('app_id:chromium', 'app_id:chromium-browser', 'chromium'):
        try:
            proc = subprocess.run(('wlrctl','toplevel','focus',target), timeout=2,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                  check=False)
            if proc.returncode == 0:
                return True
        except (OSError, subprocess.SubprocessError):
            pass
    return False

def handle_action(payload):
    action = payload.get('action')
    if action not in ACTIONS:
        raise ValueError('Okänt kommando')
    focused = None
    if action in KEYS or action in ('back','type'):
        focused = focus_browser()
    if action in KEYS:
        run('wtype','-k',KEYS[action])
    elif action == 'back':
        run('wtype','-M','alt','-k','Left','-m','alt')
    elif action == 'type':
        value = payload.get('value')
        if not isinstance(value,str) or not 1 <= len(value) <= 140 or any(ord(c) < 32 for c in value):
            raise ValueError('Text måste vara 1–140 vanliga tecken')
        run('wtype','-d','15','--',value)
    elif action == 'move':
        def delta(name):
            v=payload.get(name,0)
            if isinstance(v,bool) or not isinstance(v,int):
                raise ValueError('Felaktig pekarrörelse')
            return max(-160,min(160,v))
        run('wlrctl','pointer','move',str(delta('dx')),str(delta('dy')))
    elif action == 'click':
        run('wlrctl','pointer','click')
    elif action == 'scrollup':
        run('wlrctl','pointer','scroll','-80','0')
    elif action == 'scrolldown':
        run('wlrctl','pointer','scroll','80','0')
    elif action == 'volumeup':
        run('wpctl','set-volume','-l','1.0','@DEFAULT_AUDIO_SINK@','5%+')
    elif action == 'volumedown':
        run('wpctl','set-volume','@DEFAULT_AUDIO_SINK@','5%-')
    elif action == 'mute':
        run('wpctl','set-mute','@DEFAULT_AUDIO_SINK@','toggle')
    return {'ok':True,'command':'sent','focus_confirmed':focused,
            'screen_confirmed':False}

def within_limit(ip):
    now=time.monotonic()
    with LIMIT_LOCK:
        events=REQUESTS[ip]
        while events and now-events[0]>1.0:
            events.popleft()
        if len(events)>=45:
            return False
        events.append(now)
        # Avoid unbounded IP history; local LAN with limited callers.
        if len(REQUESTS)>512:
            for k in list(REQUESTS):
                if not REQUESTS[k] or now-REQUESTS[k][-1]>60:
                    del REQUESTS[k]
        return True

def browser_running():
    try:
        cp=subprocess.run(('pgrep','-u',str(os.getuid()),'-x','chromium'),
                          timeout=2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return cp.returncode==0
    except (OSError, subprocess.SubprocessError):
        return False

class Handler(BaseHTTPRequestHandler):
    server_version='PiTV/3.0'
    sys_version=''
    def log_message(self, fmt, *args):
        # Only path-free metrics: never log Bearer header, URLs, user payload or token.
        logging.info('client=%s request_status=%s', self.client_address[0], args[1] if len(args)>1 else '-')
    def reply(self, status, data):
        body=json.dumps(data,ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):pass
    def allowed(self):
        if not within_limit(self.client_address[0]):
            self.reply(429,{'ok':False,'error':'För många kommandon'})
            return False
        provided=self.headers.get('Authorization','')
        token=(ROOT/'api-token').read_text(encoding='ascii').strip()
        if not hmac.compare_digest(provided,'Bearer '+token):
            self.reply(401,{'ok':False,'error':'Ogiltig nyckel'})
            return False
        return True
    def do_GET(self):
        if self.path!='/api/status':
            self.reply(404,{'ok':False,'error':'Hittades inte'});return
        if not self.allowed():return
        self.reply(200,{'ok':True,'version':'3.0','server':'online',
                        'chromium_running':browser_running(),
                        'playback_verified':False})
    def do_POST(self):
        if self.path!='/api/action':
            self.reply(404,{'ok':False,'error':'Hittades inte'});return
        if not self.allowed():return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<2 or size>2048:raise ValueError('Felaktig meddelandestorlek')
            body=json.loads(self.rfile.read(size))
            if not isinstance(body,dict):raise ValueError('Felaktigt JSON-format')
            with LOCK:result=handle_action(body)
            self.reply(200,result)
        except (ValueError,RuntimeError,json.JSONDecodeError) as exc:
            logging.warning('command rejected or failed: %s',str(exc))
            self.reply(400,{'ok':False,'error':str(exc)})
    def do_OPTIONS(self):
        self.reply(405,{'ok':False,'error':'Inte tillåtet'})

class Server(ThreadingHTTPServer):
    daemon_threads=True
    request_queue_size=16

def main():
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    if not (ROOT/'api-token').is_file():
        raise SystemExit('api-token saknas: kör install-v3.sh')
    cert,key=ROOT/'tls-cert.pem',ROOT/'tls-key.pem'
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version=ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(str(cert),str(key))
    server=Server((BIND,PORT),Handler)
    server.socket=ctx.wrap_socket(server.socket,server_side=True)
    logging.info('PiTV V3 HTTPS start on port %d',PORT)
    server.serve_forever()

if __name__=='__main__':main()
