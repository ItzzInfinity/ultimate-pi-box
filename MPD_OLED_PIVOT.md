# mpd_oled Design Pivot

## Goal

Move OLED ownership for music-centric display states away from custom Python drawing and toward the community-backed `mpd_oled` engine.

## What Is Implemented

- The project now vendors the `mpd_oled` source under `OLED_Demo/mpd_oled/`.
- The Python app includes an `MpdOledController` runtime wrapper.
- Idle screensaver ownership can hand off to `mpd_oled`, which uses its built-in clock and stop-screen mode.
- Media components are tagged as `media_screen` and are prepared for future handoff.
- Build and MPD FIFO helper scripts were added under `scripts/`.

## What Is Intentionally Frozen

- Existing playback backends remain as they are for now.
- Python still renders menu and rotary-encoder list screens.
- Media playback handoff to `mpd_oled` is wired but disabled by default with:
  - `AppConfig.mpd_oled_media_handoff = False`

This is deliberate. `mpd_oled` reads MPD state, while several current project components still play through VLC or other direct integrations. Enabling handoff immediately would risk mismatched on-screen metadata.

## Activation Path

### Already active

- idle / screensaver display ownership

### Prepared but disabled

- `My Music`
- `Youtube Online`
- `Connect Phone`
- `Internet Radio`
- `DLNA/UPnP`

## Runtime Rules

- Python OLED rendering is still authoritative for:
  - main menu
  - non-media settings screens
  - encoder-driven lists
- `mpd_oled` is authoritative for:
  - idle clock mode when started successfully
- Future media handoff should only be enabled after the relevant playback source is MPD-backed or bridged to MPD state.

## Build Notes

Build the vendored source on the Pi with:

```bash
./scripts/build_mpd_oled_local.sh
```

To configure MPD FIFO spectrum support, inspect:

```bash
./scripts/install_mpd_fifo_snippet.sh
```

## Next Safe Step

Migrate one playback backend at a time to MPD-compatible control, then turn on `mpd_oled_media_handoff`.
