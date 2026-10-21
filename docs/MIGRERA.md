# Uppgradera en redan fungerande PiTV-installation

Om du redan har PiTV V3.2 och Android-appen fungerar: **kör inga installationsskript igen**. Detta repo är dokumentation och versionshistorik tills du medvetet vill migrera.

Om du har en PiTV V2.4-instans med fungerande Netflix/Disney+, kör endast V3 stegvis:

```bash
cd ~/PiTV-GitHub
bash src/pi/v3.0/install-v3.sh
sudo reboot
bash ~/pi-tv-v3/check-v3.sh
```

Installationsskriptet kopierar server och hjälpskript men ska inte skriva över V2 Chromium-profilen. Bygg Android-appen enligt [ANDROID.md](ANDROID.md). Kontrollera anslutningen. Därefter installerar du patcharna **i ordningen**. Om hela repot redan finns under `~/PiTV-GitHub`, kör:

```bash
cp ~/PiTV-GitHub/patches/v3.1/rollback-v31.sh ~/
cp ~/PiTV-GitHub/patches/v3.2/rollback-v32.py ~/
python3 ~/PiTV-GitHub/patches/v3.1/install-v31.py
python3 ~/PiTV-GitHub/patches/v3.2/install-v32.py
sudo reboot
```

Båda patcharna kontrollerar kända källkodsmönster och avbryter vid oväntade filer. De är versionsbundna och ska inte köras slentrianmässigt efter andra ändringar. När alla V3-funktioner fungerar: `bash ~/pi-tv-v3/lockdown-v2.sh` och omstart, för att begränsa V2 till `127.0.0.1`. Om du redan har lockdown: gör inte om den.

**Backup:** Skapa gärna en image av din Pi:s lagring innan förändringar. Sparade tokens, certifikat och Chrome-profil ska aldrig laddas upp till GitHub. Samtliga historiska 1.x/2.x-fixar finns för referens under `history/`, inte som rekommenderad nyinstallationsväg.
