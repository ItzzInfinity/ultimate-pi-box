# Data Directory

This directory holds runtime content for the modular app.

## Planned Files

- `radio_stations.csv`
  Internet radio station list.
- `youtube_favorites.csv`
  Saved YouTube entries when SQLite is not used.
- `youtube.db`
  Optional SQLite database for YouTube metadata.
- `music/`
  Local songs for the `My Music` component.

## Expected Formats

### `radio_stations.csv`

Recommended columns:

- `Station Name`
- `Station URL`

### `youtube_favorites.csv`

Recommended columns:

- `Title`
- `URL`
- `Video ID`

## Notes

- Keep this directory data-only.
- Component logic should read from here, not from hard-coded desktop paths.
