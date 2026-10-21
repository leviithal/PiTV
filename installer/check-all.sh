#!/usr/bin/env bash
set -u
echo '=== PiTV current status (no secrets) ==='
printf 'OS: '; . /etc/os-release; printf '%s\n' "$PRETTY_NAME"
printf 'Architecture: '; uname -m
printf 'Chromium: '; (chromium --version || chromium-browser --version || true) 2>/dev/null
for cmd in labwc wtype wlrctl wpctl openssl python3;do command -v "$cmd" >/dev/null && echo "$cmd: yes" || echo "$cmd: MISSING";done
printf 'Local-only V2 port: '; if ss -ltn 2>/dev/null | grep ':8765 ' | grep -q '127.0.0.1:8765';then echo OK;else echo 'verify manually';fi
printf 'TLS V3 port 8766: '; ss -ltn 2>/dev/null | grep ':8766 ' || true
printf 'V3 service: '; systemctl --user is-active pitv-v3.service 2>/dev/null || true
printf 'Video player and Android buttons require MANUAL testing (see docs/TESTPLAN.md).\n'
