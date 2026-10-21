#!/usr/bin/env python3
"""Ta bort Netflix/Disney+-snabbknappar från enbart PiTV:s mobilfjärrkontroll."""
from pathlib import Path
from datetime import datetime
import re
import shutil

p = Path.home() / 'pi-tv' / 'phone-remote.html'
if not p.is_file():
    raise SystemExit(f'Hittar inte {p}. Ingen ändring gjord.')
s = p.read_text(encoding='utf-8')
# Bara de två mobilknapparna. Ändra inte TV-startsidan eller servern.
pattern = r'<button\b(?=[^>]*\bdata-a=["\'](?:netflix|disney)["\'])[^>]*>.*?</button>\s*'
updated, removed = re.subn(pattern, '', s, flags=re.S | re.I)
if removed == 0:
    print('Netflix/Disney+-snabbknappar saknas redan i mobilfjärrkontrollen. Ingen ändring behövs.')
    raise SystemExit(0)
# Ta bort tom apps-container, men behåll annat innehåll om det finns.
updated = re.sub(r'<div\s+class=["\']apps["\']\s*>\s*</div>\s*', '', updated, flags=re.I)
# Ingen text ska hänvisa till snabbknappar som inte längre finns.
updated = updated.replace(
    'Tryck Netflix eller Disney+ och styr med pilarna + OK. Musen finns som reserv.',
    'Styr TV:n med pilarna och OK. Musen finns som reserv.'
)
backup = p.with_name(p.name + '.bak-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
shutil.copy2(p, backup)
p.write_text(updated, encoding='utf-8')
print(f'Klart: {removed} appknapp(ar) borttagna från mobilfjärrkontrollen.')
print('TV:ns startsida, Chromium, Widevine och fjärrkontrollens nyckel är oförändrade.')
print('Säkerhetskopia:', backup)
print('Uppdatera mobilfjärrkontrollen i webbläsaren (vid behov i ny flik).')
