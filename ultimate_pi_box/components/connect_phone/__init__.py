from __future__ import annotations

from ..base import BaseComponent
from ...rendering import draw_message
from ...system import get_paired_devices, run_command


class ConnectPhoneComponent(BaseComponent):
    key = "connect_phone"
    label = "Connect Phone"

    def render(self, app) -> None:
        result = run_command(["bluetoothctl", "devices", "Connected"])
        connected_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        paired_count = len(get_paired_devices())
        if connected_lines:
            device_text = connected_lines[0].replace("Device ", "", 1)
            lines = [
                "Connected device:",
                device_text,
                f"Paired devices: {paired_count}",
                "Control module next",
            ]
        else:
            lines = [
                "No phone connected",
                f"Paired devices: {paired_count}",
                "Pair from BT Settings",
                "Press to refresh",
            ]
        draw_message(app.hardware, self.label, lines, "Long press to exit")

    def on_short_press(self, app) -> None:
        self.render(app)
