# Publicera PiTV på GitHub med alla versions-taggar

**Rekommenderat:** använd `PiTV-full-history.bundle` från leveranspaketet. Git-bundlen innehåller alla commits och taggar v1.0–v3.2, så alla kodversioner är navigerbara i GitHub. **Commit-/tagg-historiken är rekonstruerad från bevarade leveransfiler i efterhand** och ska inte presenteras som den ursprungliga utvecklingsloggens tidsstämplar. ZIP-arkivet för sig innehåller källkoden, men inte hela Git-historiken.

## Steg 1 – Förbered GitHub

Skapa ett **tomt repository** på GitHub, t.ex. `PiTV` (Public eller Private). Avmarkera "Add a README", `.gitignore` och "Choose a license" eftersom de redan hanteras i projektet. Bestäm om du vill lägga till en licens via `LICENSE-CHOICE.md` senare.

## Steg 2 – Klona lokala historiken på Windows

Installera Git for Windows om det saknas. Öppna PowerShell i katalogen där du laddat ner `.bundle`:

```powershell
git clone .\PiTV-full-history.bundle PiTV
cd PiTV
git branch --show-current
git tag --list
```

Du ska se `main` och taggarna `v1.0`, `v2.0`, `v2.1`, `v2.2`, `v2.3`, `v2.4`, `v3.0`, `v3.1`, `v3.2`. Git-kommandona fungerar bara om Git är installerat. Alternativt kan du ladda upp `PiTV-GitHub-Repository.zip` via GitHub-webben, men då följer inte de lokala commits/taggarna med.

## Steg 3 – Byt remote och pusha

```powershell
git remote remove origin
git remote add origin https://github.com/DITT-KONTO/PiTV.git
git push -u origin main
git push origin --tags
```

Byt `DITT-KONTO`. GitHub kan begära webbläsarinloggning. **Ingen API-nyckel för PiTV ska någonsin matas in här.**

## Steg 4 – GitHub Releases

Under **Releases → Draft a new release** välj taggen `v3.2`. Använd `CHANGELOG.md` som release notes och bifoga endast **källkodsarkiv**, aldrig en nyckelförsedd backup av Pi:n.

## Steg 5 – Visa projektet i din portfolio

Exempel på kort beskrivning:

> **PiTV** – A Raspberry Pi 5-based DIY Smart TV interface with a native Kotlin Android remote, a Python HTTPS control API, Wayland kiosk mode and Chromium/Widevine streaming support. Iteratively prototyped, debugged and tested on real hardware, with secure local pairing and versioned releases.

Berätta gärna om problemen du löste (Widevine, Windows-path med `&`, Java 25/Gradle, webbläsarfokus, Back, videohelskärm). Ange tydligt att Netflix/Disney+ är externa tjänster, att lösningen inte implementerar Google Cast och att projektet utvecklades med AI-assisterad kodhjälp.

## Säkert före publicering

```powershell
python tools/security-scan.py
git status --short
```

Titta över alla filer visuellt också. GitHub Actions ska inte få dina riktiga API-nycklar. `SECURITY.md` förklarar hotmodell och skydd.
