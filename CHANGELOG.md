# Ändringshistorik

Se **Git-taggarna v1.0 till v3.2** och mappen `history/` för källorna till varje steg.

## v3.2 (21 oktober 2026)
- Försök att sätta faktisk videospelare i fullskärm vid uppspelning genom separat Chromium content script och lokal policy; användaren bekräftade att det fungerade på sin test-Pi.
- Funktionen är experimentell och förändringar i streamingwebbplatser kan påverka beteendet.

## v3.1 (21 oktober 2026)
- Chromium startas i kiosk-läge.
- Bakåt via Chromium-tilläggets `chrome.tabs.goBack` i stället för `Alt+Left`, som kunde spola video.

## v3.0 (19–21 oktober 2026)
- Native Android-app med D-pad, volym, media, back och reservstyrplatta.
- HTTPS/Python-server 8766, API-token i header och certifikat-pin, systemd-användartjänst.
- Gradle 8.11.1 + SDK 35/JDK 21. Förbättrat PowerShell-skript hanterar `&` i Windows-sökvägar.

## v2.4 (19 oktober 2026)
- Roterad webb-token och loggmaskering, Hem borttagen från mobilfjärren, appgenvägar borttagna.
- Faktiskt insamlad kodfrysbild under `src/pi/v2.4/`.

## v2.3 (19 oktober 2026)
- YouTube bort från TV-startsida; förenklat fjärrgränssnitt.

## v2.2 (19 oktober 2026)
- Direktnavigering till streamingtjänster i samma Chromium-flik, keyring-workaround, kontrollerad återställning.

## v2.1 (19 oktober 2026)
- Försök att få OK/Enter att fungera även när Chromium saknar fokus.

## v2.0 (19 oktober 2026)
- D-pad, UI och Chromium-tillägg för spatial navigering.

## v1.0 (18 oktober 2026)
- Första PiTV Mini med startsida och HTTP/webbfjärr.

*Dateringen är projektets dokumenterade samtal/tillkomst, inte officiella utgivningsdatum i någon appbutik.*

## v3.3.1 Stable — consolidated release (2026-11-02)
- Combines v3.3.1 Revised with Hotfix 1's `navigation.js` and Chromium `TranslateEnabled: false` policy.
- Includes existing v3.1 browser-history Back, v3.2 auto film fullscreen, and native Android/HTTPS API without changing verified app logic.
- Adds self-contained clean install for *new* Raspberry Pi 5 and non-destructive backup/rollback.
- Fresh installs no longer require the v1/v2 HTTP remote and never place a URL token in a Chromium command line.
- Adds tests, release notes and safeguards against overwriting an existing PiTV installation.
- New-install end-to-end video test on a second Pi remains pending.
