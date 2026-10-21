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
