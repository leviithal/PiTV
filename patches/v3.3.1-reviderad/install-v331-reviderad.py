#!/usr/bin/env python3
"""PiTV V3.3.1 REVIDERAD - complete, fail-closed upgrade V3.2 -> V3.3.1.

Does NOT require V3.3. Preserves Chrome profile, Widevine, PiTV HTTPS API,
Android APK, browser Back service worker and automatic film fullscreen.

--check: read-only preflight; --install: checks again, backups, updates only
manifest.json, navigation.js, start.sh and adds navigation-core.js.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

EXT_VERSION_FROM = '2.2.0'
EXT_VERSION_TO = '2.3.1'
START_SENTINEL = '--kiosk --start-maximized'
TRANSLATE_FLAG = '--disable-features=Translate'
TARGET_NAMES = ('manifest.json', 'navigation.js', 'start.sh', 'navigation-core.js')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def assert_syntax(src: Path, start: bytes):
    subprocess.run(['bash', '-n'], input=start, check=True, capture_output=True)
    if shutil.which('node'):
        for f in ('navigation.js', 'navigation-core.js'):
            result = subprocess.run(['node', '--check', str(src / f)], capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(f'JavaScript-syntaxfel {f}: {result.stderr.strip()}')


def stage(ext: Path, start_path: Path, source: Path):
    manifest_path = ext / 'manifest.json'
    nav_path = ext / 'navigation.js'
    core_path = ext / 'navigation-core.js'
    original_paths = {
        'manifest.json': manifest_path,
        'navigation.js': nav_path,
        'start.sh': start_path,
    }
    for path in [*original_paths.values(), ext / 'pitv-background.js', ext / 'pitv-auto-fullscreen.js']:
        if not path.is_file():
            raise RuntimeError(f'Saknad V3.2-fil: {path}')
    if core_path.exists():
        raise RuntimeError('navigation-core.js finns redan: förväntade en orörd V3.2. Avbryter.')
    for f in ('navigation.js', 'navigation-core.js'):
        if not (source / f).is_file():
            raise RuntimeError(f'Paketet saknar: {f}')

    old = {name: path.read_bytes() for name, path in original_paths.items()}
    oldm = json.loads(old['manifest.json'])
    if oldm.get('manifest_version') != 3 or oldm.get('version') != EXT_VERSION_FROM:
        raise RuntimeError(f'Kräver V3.2 (manifest {EXT_VERSION_FROM}); hittade {oldm.get("version")}')
    if oldm.get('background', {}).get('service_worker') != 'pitv-background.js':
        raise RuntimeError('V3.1:s Bakåt-service-worker känns inte igen.')
    if 'pitv-browser-back' not in oldm.get('commands', {}):
        raise RuntimeError('V3.1:s Bakåt-genväg saknas.')
    scripts = oldm.get('content_scripts', [])
    if not isinstance(scripts, list):
        raise RuntimeError('Ogiltigt content_scripts i manifest.')
    navs = [s for s in scripts if isinstance(s, dict) and 'navigation.js' in s.get('js', [])]
    movies = [s for s in scripts if isinstance(s, dict) and 'pitv-auto-fullscreen.js' in s.get('js', [])]
    if len(navs) != 1 or navs[0].get('js') != ['navigation.js'] or len(movies) != 1:
        raise RuntimeError('V3.2:s D-pad eller filmhelskärm stämmer inte med väntad filordning.')
    if movies[0].get('js') != ['pitv-auto-fullscreen.js']:
        raise RuntimeError('V3.2:s filmhelskärmsmodul har ändrats.')
    nav_matches = navs[0].get('matches', [])
    if not any('netflix.com' in m for m in nav_matches) or not any('disneyplus.com' in m for m in nav_matches):
        raise RuntimeError('Netflix/Disney+ matchningsregler saknas.')
    if b'PiTV D-pad' not in old['navigation.js']:
        raise RuntimeError('Den äldre navigation.js känns inte igen. Ingen ändring.')

    start_text = old['start.sh'].decode('utf-8')
    if start_text.count(START_SENTINEL) != 1:
        raise RuntimeError('Kioskstarten i start.sh känns inte igen eller förekommer flera gånger.')
    if '--disable-features=' in start_text:
        raise RuntimeError('start.sh har redan disable-features. Avbryter för att undvika dubbel inställning.')
    if 'dpad-extension' not in start_text:
        raise RuntimeError('Chromium verkar inte ladda vårt D-pad-tillägg.')
    new_start = start_text.replace(START_SENTINEL, f'{TRANSLATE_FLAG} {START_SENTINEL}', 1).encode('utf-8')

    navs[0]['js'] = ['navigation-core.js', 'navigation.js']
    navs[0]['matches'] = [m for m in nav_matches if 'youtube.com' not in m.lower()]
    if not navs[0]['matches']:
        raise RuntimeError('Tomma matchningsregler efter uppdateringen.')
    oldm['version'] = EXT_VERSION_TO
    oldm['description'] = 'PiTV 3.3.1 Reviderad: spatial navigation, Disney+ scroll and Netflix play intent.'
    new_manifest = (json.dumps(oldm, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    new_nav = (source / 'navigation.js').read_bytes()
    new_core = (source / 'navigation-core.js').read_bytes()
    if len(new_nav) < 7000 or len(new_core) < 400:
        raise RuntimeError('Navigeringsfilerna verkar vara ofullständiga.')
    if b'PiTV 3.3.1' not in new_nav or b'PiTV 3.3' not in new_core:
        raise RuntimeError('Uppdateringspaketet innehåller fel navigeringsversion.')
    assert_syntax(source, new_start)
    changed = {
        'manifest.json': new_manifest,
        'navigation.js': new_nav,
        'start.sh': new_start,
        'navigation-core.js': new_core,
    }
    if json.loads(new_manifest)['content_scripts'][scripts.index(navs[0])]['js'] != ['navigation-core.js', 'navigation.js']:
        raise RuntimeError('Manifestets ordning kunde inte verifieras.')
    return original_paths, old, changed


def atomic(path: Path, payload: bytes, mode: int):
    tmp = path.with_name('.' + path.name + '.v331r-temp-' + str(os.getpid()))
    try:
        with tmp.open('wb') as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        tmp.chmod(mode)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description='PiTV V3.3.1 Reviderad: direkt V3.2 -> V3.3.1')
    selection = ap.add_mutually_exclusive_group(required=True)
    selection.add_argument('--check', action='store_true', help='Ingen ändring görs')
    selection.add_argument('--install', action='store_true', help='Backup och uppgradering')
    ap.add_argument('--extension-dir', type=Path, default=Path.home() / 'pi-tv/dpad-extension')
    ap.add_argument('--start-file', type=Path, default=Path.home() / 'pi-tv/start.sh')
    ap.add_argument('--backup-root', type=Path, default=Path.home() / 'pi-tv-v331-reviderad-backups')
    a = ap.parse_args()
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        raise RuntimeError('Kör som vanlig Pi-användare, aldrig sudo.')
    ext = a.extension_dir.expanduser().resolve()
    start_path = a.start_file.expanduser().resolve()
    source = Path(__file__).resolve().parent
    original_paths, old, updated = stage(ext, start_path, source)
    print('Förkontroll OK: V3.2 (manifest 2.2.0) igenkänd.')
    print('V3.3 behöver INTE installeras först.')
    print('Endast manifest.json, navigation.js, start.sh samt NY navigation-core.js påverkas.')
    print('Netflix/Disney+ Widevine, profil, Android-app och API lämnas orörda.')
    if a.check:
        print('Ingen fil, backup eller inställning har ändrats.')
        return

    root = a.backup_root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = root / ('backup-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + str(os.getpid()))
    backup.mkdir(mode=0o700)
    modes = {name: stat.S_IMODE(path.stat().st_mode) for name, path in original_paths.items()}
    for name, data in old.items():
        f = backup / name
        f.write_bytes(data)
        f.chmod(0o600)
    record = {
        'format': 2,
        'release': 'PiTV V3.3.1 Reviderad',
        'from': '3.2', 'to': '3.3.1-reviderad',
        'old_sha256': {k: digest(v) for k, v in old.items()},
        'new_sha256': {k: digest(v) for k, v in updated.items()},
        'old_modes': modes,
    }
    (backup / 'record.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    (backup / 'in-progress').write_text('installing\n', encoding='ascii')
    targets = {**original_paths, 'navigation-core.js': ext / 'navigation-core.js'}
    try:
        for name in TARGET_NAMES:
            atomic(targets[name], updated[name], modes.get(name, 0o644))
        for name in TARGET_NAMES:
            if digest(targets[name].read_bytes()) != digest(updated[name]):
                raise RuntimeError(f'Efterkontroll misslyckades: {name}')
        if json.loads(targets['manifest.json'].read_text())['version'] != EXT_VERSION_TO:
            raise RuntimeError('Fel manifestversion efter installation.')
        (backup / 'installed').write_text('ok\n', encoding='ascii')
        (backup / 'in-progress').unlink(missing_ok=True)
    except BaseException:
        errors = []
        for name, data in old.items():
            try:
                atomic(targets[name], data, modes[name])
            except Exception as e:
                errors.append(f'{name}: {e}')
        try:
            targets['navigation-core.js'].unlink(missing_ok=True)
        except Exception as e:
            errors.append(f'navigation-core.js: {e}')
        if errors:
            raise RuntimeError('Installation misslyckades och automatisk rollback var ofullständig: ' + '; '.join(errors))
        (backup / 'in-progress').unlink(missing_ok=True)
        raise
    print('\nKLART: PiTV V3.3.1 Reviderad installerad direkt från V3.2.')
    print('Din backup av ORIGINAL V3.2:', backup)
    print('Omstart: sudo reboot')
    print('Återställ direkt till V3.2 vid problem:')
    print('  python3 ~/pitv-v331-reviderad/rollback-v331-reviderad.py "' + str(backup) + '"')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('AVBRÖT: ' + str(exc), file=sys.stderr)
        sys.exit(1)
