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


def build_config(root_dir: Path | None = None) -> AppConfig:
    resolved_root = root_dir or Path(__file__).resolve().parents[1]
    package_dir = resolved_root / "ultimate_pi_box"
    data_dir = resolved_root / "data"
    return AppConfig(
        root_dir=resolved_root,
        package_dir=package_dir,
        menu_path=resolved_root / "menu.json",
        data_dir=data_dir,
        music_dir=Path("/home/infinity/Music"),
        radio_csv=data_dir / "radio_stations.csv",
        youtube_csv=data_dir / "youtube_favorites.csv",
        youtube_db=data_dir / "youtube.db",
    )
