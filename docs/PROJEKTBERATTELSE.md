# PiTV – projektberättelse

**Problemet:** En vanlig Skantic B3211HD (32 tum, HD Ready) saknade inbyggd casting, och en Android-användare behövde Netflix och Disney+ på TV:n. Målet var att återanvända befintlig Raspberry Pi 5, inte köpa en Chromecast med begränsad framtida livslängd.

**Prototypen:** Raspberry Pi OS Desktop med Chromium och Widevine. Netflix gav först felkoden **M7701-1003**; uppdatering/ominstallation av Chromium- och Widevine-relaterade paket på Pi:n fick både Netflix och Disney+ att spela. Detta var det avgörande kompatibilitetstestet.

**PiTV Mini V1/V2:** Webbfjärr, mörk TV-startsida, D-pad, och Chromium-tillägg för att välja element. Efter test framkom problem med OK, keyring-autentisering, Hem/Bakåt och att vanlig webbläsarnavigering inte beter sig som en certifierad TV-app. Iterativa versioner V2.1–V2.4 gjorde gränssnittet enklare, tog bort YouTube och roterade fjärrnyckeln.

**PiTV V3:** En riktig Android-APK ersatte webbfjärren. Den bygger på Kotlin, Android Keystore-lagrad token, HTTPS-certifikatpin och ett separat Python-API på Raspberry Pi. Windowsbygg krävde en lösning för användarsökväg med `&` och att Gradle 8.11.1 körs på JDK 21 i stället för Java 25.

**V3.1/V3.2:** Webbläsaren sattes i kiosk-läge. Bakåt separerades från Netflix vänsterpil genom Chromiums tilläggs-API. Automatisk filmhelskärm lades till som experimentell uppspelarspecifik förbättring. Användaren bekräftade därefter att funktionerna fungerade på sin test-Pi.

**Resultat:** En användbar Raspberry Pi-baserad streamingstation med egen Android-fjärrkontroll och utan ny inköpt streamingbox. Lösningen förlitar sig fortsatt på webbläsare, Widevine och streamingtjänsternas aktuella gränssnitt och är därför inte en fullständig ersättare för en officiellt certifierad streamingbox.

## Lärdomar

- Kontrollera DRM/uppspelning innan UI byggs.
- Behandla webbspelares kortkommandon och TV-D-pad som olika problem.
- Testa fjärrkommandon hela vägen till skärmen; HTTP 200 är inte en kvittens från spelaren.
- Gör nya funktioner reversibla och bevara kända fungerande tillstånd.
- Lägg inte nycklar i URL:er/loggar när du bygger en riktig app.
- Lägg till versionskontroll och ett reproducerbart installationsflöde tidigt.
