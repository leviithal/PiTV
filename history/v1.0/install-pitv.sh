#!/usr/bin/env bash
# PiTV Mini - Raspberry Pi OS (Wayland/labwc) + already working Chromium/Widevine.
# Does not reinstall Chromium, modify its profile, or touch Widevine.
set -euo pipefail

if (( EUID == 0 )); then
  echo 'Run this installer as your normal Raspberry Pi user (without sudo).'
  exit 1
fi
if ! command -v chromium >/dev/null 2>&1 && ! command -v chromium-browser >/dev/null 2>&1; then
  echo 'Chromium was not found. Keep your current working Netflix installation and check PATH.'
  exit 1
fi
if ! command -v raspi-config >/dev/null 2>&1; then
  echo 'This setup is intended for Raspberry Pi OS Desktop.'
  exit 1
fi

printf '\nPiTV Mini | Installer\n'
printf 'Keeps existing Chromium, Widevine and streaming logins.\n'
sudo apt update
sudo apt install -y wtype wlrctl

mkdir -p "$HOME/pi-tv" "$HOME/.config/labwc" "$HOME/.cache/pi-tv"
# Generate token only once, so previously saved mobile bookmarks keep working.
if [ ! -f "$HOME/pi-tv/remote-token" ]; then
  python3 - <<'PY'
from pathlib import Path
import secrets
p = Path.home()/'pi-tv'/'remote-token'
p.write_text(secrets.token_urlsafe(24), encoding='utf-8')
p.chmod(0o600)
PY
fi

