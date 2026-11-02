# PiTV – egen Smart-TV på Raspberry Pi 5

**Senaste dokumenterade version: [PiTV v3.3.1 Stable](docs/RELEASE-331.md)** · Raspberry Pi OS Desktop · Chromium/Widevine · Native Android-fjärrkontroll · HTTPS

En fungerande återanvändningslösning för en vanlig HDMI-TV, utan Chromecast eller ny streaminghårdvara. Projektet har vuxit fram genom praktiska tester på Raspberry Pi 5. Netflix/Disney+ är webbversioner; PiTV är **inte** officiellt stödd eller certifierad av tjänsterna.

## Funktioner

- **TV-startsida** med bara Netflix och Disney+ (ingen YouTube).
- **Native Kotlin Android-app** med pilar, OK, Bakåt, volym, play/paus och reservmus.
- **HTTPS API på port 8766** med egen nyckel och certifikatfingeravtryck, utan den gamla öppna V2 HTTP-fjärrkontrollen i en nyinstallation.
- **Kiosk- och filmhelskärm**, Chromium-översättning avstängd via policy.
- **Navigeringshjälp** för Netflix-filmer och Disney+-scrollning, med försiktig fallback; webbgränssnitt kan ändras.
- **Säker installation och rollback** med backup. Nyinstallationen kräver inte att gamla reparationsskript körs i följd.

**Verifieringsnivå:** V3.3.1 Reviderad + HF1 har fungerat på den ursprungliga Raspberry Pi:n enligt användarens tester den 2 november 2026. Den nya *konsoliderade* installeraren har automatiserade isolerade tester, men har ännu inte verifierats på en andra fysisk Raspberry Pi. Android-projektets källa har bevarats; en ny APK måste byggas/testas lokalt.

## Installera

| Scenario | Instruktion |
| --- | --- |
| **Helt ny Raspberry Pi** | [Nyinstallation V3.3.1 Stable](docs/INSTALL-V331-STABLE.md) |
| **Befintlig fungerande PiTV V3.3.1** | Ändra ingenting; säkerhetskopiera SD-kort och lokala filer före framtida uppdateringar |
| Android-app från Windows | [Byggguide](docs/ANDROID.md) |
| Historiska versioner | `history/`, `patches/` och `release-archives/` |
| GitHub-release | [Publiceringsguide](docs/PUBLICERA-V331.md) |
| Säkerhet | [SECURITY.md](SECURITY.md) |

Nyinstallation på Pi efter att Netflix/Disney+ spelat med bild + ljud i Chromium:

```bash
python3 ~/PiTV-v3.3.1-Stable/installer/install-v331-stable.py --check
python3 ~/PiTV-v3.3.1-Stable/installer/install-v331-stable.py --install
sudo reboot
python3 ~/pi-tv-v3/check.py
```

**Kör aldrig den nya installeraren på en befintlig PiTV-installation.** Den vägrar som säkerhetsåtgärd att skriva över `~/pi-tv` eller `~/pi-tv-v3`.

## Arkitektur

```text
Android PiTV Remote (Kotlin, APK)
             | HTTPS :8766 + Bearer token + cert fingerprint
             v
PiTV Python API (systemd user service)
             | wtype / wlrctl / wpctl
             v
Chromium kiosk + D-pad extension + Widevine
             |                     |
       Netflix Web            Disney+ Web
```

Säkerhet: port 8766 är för ett **betrott lokalt nät**; portforwarda inte. Android-appen är ingen Cast-mottagare. Inga abonnemang, DRM-nycklar eller privata inloggningsuppgifter ingår.

## Versionsresa

| Version | Viktig milstolpe |
| --- | --- |
| v1.0–v2.4 | Prototyp, D-pad, autentisering, keyring/Netflix-felsökning, borttagning av YouTube |
| v3.0 | Native Android, autentiserat HTTPS API |
| v3.1 | Kiosk och webbläsarhistorik-Bakåt |
| v3.2 | Automatisk filmhelskärm – tidigare stabil referens |
| v3.3 | Experimentell navigation och fokus |
| v3.3.1 Reviderad | Direktuppgradering från v3.2 och Disney/Netflix-förbättringar |
| v3.3.1 HF1 | Netflix Play-fallback och Chromiums Translate-policy |
| **v3.3.1 Stable** | Sammanhållen källkod och nyinstallationspaket |

**Historiska Git-commits/taggar har rekonstruerats från bevarade filer och utgör inte en ursprunglig arbetslogg.** För fullständiga begränsningar: [release notes](docs/RELEASE-331.md) och [säkerhetsinformation](SECURITY.md).

PiTV utvecklades genom praktisk felsökning och testning med kod- och dokumentationshjälp från ChatGPT. Netflix och Disney+ är respektive företags varumärken. Välj licens före öppen återanvändning: [LICENSE-CHOICE.md](LICENSE-CHOICE.md).
