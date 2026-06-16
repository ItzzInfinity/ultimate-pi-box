from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    root_dir: Path
    package_dir: Path
    menu_path: Path
    data_dir: Path
    music_dir: Path
    radio_csv: Path
    youtube_csv: Path
    youtube_db: Path
    mpd_oled_source_dir: Path
    mpd_oled_binary_candidates: tuple[str, ...]
    long_press_seconds: float = 1.0
    idle_timeout_seconds: float = 30.0
    poll_interval_seconds: float = 0.1
    vlc_host: str = "127.0.0.1"
    vlc_port: int = 4212
    oled_port: int = 1
    oled_address: int = 0x3C
    encoder_clk_pin: int = 17
    encoder_dt_pin: int = 22
    encoder_button_pin: int = 27
    encoder_max_steps: int = 0
    wifi_device: str = "wlan0"
    bluetooth_adapter: str = "hci0"
    default_font_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    title_font_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    web_host: str = "0.0.0.0"
    web_port: int = 8080
    audio_extensions: tuple[str, ...] = ("mp3", "wav", "flac", "m4a", "ogg", "aac")
    mpd_oled_oled_type: int = 6
    mpd_oled_bars: int = 16
    mpd_oled_gap: int = 1
    mpd_oled_framerate: int = 15
    mpd_oled_scroll: str = "8,5,12,5"
    mpd_oled_pause_screen: str = "s"
    mpd_oled_invert: str = "n"
    mpd_oled_player: str = "mpd"
    mpd_oled_rotate180: bool = False
    mpd_oled_media_handoff: bool = False


def build_config(root_dir: Path | None = None) -> AppConfig:
    resolved_root = root_dir or Path(__file__).resolve().parents[1]
    package_dir = resolved_root / "ultimate_pi_box"
    data_dir = resolved_root / "data"
    mpd_oled_source_dir = resolved_root / "OLED_Demo" / "mpd_oled"
    return AppConfig(
        root_dir=resolved_root,
        package_dir=package_dir,
        menu_path=resolved_root / "menu.json",
        data_dir=data_dir,
        music_dir=Path("/home/infinity/Music"),
        radio_csv=data_dir / "radio_stations.csv",
        youtube_csv=data_dir / "youtube_favorites.csv",
        youtube_db=data_dir / "youtube.db",
        mpd_oled_source_dir=mpd_oled_source_dir,
        mpd_oled_binary_candidates=(
            "/usr/local/bin/mpd_oled",
            str(mpd_oled_source_dir / "src" / "mpd_oled"),
            "mpd_oled",
        ),
    )
