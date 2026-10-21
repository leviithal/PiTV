#!/usr/bin/env bash
set -Eeuo pipefail
[[ $(id -u) -ne 0 ]] || { echo 'Kör utan sudo';exit 1; }
if [[ -f "$HOME/pi-tv/remote.py.pre-v3-lockdown" ]]; then
  cp "$HOME/pi-tv/remote.py.pre-v3-lockdown" "$HOME/pi-tv/remote.py"
fi
systemctl --user stop pitv-v3.service 2>/dev/null || true
systemctl --user disable pitv-v3.service 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/pitv-v3.service"
python3 - <<'PY'
from pathlib import Path
p=Path.home()/'.config/labwc/autostart'
if p.exists():
 s=p.read_text()
 b='# PITV-V3-BEGIN';e='# PITV-V3-END'
 if s.count(b)==1 and s.count(e)==1:
  start=s.index(b);end=s.index(e,start)+len(e)
  p.write_text(s[:start].rstrip('\n')+'\n'+s[end:].lstrip('\n'))
PY
systemctl --user daemon-reload 2>/dev/null || true
printf 'V3 startas inte längre. V2 återställd till ursprunglig fjärråtkomst om lockdown hade körts.\n'
printf 'Dina V3-nycklar och filer finns kvar i ~/pi-tv-v3 för eventuell framtida felsökning.\n'
printf 'Kör sudo reboot för att verkställa.\n'
