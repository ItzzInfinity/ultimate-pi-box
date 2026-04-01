# Shared Runtime Package

This package contains the common runtime used by all components.

## Files

- `app.py`
  Main event loop, menu handling, and input dispatch.
- `config.py`
  Path and runtime configuration.
- `hardware.py`
  OLED, rotary encoder, and button setup with mock fallbacks.
- `players.py`
  VLC helper utilities.
- `rendering.py`
  OLED rendering helpers for menus, messages, volume, player screens, and idle clock.
- `system.py`
  OS-level helpers for volume, Bluetooth, Wi-Fi, and IP/network info.
- `components/`
  Feature-specific component implementations and docs.

## Design Goals

- Keep hardware-specific code centralized.
- Avoid hard-coded absolute runtime paths.
- Make each component independent enough to test and replace later.
