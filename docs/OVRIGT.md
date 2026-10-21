# Underhåll och hårdvara

## Upplösning och överskanning

På Skantic B3211HD kan 1280×720 vid 60 Hz vara lämpligt, men testa TV:ns faktiska stödda lägen via `wlr-randr`. Välj bara en HDMI-utgång och mode som verkligen listas. Vid avklippta kanter, försök först med TV-inställningar *Just Scan*, *Screen Fit*, 1:1 eller PC-läge. Ändring från andra test-TV:n till barnets TV kan kräva ny upplösning.

## Ljud

```bash
wpctl status
# Ändra standardutgång manuellt med wpctl set-default <ID> om HDMI-valet är fel.
```

## Backup

Spara en offline-avbild av microSD/SSD när allt fungerar. Lägg **inte** avbilden på GitHub: den kan innehålla cookies, certifikat, API-token och streaminginloggning. Dokumentera programvaruversioner (`chromium --version`, `cat /etc/os-release`) separat från inloggningsuppgifter.

## Framtida arbete

- Riktig övervakning av UI-åtgärder (skilj mellan `command:sent` och verifierad effekt)
- Bättre TV-fokus på webbplatser som ändrar HTML
- Automatisk backup som inte exporterar hemligheter
- Mer pålitlig autostart än fast `sleep 2` i V2-startscript
- Nyckelrotation och certifikatförnyelse med enkel parkoppling i Android-appen
