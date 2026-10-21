PiTV Mini V2.4 – ny nyckel och Hem/Bakåt utan scroll
========================================================

FÖRUTSÄTTNINGAR
- Raspberry Pi OS med redan fungerande PiTV V2.3.
- Kör som vanliga Pi-användaren, aldrig via sudo.
- Installerar inte om Chromium, Widevine eller Netflix/Disney+.

INSTALLERA (om ZIP laddats ned i ~/Downloads)
  cd ~/Downloads
  unzip -o pitv-v24-nyckel-hem.zip
  python3 uppdatera-pitv-v24.py
  sudo reboot

EFTER OMSTART
Öppna terminalen på Pi:n och generera den NYA mobilfjärrlänken:

  printf 'http://%s:8765/?key=%s\n' "$(hostname -I | awk '{print $1}')" "$(cat ~/pi-tv/remote-token)"

Klistra in länken på Android-telefonen och ersätt det gamla bokmärket.
Skicka aldrig din fullständiga fjärrlänk/token till någon.

TESTA
1. Öppna Netflix, scrolla långt ned och tryck Hem från mobilen.
   Förväntat: TV-startsidan visas direkt.
2. Öppna Netflix, gå in på en serie/film och tryck Bakåt.
   Förväntat: ett steg tillbaka i webbläsarhistoriken.
3. Scrolla långt ned på MOBILENS fjärrkontroll.
   Förväntat: Hem och Bakåt är alltid synliga längst ned.
4. Båda streamingtjänsterna ska fortfarande fungera.

Om Hem inte fungerar kan du kontrollera `tail -n 30 ~/.cache/pi-tv/remote.log`.
Loggning från V2.4 maskerar nya tokenvärden, men dela ändå inte hela fjärrlänken.

BACKUP/ÅTERSTÄLLNING
Filerna remote.py och phone-remote.html säkerhetskopieras under
~/pi-tv/backups/v24-ÅÅÅÅMMDD-HHMMSS/.
Den gamla nyckeln säkerhetskopieras INTE. Behåll den nya vid återställning.

Vid problem, hitta senaste backupkatalog med:
  ls -dt ~/pi-tv/backups/v24-* | head -1
Kopiera tillbaka remote.py och phone-remote.html från backupkatalogen
(ersätt BACKUPKATALOG med utskriften ovan) och kör sudo reboot.

SÄKERHET
Detta använder HTTP på lokalt nät. Port 8765 ska inte vidarebefordras
mot internet. Token skyddar fjärrkontrollen men hindrar inte avlyssning
på ett opålitligt nät. Tillåt bara familjens betrodda enheter i UniFi.
