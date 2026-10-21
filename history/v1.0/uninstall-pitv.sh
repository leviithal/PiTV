#!/usr/bin/env bash
set -euo pipefail
F="$HOME/.config/labwc/autostart"
if [ -f "$F" ]; then
  cp "$F" "$HOME/.config/labwc/autostart-before-remove-pitv"
  sed -i '/^# PiTV Mini$/d; /\/pi-tv\/start\.sh &$/d' "$F"
fi
pkill -f '^python3 .*/pi-tv/remote.py$' || true
printf 'PiTV Mini autostart removed. Reboot with: sudo reboot\n'
printf 'Streaming browser and profiles have not been changed.\n'
