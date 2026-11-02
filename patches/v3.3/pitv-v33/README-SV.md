# PiTV V3.3 – Navigation & App Experience (testversion)

Detta är **inte** en ny Android-app, inte Android TV och inte en ny webbläsare. Det är en **lokal och återställningsbar uppdatering av Chromium-tilläggets D-pad-navigering** ovanpå en **redan fungerande PiTV V3.2**. Netflix och Disney+ förblir sina webbversioner.

## Förändringar

- Mer TV-liknande fokus: tydlig gul markering på valbart kort, meny eller dialogruta.
- Vänster/höger prioriterar objekt på samma rad; upp/ned prioriterar samma kolumn.
- När listan tar slut kan D-pad scrolla i scrollbara listor och fortsätta navigera.
- OK klickar på markerat objekt. Första OK utan valt kort markerar ett första val, av säkerhetsskäl.
- F9 väljer första valbara objekt om fokus tappats.
- Respekterar textsökning och låter filmspelaren ta emot sina vanliga tangenter.
- Begränsar D-pad-tilläggets webbplatsmatchning till Netflix och Disney+ (inte YouTube).
- Lämnar den fungerande PiTV V3 HTTPS-servern, Android-applikationen, V3.1:s Bakåt och V3.2:s filmhelskärm orörda.

> **Begränsning:** Netflix och Disney+ äger sin webbläsarnavigering och kan ändra sidstrukturen. Vissa kort/menyer kan fortfarande kräva reservmus. Ändringen är inte testad mot båda verkliga sajterna på en fysisk Pi ännu.

## Före installation

1. Kontrollera att PiTV V3.2 redan fungerar med Netflix, Disney+, Bakåt och auto-filmhelskärm.
2. Behåll den gamla Android-appen – den behöver **inte** kompileras om.
3. Kopiera mappen `pitv-v33` till Pi-användarens hemkatalog med SCP. Kör **inte** med `sudo`.

### På Windows, i den uppackade ZIP-mappen

```powershell
scp -r .\pitv-v33 pi@192.168.1.XX:~/
ssh pi@192.168.1.XX
```

Byt IP-adressen till Pi:ns faktiska IP. Om användarnamnet är annat än `pi`, byt även det.

### På Raspberry Pi – alltid förkontroll först

```bash
python3 ~/pitv-v33/install-v33.py --check
```

Krav: den befintliga Chromium-extensionens manifest ska vara version `2.2.0` efter V3.2 och ha V3.1:s `pitv-background.js` och V3.2:s `pitv-auto-fullscreen.js`. Om kontrollen avbryter ska du **inte** tvinga igenom installationen.

### Installera efter lyckad kontroll

```bash
python3 ~/pitv-v33/install-v33.py --install
sudo reboot
```

Installeraren skriver ut exakt sökväg till backup under `~/pi-tv-v33-backups/`. Spara den. Endast följande tre filer hanteras:

- `~/pi-tv/dpad-extension/navigation.js` (ersätts)
- `~/pi-tv/dpad-extension/navigation-core.js` (ny)
- `~/pi-tv/dpad-extension/manifest.json` (versionshöjning till `2.3.0` och script-ordning)

Ingen token, certifikat, Chromium-profil, Widevine-konfiguration eller mediafil ändras.

## Test på din TV

1. Starta från vanliga PiTV-startsidan: Netflix → välj ett filmkort med pilar och OK.
2. Verifiera att gul fokusmarkering följer höger/vänster, upp/ned på flera rader.
3. Öppna en serie-/filmdetalj och testa att fokus flyttar sig mellan synliga knappar.
4. Starta film och verifiera att **Bakåt fortfarande fungerar** och att pilarna under film inte blir kapade av tillägget.
5. Upprepa i Disney+. Prova även undertexter och automatisk filmhelskärm.
6. Testa ett sökfält med Android-appens reservtangentbord så D-pad inte fångar textinmatning.
7. Starta om Pi:n och upprepa snabbtest med båda tjänsterna.

Om en webbsida ändrats kan urvalet behöva justeras. Att skript och simuleringstester passerar betyder inte att samtliga Netflix-/Disney+-menyer kommer att fungera.

## Återställning

Använd **sökvägen som installeraren skrev ut**:

```bash
python3 ~/pitv-v33/rollback-v33.py /home/pi/pi-tv-v33-backups/backup-EXEMPEL
sudo reboot
```

**Obs:** Sätt inte `~` inne i citationstecken: använd i stället den faktiska absoluta sökvägen, t.ex. `/home/pi/pi-tv-v33-backups/backup-...`.

Rollback vägrar skriva över filer som ändrats efter installationen. Om du också vill återställa V3.2 och V3.1, gör **V3.3 först**.

## Testa utvecklarpaketet på dator (utan Pi)

```bash
node patches/v3.3/test-v33-core.js
python3 patches/v3.3/test-v33-installer.py
```

Med lokalt Chromium och Python Playwright:

```bash
python3 patches/v3.3/test-v33-browser.py
```

## GitHub

Lägg `patches/v3.3/` i din befintliga `PiTV`-källkod. Commit:a gärna som **v3.3-rc1** tills du testat på riktigt vid TV:n. Publicera inte API-token, privata TLS-nycklar eller Chromium-profil. Källkoden innehåller inga sådana filer.
