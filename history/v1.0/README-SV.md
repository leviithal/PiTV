# PiTV Mini – Raspberry Pi 5 + mobil som fjärrkontroll

Detta är en liten, separat installation **ovanpå din befintliga Raspberry Pi OS Desktop / Wayland-labwc**. Den återanvänder den Chromium-profil där Netflix och Disney+ redan fungerar. Den installerar **inte** om Chromium, Widevine, operativsystemet eller dina streamingsessioner.

## Förutsättningar
- Raspberry Pi OS Desktop med `labwc`, Chromium och fungerande Netflix/Disney+.
- Pi 5 med strömförsörjning, micro-HDMI till TV, nätverk, och en användare med `sudo`.
- En Android-telefon med åtkomst till Pi:ns IP-adress på det lokala nätverket.
- Testa först vid din egen TV.

## Installera (från Windows PC)

1. Ladda ned `install-pitv.sh` till din PC, exempelvis till `Downloads`.
2. Öppna PowerShell i mappen Downloads:

   ```powershell
   scp .\install-pitv.sh PI_ANVANDARE@PI_IP:/home/PI_ANVANDARE/
   ssh PI_ANVANDARE@PI_IP
   ```

   Byt `PI_ANVANDARE` och `PI_IP` mot Pi:ns faktiska användarnamn/IP, t.ex. `fredrik` och `192.168.1.50`.

3. Väl inloggad på Pi:n:

   ```bash
   bash ~/install-pitv.sh
   sudo reboot
   ```

Du kan även ladda ned filen direkt på Pi:n och köra `bash ~/Downloads/install-pitv.sh` om det är dit webbläsaren sparade den.

## Resultat efter omstart
- Raspberry Pi OS loggar in automatiskt på skrivbordet och skärmsläckning stängs av.
- Chromium öppnar sidan **Filmkväll** i helskärm med Netflix, Disney+ och YouTube.
- En liten HTTP-baserad fjärrkontroll startar på port `8765`.
- Inloggningar i streamingtjänsterna ligger kvar i Chromiums vanliga användarprofil.

## Visa mobilens fjärrkontroll-länk

Kör på Pi:n:

```bash
printf 'http://%s:8765/?key=%s\n' "$(hostname -I | awk '{print $1}')" "$(cat ~/pi-tv/remote-token)"
```

Öppna länken i Android-telefonens webbläsare. Du kan lägga till den på hemskärmen i Chrome via menyn **Lägg till på startskärmen**. Ingen separat app behövs.

**Knappar:** Netflix / Disney+ / YouTube öppnar tjänsten i ny flik; Hem återvänder till startsidan (flik 1); Bakåt går till föregående sida; Stäng flik återgår vanligtvis till föregående flik; pilar + OK navigerar; fingerplattan flyttar muspekaren; klick aktiverar; skrivfältet skriver i det fokuserade fältet på TV:n; volymknappar ändrar Pi:ns ljudstyrka.

Det här är **fjärrstyrning av Raspberry Pi**, inte Google Cast från Netflix-appen. Video och ljud spelas direkt på TV:n via HDMI.

## Kontrollera ljud

```bash
wpctl status
```

Under `Sinks` väljer du HDMI-utgången som Pi:n är kopplad till. Om stjärnan (*) ligger på fel utgång:

```bash
wpctl set-default ID
```

Byt `ID` mot aktuell HDMI-sinks ID. Alternativt högerklicka på högtalarsymbolen på Pi:ns skrivbord och välj HDMI.

## Felsökning

- **Ser bara skrivbordet efter omstart?** Kör `cat ~/.cache/pi-tv/chromium.log`, `cat ~/.cache/pi-tv/remote.log`, och `tail -10 ~/.config/labwc/autostart`. Kontrollera `pgrep -a labwc`.
- **Mobilen når inte fjärrkontrollen?** Kontrollera `hostname -I`, använd exakt länk inklusive `?key=...`, och kör `ss -tln | grep 8765`. Säkerställ att VLAN och klientisolering inte blockerar TCP 8765.
- **Fjärrkontrollen visas, men styr inte?** Kör `pgrep -a labwc`, `wtype -k Return`, `wlrctl pointer move 20 20` från Pi:ns lokala grafiska terminal, och kontrollera loggfilen `~/.cache/pi-tv/remote.log`.
- **Kan inte välja textfält eller logga in?** Peka och klicka på fältet via styrplattan, skriv sedan på mobilen och tryck **Skriv på TV**. Alternativt använd USB-mus och tangentbord under första inloggningen.
- **Svart bild vid Netflix/Disney+?** Bekräfta uppspelning lokalt, stäng andra Chromium-fönster och se om tjänsten fungerar i normalt Chromium. Installeraren har inte ändrat Widevine.
- **TV:n tar över en annan upplösning?** Raspberry Pi Control Centre → skärminställningar; testa 1280 × 720 vid 60 Hz till Skantic-TV:n om bilden ser fel ut. Tvinga inte upplösning innan du ser ett problem.

## Säkerhet / nätverk

Fjärrkontrollen lyssnar på Pi:ns nätverksgränssnitt och kräver en lång, slumpmässig nyckel i adressen. Använd **endast på ditt betrodda hemnät**. Öppna **inte TCP 8765 mot internet** och publicera inte fjärrkontrollen via Cloudflare Tunnel. HTTP skyddar inte nyckeln mot avlyssning på ett komprometterat LAN. Ge telefonen rätt att nå Pi:ns IP via din UniFi-brandvägg (TCP 8765). Om mobilen ligger på FM-Guest och Pi:n på FM-Internal krävs en uttrycklig brandväggsregel, och gästisolering kan fortfarande blockera.

## Ångra installationen

Kör:

```bash
bash ~/uninstall-pitv.sh
sudo reboot
```

Detta stoppar auto-starten och webbservern. Det raderar **inte** Chromium, Widevine, sparade streaming-inloggningar eller personliga data. Skärmsläckning (avstängd av installeraren) kan återaktiveras med `sudo raspi-config nonint do_blanking 0`. Automatisk skrivbordsinloggning (B4) ändras inte tillbaka automatiskt: välj tidigare alternativ under `sudo raspi-config` → System Options → Boot / Auto Login om du vill återställa även det. Filerna i `~/pi-tv/` får vara kvar för senare återaktivering.
