# Felsökning

| Symptom | Vanlig orsak | Kontroll / åtgärd |
| --- | --- | --- |
| Netflix M7701-1003 | Widevine/Chromium saknas eller fel version | `sudo apt update && sudo apt full-upgrade`, kontrollera `apt policy chromium rpi-chromium-mods libwidevinecdm0`; testa med video+ljud |
| Disney+ spelar inte | DRM, webbläsarstöd, nätverk | Testa först direkt i Chromium med mus/tangentbord |
| Fjärrappen offline | Fel IP, certifikatpin eller port | `bash ~/pi-tv-v3/check-v3.sh`, kontrollera TCP 8766 och VLAN |
| SSL/certifikatfel | Ny IP eller nytt certifikat | `renew-certificate.sh` med uppdaterat fingeravtryck i appen |
| Bakåt spolar 10 sekunder | Gammal V3.0 skickar Alt+Left | Installera/återställ V3.1 korrekt, kontrollera extension-genvägen `Ctrl+Shift+Y` |
| Netflix visar adressrad | Chromium startar utan kiosk | Kontrollera `~/pi-tv/start.sh` efter V3.1 och labwc autostart |
| Film blir inte automatiskt helskärm | V3.2 extension/policy eller ändrad webbspelare | `chrome://extensions`, `chrome://policy`, manuellt `F` vid behov |
| Keyring-dialog vid uppstart | Autologin och Chromiums nyckelring | `--password-store=basic` i V2.2+ (säkerhetskompromiss) |
| TV:n klipper kanter | Overscan/fel upplösning | `wlr-randr`, TV-inställning 1:1/Just Scan, testa 1280×720 för HD Ready |
| OK/pilar fungerar bara ibland | Fel Chromium-fönster i fokus | `wlrctl toplevel list` och kontrollera extension och API-kommandon |
| Android `BUILD FAILED 25.0.3` | Inkompatibel Java 25 | Installera JDK 21 och kör `android/build-android-jdk21.ps1` |

## Loggar

```bash
systemctl --user status pitv-v3.service --no-pager
journalctl --user -u pitv-v3.service -n 80 --no-pager
tail -n 40 ~/.cache/pi-tv/chromium.log
```

**Redigera känsligt innehåll före delning.** Särskilt historiska V2-loggar kan innehålla autentiseringsnycklar i URL. Exempel:

```bash
tail -n 40 ~/.cache/pi-tv/remote.log | sed -E 's/key=[^&[:space:]]+/key=REDACTED/g'
```

HTTP 200 betyder att API-kommandot tagits emot/skickats, inte att Netflix visat rätt resultat på TV-skärmen.
