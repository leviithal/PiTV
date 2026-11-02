#!/usr/bin/env python3
"""Read-only local check; prints no API token, TLS key, browser profile or URL secrets."""
from pathlib import Path
import json
import ssl
import subprocess
import urllib.request

root=Path.home()/'pi-tv-v3'
print('PiTV v3.3.1 Stable: lokalt funktionstest')
proc=subprocess.run(['systemctl','--user','is-active','pitv-v3.service'],text=True,capture_output=True)
print('systemd:',proc.stdout.strip() or 'inactive')
if proc.returncode: raise SystemExit('HTTPS-tjänsten är inte aktiv. Kör journalctl --user -u pitv-v3 -n 40')
token=(root/'api-token').read_text().strip()
ctx=ssl.create_default_context(cafile=str(root/'tls-cert.pem'))
req=urllib.request.Request('https://127.0.0.1:8766/api/status',headers={'Authorization':'Bearer '+token})
try:
    with urllib.request.urlopen(req,context=ctx,timeout=5) as res:
        data=json.load(res)
        assert res.status==200 and data.get('ok') is True
        print('HTTPS och autentisering: OK')
        print('Chromium igång:', data.get('chromium_running'))
        print('Uppspelning verifierad av API:',data.get('playback_verified'))
        print('Obs: video och D-pad måste testas på TV:n; API-status kan inte verifiera uppspelningen.')
except Exception as exc:
    raise SystemExit(f'HTTPS-kontroll misslyckades: {type(exc).__name__}: {exc}')
