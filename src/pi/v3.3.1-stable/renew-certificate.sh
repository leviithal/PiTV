#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$HOME/pi-tv-v3"
[[ -f "$ROOT/tls-cert.pem" && -f "$ROOT/tls-key.pem" ]] || { echo 'PiTV V3-certifikat saknas'; exit 1; }
IP=$(hostname -I | tr ' ' '\n' | grep -m1 -E '^([0-9]{1,3}\.){3}[0-9]{1,3}$')
mkdir -p "$ROOT/backup-certs"
STAMP=$(date +%Y%m%d-%H%M%S)
cp -p "$ROOT/tls-cert.pem" "$ROOT/backup-certs/tls-cert-$STAMP.pem"
cp -p "$ROOT/tls-key.pem" "$ROOT/backup-certs/tls-key-$STAMP.pem"
openssl req -x509 -newkey rsa:3072 -nodes -days 365 -sha256 \
  -keyout "$ROOT/tls-key-new.pem" -out "$ROOT/tls-cert-new.pem" \
  -subj '/CN=PiTV V3' -addext "subjectAltName=IP:${IP},IP:127.0.0.1,DNS:localhost" >/dev/null 2>&1
mv "$ROOT/tls-cert-new.pem" "$ROOT/tls-cert.pem"
mv "$ROOT/tls-key-new.pem" "$ROOT/tls-key.pem"
chmod 600 "$ROOT/tls-key.pem"
systemctl --user restart pitv-v3.service
printf 'Nytt certifikat skapat för IP %s. Ange nytt fingeravtryck i Android-appen.\n' "$IP"
bash "$ROOT/show-connection.sh"
