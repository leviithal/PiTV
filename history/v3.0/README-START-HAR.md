# PiTV V3 – Windows → Raspberry Pi → riktig Android-app

Det här paketet utgår från din granskade PiTV V2.4 (Raspberry Pi OS Trixie, labwc, Chromium + Widevine). **V2.4 med fungerande Netflix och Disney+ lämnas oförändrad under testet.** V3 installerar bara en parallell HTTPS-server på port 8766 och en Android-app. Appen är native Kotlin, inte en webbsida/WebView/PWA.

## Vad ingår?

- `Pi/`: HTTPS-kommandoserver, installerare, statuskontroll, säker anslutningsinformation, valfri åtstramning av V2 och återställning.
- `Android/PiTVRemote/`: Native Android-app med pilar/OK, Back, ljud, play/paus, reservmus, tangentbord, status och säker inställningslagring.
- `Android/build-android.ps1`: Bygger en **debug-signerad installerbar APK** på Windows. Kräver Android SDK via Android Studio och internet första gången.
- `tests/`: Isolerade API-tester utan åtkomst till din verkliga Pi.

**Viktigt:** Ingen APK är förbyggd i paketet. Byggsteget måste utföras på Windows med Android SDK. Jag har inte kunnat köra ett Android SDK-bygge eller telefonstest här. Serverns isolerade integrationstester och installerarens syntax är kontrollerade.

## 1. Lägg ZIP på Windows

Packa upp `PiTV-V3-komplett.zip` till exempelvis `C:\PiTV-V3`. Öppna PowerShell.

Kontrollera adressen på Pi:n med `hostname -I` på Pi:n. Byt sedan IP-adressen nedan:

```powershell
ssh pi@192.168.1.XX "mkdir -p ~/pitv-v3-upload"
scp -r "C:\PiTV-V3\Pi" pi@192.168.1.XX:~/pitv-v3-upload/
```

Resultat på Pi:n: `~/pitv-v3-upload/Pi/install-v3.sh`. Om ZIP-filen har packats upp med en extra överordnad mapp, öppna den i Utforskaren och justera Windows-sökvägen till den faktiska `Pi`-mappen.

## 2. Installera på Pi:n (SSH från Windows)

```powershell
ssh pi@192.168.1.XX
```

Kör dessa på Pi:n:

```bash
bash ~/pitv-v3-upload/Pi/install-v3.sh
sudo reboot
```

Installationsskriptet installerar V3 i `~/pi-tv-v3`, skapar stark unik token och självsignerat TLS-certifikat, registrerar en systemd-användartjänst och startar den när labwc är redo. Det avinstallerar ingenting från V2.4.

## 3. Efter omstart – verifiera Pi och få anslutningsuppgifter

SSH:a in igen. Kör:

```bash
bash ~/pi-tv-v3/check-v3.sh
bash ~/pi-tv-v3/show-connection.sh
```

Om `check-v3.sh` saknas kan du köra `systemctl --user status pitv-v3.service`, men den ordinarie installeraren ska kopiera kontrollskriptet till `~/pi-tv-v3`.

`check-v3.sh` ska visa `active (running)` samt ett JSON-svar med `"server":"online"`. `show-connection.sh` visar tre fält: Pi IP, API-nyckel, certifikatets SHA-256-fingeravtryck. **Skicka inte nyckeln till någon** och dela inte skärmbilder med den.

## 4. Bygg APK på Windows

Installera Android Studio från https://developer.android.com/studio (om det saknas). Starta Studio och installera **Android SDK Platform 35**, Android SDK Build-Tools och Android SDK Platform-Tools via `Tools → SDK Manager`. JDK 17 ingår vanligtvis i Studio.

Öppna PowerShell från `C:\PiTV-V3\Android`:

```powershell
cd C:\PiTV-V3\Android
Set-ExecutionPolicy -Scope Process Bypass
.\build-android.ps1
```

Detta hämtar Gradle 8.11.1 första gången, bygger appen och skapar `C:\PiTV-V3\Android\PiTV-Remote-installera-pa-Android.apk`. Om byggverktyget klagar, öppna mappen `PiTVRemote` i Android Studio och bygg med `Build → Build APK(s)`; APK:n hittas då i `PiTVRemote\app\build\outputs\apk\debug\app-debug.apk`.

