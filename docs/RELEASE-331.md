# PiTV v3.3.1 – Stable release notes

**Status:** Stable på användarens testade Raspberry Pi 5-konfiguration (V3.3.1 Reviderad + Hotfix 1). **Nyinstallation från det konsoliderade paketet har inte verifierats på en andra fysisk Pi.**

## Funktioner

- Raspberry Pi 5 / Raspberry Pi OS Desktop 64-bit (labwc) som egen streamingbox
- Netflix och Disney+ i Chromium/Widevine, TV-startsida med endast två val
- Android-app i Kotlin, inte WebView: pilar, OK, Bakåt, volym, play/paus och reservmus
- Python HTTPS API på lokal port 8766 med unik API-token och självsignerat certifikat som verifieras av Android-appen
- Kiosk-läge, V3.1 webbhistorik-Bakåt, V3.2 automatisk filmhelskärm
- V3.3.1 navigering inklusive Disney-scroll och Netflix Play-hjälp
- Hotfix 1: Chromium managed policy `TranslateEnabled = false`, Netflix fallback för Play

## Underhåll och kända begränsningar

- Tjänsterna har ingen officiell PiTV-integration. Netflix/Disney+ webb-DOM och DRM-beteende kan ändras.
- Autofullskärm är beroende av plattformens tillåtna Fullscreen API. Inloggningar kan påverkas av `--password-store=basic`, som är mindre säkert än krypterad keyring-lagring.
- Nyinstallationen använder *endast* native HTTPS-API:t. Äldre HTTP V2-fjärrkontroll och dess tokens följer inte med.
- API 200 betyder att servern sänt kommandot; det garanterar inte visuellt resultat på TV:n.
- Port 8766 ska **aldrig** vidarebefordras till internet. Använd betrodd LAN/Wi-Fi och tillåt inte gästklienter utan avsikt.
- Bygget av ny APK samt nyinstallation behöver testas i respektive miljö; den faktiska Android-appen fungerade i användarens tidigare installation.

## Versionshistorik

- v1.0–v2.4: webbkontroll/prototyper, felsökning av DRM, keyring och knappar.
- v3.0: native Android och HTTPS-API.
- v3.1: kiosk-läge och riktig Chrome Back via tillägget.
- v3.2: automatisk filmhelskärm.
- v3.3: experimentell riktningsnavigering.
- v3.3.1 Reviderad: komplett navigeringsmotor utgående från v3.2.
- v3.3.1 Reviderad Hotfix 1: Netflix Play-fallback och Chromium Translate-policy; testad och fungerar hos användaren.
- **v3.3.1 Stable:** konsoliderad källkod och nyinstallationspaket utan kedja av gamla patchar; ingen ändring av streaminglogiken jämfört med HF1.

Versionshistoriken före GitHub-publiceringen är rekonstruerad från bevarade filer och är inte en ursprunglig historisk commit-logg.

## Säkerhet och immateriella rättigheter

PiTV innehåller inga appar, upphovsrättsskyddade mediefiler eller DRM-nycklar från Netflix/Disney+. Namnen är varumärken som tillhör respektive ägare. Användaren tillhandahåller egna giltiga abonnemang. Ingen licens för PiTV-koden är vald i detta paket; välj licens före offentlig publicering om återanvändningsrättigheter ska ges.
