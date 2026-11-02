# PiTV V3.3.1 – Reviderad HF1

**Utgångspunkt: PiTV V3.3.1 Reviderad (RC1) är redan installerad. Gör INGEN rollback till V3.2 före detta paket.**

## Varför denna hotfix?

1. Chromium 155 kan visa *Translate this site* även med `--disable-features=Translate`. Flaggan är inte tillförlitlig i nya Chromium. Den här hotfixen inför i stället den dokumenterade **hanterade Chromium-policyn** `TranslateEnabled: false` i `/etc/chromium/policies/managed/pitv-translate-disabled.json`.
2. Netflix försöker i föregående version klicka programmatiskt på *Spela upp*. Sådana klick kan nekas av Netflix. Den nya navigeringen utökar letandet efter *Spela upp* i detaljrutan och försöker först ett automatiskt klick. Om det inte startar filmen läggs fokus på *Spela upp*, så att användaren kan trycka **OK igen** via den riktiga Android-fjärrkontrollen. Detta **garanterar inte automatisk uppspelning med ett tryck** på alla Netflix-vyer. Den exakta live-sidan måste fortfarande verifieras.
3. Disney+-scrollningen, D-pad, Back, V3.2-filmhelskärm, Android-appen, HTTPS-API, Widevine och cookies ändras inte.

## Installation – Windows

Packa upp ZIP-filen och öppna PowerShell i mappen som innehåller `pitv-v331-hf1`:

```powershell
scp -r .\pitv-v331-hf1 pi@192.168.1.XX:~/
ssh pi@192.168.1.XX
```

Ändra IP till Pi:ns IP.

## Installation – Raspberry Pi

Först skrivskyddad förkontroll:

```bash
python3 ~/pitv-v331-hf1/hotfix.py --check
```

**Fortsätt bara om förkontrollen godkänns.**

```bash
python3 ~/pitv-v331-hf1/hotfix.py --install
sudo reboot
```

Du kan behöva skriva sudo-lösenord när skriptet installerar Chromium-policyn. Notera den utskrivna backup-sökvägen. Inga streaminginloggningar eller API-nycklar läses av skriptet.

## Verifiering

1. På Pi:n: öppna `chrome://policy` i Chromium (via tangentbord tillfälligt), tryck **Reload policies** och bekräfta att `TranslateEnabled = false` och att ingen policyfelstatus visas. Om policyn inte syns använder Chromium möjligen annan policykatalog; fortsätt då inte med fler experiment utan rapportera detta.
2. Besök Netflix och Disney+; översättningsrutan ska inte dyka upp.
3. Välj ett filmkort i Netflix med OK. Om filmen inte startar direkt: se om **Spela upp** har fått fokus (gul markering) och tryck OK igen. Om det inte hjälper, notera om Netflix visar en *detaljpanel ovanpå sidan*, en *ny flik* eller ett *separat fönster*. Skicka inte skärmbilder med kontoinformation.
4. Testa Bakåt, Netflix-filmhelskärm och Disney+-scrollning.

## Ångra endast HF1 (tillbaka till V3.3.1 Reviderad)

Använd backup-sökvägen som installeraren skrev ut:

```bash
python3 ~/pitv-v331-hf1/hotfix.py --rollback '/home/pi/pi-tv-v331-hf1-backups/backup-EXAKT-NAMN'
sudo reboot
```

**OBS:** Det här återställer till V3.3.1 Reviderad, inte V3.2. Din tidigare backup från V3.2 påverkas inte. Om du senare vill ångra hela V3.3.1 ska du först rulla tillbaka HF1 och sedan använda den ursprungliga V3.3.1-Reviderad-backupen.

## Avgränsningar och teststatus

- Skrivskyddad förkontroll, installation och rollback har testats med en simulerad PiTV-katalog utan rootprivilegier.
- JavaScript har syntaxkontrollerats med Node.js. Källfilerna från originalpaketet har kontrollerats med SHA-256. Fel originalversion avbryts utan att skriva över något.
- Verklig Chromium-policy och Netflix live-sida kan **inte** testas från den här miljön. Den viktigaste kontrollen sker på den faktiska Pi:n.
- Policyn påverkar alla Chromium-profiler som använder systemets hanterade policykatalog, inte bara PiTV-fliken.
