PiTV V3.2 - Experimentell automatisk FILM-helskärm
=================================================

Du har bekräftat att PiTV V3.1 fungerar med Netflix/Disney+ och Bakåt.
Denna uppdatering påverkar INTE Android-appen, Wi-Fi, Widevine, Chromium-profilen,
inloggningar, PiTV API V3, Back-kommandon eller videoljud.

Vad den gör:
- Tilläggsskript bevakar stora, faktiskt spelande filmer på Netflix /watch/...
  eller Disney+ /play/, /video/, /watch/.
- Försöker sätta själva video-spelaren (med omgivande kontroller där det går)
  i helskärm genom webbläsarens Fullscreen API EN gång per film.
- Ger enbart www.netflix.com och www.disneyplus.com rätt att begära automatisk
  helskärm med en lokal Chromium-policy. Detta är ett medvetet undantag från
  webbläsarens normala krav på användarhandling.

VIKTIGT - detta kan INTE garanteras utan test på din Pi. Förändringar i Netflix
eller Disney+ kan påverka upptäckt av filmspelaren, undertexter, överlägg etc.
Om undertexter/knappar försvinner: kör rollback direkt.

INSTALLATION
1. Packa upp ZIP på Windows.
2. PowerShell i den mappen:
   scp .\install-v32.py .\rollback-v32.py .\pitv-auto-fullscreen.js pi@PI-IP:~/
3. På Pi:n:
   python3 ~/install-v32.py
   sudo reboot
4. I Chromium: chrome://policy och kontrollera att
   AutomaticFullscreenAllowedForUrls visas utan fel.
5. Testa en film i Netflix och Disney+. Prova undertexter, Bakåt, pausa och play.

OBS Chrome-policy ger de två tjänsterna automatisk fullscreenbehörighet. Den ger
inte några rättigheter till andra webbplatser. Styrningen sker endast lokalt;
ingen token exponeras och ingen nätverkstrafik skickas från tillägget.

ROLLBACK
Kör:
  python3 ~/rollback-v32.py ~/pi-tv-v32-backups/backup-XXXXXXXX-XXXXXX-PID
  sudo reboot

Den exakta backup-sökvägen skrivs ut av installationsskriptet.

Om policy inte syns i chrome://policy kan din Chromium-distribution använda en
annan katalog eller sakna stödet. Kör då rollback och rapportera statusen;
försök inte upprepat starta om eller lägga till slumpmässiga Chromium-flaggor.

Manuellt alternativ om auto inte fungerar: välj uppspelning och använd fysiskt
tangentbord med F (Netflix och Disney+ stöder tangentkommandot för helskärm).
