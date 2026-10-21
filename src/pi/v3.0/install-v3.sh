#!/usr/bin/env bash
set -Eeuo pipefail
[[ $(id -u) -ne 0 ]] || { echo 'Kör som vanliga Pi-användaren, INTE sudo.'; exit 1; }
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$HOME/pi-tv-v3"
[[ -f "$HOME/pi-tv/remote.py" ]] || { echo 'Din PiTV V2 hittas inte i ~/pi-tv. Avbryter.'; exit 1; }
for cmd in python3 openssl wtype wlrctl wpctl systemctl; do
  command -v "$cmd" >/dev/null || { echo "Saknar verktyget $cmd. Avbryter utan ändringar."; exit 1; }
done
IP=$(hostname -I | tr ' ' '\n' | grep -m1 -E '^([0-9]{1,3}\.){3}[0-9]{1,3}$' || true)
[[ -n "$IP" ]] || { echo 'Ingen IPv4 hittades. Kontrollera nätverket.'; exit 1; }
mkdir -p "$ROOT" "$HOME/.config/systemd/user" "$HOME/.config/labwc"
chmod 700 "$ROOT"
install -m 700 "$BASE/server.py" "$ROOT/server.py"
for script in show-connection.sh check-v3.sh lockdown-v2.sh rollback-v3.sh renew-certificate.sh; do
  install -m 700 "$BASE/$script" "$ROOT/$script"
done
if [[ ! -f "$ROOT/api-token" ]]; then
  python3 - "$ROOT/api-token" <<'PY'
import secrets,sys,os
fd=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:f.write(secrets.token_urlsafe(32)+'\n')
PY
fi
chmod 600 "$ROOT/api-token"
if [[ ! -f "$ROOT/tls-cert.pem" || ! -f "$ROOT/tls-key.pem" ]]; then
  openssl req -x509 -newkey rsa:3072 -nodes -days 365 -sha256 \
    -keyout "$ROOT/tls-key.pem" -out "$ROOT/tls-cert.pem" \
    -subj '/CN=PiTV V3' -addext "subjectAltName=IP:${IP},IP:127.0.0.1,DNS:localhost" >/dev/null 2>&1
fi
chmod 600 "$ROOT/tls-key.pem"
chmod 644 "$ROOT/tls-cert.pem"
cat > "$HOME/.config/systemd/user/pitv-v3.service" <<'EOF'
[Unit]
Description=PiTV V3 native Android remote HTTPS API
After=default.target
[Service]
Type=simple
WorkingDirectory=%h/pi-tv-v3
ExecStart=/usr/bin/python3 %h/pi-tv-v3/server.py
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
UMask=0077
[Install]
WantedBy=default.target
EOF
AUTOSTART="$HOME/.config/labwc/autostart"
touch "$AUTOSTART"
if ! grep -q '# PITV-V3-BEGIN' "$AUTOSTART"; then
cat >> "$AUTOSTART" <<'EOF'

# PITV-V3-BEGIN
systemctl --user import-environment WAYLAND_DISPLAY XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS
systemctl --user restart pitv-v3.service
# PITV-V3-END
EOF
fi
# Service is deliberately started through labwc session, to inherit Wayland environment.
# Do not enable globally: service would start before login/Wayland session.
XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" systemctl --user daemon-reload || true
printf '\nPiTV V3 installerad parallellt. V2 och Netflix/Disney+ är orörda.\n'
printf 'Starta om Pi:n med: sudo reboot\n'
printf 'Efter omstart: bash ~/pi-tv-v3/show-connection.sh\n'
