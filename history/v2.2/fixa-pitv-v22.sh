#!/usr/bin/env bash
# PiTV Mini V2.2: reliable same-tab navigation, optional Chromium basic password store.
# Leaves Widevine packages and Chromium's existing user data directory untouched.
set -euo pipefail
if (( EUID == 0 )); then
  echo 'Kör som din vanliga Pi-användare (utan sudo).'
  exit 1
fi
DIR="$HOME/pi-tv"
for item in start.sh remote.py tv-home.html remote-token; do
  if [[ ! -f "$DIR/$item" ]]; then
    echo "Saknad fil: $DIR/$item – avbryter utan ändringar."
    exit 1
  fi
done
if ! grep -q 'def act(data):' "$DIR/remote.py" || ! grep -q 'async function launch(name)' "$DIR/tv-home.html"; then
  echo 'Oväntad PiTV-version. Inga filer ändrade; skicka start.sh + remote.py utan remote-token.'
  exit 1
fi
STAMP="$(date +%Y%m%d-%H%M%S)"
BACK="$DIR/backups/v22-$STAMP"
mkdir -p "$BACK"
for f in start.sh remote.py tv-home.html; do cp -p "$DIR/$f" "$BACK/$f"; done
echo "Backup skapad: $BACK"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
cp "$DIR/remote.py" "$TMP/remote.py"
cp "$DIR/tv-home.html" "$TMP/tv-home.html"

python3 - "$TMP" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
r = p/'remote.py'
s = r.read_text()
# Replace only the V2 tab automation branch; retain all existing input actions.
start = s.index("    if name in URLS:", s.index('def act(data):'))
end = s.index("    elif name in KEYS:", start)
new = '''    if name in URLS:
        # Use current Chromium tab. No dependence on startup tabs 1 and 2.
        navigate(URLS[name])
    elif name == 'home':
        navigate('http://127.0.0.1:8765/tv?key=' + TOKEN)
    elif name == 'back':
        hotkey('alt', 'Left')
    elif name == 'close':
        navigate('http://127.0.0.1:8765/tv?key=' + TOKEN)
'''
s = s[:start] + new + s[end:]
# Use active browser window; wtype cannot enter keys into a keyring prompt.
marker = '\ndef act(data):'
method = '''
def navigate(url):
    # Bring Chromium to front if labwc supports focusing by app/title.
    try:
        subprocess.run(('wlrctl', 'toplevel', 'focus', 'chromium'),
                       check=False, timeout=2, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        pass
    hotkey('ctrl', 'l')
    execute('wtype', '--', url)
    execute('wtype', '-k', 'Return')

'''
if 'def navigate(url):' not in s:
    s = s.replace(marker, '\n' + method + marker, 1)
r.write_text(s)
h = p/'tv-home.html'
s = h.read_text()
start = s.index('async function launch(name)')
end = s.index('\nbuttons.forEach(', start)
# Native window.location directly navigates Chromium, so no key injection or tabs.
new = """const SERVICES={netflix:'https://www.netflix.com/',disney:'https://www.disneyplus.com/',youtube:'https://www.youtube.com/'};
function launch(name){if(!SERVICES[name])return;msg.textContent='Öppnar '+name+' …';window.location.assign(SERVICES[name]);}"""
s = s[:start] + new + s[end:]
h.write_text(s)
PY
python3 -m py_compile "$TMP/remote.py"
# Write new startup file, preserving Chromium's default user profile and extension.
cat > "$TMP/start.sh" <<'START'
#!/usr/bin/env bash
# PiTV V2.2: one Chromium window/tab; keep default Chromium profile & Widevine.
set -u
mkdir -p "$HOME/.cache/pi-tv"
python3 "$HOME/pi-tv/remote.py" >> "$HOME/.cache/pi-tv/remote.log" 2>&1 &
sleep 2
BROWSER="$(command -v chromium || command -v chromium-browser)"
KEY="$(tr -d '\r\n' < "$HOME/pi-tv/remote-token")"
EXTRA=()
if [[ -d "$HOME/pi-tv/dpad-extension" ]]; then
  EXTRA+=("--load-extension=$HOME/pi-tv/dpad-extension")
fi
# basic password store avoids an interactive GNOME Keyring unlock in an auto-login kiosk.
# WARNING: Chromium's basic store is not protected by the desktop keyring.
"$BROWSER" "${EXTRA[@]}" \
  --password-store=basic \
  --start-fullscreen --no-first-run --no-default-browser-check \
  --disable-session-crashed-bubble --noerrdialogs \
  "http://127.0.0.1:8765/tv?key=$KEY" \
  >> "$HOME/.cache/pi-tv/chromium.log" 2>&1 &
START
chmod +x "$TMP/start.sh"
bash -n "$TMP/start.sh"
cp -p "$TMP/remote.py" "$DIR/remote.py"
cp -p "$TMP/tv-home.html" "$DIR/tv-home.html"
cp -p "$TMP/start.sh" "$DIR/start.sh"
chmod +x "$DIR/start.sh"
cat > "$BACK/aterstall.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cp -p '$BACK/start.sh' '$DIR/start.sh'
cp -p '$BACK/remote.py' '$DIR/remote.py'
cp -p '$BACK/tv-home.html' '$DIR/tv-home.html'
echo 'PiTV föregående filer återställda. Starta om: sudo reboot'
EOF
chmod +x "$BACK/aterstall.sh"
cat <<EOF

PiTV V2.2 reparerad!
- Netflix/Disney+ via TV-startsidan: direkt i samma Chromium-flik.
- Mobilens Hem/Netflix/Disney+: adressbyte i samma flik.
- Chromium startas med --password-store=basic (slipper normalt keyring-frågan).
- Chromium/Widevine och användarprofil har inte raderats.

VIKTIGT: basic lagrar webbläsarhemligheter med lägre skydd, och du kan
behöva logga in på streamingtjänsterna igen. Skydda Pi-användarkontot.
Stäng Chromium-fönstret och kör: sudo reboot

Återställning om något går fel:
  bash "$BACK/aterstall.sh"
  sudo reboot

Skärmens upplösning: kör wlr-randr på Pi:ns grafiska skrivbord,
och välj upplösning som finns i listan. Inga bildlägen har tvångsändrats.
EOF
