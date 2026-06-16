# Progress Log

## 2026-06-16

### Completed (ROADMAP.md actions 1-5)

- **Action 1 — Repo hygiene:** untracked 85 generated files (`__pycache__/*.pyc`, `desktop.ini`)
  from git via `git rm --cached`, and added `__pycache__/`, `*.pyc`, `desktop.ini` to `.gitignore`
  so they stop reappearing as noise in future diffs.
- **Action 2 — My Music search:** added an in-list `[Search]` entry at the top of the track
  browser. Selecting it opens a rotary-encoder character-entry screen (`draw_search` in
  `rendering.py`) built from `SEARCH_CHARSET` (a-z, 0-9, space, `<DEL>`, `<OK>`); rotate cycles the
  current character, short-press appends it (or deletes/confirms), long-press cancels back to the
  list without exiting the component. Confirming filters `self.filtered` by case-insensitive
  substring match against track filenames; an empty query clears the filter.
- **Action 3 — My Music shuffle:** added a `shuffle_mode` flag distinct from `repeat_mode`. The
  4th player control now cycles `off -> shuffle -> repeat -> off` and shows `S`/`R`/`-` on the
  OLED. Shuffle picks a random next track (excluding the current one) on next/previous/auto-advance;
  repeat and sequential playback behavior are unchanged from before.
- **Action 4 — My Music bitrate:** added `estimate_bitrate_kbps()` to `system.py` (file size over
  known duration, no new dependency). The player screen's footer-right now shows real
  `NNNkbps` once duration is known, replacing the previous static track-count text.
- **Action 5 — Volume + WiFi tile on player screen:** `draw_player()` in `rendering.py` now always
  draws WiFi signal bars in the top-right corner (title marquee width is reduced to make room) and
  the current system volume percentage centered in the footer row. This is additive to
  `draw_player`, so `internet_radio` and `dlna_upnp` (which reuse the same renderer) automatically
  pick it up with no code changes on their end.

### Verification performed

- Imported all touched modules to confirm no syntax/import errors.
- Scripted smoke test driving `MyMusicComponent` end-to-end in mock-hardware mode: loaded 3 fake
  tracks, entered search mode, typed "alpha", confirmed filter narrowed to the 2 matching tracks,
  played a filtered result, and cycled shuffle -> repeat -> off via the 4th control — all assertions
  passed.
- Called `draw_player`/`draw_search` directly against the mock OLED bundle to confirm they render
  without exceptions, including a radio-style call (no `my_music`-specific args) to confirm
  `internet_radio`/`dlna_upnp` remain compatible with the changed renderer.
- Ran `python main.py` in the background for several seconds in mock mode; no exceptions in the
  log.

### Notes

- Real hardware validation (actual VLC bitrate accuracy, OLED corner-spacing legibility, rotary
  feel of the character-entry screen) still needs to happen on the Pi — this environment only has
  mock GPIO/OLED.
- Roadmap actions 6+ (floating corner bar graph, YouTube playback, Connect Phone DBus metadata, BT
  Settings controls, MyIP WiFi connect flow, mpd_oled media handoff migration, realtime web UI) are
  still open — see `ROADMAP.md`.

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
