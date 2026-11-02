#!/usr/bin/env python3
"""PiTV v3.3.1 Stable - new Raspberry Pi installation ONLY.

Does not modify an existing PiTV. --check is read-only. --install snapshots
an existing autostart before adding a single launcher. --rollback preserves
newly generated credentials by moving installed files to the backup directory.

The native Android app is built separately on Windows. No Widevine or Chromium
profiles are installed/modified. First prove Netflix & Disney+ playback manually.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import stat
import subprocess
import sys

VERSION = 'v3.3.1-stable'
SRC = Path(__file__).resolve().parents[1] / 'src/pi/v3.3.1-stable'
HOME = Path.home()
PI = HOME / 'pi-tv'
API = HOME / 'pi-tv-v3'
AUTOSTART = HOME / '.config/labwc/autostart'
SERVICE = HOME / '.config/systemd/user/pitv-v3.service'
POLICY = Path('/etc/chromium/policies/managed/pitv-v331-stable.json')
BACKUPS = HOME / 'PiTV-backups'
BEGIN = '# PITV-STABLE-3.3.1-BEGIN'
END = '# PITV-STABLE-3.3.1-END'
REQUIRED = ('python3', 'openssl', 'chromium', 'wtype', 'wlrctl', 'wpctl', 'systemctl', 'labwc', 'raspi-config')


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_ip() -> str:
    result = run('hostname', '-I', capture_output=True, text=True)
    for word in result.stdout.split():
        try:
            ip = ipaddress.ip_address(word)
            if ip.version == 4 and not ip.is_loopback and not ip.is_link_local:
                return str(ip)
        except ValueError:
            pass
    raise RuntimeError('Ingen lokal IPv4-adress hittades; kontrollera Wi-Fi/Ethernet.')


def preflight() -> str:
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        raise RuntimeError('Kör som vanlig Pi-användare, INTE sudo.')
    if platform.machine() not in ('aarch64', 'arm64'):
        raise RuntimeError('Kräver Raspberry Pi OS Desktop ARM64 (aarch64).')
    missing = [cmd for cmd in REQUIRED if not shutil.which(cmd)]
    if missing:
        raise RuntimeError('Saknade kommandon: ' + ', '.join(missing))
    for p in (PI, API, SERVICE):
        if p.exists():
            raise RuntimeError(f'Befintlig installation/fil: {p}. Inget får skrivas över.')
    if POLICY.exists():
        raise RuntimeError(f'Chromium-policy finns redan: {POLICY}. Avbryter.')
    if AUTOSTART.is_file() and BEGIN in AUTOSTART.read_text(encoding='utf-8'):
        raise RuntimeError('PiTV Stable finns redan i labwc autostart.')
    required_files = ('server.py', 'start.sh', 'tv-home.html', 'chromium-policy.json',
                      'dpad-extension/manifest.json', 'dpad-extension/navigation.js',
                      'dpad-extension/navigation-core.js', 'dpad-extension/pitv-background.js',
                      'dpad-extension/pitv-auto-fullscreen.js')
    for name in required_files:
        if not (SRC / name).is_file():
            raise RuntimeError(f'Installationspaketet saknar {name}')
    manifest = json.loads((SRC / 'dpad-extension/manifest.json').read_text(encoding='utf-8'))
    if manifest.get('version') != '2.3.1':
        raise RuntimeError('Fel manifestversion i källkodspaketet')
    pol = json.loads((SRC / 'chromium-policy.json').read_text(encoding='utf-8'))
    if pol.get('TranslateEnabled') is not False or 'AutomaticFullscreenAllowedForUrls' not in pol:
        raise RuntimeError('Ogiltig Chromium-policy')
    return local_ip()


def snapshot_original(dest: Path, backup: Path, name: str):
    if dest.exists():
        shutil.copy2(dest, backup / (name + '.before'))
        return True
    return False


def service_text():
    return '''[Unit]
Description=PiTV v3.3.1 HTTPS remote (Android)
After=default.target
[Service]
Type=simple
WorkingDirectory=%h/pi-tv-v3
ExecStart=/usr/bin/python3 %h/pi-tv-v3/server.py
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
UMask=0077
[Install]
WantedBy=default.target
'''


def install():
    ip = preflight()
    print('Förkontroll godkänd. Chromecast-liknande casting ingår INTE.')
    print('Kontrollera att Netflix och Disney+ spelar med ljud i Chromium INNAN installation.')
    print('Installation aktiverar Desktop Autologin och inaktiverar skärmsläckning om raspi-config stöder det.')
    if input('Skriv INSTALL för att fortsätta: ').strip() != 'INSTALL':
        print('Avbrutet utan ändringar.'); return
    # Request sudo before any file change. Needed for ONLY managed Chromium policy and raspi-config.
    run('sudo', '-v')
    backup = BACKUPS / ('v331-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + str(os.getpid()))
    backup.mkdir(parents=True, mode=0o700)
    state = {'release': VERSION, 'autostart_existed': snapshot_original(AUTOSTART, backup, 'autostart'),
             'service_existed': False, 'policy': str(POLICY), 'installed': False}
    (backup / 'state.json').write_text(json.dumps(state, indent=2)+'\n', encoding='utf-8')
    try:
        shutil.copytree(SRC, PI, ignore=shutil.ignore_patterns('server.py','chromium-policy.json','show-connection.sh','renew-certificate.sh'))
        PI.chmod(0o700)
        (PI / 'start.sh').chmod(0o700)
        API.mkdir(mode=0o700)
        for filename in ('server.py','show-connection.sh','renew-certificate.sh','check.py'):
            shutil.copy2(SRC / filename, API / filename)
            (API / filename).chmod(0o700)
        tok = API / 'api-token'
        with tok.open('x', encoding='ascii') as out:
            out.write(secrets.token_urlsafe(32) + '\n')
        tok.chmod(0o600)
        run('openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-nodes', '-days', '365', '-sha256',
            '-keyout', str(API/'tls-key.pem'), '-out', str(API/'tls-cert.pem'),
            '-subj', '/CN=PiTV Stable',
            '-addext', f'subjectAltName=IP:{ip},IP:127.0.0.1,DNS:localhost',
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        (API/'tls-key.pem').chmod(0o600)
        (API/'tls-cert.pem').chmod(0o644)
        SERVICE.parent.mkdir(parents=True,exist_ok=True)
        SERVICE.write_text(service_text(),encoding='utf-8')
        AUTOSTART.parent.mkdir(parents=True,exist_ok=True)
        with AUTOSTART.open('a',encoding='utf-8') as out:
            out.write(f'\n{BEGIN}\n"{PI / "start.sh"}" &\n{END}\n')
        run('sudo','install','-D','-m','0644',str(PI/'chromium-policy.json') if (PI/'chromium-policy.json').exists() else str(SRC/'chromium-policy.json'),str(POLICY))
        run('systemctl','--user','daemon-reload')
        state['installed'] = True
        (backup/'state.json').write_text(json.dumps(state, indent=2)+'\n',encoding='utf-8')
    except BaseException:
        print('Installationen avbröts. Försöker återställa filer. Backup:',backup,file=sys.stderr)
        rollback(backup, automatic=True)
        raise
    # Only system settings are best-effort, not part of the rollback.
    for args in [('nonint','do_blanking','1'),('nonint','do_boot_behaviour','B4')]:
        cp=subprocess.run(['sudo','raspi-config',*args],check=False)
        if cp.returncode:
            print('OBS: raspi-config misslyckades för',args[-2:],'- välj Desktop Autologin/blanking manuellt.')
    print('\nPiTV v3.3.1 Stable installerad som NY installation. Backup:', backup)
    print('Starta om: sudo reboot')
    print('Kontrollera: python3 ~/pi-tv-v3/check.py')
    print('Android-parning: bash ~/pi-tv-v3/show-connection.sh (dela aldrig nyckeln)')


def rollback(backup: Path, automatic=False):
    b = backup.expanduser().resolve()
    if b.parent != BACKUPS.resolve() or not b.name.startswith('v331-') or not (b/'state.json').is_file():
        raise RuntimeError('Backup-katalogen känns inte igen. Återställning avbruten.')
    state = json.loads((b/'state.json').read_text(encoding='utf-8'))
    if state.get('release') != VERSION:
        raise RuntimeError('Fel backupversion.')
    if not automatic:
        print('Detta avaktiverar PiTV Stable; filer och nycklar flyttas till backupen, raderas INTE.')
        if input('Skriv ROLLBACK för att fortsätta: ').strip() != 'ROLLBACK':
            print('Avbrutet'); return
    subprocess.run(['systemctl','--user','stop','pitv-v3.service'],check=False)
    if PI.exists():
        PI.rename(b/'pi-tv-retained')
    if API.exists():
        API.rename(b/'pi-tv-v3-retained')
    if SERVICE.is_file(): SERVICE.unlink()
    if state.get('autostart_existed'):
        shutil.copy2(b/'autostart.before', AUTOSTART)
    elif AUTOSTART.exists():
        AUTOSTART.unlink()
    if POLICY.exists():
        subprocess.run(['sudo','rm','-f','--',str(POLICY)],check=True)
    subprocess.run(['systemctl','--user','daemon-reload'],check=False)
    print('Återställd. Tidigare genererade hemligheter finns kvar under:',b)


def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--check',action='store_true',help='Skrivskyddad kontroll')
    g.add_argument('--install',action='store_true',help='Bara ny Pi; kräver bekräftelse')
    g.add_argument('--rollback',type=Path,metavar='BACKUP',help='Återställ från exakt backup-sökväg')
    args=ap.parse_args()
    if hasattr(os,'geteuid') and os.geteuid()==0:
        raise RuntimeError('Kör som vanlig användare, aldrig sudo.')
    if args.check:
        print('FÖRKONTROLL OK: ny Pi, ARM64/labwc, alla filer/verktyg och IPv4 finns:',preflight())
        print('Inga filer ändrade. Netflix/Disney+ video+audio måste testas manuellt.')
    elif args.install:install()
    else:rollback(args.rollback)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('AVBRÖT:',exc,file=sys.stderr);sys.exit(1)
