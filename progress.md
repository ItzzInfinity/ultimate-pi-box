# Progress Log

## 2026-04-01

### Completed

- Created a fresh `v2` rewrite directory.
- Added the root entry file `main.py`.
- Added `menu.json` for menu-driven configuration.
- Added shared package files under `ultimate_pi_box/`.
- Added project-level documentation files.
- Added per-directory markdown scaffolding for planned components.
- Fixed the OLED footer overlap by reserving body lines when a footer is shown.
- Fixed the clock screen saver layout so the date and volume no longer share the same row.
- Replaced text-based Wi-Fi bars with height-based signal bars on the clock screen.
- Wired `My Music` to load files from `data/music/` and play them through VLC.
- Wired `Internet Radio` to load `data/radio_stations.csv` and start streams through VLC.
- Added `DLNA/UPnP` to the main menu.
- Added a minimal Flask web interface for remote control on the local network.
- Shifted local music scanning to `/home/infinity/Music`.
- Improved marquee scrolling for long OLED titles.
- Upgraded the web UI to show live component state and media lists with transport actions.
- Replaced the DLNA placeholder with discovery, browsing, and basic network playback wiring.
- Integrated a vendored `mpd_oled` runtime wrapper for the display pivot.
- Switched idle/screensaver ownership toward `mpd_oled`.
- Added local build and MPD FIFO helper scripts for the vendored `mpd_oled` source.
- Kept media handoff disabled by default to preserve the frozen VLC-based feature behavior until playback backends are migrated.

### Shared Runtime Added

- `config.py`
- `hardware.py`
- `players.py`
- `rendering.py`
- `system.py`
- `app.py`

### Next Development Steps

- Improve Bluetooth phone metadata and transport controls through DBus.
- Add YouTube playback from CSV and SQLite sources.
- Add encoder-driven Wi-Fi password entry.
- Validate VLC, Flask, GPIO, and OLED behavior on the Raspberry Pi hardware.
- Add direct YouTube playback instead of list-only browsing.
- Migrate media playback sources one by one to MPD-compatible backends, then enable `mpd_oled_media_handoff`.

### Notes

- The current repository did not contain stable `stations.csv`, `menu.json`, or YouTube source data, so the rewrite is being structured first.
- This directory is intended to become the final maintainable version instead of extending the monolithic prototype further.
- Internet radio and local music are now wired at the component level, but both still need device-level validation on the Pi because this workspace is not attached to the target hardware.
- DLNA depends on `upnpclient` being installed on the Pi before discovery works.
- `mpd_oled` media handoff is intentionally disabled until the relevant playback source is MPD-backed, to avoid stale or incorrect metadata on the OLED.
