#!/usr/bin/env bash
set -Eeuo pipefail
[[ $(id -u) -ne 0 ]] || { echo 'Kör INTE med sudo';exit 1; }
[[ $# -eq 1 ]] || { echo 'Använd: bash rollback-v31.sh ~/pi-tv-v31-backups/backup-YYYY...';exit 1; }
BACKUP="$(realpath -e "$1")"
case "$BACKUP" in "$HOME"/pi-tv-v31-backups/backup-*) ;; *) echo 'Fel plats för backup';exit 1;; esac
for name in server.py start.sh manifest.json; do
 [[ -f "$BACKUP/$name" ]] || { echo "Saknar $name i backup";exit 1; }
done
install -m 700 "$BACKUP/server.py" "$HOME/pi-tv-v3/server.py"
install -m 755 "$BACKUP/start.sh" "$HOME/pi-tv/start.sh"
install -m 644 "$BACKUP/manifest.json" "$HOME/pi-tv/dpad-extension/manifest.json"
rm -f "$HOME/pi-tv/dpad-extension/pitv-background.js"
echo 'Ursprungliga filer återställda. Kör sudo reboot.'
