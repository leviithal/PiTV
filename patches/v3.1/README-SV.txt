PiTV V3.1 – helskärm och riktig Bakåt
====================================
Uppdatering byggd för din granskade V2.4 + V3-installation.

VIKTIGT
- Ingen ändring görs på Android-apk, API-nyckel, certifikat, Chromium-profil eller Widevine.
- Skapar lokala säkerhetskopior och vägrar ändra okända versioner.
- Netflix & Disney+ webbsidor öppnas i Chromiums kiosk/fullskärmsläge vid nästa omstart.
- Bakåt-kommandot i Android-appen går via ett Chrome-extension-kommando till
  chrome.tabs.goBack(), INTE en vänsterpil som Netflix kan tolka som spolning.
- Automatisk HELSKÄRM för själva videospelaren ingår INTE. Netflix har F som
  kortkommando när en video spelas, men Chrome-vyn blir helskärm med kiosk.

1. Från Windows PowerShell i katalogen PiTV-V3.1-Fix:
    scp .\install-v31.py .\rollback-v31.sh pi@PI-IP:~/

2. SSH till Pi och kör:
    python3 ~/install-v31.py
    sudo reboot

3. Testa efter omstart:
   - PiTV hemskärm fyller TV:n utan adressrad.
   - Netflix och Disney+ fyller fönstret utan webbläsarens ram.
   - Välj en Netflix-film; tryck Bakåt i Android-appen.
   - Den ska gå till föregående vy och INTE hoppa 10 sekunder bakåt.
   - Kontrollera att pilar, OK, ljud och båda streamingtjänsterna fungerar.

   OBS: Testa Chromium-extensionens genväg Ctrl+Shift+Y med fysiskt tangentbord.
   Om Bakåt inte fungerar kan Chrome ha avaktiverat genvägen. Kontrollera
   chrome://extensions/shortcuts i Chromium; sätt "PiTV: tillbaka en sida" till
   Ctrl+Shift+Y. Tryck aldrig LÅNGT på Back om den inte reagerar.

4. Om problem uppstår:
   Använd backup-sökvägen som installeraren skrev ut, t.ex.:
     bash ~/rollback-v31.sh ~/pi-tv-v31-backups/backup-20261021-120000-1234
     sudo reboot

N.B. Kiosk-läge påverkar Chromium på nästa omstart, inte befintliga öppna fönster.
HTTPS-API fortsätter på port 8766. Håll den porten inom ditt lokala nät.
