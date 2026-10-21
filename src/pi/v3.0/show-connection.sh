#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$HOME/pi-tv-v3"
IP=$(hostname -I | tr ' ' '\n' | grep -m1 -E '^([0-9]{1,3}\.){3}[0-9]{1,3}$')
[[ -f "$ROOT/api-token" && -f "$ROOT/tls-cert.pem" ]] || { echo 'PiTV V3 är inte installerad'; exit 1; }
printf '\n=== Uppgifter att skriva in i Android-appen ===\n'
printf 'Pi IP: %s\nPort: 8766 (förvald i appen)\n' "$IP"
printf 'API-nyckel: '; cat "$ROOT/api-token"
printf 'Certifikatets SHA-256: '
openssl x509 -in "$ROOT/tls-cert.pem" -outform DER | sha256sum | awk '{print toupper($1)}'
printf '\nDela ALDRIG API-nyckeln här i chatten eller i en skärmbild.\n'
printf 'Certifikatet är giltigt för IP-adressen när det genererades.\n'
