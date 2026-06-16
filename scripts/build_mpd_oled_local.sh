#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MPD_OLED_DIR="$ROOT_DIR/OLED_Demo/mpd_oled"

if [[ ! -d "$MPD_OLED_DIR" ]]; then
  echo "mpd_oled source directory not found: $MPD_OLED_DIR" >&2
  exit 1
fi

cd "$MPD_OLED_DIR"

./bootstrap
CPPFLAGS="-W -Wall -Wno-psabi" ./configure
make -j"$(nproc)"

echo
echo "Build complete."
echo "Binary candidate: $MPD_OLED_DIR/src/mpd_oled"
echo
echo "If you also need mpd_oled_cava, build and install cava separately as documented in:"
echo "  $MPD_OLED_DIR/doc/install_volumio3_source.md"
