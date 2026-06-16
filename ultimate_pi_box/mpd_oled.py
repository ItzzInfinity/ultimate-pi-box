from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class MpdOledController:
    def __init__(self, config) -> None:
        self.config = config
        self.process: subprocess.Popen | None = None
        self.owner: str | None = None
        self.binary_path = self._resolve_binary()

    def _resolve_binary(self) -> str | None:
        for candidate in self.config.mpd_oled_binary_candidates:
            if not candidate:
                continue
            if "/" in candidate or "\\" in candidate:
                path = Path(candidate)
                if path.exists():
                    return str(path)
            else:
                found = shutil.which(candidate)
                if found:
                    return found
        return None

    def is_available(self) -> bool:
        return self.binary_path is not None

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def is_owned_by(self, owner: str) -> bool:
        return self.is_running() and self.owner == owner

    def start(self, owner: str) -> bool:
        if owner != "idle" and not self.config.mpd_oled_media_handoff:
            return False
        if not self.is_available():
            return False
        if self.is_running():
            if self.owner == owner:
                return True
            self.stop()

        command = self._command()
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self.owner = owner
        return True

    def stop(self) -> None:
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=1.0)
            except Exception:
                self.process.kill()
            self.process = None
        self.owner = None

    def stop_if_owned_by(self, owner: str) -> None:
        if self.owner == owner:
            self.stop()

    def _command(self) -> list[str]:
        command = [
            self.binary_path or "mpd_oled",
            "-o",
            str(self.config.mpd_oled_oled_type),
            "-b",
            str(self.config.mpd_oled_bars),
            "-g",
            str(self.config.mpd_oled_gap),
            "-f",
            str(self.config.mpd_oled_framerate),
            "-s",
            self.config.mpd_oled_scroll,
            "-P",
            self.config.mpd_oled_pause_screen,
            "-I",
            self.config.mpd_oled_invert,
            "-a",
            f"{self.config.oled_address:02X}",
            "-B",
            str(self.config.oled_port),
            "-p",
            self.config.mpd_oled_player,
        ]
        if self.config.mpd_oled_rotate180:
            command.append("-R")
        return command

    def status(self) -> dict[str, object]:
        return {
            "available": self.is_available(),
            "binary_path": self.binary_path,
            "running": self.is_running(),
            "owner": self.owner,
            "source_dir": str(self.config.mpd_oled_source_dir),
            "media_handoff_enabled": self.config.mpd_oled_media_handoff,
        }
