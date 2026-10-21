#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$HOME/pi-tv"
FILE="$ROOT/remote.py"
[[ -f "$FILE" ]] || { echo 'V2 remote.py saknas'; exit 1; }
[[ -f "$HOME/pi-tv-v3/api-token" ]] || { echo 'Installera och testa V3 först'; exit 1; }
python3 - "$FILE" <<'PY'
from pathlib import Path
import sys,shutil,datetime
p=Path(sys.argv[1]); s=p.read_text()
old="ThreadingHTTPServer(('0.0.0.0', PORT), Handler)"
new="ThreadingHTTPServer(('127.0.0.1', PORT), Handler)"
if new in s:
 print('V2 är redan begränsad till localhost.');quit()
if s.count(old)!=1:raise SystemExit('Oväntad V2-kod: ingen ändring gjord.')
bak=p.with_name('remote.py.pre-v3-lockdown')
if not bak.exists():shutil.copy2(p,bak)
p.write_text(s.replace(old,new))
print('V2 kan nu bara nås från Pi:n lokalt efter omstart.')
PY
printf '\nKlart. Kör sudo reboot. Gammal mobilfjärr på port 8765 slutar fungera från LAN, men TV-startsidan fortsätter fungera lokalt.\n'
