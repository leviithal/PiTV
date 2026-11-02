# PiTV v3.3.1 Stable – nyinstallation

> **Viktigt:** Installationsskriptet är BARA för en *ny* Raspberry Pi OS Desktop 64-bit-installation. Kör inte detta på en Pi där `~/pi-tv` eller `~/pi-tv-v3` redan finns. Din befintliga fungerande PiTV V3.3.1 ska lämnas orörd.

## Förutsättningar

- Raspberry Pi 5 med lämpligt microSD/SSD, strömförsörjning och micro-HDMI–HDMI-kabel.
- Raspberry Pi OS Desktop **64-bit**, `labwc`, internetuppkoppling, vanlig användare med `sudo`-rättigheter.
- Aktuellt Chromium med Widevine installerat för den valda Raspberry Pi OS-versionen, t.ex. `sudo apt update && sudo apt full-upgrade` och, när paketen finns i dina Raspberry Pi OS-förråd, `sudo apt install chromium libwidevinecdm0`.
- Kontrollera **både Netflix och Disney+ med ljud och bild** i Chromium *innan* du installerar PiTV. DRM/CDM, tjänsternas villkor och streamingkompatibilitet garanteras inte av vårt projekt.
- Verktygen `python3 openssl wtype wlrctl wpctl systemctl labwc raspi-config chromium` måste finnas. På Raspberry Pi OS kan du normalt installera `wtype wlrctl` via `sudo apt install wtype wlrctl`; `wpctl` brukar ingå via PipeWire/WirePlumber.
- Android SDK Platform 35 + JDK 21 för att bygga Android-appen på Windows, inte för själva Pi-installationen.

## 1. Från Windows till Raspberry Pi

1. Packa upp `PiTV-v3.3.1-Stable-Install.zip` på Windows. Du får mappen `PiTV-v3.3.1-Stable`.
2. Öppna PowerShell i katalogen **ovanför** den mappen.
3. Byt `192.168.1.XX` mot Pi:ns IP och kör:

```powershell
scp -r .\PiTV-v3.3.1-Stable pi@192.168.1.XX:~/
ssh pi@192.168.1.XX
```

## 2. Läs av och installera på Pi:n

```bash
python3 ~/PiTV-v3.3.1-Stable/installer/install-v331-stable.py --check
```

Om kontrollen är godkänd **och du testat streaminguppspelning**, kör:

```bash
python3 ~/PiTV-v3.3.1-Stable/installer/install-v331-stable.py --install
```

Bekräfta med `INSTALL`. Skriptet genererar unika HTTPS-nycklar/certifikat och ställer in autostart med labwc. Det öppnar **ingen** gammal HTTP-fjärrkontroll på port 8765.

```bash
sudo reboot
```

Efter omstart (från SSH eller terminal):

```bash
python3 ~/pi-tv-v3/check.py
bash ~/pi-tv-v3/show-connection.sh
```

`show-connection.sh` visar API-nyckel och TLS SHA-256-fingeravtryck. **Publicera inte dessa.** Om enhets-IP ändras kan ett nytt certifikat och omparning behövas.

## 3. Bygg och installera Android-appen

Android-projektet ligger i `android/PiTVRemote`. Öppna Android Studio på Windows eller använd `android/build-android-jdk21.ps1` från PowerShell i `android`-mappen. JDK **21** rekommenderas för Gradle 8.11.1 och Android Gradle Plugin 8.9.2. Om projektmappen ligger under ett Windows-användarnamn med `&` stöder medföljande PowerShell-skript tillfällig enhetsbokstav.

Bygg en *debug APK* för test. Installera den via Quick Share, filöverföring eller `adb install -r`. Öppna PiTV Remote och ange IP, port 8766, API-nyckel samt certifikatfingeravtryck.

## 4. Testlista vid TV:n

- [ ] Pi:n autostartar till en startsida med **Netflix** och **Disney+** (inte YouTube)
- [ ] Chromium visas utan adressfält, men Netflix och Disney+ spelar med ljud
- [ ] Android-appen ansluter och vänster/höger/OK fungerar på startsidan
- [ ] Netflix navigering och filmstart fungerar i ditt gränssnitt
- [ ] Disney+ scrollar med D-pad som önskat
- [ ] Filmhelskärm fungerar och undertexter fungerar
- [ ] Bakåt går till webbläsarhistoriken utan att spola Netflix
- [ ] I `chrome://policy` syns `TranslateEnabled = false` och `AutomaticFullscreenAllowedForUrls` utan fel
- [ ] Appen återansluter efter en **fullständig omstart**

Netflix/Disney+ kan ändra sina webbsidor så fokusnavigeringen kräver underhåll. Detta är **inte** officiella Android TV-appar och projektet innehåller inte DRM-nycklar.

## 5. Backup och rollback

Skriptet sparar original av labwc-autostart under `~/PiTV-backups/v331-...`. Den exakta sökvägen skrivs ut vid installation. Om en nyinstallation ska ångras:

```bash
python3 ~/PiTV-v3.3.1-Stable/installer/install-v331-stable.py --rollback '/home/pi/PiTV-backups/v331-EXAKT-NAMN'
sudo reboot
```

Skriv `ROLLBACK` när du tillfrågas. PiTV-filer, token och certifikat **flyttas till den privata backupkatalogen**, så de går att rädda vid behov. Autostart och service återställs. Om användarens `raspi-config`-inställningar ändrades under installationen behöver dessa återställas manuellt vid behov.

**På befintlig PiTV:** Gör i stället backup av SD-kort eller relevanta `~/pi-tv`, `~/pi-tv-v3`, `~/.config/labwc`, `/etc/chromium/policies/managed/` samt Android-projektets källa. Hantera API-token och TLS-privatnyckel privat; lägg inte med dem i GitHub-arkiv.
