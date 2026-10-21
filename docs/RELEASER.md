# Release-filer och versionsgränser

- **v1.0**: `history/v1.0/` (ursprunglig HTTP-webbfjärr).
- **v2.0**: `history/v2.0/` (första D-pad).
- **v2.1–v2.3**: `history/v2.x/` (historiska reparationsskript).
- **v2.4**: `history/v2.4/` (ändringsskript) och `src/pi/v2.4/` (faktisk kodfrysbild som laddats upp från Pi:n).
- **v3.0**: `src/pi/v3.0/` + `android/PiTVRemote/` (Kotlin-app och HTTPS-API).
- **v3.1**: `patches/v3.1/` ovanpå V3.0 (Back + kiosk).
- **v3.2**: `patches/v3.2/` ovanpå V3.1 (experimentell automatisk helskärm).

Filer under `release-archives/` är originalarkiv, inte färdiga kompletta systemimages. För en ny Pi, följ `docs/INSTALL-NY-PI.md` och använd `installer/install-fresh-pi.sh` – inte de gamla patcharna slumpmässigt.

**Versionshistoriken är rekonstruerad.** Koden bevarar de historiska stegen, men taggarnas Git-committidsstämplar representerar återställningen av källfilerna och ska inte tolkas som originalutvecklingens egentliga Git-logg.