**Det här är en debug-signerad APK för privat testning**, inte en Play Store-/release-signerad app. Håll kvar samma Windows-byggmiljö/keystore för framtida uppgraderingar.

## 5. Lägg APK på Android och installera

Överför APK-filen från Windows till **telefonen**, t.ex. med USB, Nearby Share/Quick Share eller annan betrodd filöverföring. Öppna APK på Android. Godkänn installation från den betrodda filhanteraren om Android frågar. Stäng sedan av tillståndet för okända appar igen.

Öppna **PiTV Remote** i applistan. Skriv:

1. Pi IP – adressen från `show-connection.sh`, **utan** `https://` och utan port.
2. API-nyckel – från Pi, kopieras helst privat med ditt vanliga terminalprogram.
3. SHA-256-fingeravtryck – hela strängen från Pi. Om den inte stämmer vägrar appen anslutning.

Tryck **Anslut säkert**. Om status blir ansluten kan du prova **vänster/höger/OK**, sedan **Bakåt** och **Volym**. Ingen Hem-/Netflix-/Disney+-snabbknapp finns i appen.

**TV-startsidans Netflix och Disney+ behålls som tidigare.** Att filmen reagerar är ett manuellt test som servern inte kan garantera.

## 6. Efter att appen verkligen fungerar: lås ned gamla fjärrservern (valfritt)

Den gamla V2-servern lyssnar fortfarande på port 8765 via HTTP. När den nya appen fungerar kan du begränsa den gamla till endast localhost:

```bash
bash ~/pi-tv-v3/lockdown-v2.sh
sudo reboot
```

Detta påverkar inte att Chromium lokalt öppnar TV-startsidan på `127.0.0.1:8765`. Den **gamla mobilens webbfjärrkontroll** slutar däremot fungera, som avsett. V3 fortsätter på HTTPS 8766. Portforwarda ingen av portarna från internet och ha telefon och Pi på betrott nät, inte isolerat gäst-Wi-Fi.

## 7. Felsökning

```bash
systemctl --user status pitv-v3.service --no-pager
journalctl --user -u pitv-v3.service -n 40 --no-pager
bash ~/pi-tv-v3/check-v3.sh
```

- **401**: Felaktig API-nyckel (ingen nyckel i URL eller logg).
- **TLS/fingerprintfel**: Kontrollera IP och SHA-256. Certifikatet är kopplat till Pi:ns IP vid installation; vid ny IP kör `bash ~/pi-tv-v3/renew-certificate.sh` och uppdatera SHA-256 i appens inställningar. Certifikatet ska verifieras på nytt.
- **Offline**: Kontrollera systemd-tjänst, IP, TCP/8766 och UniFi-klientisolering/VLAN-brandvägg.
- **Skickat men inget händer**: Kontrollera att Chromium är på aktivt labwc-skrivbord; kommandot kan ha skickats även om TV:n inte reagerade.
- **Netflix/Disney+ fel**: Backa inte tillbaka Chromium/Widevine; V3 rör dem inte.

## 8. Ångra V3

```bash
bash ~/pi-tv-v3/rollback-v3.sh
sudo reboot
```

Det tar bort V3-autostarten och återställer V2 fjärrserverns bindning om lockdown hade körts. Dina nya certifikat/nycklar ligger kvar lokalt för eventuell felsökning. Inga streamingprofiler tas bort.

## Säkerhets- och driftgränser

TLS används med **manuellt verifierat certifikatfingeravtryck**, vilket hindrar obehöriga servrar om du kontrollerar fingeravtrycket från Pi:n. Telefonens token lagras krypterad med Android Keystore och skickas i HTTP Authorization-header **över TLS**, aldrig i URL. Certifikatet är självsignerat och har ett års giltighet; vid utgång krävs planerad certifikatsförnyelse/omparkoppling. PiTV-servern lyssnar på 0.0.0.0:8766 för lokala nät; använd brandvägg/VLAN och exponera inte tjänsten externt. TLS skyddar trafiken men ger inte automatiskt rätt åtkomst över ditt UniFi-gästnät.

Appen är en Android-fjärr till webbläsaren: den **förvandlar inte Netflix/Disney+ till deras officiella TV-appar**, och DRM-/webbplatsnavigering är beroende av befintliga Chromium-uppspelningen. D-pad-buggar i V2:s webbplatstillägg är inte ändrade i detta paket.
