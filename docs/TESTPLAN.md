# Testprotokoll före skarp användning

## Installerade beroenden

- [ ] Raspberry Pi OS Desktop 64-bit, `labwc` aktiv
- [ ] `chromium`, `wtype`, `wlrctl`, `wpctl` finns
- [ ] Widevine: Netflix och Disney+ visar **bild OCH ljud** i Chromium
- [ ] Nätverk/brandvägg: endast betrodda enheter når 8766

## Fjärrkontroll

- [ ] Android-APK installeras och startas utan webbläsare
- [ ] Nyckel+certifikat verifieras, fel uppgifter nekas
- [ ] Upp/ned/vänster/höger/OK väljer tjänst på TV-startsidan
- [ ] Bakåt backar en nivå utan att spola Netflix-video
- [ ] Volym, play/paus fungerar
- [ ] Reservmus fungerar när webbspelarens fokusnavigering misslyckas
- [ ] API visar offline när Pi:n är avstängd

## Kiosk och film

- [ ] Pi:n startar till startskärmen efter kallstart
- [ ] Inga adressfält/webbläsarflikar syns
- [ ] Netflix spelar i faktisk filmhelskärm
- [ ] Disney+ spelar i faktisk filmhelskärm
- [ ] Undertexter och menyer fungerar korrekt
- [ ] Efter omstart återansluter appen och båda tjänster fungerar

## Säkerhet, återställning och underhåll

- [ ] Ingen API-nyckel eller privat certifikatnyckel finns i repot
- [ ] V2 port 8765 bara localhost
- [ ] Backuper/image finns av Pi:s fungerande lagring
- [ ] GitHub-release taggas, dokumenteras och kan återställas
