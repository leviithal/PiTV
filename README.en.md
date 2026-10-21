# PiTV — Raspberry Pi 5 Smart TV with a native Android remote

PiTV is an open-source-ready portfolio project that reuses a Raspberry Pi 5 as a TV streaming interface. Netflix and Disney+ run through Chromium/Widevine on Raspberry Pi OS Desktop; a native Kotlin Android remote communicates with a Python HTTPS API (port 8766), using a local bearer token and a pinned TLS certificate.

## Features
- Custom Netflix/Disney+ launcher, Chromium kiosk mode and D-pad navigation.
- Dedicated Android APK with Back, OK, volume, playback controls and backup touchpad.
- v3.1 browser-history Back avoids accidental 10-second Netflix rewind.
- v3.2 experimental automatic video fullscreen.
- Versioned sources from v1.0 through v3.2; backup and rollback scripts.

## Documentation
See [Swedish README](README.md) and the [fresh-install guide](docs/INSTALL-NY-PI.md), [Android build guide](docs/ANDROID.md), [architecture](docs/ARKITEKTUR.md), and [security](SECURITY.md).

## Limitations
PiTV does **not** implement Google Cast, and is **not** affiliated with Netflix, Disney+, Google or Raspberry Pi. Streaming compatibility may change. Playback requires legitimate accounts, compatible DRM support and an appropriate network. This project does not distribute streaming content or credentials.

The Git commits and tags are **retrospectively reconstructed** from retained project artifacts, not recovered timestamps of the original development history. Real-hardware functionality was confirmed by the project owner; reproducibility on other systems is not guaranteed. The work was developed with AI assistance, with integration testing performed by the owner.