cat > "$HOME/pi-tv/tv-home.html" <<'TVHTML'
<!DOCTYPE html>
<html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Filmkväll</title><style>
:root {color-scheme:dark} * {box-sizing:border-box}
body {margin:0;min-height:100vh;font-family:system-ui,Arial,sans-serif;color:#f8fafc;background:radial-gradient(ellipse at 14% 20%,#342253 0,transparent 45%),radial-gradient(ellipse at 90% 89%,#182d50 0,transparent 46%),#090d18;display:flex;align-items:center;justify-content:center}
main {width:min(1100px,94vw);padding:28px 10px}
.kicker {font-size:16px;letter-spacing:0.24em;text-transform:uppercase;color:#c4b5fd;font-weight:750}
h1 {margin:12px 0 6px;font-size:clamp(40px,5vw,72px);letter-spacing:-.055em}
p {color:#9ba7bb;font-size:clamp(15px,1.65vw,21px);margin:0 0 32px}
.grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
a {height:230px;display:flex;flex-direction:column;align-items:flex-start;justify-content:flex-end;gap:10px;text-decoration:none;color:white;border-radius:24px;padding:30px;border:1px solid #ffffff22;box-shadow:0 14px 34px #0006;transition:transform .16s,border-color .16s}
a:hover,a:focus-visible {transform:translateY(-5px);border-color:#d5c7ff;outline:3px solid #7c3aed}
a b {font-size:clamp(27px,3vw,43px);letter-spacing:-.035em} a small {font-size:15px;color:#ffffffd6}
.netflix {background:linear-gradient(150deg,#851317,#200408 75%)}
.disney {background:linear-gradient(150deg,#1f4eab,#08182c 78%)}
.youtube {background:linear-gradient(150deg,#b82429,#321014 80%)}
footer {font-size:15px;color:#78869c;margin-top:32px}
@media(max-width:680px){main{padding:20px}.grid{grid-template-columns:1fr;gap:12px}a{height:125px;padding:18px}h1{font-size:40px}p{margin-bottom:18px}}
</style></head><body><main>
<div class="kicker">Välkommen hem</div>
<h1>Vad ska vi titta på? 🍿</h1>
<p>Välj en tjänst. Använd mobilens fjärrkontroll för att navigera.</p>
<div class="grid">
<a class="netflix" href="https://www.netflix.com/" target="_blank" rel="noopener"><b>Netflix</b><small>Filmer och serier</small></a>
<a class="disney" href="https://www.disneyplus.com/" target="_blank" rel="noopener"><b>Disney+</b><small>Disney, Pixar, Marvel med mera</small></a>
<a class="youtube" href="https://www.youtube.com/" target="_blank" rel="noopener"><b>YouTube</b><small>Videor och favoriter</small></a>
</div>
<footer>Tips: tryck Hem på mobilens fjärrkontroll för att återvända hit.</footer>
</main></body></html>
TVHTML

cat > "$HOME/pi-tv/remote.py" <<'PYREMOTE'
#!/usr/bin/env python3
"""Minimal local-only-by-network-design remote. Long token is required on all calls.
Do not forward port 8765 to the internet; allow only trusted home devices.
"""
import hmac
import json
import logging
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path.home() / 'pi-tv'
TOKEN = (ROOT/'remote-token').read_text(encoding='utf-8').strip()
PORT = 8765
LOCK = threading.Lock()
URLS = {'netflix':'https://www.netflix.com/', 'disney':'https://www.disneyplus.com/', 'youtube':'https://www.youtube.com/'}
KEYS = {'up':'Up', 'down':'Down', 'left':'Left', 'right':'Right', 'ok':'Return', 'esc':'Escape', 'tab':'Tab', 'space':'space', 'backspace':'BackSpace'}


def execute(*args):
    subprocess.run(args, check=True, timeout=5, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def hotkey(mod, key):
    execute('wtype', '-M', mod, '-k', key, '-m', mod)


def act(data):
    name = data.get('action', '')
    if name in URLS:
        hotkey('ctrl', 't')
        execute('wtype', '--', URLS[name])
        execute('wtype', '-k', 'Return')
    elif name == 'home':
        hotkey('ctrl', '1')
    elif name == 'back':
        hotkey('alt', 'Left')
    elif name == 'close':
        # Close the current service tab; first tab is the local launcher.
        hotkey('ctrl', 'w')
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
        logging.info('%s - %s', self.client_address[0], fmt % args)

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
PYREMOTE

cat > "$HOME/pi-tv/phone-remote.html" <<'PHONEHTML'
<!DOCTYPE html><html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no"><title>PiTV • Fjärrkontroll</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0b1020;color:#f8fafc;font-family:system-ui,Arial,sans-serif;touch-action:pan-y}main{max-width:520px;margin:auto;padding:18px 14px 38px}h1{font-size:27px;letter-spacing:-.04em;margin:5px 0}p{color:#9ba7bb;margin:0 0 16px;font-size:13px}.apps{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}button{border:1px solid #ffffff23;border-radius:16px;background:#232f47;color:#fff;padding:15px 6px;font:600 16px system-ui;min-height:56px;cursor:pointer;-webkit-tap-highlight-color:transparent}button:active{background:#514480}button.netflix{background:#82191b}button.disney{background:#174a9c}button.youtube{background:#9f2027}.line{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}.dpad{display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:repeat(3,58px);gap:8px;max-width:290px;margin:18px auto}.dpad button{min-height:0;padding:6px;font-size:22px}.dpad .up{grid-column:2}.dpad .left{grid-column:1;grid-row:2}.dpad .ok{grid-column:2;grid-row:2;background:#543fb0}.dpad .right{grid-column:3;grid-row:2}.dpad .down{grid-column:2;grid-row:3}.touch{height:110px;background:linear-gradient(145deg,#1c2740,#141b2f);border:1px dashed #6f7f9c;border-radius:16px;display:flex;align-items:center;justify-content:center;color:#aab8d1;touch-action:none;user-select:none;margin:10px 0}.small{font-size:12px;color:#9ba7bb;margin-top:12px}.search{display:flex;gap:8px;margin-top:10px}.search input{flex:1;min-width:0;border-radius:14px;border:1px solid #ffffff33;background:#151f34;padding:12px;font-size:16px;color:#fff}.search button{min-height:46px;font-size:14px}#status{font-size:12px;min-height:20px;color:#9be4be;margin:12px 0}
</style></head><body><main>
<h1>🎬 PiTV</h1><p>Fjärrkontroll till TV:n • spara den här sidan på hemskärmen</p>
<div class="apps"><button class="netflix" data-a="netflix">Netflix</button><button class="disney" data-a="disney">Disney+</button><button class="youtube" data-a="youtube">YouTube</button></div>
<div class="line"><button data-a="home">⌂ Hem</button><button data-a="back">↶ Bakåt</button><button data-a="close">✕ Stäng flik</button></div>
<div class="dpad"><button class="up" data-a="up">↑</button><button class="left" data-a="left">←</button><button class="ok" data-a="ok">OK</button><button class="right" data-a="right">→</button><button class="down" data-a="down">↓</button></div>
<div class="line"><button data-a="volumedown">🔉 −</button><button data-a="space">⏯ Spela/pausa</button><button data-a="volumeup">🔊 +</button></div>
<div class="line"><button data-a="mute">Tyst</button><button data-a="esc">Esc</button><button data-a="tab">Tabb</button></div>
<p class="small">Styrplatta: dra fingret för att flytta muspekaren. Tryck på styrplattan för vänsterklick.</p>
<div class="touch" id="pad">Dra fingret här · tryck för att klicka</div>
<div class="line"><button data-a="scrollup">⇡ Scrolla</button><button data-a="click">🖱 Klick</button><button data-a="scrolldown">⇣ Scrolla</button></div>
<div class="search"><input id="typed" placeholder="Sök eller skriv text …" autocomplete="off"/><button id="send">Skriv på TV</button></div>
<div id="status">Redo</div>
</main><script>
const key=new URLSearchParams(location.search).get('key');
const status=document.getElementById('status');
let last=0;
async function send(action,extra={}){try{const r=await fetch('/action?key='+encodeURIComponent(key),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,...extra})});if(!r.ok){const e=await r.json().catch(()=>({error:r.status}));throw Error(e.error||'Fel '+r.status)}status.textContent='✓ '+action;status.style.color='#9be4be'}catch(e){status.textContent='Fel: '+e.message;status.style.color='#ffb4b4'}}
document.querySelectorAll('[data-a]').forEach(b=>b.addEventListener('click',()=>send(b.dataset.a)));
const pad=document.getElementById('pad');let origin=null,moved=false;
pad.addEventListener('pointerdown',e=>{origin={x:e.clientX,y:e.clientY};moved=false;pad.setPointerCapture(e.pointerId)});
pad.addEventListener('pointermove',e=>{if(!origin)return;const dx=Math.round((e.clientX-origin.x)*1.6),dy=Math.round((e.clientY-origin.y)*1.6);if(Math.abs(dx)+Math.abs(dy)<3)return;moved=true;if(Date.now()-last>45){send('move',{dx,dy});last=Date.now();origin={x:e.clientX,y:e.clientY}}});
pad.addEventListener('pointerup',()=>{if(!moved)send('click');origin=null});
pad.addEventListener('pointercancel',()=>{origin=null});
document.getElementById('send').addEventListener('click',()=>{const i=document.getElementById('typed');if(i.value)send('type',{value:i.value})});
</script></body></html>
PHONEHTML

cat > "$HOME/pi-tv/start.sh" <<'START'
#!/usr/bin/env bash
# Executed from the graphical Wayland/labwc session on login.
set -u
mkdir -p "$HOME/.cache/pi-tv"
python3 "$HOME/pi-tv/remote.py" >> "$HOME/.cache/pi-tv/remote.log" 2>&1 &
sleep 2
BROWSER="$(command -v chromium || command -v chromium-browser)"
"$BROWSER" --start-fullscreen --no-first-run --no-default-browser-check "file://$HOME/pi-tv/tv-home.html" >> "$HOME/.cache/pi-tv/chromium.log" 2>&1 &
START
chmod +x "$HOME/pi-tv/start.sh"

AUTOSTART="$HOME/.config/labwc/autostart"
if [ -f "$AUTOSTART" ] && [ ! -f "$HOME/pi-tv/autostart-before-pitv" ]; then
  cp "$AUTOSTART" "$HOME/pi-tv/autostart-before-pitv"
fi
touch "$AUTOSTART"
if ! grep -Fq '# PiTV Mini' "$AUTOSTART"; then
  printf '\n# PiTV Mini\n%s\n' "$HOME/pi-tv/start.sh &" >> "$AUTOSTART"
fi

# Preserve setup's originally working Chromium/Widevine installation.
# A TV should not blank halfway through a movie.
sudo raspi-config nonint do_blanking 1
sudo raspi-config nonint do_boot_behaviour B4

IP="$(hostname -I | awk '{print $1}')"
KEY="$(cat "$HOME/pi-tv/remote-token")"
printf '\nInstallation complete. REBOOT TO START: sudo reboot\n'
printf 'Phone remote address: http://%s:8765/?key=%s\n' "${IP:-PI_IP_HERE}" "$KEY"
printf 'TV home: file://%s/pi-tv/tv-home.html\n' "$HOME"
printf 'Revert: see README provided with installer.\n\n'
