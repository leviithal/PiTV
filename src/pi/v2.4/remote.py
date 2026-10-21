#!/usr/bin/env python3
"""Minimal local-only-by-network-design remote. Long token is required on all calls.
Do not forward port 8765 to the internet; allow only trusted home devices.
"""
import hmac
import json
import logging
import re
import time
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path.home() / 'pi-tv'
TOKEN = (ROOT/'remote-token').read_text(encoding='utf-8').strip()
PORT = 8765
LOCK = threading.Lock()
URLS = {'netflix':'https://www.netflix.com/', 'disney':'https://www.disneyplus.com/'}
KEYS = {'up':'Up', 'down':'Down', 'left':'Left', 'right':'Right', 'ok':'Return', 'esc':'Escape', 'tab':'Tab', 'space':'space', 'backspace':'BackSpace', 'focus':'F9'}


def execute(*args):
    subprocess.run(args, check=True, timeout=5, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def hotkey(mod, key):
    execute('wtype', '-M', mod, '-k', key, '-m', mod)



def focus_browser():
    # labwc/Wayland: focus the Chromecast replacement's own Chromium window.
    # Some wlrctl releases accept app_id selectors; older ones accept 'chromium'.
    for target in ('app_id:chromium', 'app_id:chromium-browser', 'chromium'):
        try:
            result = subprocess.run(
                ('wlrctl', 'toplevel', 'focus', target),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=2, check=False)
            if result.returncode == 0:
                return
        except (OSError, subprocess.SubprocessError):
            pass


def navigate(url):
    # Browser-level Ctrl+L is independent of the web page's scroll position
    # and bypasses Netflix/Disney+ page navigation code.
    focus_browser()
    hotkey('ctrl', 'l')
    time.sleep(0.18)
    execute('wtype', '--', url)
    time.sleep(0.12)
    execute('wtype', '-k', 'Return')


def act(data):
    name = data.get('action', '')
    if name in URLS:
        # Use current Chromium tab. No dependence on startup tabs 1 and 2.
        navigate(URLS[name])
    elif name == 'home':
        navigate('http://127.0.0.1:8765/tv?key=' + TOKEN)
    elif name == 'back':
        focus_browser()
        hotkey('alt', 'Left')
    elif name == 'close':
        hotkey('alt', 'Left')
    elif name in KEYS:
        execute('wtype', '-k', KEYS[name])
    elif name == 'move':
        dx = max(-160, min(160, int(data.get('dx', 0))))
        dy = max(-160, min(160, int(data.get('dy', 0))))
        execute('wlrctl', 'pointer', 'move', str(dx), str(dy))
    elif name == 'click':
        execute('wlrctl', 'pointer', 'click')
    elif name == 'scrollup':
        execute('wlrctl', 'pointer', 'scroll', '-80', '0')
    elif name == 'scrolldown':
        execute('wlrctl', 'pointer', 'scroll', '80', '0')
    elif name == 'volumeup':
        execute('wpctl', 'set-volume', '-l', '1.0', '@DEFAULT_AUDIO_SINK@', '5%+')
    elif name == 'volumedown':
        execute('wpctl', 'set-volume', '@DEFAULT_AUDIO_SINK@', '5%-')
    elif name == 'mute':
        execute('wpctl', 'set-mute', '@DEFAULT_AUDIO_SINK@', 'toggle')
    elif name == 'type':
        s = data.get('value', '')
        if not isinstance(s, str) or not (1 <= len(s) <= 140):
            raise ValueError('Text must contain 1–140 characters')
        execute('wtype', '-d', '15', '--', s)
    else:
        raise ValueError('Unknown action')


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        safe = re.sub(r'(?i)(key=)[^&\s\"]+', r'\1REDACTED', fmt % args)
        logging.info('%s - %s', self.client_address[0], safe)

    def _response(self, code, content, mime='text/plain; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def authenticated(self, parsed):
        supplied = parse_qs(parsed.query).get('key', [''])[0]
        return hmac.compare_digest(supplied, TOKEN)

    def do_GET(self):
        parsed = urlparse(self.path)
        if not self.authenticated(parsed):
            self._response(403, b'Incorrect or missing remote key')
            return
        if parsed.path in ('/', '/remote'):
            self._response(200, (ROOT/'phone-remote.html').read_bytes(), 'text/html; charset=utf-8')
        elif parsed.path == '/tv':
            self._response(200, (ROOT/'tv-home.html').read_bytes(), 'text/html; charset=utf-8')
        elif parsed.path == '/status':
            self._response(200, b'{"ok":true}', 'application/json')
        else:
            self._response(404, b'Not found')

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != '/action' or not self.authenticated(parsed):
            self._response(403, b'Forbidden')
            return
        length = int(self.headers.get('Content-Length', '0'))
        if length < 1 or length > 2048:
            self._response(413, b'Invalid request size')
            return
        try:
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('Invalid JSON object')
            with LOCK:
                act(data)
            self._response(200, b'{"ok":true}', 'application/json')
        except (ValueError, TypeError, OSError, subprocess.SubprocessError) as exc:
            logging.exception('Remote action failed')
            msg = json.dumps({'ok': False, 'error': str(exc)}).encode()
            self._response(400, msg, 'application/json')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    server = ThreadingHTTPServer(('0.0.0.0', PORT), Handler)
    print(f'PiTV remote: http://<PI-IP>:{PORT}/?key=<token>', flush=True)
    server.serve_forever()