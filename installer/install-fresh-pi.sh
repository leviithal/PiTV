#!/usr/bin/env bash
# Reproducible staged setup on a NEW Raspberry Pi OS Desktop (64-bit) installation.
# Keep historical source unchanged; V2 is made localhost-only on *this* fresh installation.
set -Eeuo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
V2="$REPO/src/pi/v2.4"
V3="$REPO/src/pi/v3.0"
V31="$REPO/patches/v3.1"
V32="$REPO/patches/v3.2"
MODE="${1:---preflight}"
if [[ "$MODE" != --preflight && "$MODE" != --install ]];then echo 'Usage: bash installer/install-fresh-pi.sh --preflight | --install';exit 2;fi
if [[ "$(id -u)" -eq 0 ]];then echo 'Run as regular Pi user (without sudo)';exit 1;fi
if [[ ! -f "$V2/remote.py" || ! -f "$V3/install-v3.sh" || ! -f "$V31/install-v31.py" || ! -f "$V32/install-v32.py" ]];then echo 'Source files missing. Download the complete repository.';exit 1;fi
for cmd in chromium python3 openssl wtype wlrctl wpctl systemctl raspi-config;do
  if ! command -v "$cmd" >/dev/null;then echo "MISSING: $cmd (install/configure before continuing)";exit 1;fi
done
if [[ -e "$HOME/pi-tv" || -e "$HOME/pi-tv-v3" ]];then
    echo 'An existing PiTV installation was found. Refusing to overwrite. See docs/MIGRERA.md';exit 1
fi
if [[ ! -d "$HOME/.config" ]];then echo 'Raspberry Pi OS Desktop/labwc expected';exit 1;fi
if [[ "$MODE" == --preflight ]];then
    echo 'Preflight OK. On install: creates ~/pi-tv and ~/pi-tv-v3, edits ~/.config/labwc/autostart and Chromium policy, may enable autologin; requires sudo.'
    echo 'Before installation, TEST Netflix and Disney+ video+audio in the existing Chromium profile.'
    exit 0
fi
read -r -p 'Continue installing on a NEW Pi? Type INSTALL to proceed: ' ok
[[ "$ok" == INSTALL ]] || { echo 'Cancelled';exit 0; }
BACKUP="$HOME/PiTV-backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP" "$HOME/pi-tv" "$HOME/.cache/pi-tv" "$HOME/.config/labwc"
chmod 700 "$HOME/pi-tv"
if [[ -f "$HOME/.config/labwc/autostart" ]];then cp -p "$HOME/.config/labwc/autostart" "$BACKUP/labwc-autostart.before";fi
# Copy the observed V2.4 snapshot, no secrets are included in the repo.
cp -a "$V2/." "$HOME/pi-tv/"
chmod 700 "$HOME/pi-tv/start.sh"
# Historical V2 server was bound to all interfaces; safe fresh installation is LOCAL ONLY.
python3 - "$HOME/pi-tv/remote.py" <<'PYCODE'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text(encoding='utf-8')
a="ThreadingHTTPServer(('0.0.0.0', PORT), Handler)"
b="ThreadingHTTPServer(('127.0.0.1', PORT), Handler)"
if s.count(a)!=1:raise SystemExit('Unexpected V2 server bind; stop before starting the server')
p.write_text(s.replace(a,b,1),encoding='utf-8')
PYCODE
python3 - "$HOME/pi-tv/remote-token" <<'PYCODE'
import os,sys,secrets
p=sys.argv[1];fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:f.write(secrets.token_urlsafe(32)+'\n')
PYCODE
chmod 600 "$HOME/pi-tv/remote-token"
AUTOSTART="$HOME/.config/labwc/autostart"
touch "$AUTOSTART"
if ! grep -q '^# PiTV Mini' "$AUTOSTART";then
  printf '\n# PiTV Mini\n%s\n' "$HOME/pi-tv/start.sh &" >> "$AUTOSTART"
fi
# Install V3 separate HTTPS service; don't reboot between stages.
bash "$V3/install-v3.sh"
cp -p "$V31/rollback-v31.sh" "$HOME/rollback-v31.sh"
python3 "$V31/install-v31.py"
cp -p "$V32/rollback-v32.py" "$HOME/rollback-v32.py"
python3 "$V32/install-v32.py"
# OS settings attempted last; review output if tool releases differ.
sudo raspi-config nonint do_blanking 1 || echo 'Warning: adjust screen blanking manually.'
sudo raspi-config nonint do_boot_behaviour B4 || echo 'Warning: enable Desktop Autologin manually.'
echo '=== Installation files created. BACKUP: '"$BACKUP"
echo 'Now: sudo reboot. Then: bash ~/pi-tv-v3/check-v3.sh'
echo 'REMINDER: Do not upload runtime tokens, TLS keys, logs or Chromium profile to GitHub.'
