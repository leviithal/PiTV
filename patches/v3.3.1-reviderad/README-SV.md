# PiTV V3.3.1 – Reviderad (RC1)

**Uppgraderingsväg: V3.2 → V3.3.1 Reviderad, direkt.**  
Du behöver **inte** installera V3.3 först. Den gamla `pitv-v331/install-v331.py` är **inte** avsedd för en återställd V3.2 och ska inte användas.

Den här reviderade utgåvan ersätter V3.3 och det tidigare V3.3.1-RC1-paketet som en **komplett uppgradering** från den V3.2 du faktiskt kör efter rollback. Paketet är en *releasekandidat*, eftersom Netflix och Disney+ inte har verifierats live mot just den här kombinationen.

## Ingår

- `install-v331-reviderad.py`: läsbar förkontroll (`--check`) och komplett installation (`--install`) från **V3.2**.
- `rollback-v331-reviderad.py`: direkt återställning till backupen av **V3.2** (inte V3.3).
- `navigation-core.js`: navigeringsmotorn som tidigare bara levererades genom V3.3.
- `navigation.js`: V3.3.1-försök till förbättrad Disney+-scrollning och Netflix Play-knapp.
- `tests/test-upgrade-v32.py`: automatiskt test av version, installation, integritet, rollback och avbruten installation.

Vid uppgradering påverkas **endast** `~/pi-tv/dpad-extension/manifest.json`, `~/pi-tv/dpad-extension/navigation.js` och `~/pi-tv/start.sh`, plus **en ny** `~/pi-tv/dpad-extension/navigation-core.js`. Övriga tjänster och filer bevaras.

## Windows → Raspberry Pi (gör så här)

1. Packa upp ZIP-filen så att du ser mappen **`pitv-v331-reviderad`**.
2. Öppna PowerShell **i katalogen som innehåller mappen** och kör (ändra IP):

   ```powershell
   scp -r .\pitv-v331-reviderad pi@192.168.1.XX:~/
   ssh pi@192.168.1.XX
   ```

3. På Pi:n, med vanliga användaren `pi` (**inte sudo**):

   ```bash
   python3 ~/pitv-v331-reviderad/install-v331-reviderad.py --check
   ```

   Du ska se **`V3.2 (manifest 2.2.0) igenkänd`**. Om kontrollen misslyckas: **installera inte**; skicka den ofarliga feltexten, aldrig lösenord/tokens.

4. Om kontrollen är godkänd:

   ```bash
   python3 ~/pitv-v331-reviderad/install-v331-reviderad.py --install
   ```

5. **Spara den backup-sökväg** som skrivs ut. Den ska börja med:
   `/home/pi/pi-tv-v331-reviderad-backups/backup-...`

6. Starta om:

   ```bash
   sudo reboot
   ```

Du behöver inte installera om Android-appen eller ändra V3-HTTPS-servern. V3.1:s Bakåt-funktion och V3.2:s filmhelskärm lämnas orörda.

## Test efter uppstart

1. Öppna Netflix/Disney+ från TV-startsidan – videouppspelning och ljud ska fungera som tidigare.
2. Disney+: prova att trycka **Ned** när du är vid nederkanten av de synliga filmkorten; kontrollera att sidan/scrollpanelen fortsätter nedåt utan separata scrollknappar.
3. Netflix: välj ett kort med OK; kontrollera om eventuellt detaljfönster leder vidare till en uttrycklig **Spela upp**-knapp. Kontrollera att inga trailers startas felaktigt. Automatisk uppspelning är **best effort**, eftersom Netflix bestämmer sidans beteende.
4. Kontrollera att Chromium inte längre erbjuder **Translate this site**.
5. Verifiera **Bakåt**, automatisk filmhelskärm, undertexter, samt Android-fjärrens OK/volym.

### Viktigt om Netflix

Den här uppdateringen kan inte installera officiella Android TV-appar, kringgå DRM eller garantera att Netflix alltid startar video automatiskt. Den försöker enbart aktivera en tydligt markerad Play-knapp **efter att användaren valt ett filmkort**. I vissa vyer krävs ett andra OK.

## Återställ direkt till V3.2

Om du inte gillar resultatet använder du **exakt** backup-sökvägen som installeraren visade:

```bash
python3 ~/pitv-v331-reviderad/rollback-v331-reviderad.py \
  '/home/pi/pi-tv-v331-reviderad-backups/backup-EXAKT-NAMN'
sudo reboot
```

Detta återställer originalversionerna av `manifest.json`, `navigation.js` och `start.sh`, samt tar bort `navigation-core.js`. Integritetskontroller stoppar återställningen om filerna ändrats av någon annan efter installationen, för att inte förstöra ditt arbete.

**Endast vid strömavbrott/avbruten installation**, och bara när rollback-skriptet uttryckligen klagar på att installationen inte markerats klar, kan du använda samma kommando med `--recover-incomplete`. Den verifierar att varje fil matchar antingen original eller känd mellanversion.

## Felsökning

- **`Kräver V3.2 (manifest 2.2.0)`**: stoppa. Du har annan version än paketet förväntar sig.
- **`navigation-core.js finns redan`**: stoppa. Versionen har kanske redan installerats eller du har annan uppgradering.
- **`start.sh har redan disable-features`**: stoppa. En annan ändring finns i Chromium-starten som måste utvärderas innan installeraren får modifiera raden.
- **Ingen automatisk scroll i Disney+**: ingen garanti – använd de gamla scrollknapparna tills vidare och rapportera vilken vy som inte fungerar.
- **Translate-popup kvar**: kontrollera den verkliga PiTV-Chromium-processens startflaggor efter omstart, utan att posta tokens från kommandoraden.
- **Netflix öppnar en separat dialog**: det är inte samma sak som separat flik/fönster. Förklara vilket du ser.

## GitHub / versionshantering

Lägg filerna under `patches/v3.3.1-reviderad/` och dokumentera releasekandidaten som **PiTV V3.3.1 – Reviderad (RC1)**. Rekommenderad Git-tagg `v3.3.1-reviderad-rc1` (annan än den äldre v3.3.1-rc1-taggen). Märk inte stabil innan test på Pi är godkänt.

## Kvalitetssäkring

- Python och JavaScript syntaxkontrollerades lokalt.
- `tests/test-upgrade-v32.py` kördes med normal (icke-root) användare och klarade test av V3.2-förkontroll, installation, dubbelinstallation, ändrade filer, exakt rollback, fel basversion och avbruten installation.
- Disney- och Netflix-liknande testwebbsidor fungerade i lokalt Chromium-test från V3.3.1-källan.
- **Inte testat** mot de live-uppkopplade tjänsterna på en fysisk Raspberry Pi med detta ombyggda paket.
