#!/usr/bin/env bash
# PiTV Stable TV session; no V2 HTTP server and no URL-embedded tokens.
set -Eeuo pipefail
mkdir -p "$HOME/.cache/pi-tv"
systemctl --user import-environment WAYLAND_DISPLAY XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS || true
systemctl --user restart pitv-v3.service
BROWSER="$(command -v chromium)"
exec "$BROWSER" \
  "--load-extension=$HOME/pi-tv/dpad-extension" \
  --kiosk --start-maximized --no-first-run --no-default-browser-check \
  --password-store=basic --disable-session-crashed-bubble --noerrdialogs \
  --disable-features=Translate \
  "file://$HOME/pi-tv/tv-home.html" >> "$HOME/.cache/pi-tv/chromium.log" 2>&1
