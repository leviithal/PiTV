# PiTV – DIY Smart TV for Raspberry Pi 5

**Latest documented release: v3.3.1 Stable.** A Raspberry Pi OS Desktop + Chromium/Widevine-based streaming launcher, with a Kotlin Android remote and a local authenticated HTTPS API.

The tested system plays Netflix and Disney+ through their **websites**, not official Android TV applications. PiTV is not a Chromecast, certified streaming device, or an affiliate of either service. Playback depends on current browsers, services, and DRM support.

## Features

- Netflix/Disney+ two-tile TV launcher, kiosk mode, video fullscreen.
- Native Android remote (D-pad, OK, browser-history Back, playback, volume and fallback mouse).
- Python HTTPS API, local port 8766, token and pinned certificate fingerprint.
- Browser extension with spatial navigation, Disney+ scrolling, and Netflix Play assist.
- Chromium managed policy disabling Translate suggestions.
- Self-contained fresh-install bundle (no intermediate patches), safe preflight, backups and rollback.

**Compatibility status:** v3.3.1 Revised + Hotfix 1 was confirmed working on the original Raspberry Pi 5 on Nov 2, 2026. The consolidated new-install procedure has passed isolated tests but is not independently tested on a second Pi. Netflix and Disney+ can change their web layouts and DRM requirements.

Read [Swedish setup instructions](docs/INSTALL-V331-STABLE.md), [release notes](docs/RELEASE-331.md), [Android build guide](docs/ANDROID.md), and [security guidance](SECURITY.md).

The historical version commits/tags were reconstructed from saved artifacts and are **not** an original development Git log. The repository contains no DRM keys, streaming content, account credentials, or live PiTV API tokens. Select an open-source license before inviting reuse.
