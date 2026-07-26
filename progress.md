# Progress Log

## 2026-07-15

### Completed (ROADMAP.md actions 6-14 and 17)

- **Action 6 — My Music floating corner bar graph:** replaced the fixed-position
  `_draw_equalizer` in `rendering.py` with `_draw_floating_bars`, a 3-bar cluster that hops to a
  different one of the four screen corners every ~8 animation ticks (`(seed // 8) % 4`). Verified in
  mock mode that the cluster's centroid visits all four corners (LT, RT, LB, RB) as `seed` advances,
  i.e. bar *positions* move, not just heights.
- **Action 7 — YouTube real playback:** `youtube_online/__init__.py` no longer says "Playback not
  wired yet." Selecting a favorite (or a search result) resolves the video id/URL to a direct audio
  stream via `resolve_youtube_stream()` (new in `system.py`, `yt-dlp -f bestaudio -g`, argv form) and
  plays it through the existing `VlcRcProcess.play_url`. A full player screen (progress bar,
  `<< / ||/> / >> / St` controls, floating bars) renders like `my_music`.
- **Action 8 — YouTube search:** a rotary character-entry screen (`draw_search`) feeds
  `search_youtube()` (new in `system.py`, `yt-dlp --flat-playlist --dump-json ytsearch10:`). Results
  render as a selectable list.
- **Action 9 — YouTube save favorites:** from a search result, an action menu (`Play` /
  `Save to favorites` / `Back`) appends `Title,Video ID,URL` to `youtube_favorites.csv` (header
  written on first save) and reloads the favorites list so the entry appears immediately.
- **Action 10 — Connect Phone now-playing via DBus:** `system.py` gained `get_bt_media_info()`,
  which walks BlueZ's `org.freedesktop.DBus.ObjectManager` to find `org.bluez.MediaPlayer1` and reads
  `Track` Title/Artist/Album and `Status`. `connect_phone` polls it (≤1 Hz) and renders a player
  screen with the real track metadata, degrading gracefully to a "no phone connected" message.
- **Action 11 — Connect Phone prev/next:** `bt_media_control()` calls
  `org.bluez.MediaPlayer1.Next()/Previous()/Play()/Pause()`. The three-way control row
  (`<< / ||-or-> / >>`) is wired to short-press and to the web transport panel.
- **Action 12 — BT Settings toggles:** `bt_settings` is now an interactive menu; entries 1-2 flip
  `Powered`/`Discoverable` via the existing `bluetooth_toggle_power/discoverable`, then re-read
  `bluetoothctl show`.
- **Action 13 — BT Settings pairing flow:** "Scan & pair new device" runs `bluetooth_scan()`
  (`bluetoothctl --timeout 8 scan on` + `devices`), filters out already-paired MACs, lists the rest,
  and pairs+trusts the selected one via `bluetooth_pair()`.
- **Action 14 — MyIP WiFi connect flow:** `my_ip` now has info → network-list → password-entry →
  result states. It lists `get_wifi_networks()` (SSID + signal), connects open networks directly, and
  for secured networks opens a **masked** rotary character-entry screen (upper/lower/digits/symbols)
  feeding `connect_wifi(ssid, password)`.
- **Action 17 — real-time web UI:** added a Server-Sent Events channel. `app.live_state()` returns a
  lightweight snapshot (active component only, so it is cheap to poll ~1 Hz); `web.py` streams it at
  `/events`, and page JS updates the "Now Playing" panel and mpd_oled status with no reload. A live
  dot indicates stream health.

### Security review — vulnerabilities found and fixed

1. **SQL injection (fixed)** — `youtube_online._load_from_db` interpolated a table name straight into
   `f"SELECT * FROM {table[0]}"`. Now the identifier is validated against `^[A-Za-z_][A-Za-z0-9_]*$`
   and quoted (`"..."`) before use; a non-matching name returns no rows.
2. **Latent command injection (fixed)** — `VlcRcProcess.play_shell` used `subprocess.Popen(..., shell=True)`
   on an f-string. It was dead code (nothing called it) and the YouTube feature was deliberately built
   on the argv-form `play_url` instead, so the method was removed to eliminate the sink entirely.
3. **Web CSRF via state-changing GET (fixed)** — `/component/<key>/<command>` and `/open/<key>` were
   GET routes reachable from `<a href>`/`<img>`/link-prefetch on any page. They are now **POST-only**
   (GET → 405) and the UI submits real forms. `/api/status` and the new `/events` stay GET (read-only).
4. **yt-dlp / VLC / nmcli / bluetoothctl invocations (verified safe)** — every new external call uses
   the argv form (never `shell=True`), so user/network-supplied ids, URLs, SSIDs and MACs cannot break
   out into a shell.

### Known residual risks (documented, not code bugs)

- The web UI has **no authentication** and binds `0.0.0.0:8080` — this is the FSD's intended
  "anyone on the LAN can control the box" model, so it is left as-is; CSRF hardening above limits
  drive-by abuse. Add a token/basic-auth if the box is ever exposed beyond a trusted LAN.
- `connect_wifi` passes the WiFi password as an `nmcli` argument, so it is briefly visible in the
  process list (`ps`) — inherent to the nmcli CLI, acceptable on a single-user appliance.
- `dlna_upnp._parse_didl` parses DLNA XML with stdlib `ElementTree`, which does not resolve external
  entities (no XXE/SSRF) but can in principle be made to expand internal entities (billion-laughs
  DoS) by a malicious LAN DLNA server. Low risk; swap to `defusedxml` if hardening further.

### Verification performed (mock-hardware environment)

- `main.py` runs for several seconds with the real Flask server and event loop, no tracebacks.
- All 9 components pass an enter → rotate → short-press → tick → long-press → `get_web_state` sweep.
- Action 6: asserted the floating cluster's centroid occupies all four distinct corners across seeds.
- Actions 7-9: drove the YouTube state machine end-to-end with stubbed network calls — search →
  results → action menu → save (CSV written with header + row) and → play (stream resolved, player
  mode entered).
- Actions 12-14: drove BT power/visibility toggles, scan→pair, and the MyIP network-list → WPA2
  password entry → connect (and open-network direct connect) with stubbed system calls; asserted the
  right `bluetooth_*` / `connect_wifi` calls fired with the expected arguments.
- Web: home renders with the SSE hook; GET on a command route returns 405; POST succeeds; `/events`
  returns `text/event-stream` and emits a `data:` frame.

### Still blocked (require physical hardware — cannot be done in this mock environment)

- **Action 15 — hardware validation pass:** needs the actual Pi Zero 2W, OLED, encoder and DAC; this
  workspace has no GPIO/OLED (`mock_mode: true`). All above is verified only in mock mode.
- **Action 16 — mpd_oled media handoff migration:** deferred per `MPD_OLED_PIVOT.md`; enabling
  handoff before each backend is MPD-compatible causes stale metadata, and it needs the Pi + a
  running MPD to validate. `mpd_oled_media_handoff` remains `False`.

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
