# Installera PiTV på en ny Raspberry Pi 5

Denna guide bygger samma **typ av installation** som den testade versionen V3.2, men är inte en garanti för framtida Netflix-/Disney+-kompatibilitet. Kör gärna på ett eget microSD/SSD så befintlig Pi inte påverkas.

## 0. Förbered Pi:n

1. Installera aktuell **Raspberry Pi OS Desktop 64-bit** på microSD/SSD med Raspberry Pi Imager.
2. Aktivera nätverk och SSH samt ge Pi:n en egen användare (exemplen använder `pi`, men det är inte ett krav).
3. Anslut via HDMI, konfigurera lokalt skrivbord och autologin, t.ex. `sudo raspi-config` → System Options → Boot / Auto Login → Desktop Autologin.
4. Starta Chromium och verifiera att både Netflix och Disney+ fungerar med **video och ljud** innan du installerar PiTV.
5. Om Widevine saknas: på Raspberry Pi OS kan du kontrollera `apt policy chromium rpi-chromium-mods libwidevinecdm0`. Installera paket som faktiskt finns för din Pi OS-version; om du redan har fungerande uppspelning – ändra inte dessa paket i onödan.

```bash
sudo apt update
sudo apt install -y wtype wlrctl
command -v chromium
command -v wtype
command -v wlrctl
command -v wpctl
pgrep -a labwc
```

`wpctl` behövs för ljudstyrning. Om saknas, kontrollera PipeWire/WirePlumber-installation på ditt Raspberry Pi OS (paketnamn varierar).

## 1. Överför projektet från Windows

Packa upp `PiTV-GitHub-Repository.zip` så att du har mappen `PiTV-GitHub`.

```powershell
scp -r .\PiTV-GitHub pi@192.168.1.XX:~/PiTV-GitHub
ssh pi@192.168.1.XX
```

Ändra IP-adressen. PowerShell-kommandot ska köras **i katalogen ovanför** PiTV-GitHub. `scp` finns vanligtvis med Windows OpenSSH. Alternativt klona repot med Git direkt på Pi.

## 2. Kör preflight

```bash
cd ~/PiTV-GitHub
bash installer/install-fresh-pi.sh --preflight
```

Den visar vad som finns och avbryter om gamla PiTV-filer redan upptäcks. Nyinstalleraren använder inte hårdkodade IP-adresser eller inloggningsnycklar.

## 3. Installera basen, V3, V3.1 och V3.2

```bash
bash installer/install-fresh-pi.sh --install
```

Installationen: kopierar dokumenterad V2.4-kodfrysbild, genererar **ny** lokal token, startar inte publik V2-server (bindning ändras till `127.0.0.1`), lägger in labwc-autostart, kör V3-installern, V3.1, V3.2. Kan begära `sudo` för Chromium-policy, autologin och skärmsläckning. Följ utskriften. Backup tas på befintlig `labwc/autostart` när den finns.

Detta påverkar systeminställningar och skapar filer. Kör endast på avsedd ny Pi, inte på redan fungerande installationskort.

## 4. Omstart och kontroll

```bash
sudo reboot
# logga in via ssh igen
bash ~/pi-tv-v3/check-v3.sh
bash ~/PiTV-GitHub/installer/check-all.sh
```

Kontrollera att TV-startsidan visas och att **Netflix + Disney+** fungerar. Certifikatet genereras för Pi:ns IP vid installation; om du senare ändrar IP måste certifikatet förnyas och fingeravtrycket ändras i Android-appen.

## 5. Android

Följ [ANDROID.md](ANDROID.md). Kör `bash ~/pi-tv-v3/show-connection.sh` lokalt för uppgifterna. **Publicera aldrig de uppgifterna.**

## 6. Om något går fel

Håll kvar en separat fungerande installation. Återställ V3 med `bash ~/pi-tv-v3/rollback-v3.sh` om V3-installern körts och du vill avaktivera V3. V3.1 och V3.2 har egna backup- och återställningsskript som skriver ut exakta sökvägar i terminalen.

Notera att `rollback-v3.sh` också kan återställa V2:s LAN-bindning om du tidigare kört `lockdown-v2.sh`; kontrollera därför alltid port 8765 efteråt. Se [MIGRERA.md](MIGRERA.md) och [SECURITY.md](../SECURITY.md).
