# Publicera PiTV v3.3.1 på GitHub

Du får två olika arkiv: `PiTV-v3.3.1-Stable-Install.zip` (för nya Raspberry Pi) och `PiTV-v3.3.1-Stable-Repository.zip` (källkod + historik).

Innan du publicerar: välj licens, kontrollera att repot inte innehåller token/certifikat/Chromium-profil och kontrollera GitHub-URL och behörighet. Publicera helst source som repo och lägg installations-ZIP under **Releases**.

Om du redan har klonat projektet på Windows: packa upp `PiTV-v3.3.1-Stable-Repository.zip` och kopiera ändrade `src/`, `installer/`, `docs/` och README-filer till ditt befintliga Git-repository; gör sedan en commit. Alternativt klona `PiTV-v3.3.1-Stable-History.bundle` (lokal rekonstruerad historik) till en ny mapp.

```powershell
git status
git remote -v
git tag --list
# Efter granskning, om huvudgrenen heter main:
git push origin main
git push origin v3.3.1
```

För ett repo som ännu inte skapats: skapa ett tomt repo med rätt owner i https://github.com/new och sätt `git remote set-url origin https://github.com/leviithal/PiTV.git` endast om det verkligen är ditt repository. `Repository not found` betyder ofta att repot inte skapats ännu eller att kontot saknar rättigheter.

Release-förslag: **PiTV v3.3.1 — Stable (Raspberry Pi 5 + Android Remote)**. Använd `docs/RELEASE-331.md` som bas för release notes och bifoga installationsarkivet. Sätt inte `pre-release` om du vill visa den som stable; notera dock att nyinstallationen inte är testad på en andra fysisk enhet.

Git-tags i de rekonstruerade historikfilerna speglar projektreleaser men är inte autentiska ursprungliga författarcommits. Undvik att hävda en original commit-historik.
