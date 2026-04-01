# Youtube Online Component

## Scope

- load saved YouTube entries from CSV or SQLite
- stream selected audio through `yt-dlp` and VLC
- show title and playback state on OLED

## Planned Inputs

- `v2/data/youtube_favorites.csv`
- optional `v2/data/youtube.db`

## Planned UI States

- saved item list
- now playing screen
- playback controls

## Notes

- Search and favorites management can be added after the base playback flow is stable.
