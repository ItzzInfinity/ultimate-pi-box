# Components Package

Each feature of the Ultimate Pi Box should live in its own directory under this package.

## Component Contract

Every component should follow the shared lifecycle used by the app:

- `enter(app)`
- `exit(app)`
- `render(app)`
- `on_rotate(app, direction)`
- `on_short_press(app)`
- `on_long_press(app)`
- `tick(app)`

## Planned Components

- `my_music/`
- `youtube_online/`
- `connect_phone/`
- `internet_radio/`
- `my_ip/`
- `bt_settings/`
- `system_volume/`
- `shutdown/`
- `dlna_upnp/`

## Purpose

- Keep UI state and playback logic isolated per feature.
- Reduce coupling with the main menu controller.
- Make it possible to implement and test one feature at a time.
