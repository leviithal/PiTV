#!/usr/bin/env bash
set -u
printf '=== PiTV V3 status ===\n'
systemctl --user --no-pager status pitv-v3.service 2>&1 | head -n 13
printf '\nHTTPS-port:\n'
ss -ltn 2>/dev/null | grep ':8766 ' || echo 'Port 8766 lyssnar inte'
printf '\nTLS-local test (utan att visa nyckel):\n'
TOKEN=$(cat "$HOME/pi-tv-v3/api-token")
printf 'header = "Authorization: Bearer %s"\n' "$TOKEN" | \
  curl -sS --max-time 5 --config - --cacert "$HOME/pi-tv-v3/tls-cert.pem" \
  https://127.0.0.1:8766/api/status || true
printf '\n'
