#!/usr/bin/env python3
"""PiTV Mini V2.4: rotate remote key, redact log URLs, robust Home, sticky phone navigation.
Designed for the previously installed PiTV V2.3. Does not alter Chromium/Widevine.
Run under the normal logged-in desktop user, never as root.
"""
from pathlib import Path
import ast
import os
import secrets
import shutil
import tempfile
from datetime import datetime

if os.geteuid() == 0:
    raise SystemExit('Kör som din vanliga Pi-användare, INTE med sudo.')

root = Path.home() / 'pi-tv'
remote = root / 'remote.py'
phone = root / 'phone-remote.html'
token = root / 'remote-token'
startup = root / 'start.sh'
required = [remote, phone, token, startup]
for path in required:
    if not path.is_file():
        raise SystemExit(f'Saknad PiTV-fil: {path}. Inga ändringar har gjorts.')

s = remote.read_text(encoding='utf-8')
m = phone.read_text(encoding='utf-8')

# Only patch the known PiTV V2.3 shape; avoid corrupting unexpected upgrades.
old_home = "    elif name == 'home':\n        hotkey('alt', 'Left')"
old_back = "    elif name == 'back':\n        hotkey('alt', 'Left')"
start_helper = '\ndef navigate(url):'
end_helper = '\ndef act(data):'
old_logging = "        logging.info('%s - %s', self.client_address[0], fmt % args)"
if any(item not in s for item in (old_home, old_back, start_helper, end_helper, old_logging)):
    raise SystemExit('remote.py ser inte ut som förväntad V2.3. Inga filer eller nycklar ändrade.')
if '<div class="line navline">' not in m:
    raise SystemExit('phone-remote.html saknar V2.3-menyn. Inga filer eller nycklar ändrade.')

s = s.replace("import logging\n", "import logging\nimport re\nimport time\n", 1)
# Replace only the complete navigation helper, preserving the remote protocol.
helper = '''\ndef focus_browser():
    # labwc/Wayland: focus the Chromecast replacement's own Chromium window.
    # Some wlrctl releases accept app_id selectors; older ones accept 'chromium'.
    for target in ('app_id:chromium', 'app_id:chromium-browser', 'chromium'):
        try:
            result = subprocess.run(
                ('wlrctl', 'toplevel', 'focus', target),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=2, check=False)
            if result.returncode == 0:
                return
        except (OSError, subprocess.SubprocessError):
            pass


def navigate(url):
    # Browser-level Ctrl+L is independent of the web page's scroll position
    # and bypasses Netflix/Disney+ page navigation code.
    focus_browser()
    hotkey('ctrl', 'l')
    time.sleep(0.18)
    execute('wtype', '--', url)
    time.sleep(0.12)
    execute('wtype', '-k', 'Return')

'''
a = s.index(start_helper)
b = s.index(end_helper, a)
s = s[:a] + helper + s[b:]
s = s.replace(old_home, "    elif name == 'home':\n        navigate('http://127.0.0.1:8765/tv?key=' + TOKEN)", 1)
s = s.replace(old_back, "    elif name == 'back':\n        focus_browser()\n        hotkey('alt', 'Left')", 1)
# Strip query-string tokens from *future* HTTP logs without changing authentication.
s = s.replace(old_logging, "        safe = re.sub(r'(?i)(key=)[^&\\s\\\"]+', r'\\1REDACTED', fmt % args)\n        logging.info('%s - %s', self.client_address[0], safe)", 1)
ast.parse(s)
assert "navigate('http://127.0.0.1:8765/tv?key=' + TOKEN)" in s
assert 'REDACTED' in s

# Permanently visible Home/Back controls on Android even while scrolling the remote.
css = '''\n/* PiTV V2.4: Hem och Bakåt är alltid åtkomliga på mobilen. */
main { padding-bottom: 112px !important; }
.navline {
  position: fixed !important;
  bottom: max(10px, env(safe-area-inset-bottom)) !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  width: min(500px, calc(100% - 22px)) !important;
  z-index: 9999 !important;
  margin: 0 !important;
  padding: 8px !important;
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0,1fr)) !important;
  background: rgba(12,18,34,.97) !important;
  border: 1px solid rgba(255,255,255,.18);
  border-radius: 20px;
  box-shadow: 0 8px 30px rgba(0,0,0,.6);
}
.navline button { min-height: 58px !important; }
'''
m = m.replace('</style>', css + '</style>', 1)

# Plan complete. Back up before touching live files.
stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
backup = root / 'backups' / f'v24-{stamp}'
backup.mkdir(parents=True, exist_ok=False)
for p in (remote, phone):
    shutil.copy2(p, backup / p.name)
# Do not copy the old key into backups: intentionally revoke it.

# Write files atomically. On an exception, restore from backup and do not rotate.
def atomic_write(p: Path, data: str, mode=0o644):
    fd, temp_name = tempfile.mkstemp(dir=p.parent, prefix='.pitv-v24-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(temp_name, mode)
        os.replace(temp_name, p)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)

try:
    atomic_write(remote, s, remote.stat().st_mode & 0o777)
    atomic_write(phone, m, phone.stat().st_mode & 0o777)
    # Generate fresh cryptographically secure 256-bit key; invalidate exposed old one.
    new_token = secrets.token_urlsafe(32)
    atomic_write(token, new_token + '\n', 0o600)
except Exception:
    shutil.copy2(backup / 'remote.py', remote)
    shutil.copy2(backup / 'phone-remote.html', phone)
    raise

print('\nPiTV V2.4 installerad!')
print('✓ Ny fjärrkontrollsnyckel genererad. Den gamla blir ogiltig efter omstart.')
print('✓ Nycklar maskeras i nya HTTP-loggar.')
print('✓ Hem går direkt till TV-startsidan via Chromiums adressfält.')
print('✓ Bakåt ger webbläsarens historiksteg och fokuserar Chromium.')
print('✓ Hem/Bakåt sitter fast längst ned på Android-fjärrkontrollen.')
print(f'✓ Säkerhetskopior utan gammal nyckel: {backup}')
print('\nOBSERVERA: Den gamla fjärrlänken slutar fungera efter omstart.')
print('Kör nu: sudo reboot')
print('När Pi:n startat, kör följande kommando på Pi:n för din NYA privata mobiladress:')
print('  printf "http://%s:8765/?key=%s\\n" "$(hostname -I | awk \'{print $1}\')" "$(cat ~/pi-tv/remote-token)"')
print('Skicka INTE nyckeln eller den fullständiga adressen i chatten.')
print('Återställ gränssnitt vid problem genom att kopiera backupfilerna, sedan starta om.')
