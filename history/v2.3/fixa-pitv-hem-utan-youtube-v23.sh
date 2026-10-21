#!/usr/bin/env bash
# PiTV V2.3 – Hem uses the Back action that already works on this Pi;
# remove YouTube from TV launcher, Android remote, and the server action map.
# Does not change Chromium, Widevine, profile, keyring, or autostart.
set -euo pipefail
if (( EUID == 0 )); then
  echo 'Kör som din vanliga användare, utan sudo.'
  exit 1
fi
DIR="$HOME/pi-tv"
for f in remote.py tv-home.html phone-remote.html; do
  if [[ ! -f "$DIR/$f" ]]; then
    echo "Saknar $DIR/$f – avbryter utan ändring."
    exit 1
  fi
done
STAMP="$(date +%Y%m%d-%H%M%S)"
BACK="$DIR/backups/v23-$STAMP"
mkdir -p "$BACK"
for f in remote.py tv-home.html phone-remote.html; do cp -p "$DIR/$f" "$BACK/$f"; done
python3 - "$DIR" <<'PY'
from pathlib import Path
import sys, re, ast
p=Path(sys.argv[1])
server=p/'remote.py'
tv=p/'tv-home.html'
phone=p/'phone-remote.html'
s=server.read_text()
h=tv.read_text()
m=phone.read_text()
# Verify expected installed V2.2 signature; avoid modifying unknown deployments.
expected="    elif name == 'home':\n        navigate('http://127.0.0.1:8765/tv?key=' + TOKEN)"
if expected not in s:
    raise SystemExit('Hem-koden avviker från V2.2. Inga filer ändrade. Kontrollera versionen.')
if '<button class="tile youtube" data-app="youtube">' not in h or '<button class="youtube" data-a="youtube">' not in m:
    raise SystemExit('HTML-filerna avviker från förväntad V2.2. Inga filer ändrade.')
# Exactly same action as working Back. No address-bar automation or token typing.
s=s.replace(expected,"    elif name == 'home':\n        hotkey('alt', 'Left')",1)
s=s.replace("    elif name == 'close':\n        navigate('http://127.0.0.1:8765/tv?key=' + TOKEN)","    elif name == 'close':\n        hotkey('alt', 'Left')",1)
s=s.replace(", 'youtube':'https://www.youtube.com/'",'',1)
h=re.sub(r'<button class="tile youtube" data-app="youtube">.*?</button>\s*','',h,count=1,flags=re.S)
h=h.replace('grid-template-columns:repeat(3,1fr);gap:24px','grid-template-columns:repeat(2,1fr);gap:24px',1)
h=h.replace(",youtube:'https://www.youtube.com/'",'',1)
h=h.replace('.youtube{background:linear-gradient(145deg,#d62531,#380c11)}','',1)
m=m.replace('<button class="youtube" data-a="youtube">YouTube</button>','',1)
m=m.replace('grid-template-columns:repeat(3,1fr);gap:8px','grid-template-columns:repeat(2,1fr);gap:8px',1)
m=m.replace('button.youtube{background:#9f2027}','',1)
# Remove the misleading Rensa spelare button (it uses the same old Home automation).
m=m.replace('<button data-a="close">✕ Rensa spelare</button>','',1)
m=m.replace('<div class="line"><button data-a="home">','<div class="line navline"><button data-a="home">',1)
m=m.replace('.line{display:grid;', '.navline{grid-template-columns:repeat(2,1fr)!important}.line{display:grid;',1)
# Validate all in memory before any write.
ast.parse(s)
if any('youtube' in value.lower() for value in (s.split('URLS = ',1)[1].split('\n',1)[0],h,m)):
    raise SystemExit('YouTube kvar i gränssnittet; avbryter.')
for f,content in ((server,s),(tv,h),(phone,m)):
    f.write_text(content)
print('✓ Hem använder samma fungerande navigering som Bakåt.')
print('✓ YouTube är borttagen från TV och fjärrkontroll.')
print('✓ Rensa spelare har tagits bort för att minska förvirring.')
PY
python3 -m py_compile "$DIR/remote.py"
cat > "$BACK/restore.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
for f in remote.py tv-home.html phone-remote.html; do cp -p '$BACK/'"\$f" '$DIR/'"\$f"; done
echo 'Återställt. Starta om: sudo reboot'
EOF
chmod +x "$BACK/restore.sh"
echo "Säkerhetskopia: $BACK"
echo 'Starta nu om: sudo reboot'
echo 'Ladda sedan om Android-sidan (gärna öppna fjärrlänken i en ny flik).'
echo 'OBS: Hem är just nu samma steg som Bakåt, dvs. ett historiksteg.'
