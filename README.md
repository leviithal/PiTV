# PiTV – Raspberry Pi 5 som Smart-TV, med egen Android-fjärrkontroll

> **Projektet har verifierats på en verklig Raspberry Pi 5 med Netflix och Disney+ i Chromium.** 
> Ett hemmabyggt alternativ för den som redan har en Raspberry Pi, inte en officiell Chromecast eller certifierad streamingbox.

## Versionshistorik

**Historiken med commits och taggar är rekonstruerad från bevarade projektfiler i efterhand**, inte en export av den ursprungliga arbetsdatorns Git-logg. Den här repo-historiken innehåller koden från den första **PiTV Mini**-versionen till **PiTV V3.2**. De ursprungliga ändringsskripten är bevarade under `history/` och de relevanta källfilerna ligger under `src/` och `patches/`. Den samlade vägen för en helt ny Raspberry Pi ligger under `installer/`.

| Version | Förbättring |
| --- | --- |
| v1.0 | PiTV Mini: webbfjärrkontroll och Raspberry Pi-startsida |
| v2.0 | Första D-pad och TV-anpassade startsidan |
| v2.1 | Korrigering av OK-knapp och fönsterfokus |
| v2.2 | Förenklad öppning av Netflix/Disney+ och keyring-workaround |
| v2.3 | Bort med YouTube och förenklad navigering |
| v2.4 | Ny fjärrnyckel och städad mobilfjärr |
| v3.0 | Native Android-app, HTTPS, separat autentiserat API |
| v3.1 | Kiosk-läge och Bakåt genom Chromiums historik-API |
| v3.2 | Experimentell, på den ursprungliga Pi:n fungerande automatisk filmhelskärm |

## Vad fungerar?

- Netflix och Disney+ via **Chromium + Widevine** i Raspberry Pi OS Desktop.
- Egen startsida med enbart Netflix och Disney+.
- Native Android-fjärrkontroll (Kotlin), **inte** en inbäddad webbsida.
- Styrkors, OK, Bakåt, volym, play/paus och reservmus.
- HTTPS mot Pi:ns lokala port **8766**, med nyckel och certifikatets SHA-256-fingeravtryck.
- Kiosk-läge och experimentell automatisk filmhelskärm.

**Begränsningar:** Netflix och Disney+ kör fortfarande sina webbversioner. Funktionerna kan påverkas av DRM, ändringar på webbplatserna och olika skärmar. Vanliga Cast-knappen i apparna stöds inte av projektet. Den egna appen kontrollerar Pi:n, den tar inte emot officiella Google Cast-sessioner.

## Snabbstart

| Situation | Läs |
| --- | --- |
| Ny Raspberry Pi OS Desktop-installation | [Installera på ny Pi](docs/INSTALL-NY-PI.md) |
| Fungerande äldre PiTV, vill uppgradera | [Migrera befintlig Pi](docs/MIGRERA.md) |
| Windows + Android Studio | [Bygg och installera APK](docs/ANDROID.md) |
| Felsökning | [Felsökning](docs/FELSOKNING.md) |
| Lägg upp på GitHub med alla versions-taggar | [GitHub-publicering](docs/GITHUB.md) |
| Systemöversikt | [Arkitektur](docs/ARKITEKTUR.md) |
| Publicera bilder från installationen | [Skärmbilder](docs/SCREENSHOTS.md) |
| Säkerhet | [Säkerhet](SECURITY.md) |

## Plattformar och krav

- **Pi:** Raspberry Pi 5, Raspberry Pi OS **Desktop 64-bit**, labwc/Wayland, Chromium, Widevine, HDMI och en fungerande uppkoppling.
- **Mobil:** Android 8.0+ enligt Android-appens `minSdk = 26` (projektet har testats på en Android-telefon, inte på alla modeller).
- **Windowsbygg:** Android Studio, SDK **Platform 35** (SDK 37 kan vara installerad parallellt), **JDK 21**, Gradle **8.11.1**.
- **Nätverk:** Tillåt TCP 8766 mellan mobil och Pi. Håll porten borta från internet, använd ett betrott LAN/VLAN.

## Repo-karta

```text
src/pi/v2.4/           Frysbild av installerade äldre PiTV-filer (utan nycklar)
src/pi/v3.0/           PiTV HTTPS API, säkerhets-/driftskript, tester
android/PiTVRemote/   Android-källkod (Kotlin)
android/build-android-jdk21.ps1  Windowsbygg som tål & i sökvägar
patches/v3.1/         Kiosk + Bakåt
patches/v3.2/         Automatisk filmhelskärm
installer/             Säker nyinstallation och kontroller
tools/transfer-to-pi.ps1  SCP-överföring från Windows
history/               Ursprungsfiler för varje release
release-archives/      Arkiv från projektets utvecklingssteg
.github/workflows/     Test på GitHub Actions
docs/                  Installation, felsökning, arkitektur, säkerhet
```

## Creditering och varumärken

Projektet växte fram genom praktisk felsökning och testning på Raspberry Pi, med kod- och dokumentations summering med hjälp av Lokal AI. Netflix och Disney+ tillhör respektive rättighetsinnehavare. **PiTV är inte anslutet till, godkänt av eller certifierat av streamingtjänsterna.** Ingen streamingmedia, inloggning eller DRM-nyckel ingår.

Se [LICENSE-CHOICE.md](LICENSE-CHOICE.md) innan du publicerar med en öppen licens.
