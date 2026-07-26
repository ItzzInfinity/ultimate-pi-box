<!-- Gap analysis and serial execution roadmap, derived from FSD.md vs actual code -->
# Roadmap: FSD Compliance Gaps & Serial Action Plan

Generated 2026-06-16 from a full read of `FSD.md` against every component module under
`ultimate_pi_box/`. Per the FSD "DESIGN PIVOT" note ("FOR NOW FREEZE EVERY FUNCTION AS IT IS
... LET'S ONE AT A TIME"), this plan is deliberately serial: each numbered action is small,
independently verifiable, and does not touch frozen/working behavior outside its own scope.

Work top to bottom. Do not start action N+1 until action N's verification step passes.

## 0. Compliance snapshot (as of this audit)

| FSD Component | Status | Notes |
|---|---|---|
| My Music | Functional, partial | playback/progress/repeat work; search, shuffle, bitrate, wifi/volume tile, floating bar graph from spec are missing |
| Youtube Online | UI-only stub | loads CSV/sqlite list; `__init__.py` explicitly says "Playback not wired yet."; no search, no favorites save, no yt-dlp invocation |
| Connect Phone | Status-only | lists paired/connected devices via `bluetoothctl`; no now-playing metadata, no prev/next transport control |
| Internet Radio | Functional | loads CSV, plays via VLC RC, matches spec |
| MyIP | Status-only | shows IP/hostname/WiFi count; no network list selection or password-entry connect flow |
| BT Settings | Status-only | shows power/discoverable/paired count; no enable/disable or pairing controls wired |
| System Volume | Functional | matches spec |
| ShutDown | Functional | matches spec |
| DLNA/UPnP | Functional | discovery, browse, playback via VLC RC, matches spec |
| Idle screensaver | Functional | clock, date, IP, wifi bars, volume; matches the FSD mock layout |
| Web interface | Functional (v2 from progress.md) | Flask UI exists; FSD section 7 future-enhancement of real-time control is not yet websocket-based |

Already-closed items from `FSD.md` "ISSUES" (overlap text, music_dir path, scrolling, screensaver
sizing) are **not** repeated below — they are done.

## 1. Repo hygiene (do first, zero functional risk) — DONE 2026-06-16

- **Goal:** stop tracking generated/junk files (`__pycache__/*.pyc`, `desktop.ini`) that currently
  show as modified in `git status`, so future diffs are signal not noise.
- **Files:** `.gitignore`, `git rm --cached` the tracked `__pycache__` and `desktop.ini` paths.
- **Verify:** `git status` shows no `__pycache__` or `desktop.ini` entries after the change; app
  still runs (`python main.py`).

## 2. My Music: add search — DONE 2026-06-16

- **Goal:** FSD 5.1 requires "a search function to quickly find specific tracks." Add a search
  mode to `MyMusicComponent` (`ultimate_pi_box/components/my_music/__init__.py`) — short-press a
  dedicated control or long-press-free gesture enters a filter-as-you-rotate mode over track stems.
- **Verify:** with 2+ tracks in `music_dir`, entering search and rotating narrows the visible list;
  selecting a filtered result plays the correct file.

## 3. My Music: add shuffle (distinct from repeat) — DONE 2026-06-16

- **Goal:** spec calls for shuffle *and* repeat as separate modes; only repeat exists today
  (`repeat_mode` toggle, control index 3). Add a shuffle flag and randomized "next track" order
  when enabled, independent of repeat.
- **Verify:** with shuffle on, repeatedly pressing "next" does not always advance sequentially;
  with shuffle off, behavior matches current sequential order exactly (no regression).

## 4. My Music: real bitrate in footer — DONE 2026-06-16

- **Goal:** FSD 5.1 wants current bitrate displayed. `draw_player` footer currently shows
  `"{len(self.tracks)} files"` (`my_music/__init__.py` render method) instead of bitrate. Compute
  bitrate (via VLC RC query or a lightweight tag read) and put it in `footer_right`, moving track
  count elsewhere or dropping it.
- **Verify:** footer value changes between two files known to have different bitrates (e.g. a
  128kbps vs 320kbps mp3), and matches `ffprobe`/file metadata.

## 5. My Music: volume + WiFi signal tile on player screen — DONE 2026-06-16

- **Goal:** FSD 5.1 wants volume and WiFi signal strength visible during playback, not just on the
  idle clock screen (`draw_idle_clock` in `rendering.py` currently owns those, `draw_player` does
  not). Add a small tile to `draw_player` reusing `_draw_signal_bars`/`get_volume_percent`.
- **Verify:** while a track plays, OLED shows current volume and a WiFi bar indicator that changes
  when volume or signal changes.

## 6. My Music: floating corner bar graph — DONE 2026-07-15

- **Goal:** FSD 5.1 describes "a bar graph floating randomly around the corners," distinct from the
  current fixed-position `_draw_equalizer` (always at 4 fixed x-coordinates). Add randomized corner
  placement per animation tick.
- **Verify:** capture two consecutive mock-OLED frames (via `HardwareBundle` mock `last_image`) and
  confirm bar positions move between corners over time, not just bar heights.

## 7. YouTube Online: wire real playback — DONE 2026-07-15

- **Goal:** close the explicit stub at `youtube_online/__init__.py` ("Playback not wired yet").
  On select, resolve the stored video ID/URL via `yt-dlp -g` (or equivalent) to a stream URL and
  play it through the existing `VlcRcProcess.play_url`/`play_shell`, mirroring how `my_music`
  drives playback.
- **Verify:** selecting a known-good entry from `youtube_favorites.csv`/`youtube.db` produces
  audible playback and the player screen (progress bar, controls) renders like `my_music`'s.

## 8. YouTube Online: search — DONE 2026-07-15

- **Goal:** FSD 5.2 requires searching YouTube for songs/playlists. Add a search mode that shells
  out to `yt-dlp` (e.g. `ytsearch:`) and lists results for selection, without touching the existing
  favorites-list rendering path.
- **Verify:** entering a query returns a non-empty result list for a known popular search term, and
  selecting a result plays it (depends on action 7).

## 9. YouTube Online: save favorites — DONE 2026-07-15

- **Goal:** FSD 5.2 requires saving favorite songs/playlists for quick access. From a search result,
  add a "save" action that appends to `youtube_favorites.csv` or `youtube.db` (whichever the
  existing loader prefers — `_load_items()` checks db first).
- **Verify:** save an item, restart the app, confirm it now appears in the main YouTube Online list
  without re-searching.

## 10. Connect Phone: real now-playing metadata via DBus — DONE 2026-07-15

- **Goal:** FSD 5.3 requires fetching currently-playing song info from the paired phone via DBus.
  Current code only shells out to `bluetoothctl devices Connected`. Add a DBus query against
  BlueZ's `org.bluez.MediaPlayer1` interface for Title/Artist/Status on the connected device.
- **Verify:** with a phone connected and actively playing audio over A2DP/AVRCP, the OLED shows the
  real track title/artist, and updates when the phone changes tracks.

## 11. Connect Phone: prev/next transport controls — DONE 2026-07-15

- **Goal:** FSD 5.3 explicitly requires previous/next controls. Wire short-press control buttons to
  `org.bluez.MediaPlayer1.Next()`/`Previous()` over DBus (depends on action 10 for the interface
  being established).
- **Verify:** pressing next/previous on the device actually skips tracks on the connected phone.

## 12. BT Settings: enable/disable + visibility controls — DONE 2026-07-15

- **Goal:** FSD 5.6 requires toggling Bluetooth on/off and visibility, not just displaying status.
  `system.py` already has `bluetooth_toggle_power()` and `bluetooth_toggle_discoverable()` —
  wire them to button/rotate input in `bt_settings/__init__.py`, which currently has no
  `on_rotate`/control logic.
- **Verify:** toggling from the OLED actually flips `bluetoothctl show` output for Powered and
  Discoverable.

## 13. BT Settings: pairing flow — DONE 2026-07-15

- **Goal:** FSD 5.6 requires managing paired devices. Add a scan-and-pair flow: enable
  discoverable/scan, list newly found unpaired devices, select to pair (`bluetoothctl pair <mac>`).
- **Verify:** a new test phone can be paired entirely from the OLED menu, then appears in
  `get_paired_devices()`.

## 14. MyIP: WiFi network connect flow with rotary password entry — DONE 2026-07-15

- **Goal:** FSD 5.5 requires listing available networks and connecting by entering a password via
  the rotary encoder. `system.py` already has `get_wifi_networks()`/`connect_wifi()`; `my_ip`
  currently only displays a count. Add network selection + a character-entry screen (rotate to
  pick character, press to confirm/advance, long-press to submit) feeding `connect_wifi`.
- **Verify:** connect to a real WPA2 network entirely from the OLED UI; `get_ip_address()` reflects
  the new network afterward.

## 15. Hardware validation pass on actual Raspberry Pi — BLOCKED (needs physical Pi)

- **Goal:** everything above (and the existing "Functional" components) has only been verified in
  mock mode in this environment. Run the full app on the target Pi Zero 2W with the real OLED,
  encoder, and DAC.
- **Verify:** `/api/status` on the web UI reports `mock_mode: false`; menu navigation, playback, and
  every component above work physically, not just in mock mode.

## 16. mpd_oled media handoff migration — one component at a time — BLOCKED (needs Pi + MPD backends)

Deferred deliberately: per `MPD_OLED_PIVOT.md`, enabling `mpd_oled_media_handoff` before a backend
is MPD-compatible causes stale/incorrect metadata. Do this only after actions 1–15 are stable.

- **16a.** Bridge `my_music` playback through MPD (e.g. add tracks to an MPD playlist instead of/in
  addition to direct VLC RC), then flip `mpd_oled_media_handoff` on for `my_music` only.
  **Verify:** OLED switches to mpd_oled's rendered now-playing screen only while `my_music` is
  active; all other components still render via Python exactly as before.
- **16b.** Repeat for `internet_radio`.
  **Verify:** same check, scoped to internet_radio only.
- **16c.** Repeat for `youtube_online` (after action 7 lands).
- **16d.** Repeat for `connect_phone` (after actions 10–11 land; note BT audio isn't MPD-controlled,
  so this may require a different bridging approach — re-evaluate feasibility before starting).
- **16e.** Repeat for `dlna_upnp`.

## 17. Future enhancement: real-time web UI (FSD section 7) — DONE 2026-07-15

- **Goal:** FSD lists a remote web interface as a future enhancement; the current Flask UI
  (`web.py`) is refresh/polling based. Add SSE or WebSocket push so the "Now Playing" panel updates
  without a manual refresh.
- **Verify:** start playback from the OLED, observe the open web page update without reloading.

---

### Notes on what NOT to change right now

- `config.py`'s `music_dir = /home/infinity/Music` is an already-closed FSD issue, not a bug —
  leave it.
- `encoder_max_steps = 0` in `config.py` is gpiozero's "unbounded" setting and is what makes menu
  scrolling work past 2 steps; the FSD's `max_steps=2` was a hardware wiring note, not a UX
  requirement — no change needed here.
- `requests`, `yt-dlp`, `dbus-python` in `requirements.txt` are currently unused but are exactly
  what actions 7–11 need — keep them, don't prune until those actions are abandoned.
