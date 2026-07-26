from __future__ import annotations

import time

from ..base import BaseComponent
from ...rendering import draw_message, draw_player
from ...system import (
    bt_media_control,
    get_bt_media_info,
    get_paired_devices,
    run_command,
)


class ConnectPhoneComponent(BaseComponent):
    key = "connect_phone"
    label = "Connect Phone"
    media_screen = True

    def __init__(self) -> None:
        self.control_index = 1
        self.seed = 0
        self.last_poll = 0.0
        self.media: dict[str, str] = {}
        self.connected_name = ""

    def enter(self, app) -> None:
        self.control_index = 1
        self.seed = 0
        self._poll(force=True)
        self.render(app)

    def _poll(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and (now - self.last_poll) < 1.0:
            return
        self.last_poll = now
        result = run_command(["bluetoothctl", "devices", "Connected"])
        connected = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        self.connected_name = connected[0].replace("Device ", "", 1) if connected else ""
        self.media = get_bt_media_info() if self.connected_name else {}

    def render(self, app) -> None:
        if not self.connected_name:
            paired_count = len(get_paired_devices())
            draw_message(
                app.hardware,
                self.label,
                [
                    "No phone connected",
                    f"Paired devices: {paired_count}",
                    "Pair from BT Settings",
                    "Press to refresh",
                ],
                "Long press to exit",
            )
            return

        title = self.media.get("title") or self.connected_name.split(" ", 1)[-1] or "Connected"
        artist = self.media.get("artist") or "Phone (A2DP)"
        status = self.media.get("status") or ""
        paused = status.lower() == "paused"
        controls = ["<<", ">" if paused else "||", ">>"]
        draw_player(
            app.hardware,
            title,
            artist,
            0.0,
            status.upper() if status else "BT",
            "",
            controls,
            self.control_index % 3,
            footer_left="PHONE",
            footer_right=status[:10] if status else "live",
            seed=self.seed,
        )

    def on_rotate(self, app, direction: int) -> None:
        if not self.connected_name:
            return
        self.control_index = (self.control_index + direction) % 3
        self.render(app)

    def on_short_press(self, app) -> None:
        if not self.connected_name:
            self._poll(force=True)
            self.render(app)
            return
        if self.control_index == 0:
            bt_media_control("Previous")
        elif self.control_index == 1:
            status = (self.media.get("status") or "").lower()
            bt_media_control("Play" if status == "paused" else "Pause")
        elif self.control_index == 2:
            bt_media_control("Next")
        self._poll(force=True)
        self.render(app)

    def tick(self, app) -> None:
        if not self.connected_name:
            return
        self.seed += 2
        self._poll()
        self.render(app)

    def get_web_state(self, app) -> dict[str, object]:
        self._poll()
        current = None
        if self.connected_name:
            title = self.media.get("title")
            artist = self.media.get("artist")
            current = f"{title} - {artist}" if title else self.connected_name
        return {
            "key": self.key,
            "label": self.label,
            "items": [self.connected_name] if self.connected_name else [],
            "selected_index": 0,
            "current_item": current,
            "status": self.media.get("status", ""),
        }

    def web_command(self, app, command: str, value: str | None = None) -> bool:
        if not self.connected_name:
            self._poll(force=True)
        if command in {"next", "previous"}:
            ok = bt_media_control("Next" if command == "next" else "Previous")
            self._poll(force=True)
            self.render(app)
            return ok
        if command == "play_pause":
            status = (self.media.get("status") or "").lower()
            ok = bt_media_control("Play" if status == "paused" else "Pause")
            self._poll(force=True)
            self.render(app)
            return ok
        return False
