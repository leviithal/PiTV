#!/usr/bin/env bash
# PiTV Mini V2.1: focus Chromium before keyboard input; make Enter actionable when a tile is focused.
# Does not touch Chromium profile, DRM, package versions or the remote key.
set -euo pipefail
if (( EUID == 0 )); then echo 'Kor som vanlig Pi-anvandare, INTE sudo.'; exit 1; fi
DIR="$HOME/pi-tv"
for f in remote.py tv-home.html dpad-extension/navigation.js; do
  if [[ ! -f "$DIR/$f" ]]; then echo "Saknas: $DIR/$f. PiTV V2 maste vara installerad."; exit 1; fi
done
TS="$(date +%Y%m%d-%H%M%S)"
BACK="$DIR/backups/ok-v21-$TS"
mkdir -p "$BACK/dpad-extension"
cp -p "$DIR/remote.py" "$BACK/remote.py"
cp -p "$DIR/tv-home.html" "$BACK/tv-home.html"
cp -p "$DIR/dpad-extension/navigation.js" "$BACK/dpad-extension/navigation.js"
export PITV_DIR="$DIR"
python3 - <<'PY'
import os
from pathlib import Path
root=Path(os.environ['PITV_DIR'])
# Focus the Chromium window before wtype sends keys. With Wayland/labwc,
# key injection goes to the active window, not an arbitrary browser tab.
p=root/'remote.py'
s=p.read_text()
needle="    name = data.get('action', '')\n    if name in URLS:"
replace="""    name = data.get('action', '')
    # PiTV is designed for one fullscreen Chromium window.
    # Re-focus it before keyboard actions; if window discovery is unavailable,
    # keep the existing behavior and let wtype report input failures.
    if name in URLS or name in KEYS or name in ('home', 'back', 'close'):
        try:
            subprocess.run(('wlrctl', 'toplevel', 'focus', 'chromium'),
                           check=False, timeout=2,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError):
            pass
    if name in URLS:"""
if 'PiTV is designed for one fullscreen Chromium window' in s:
    print('remote.py: fokusfix finns redan')
elif needle in s:
    p.write_text(s.replace(needle, replace, 1))
    print('remote.py: Chromium-fokus före knapparna')
else:
    raise SystemExit('remote.py har annat innehall an forvantat; avbryter utan att gissa.')
# Make the launcher respond reliably to Return even if focus was lost.
p=root/'tv-home.html'
s=p.read_text()
needle="window.addEventListener('keydown',e=>{if(!['ArrowRight','ArrowLeft','ArrowUp','ArrowDown'].includes(e.key))return;const index=buttons.indexOf(document.activeElement);let next=index;"
replace="""window.addEventListener('keydown',e=>{
  if(e.key==='Enter' && e.target instanceof HTMLElement && e.target.closest('button[data-app]')){
    e.preventDefault();e.stopImmediatePropagation();
    e.target.closest('button[data-app]').click();return;
  }
  if(!['ArrowRight','ArrowLeft','ArrowUp','ArrowDown'].includes(e.key))return;
  const index=buttons.indexOf(document.activeElement);let next=index;"""
if "e.target.closest('button[data-app]').click();return;" in s:
    print('tv-home.html: OK-fix finns redan')
elif needle in s:
    p.write_text(s.replace(needle, replace, 1))
    print('tv-home.html: explicit Enter/OK pa startplattan')
else:
    raise SystemExit('tv-home.html har annat innehall an forvantat; avbryter.')
# The V2 extension only clicked when an internal selection was already stored;
# initialize selection from actual DOM focus, otherwise select the first option.
p=root/'dpad-extension/navigation.js'
s=p.read_text()
old="""if(e.key==='Enter'){
  if(active&&document.contains(active)){e.preventDefault();e.stopImmediatePropagation();active.click();}
  return;
 }"""
new="""if(e.key==='Enter'){
  const list=candidates();
  const nativeFocus=document.activeElement;
  const target=(active&&list.includes(active))?active:(list.includes(nativeFocus)?nativeFocus:null);
  if(target){
    e.preventDefault();e.stopImmediatePropagation();
    remember(target);target.click();
  }else if(list.length){
    // Nothing is selected yet: show a selection instead of silently doing nothing.
    e.preventDefault();e.stopImmediatePropagation();first();
  }
  return;
 }"""
if 'Nothing is selected yet: show a selection' in s:
    print('navigation.js: OK-fix finns redan')
elif old in s:
    p.write_text(s.replace(old,new,1))
    print('navigation.js: OK valjer synlig knapp eller markerar forsta valet')
else:
    raise SystemExit('navigation.js har annat innehall an forvantat; avbryter.')
PY
python3 -m py_compile "$DIR/remote.py"
if command -v node >/dev/null 2>&1; then node --check "$DIR/dpad-extension/navigation.js"; fi
echo
echo 'Klart! Backup:' "$BACK"
echo 'Nu kraver andringen omstart for ny fjarrserver och Chromium-tillagg:'
echo '  sudo reboot'
echo 'Aterstall vid behov: kopiera tillbaka filerna fran backupkatalogen och starta om.'
