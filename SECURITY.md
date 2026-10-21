# Säkerhet / Security

**Hotmodell:** Projektet avser ett betrott lokalt nät. Det är inte byggt som en publik internetexponerad fjärrstyrning. Ställ INTE in portforwarding till 8765 eller 8766.

## Hemligheter som aldrig får hamna på GitHub

- `~/pi-tv/remote-token`, `~/pi-tv-v3/api-token`
- `~/pi-tv-v3/tls-key.pem`, certifikatfiler om de identifierar din maskin
- Chromium-profil, cookies, sparade lösenord, Netflix- och Disney+-inloggning
- Oredigerade loggar som kan innehålla `?key=...`, hem-IP, privata filer
- APK-signeringens privata nyckel, privata `local.properties`

Historiska V1/V2-skript använder **HTTP och nyckel i URL**, vilket är sämre skydd. Nyinstalleraren binder V2-servern till `127.0.0.1` och installerar V3 med TLS på port 8766. `--password-store=basic` minskar popup-dialoger men skyddar sparade uppgifter sämre. Använd en dedikerad Pi-profil och ett betrott nät.

## V3-modell

- Lokalt genererad stark API-nyckel (inte i repot)
- Authorization: Bearer i header, ej URL
- Självsignerat certifikat; Android-app kontrollerar SHA-256-fingeravtryck och hostname
- Nycklar och privat certifikat på Pi med filrättighet 0600
- Kommandon via explicit allowlist, inte exekvering av godtyckliga kommandon
- 429 rate limiting, 4 s timeout per kommando och ingen nyckel i vanliga loggar

**Risker som finns kvar:** Tillgång till Pi:s lokala port ger en möjlighet att försöka fjärrstyra. Om Android-mobilen förloras bör API-nyckeln bytas (och Android-appen uppdateras). Certifikatet gäller normalt 365 dagar; använd `renew-certificate.sh` med nytt SHA-256-fingeravtryck. Servern kan bekräfta att kommandot skickats men inte att TV:n reagerade. HTTPS på lokalt nät är inte en ersättning för nätverkssegmentering.

## Kontrollera före push

Kör `python3 tools/security-scan.py` och `git status --short`. Granska eventuella fynd manuellt. Skriptet är ett extra skydd, inte en garanti mot alla typer av hemligheter. Verifiera även `git log -p` om du tidigare committat egna nycklar; `.gitignore` tar inte bort hemligheter ur gamla commits.

## Ansvarsfriskrivning

Ingen DRM-nyckel, stream, Netflix/Disney+-program eller kringgående verktyg distribueras. Uppspelningen är beroende av legitim inloggning och stöd för Chromium/Widevine.
