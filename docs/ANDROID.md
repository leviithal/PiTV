# Native Android-app: bygg på Windows och installera

**Det här är en riktig Android-app i Kotlin**, inte en WebView eller en bokmärkesgenväg. Appen styr lokalt PiTV API V3 på HTTPS/8766.

## Programkrav

- Windows 10/11 med PowerShell, Android Studio och Android SDK Platform **35**.
- JDK 21 (t.ex. Eclipse Temurin 21). **Gradle 8.11.1 ska inte köras med Java 25**. Din vanliga Android Studio kan fortfarande använda Java 25 i andra projekt. Se officiell Gradle-kompatibilitetsmatris.
- Internet vid första Gradle-nedladdningen. Projektet använder AGP 8.9.2/Kotlin 2.2.20 och Gradle 8.11.1.

JDK 21 kan installeras med:

```powershell
winget install --id EclipseAdoptium.Temurin.21.JDK --exact --source winget
```

SDK 35 installeras via **Android Studio → Tools → SDK Manager → SDK Platforms → Android 15 (API 35)**. Du behöver inte avinstallera SDK 37 om du har den.

## Bygg

Öppna PowerShell i repo-mappen:

```powershell
cd .ndroid
Set-ExecutionPolicy -Scope Process Bypass
.uild-android-jdk21.ps1
```

Byggskriptet söker JDK 21/17, inte en eventuellt inkompatibel Java 25. För Windows-konton med `&` eller mellanslag i sökvägen använder det tillfällig `SUBST`-enhet och städar efteråt.

Vid lyckat bygge skapas:

`android/PiTV-Remote-installera-pa-Android.apk`

Denna debug-signerade APK fungerar för privat test, men **bygg och signera en riktig release** om du vill distribuera APK offentligt. Publicera inte debug- eller privata signeringsnycklar.

## Installera på Android

- Överför APK:n via Quick Share, USB-filöverföring eller annan betrodd kanal.
- Öppna APK:n i telefonens filhanterare, godkänn engångsinstallation från den valda källan och installera.
- Starta PiTV Remote. Fyll i Pi:ns IP, API-nyckeln och certifikatets SHA-256-fingeravtryck.
- På Pi: `bash ~/pi-tv-v3/show-connection.sh` – använd uppgifterna på enheten, dela dem aldrig i en logg eller issue.

Om telefon och Pi ligger i olika VLAN måste brandväggen tillåta TCP 8766. HTTP-port 8765 är inte avsedd för Android-appen.

## Kända felsituationer

`JAVA_HOME` saknas: installera JDK 21 och använd det korrigerade byggskriptet.

`'M' is not recognized`: Windows-konton med `F&M` eller annat `&` kan förstöra äldre Gradle batch-anrop – byggskriptet här använder SUBST.

`25.0.3` som enda fel: Gradle 8.11.1 försöker startas med Java 25, använd JDK 21.

`android-35/android.jar` saknas: installera SDK Platform 35 trots att SDK 37 finns.

Fel certifikat: kör `show-connection.sh` igen och kontrollera om Pi:ns IP/certifikat har ändrats. Bygg inte om Android-appen bara för certifikatbyte.
