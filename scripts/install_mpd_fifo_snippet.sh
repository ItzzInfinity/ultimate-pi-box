#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIFO_SNIPPET="$ROOT_DIR/OLED_Demo/mpd_oled/scripts/mpd_oled_fifo.conf"

if [[ ! -f "$FIFO_SNIPPET" ]]; then
  echo "FIFO snippet not found: $FIFO_SNIPPET" >&2
  exit 1
fi

echo "Append the following block to your MPD config if you want MPD-backed spectrum:"
echo
cat "$FIFO_SNIPPET"
echo
echo "Typical target file: /etc/mpd.conf"
