# PiTV Mini V2 – D-pad & appkänsla

Denna uppdatering ersätter bara `~/pi-tv/{remote.py,phone-remote.html,tv-home.html,start.sh}` och lägger till ett lokalt Chromium-tillägg i `~/pi-tv/dpad-extension/`.

- Inga ändringar av OS, Chromium, Widevine eller Chromiums användarprofil.
- Netflix, Disney+ och YouTube använder en fast andra Chromium-flik i fullskärmsläge, så inga nya flikar staplas.
- Netflix och Disney+ är fortfarande webbversionerna – **inte** äkta Android TV-appar, och vissa kontroller kan kräva musreserv.
- Hem är alltid flik 1; tjänster alltid flik 2.
- Pilknappar markerar fokuserbara val med gul ram; OK trycker på valt objekt.
- Vid aktiv videospelning lämnas pilknapparna till Netflix/Disney+/YouTube (spolning/volym).
- Inloggningar och Widevine bevaras.

## Installera

1. Kopiera ZIP till Pi:n (eller filerna `upgrade-pitv-v2.sh`, om du har skriptet separat).
2. `unzip pitv-mini-v2.zip -d ~/pitv-v2`.
3. `bash ~/pitv-v2/upgrade-pitv-v2.sh`.
4. `sudo reboot`.
5. Öppna samma Android-fjärrkontrolladress som tidigare. Gör en siduppdatering i mobilen.

## Testa

1. Tryck `Hem`: TV:n visar tre stora val.
2. Tryck pilar och `OK` på mobilfjärren – fokusram på startsidan.
3. Välj Netflix – tryck `◎ Visa val` – på hemsidan hos Netflix ska en gul ram visas kring ett valbart objekt; pilarna flyttar ramen; `OK` aktiverar det.
4. Välj Disney+ och gör samma test.
5. Om ett enskilt element inte går att nå med pilar: öppna reservmusen i mobilfjärren.
6. Tryck `Hem` och kontrollera att tidigare video pausar.

## Om Chromium startar med gammal layout

Avsluta Chromium korrekt (`Alt+F4` på anslutet tangentbord) och starta om Pi:n; flaggan `--load-extension` tillämpas bara när Chromium startar första processen i en profil.

## Återställ gamla filer

Skriptet säkerhetskopierar till `~/pi-tv/backups/YYYYmmdd-HHMMSS/`. Använd exempelvis:

`cp ~/pi-tv/backups/TA_DITT_DATUM/start.sh ~/pi-tv/start.sh`

Gör motsvarande för övriga tre filer, följt av omstart. `remote-token` och Chromium-profilen ändras aldrig.
