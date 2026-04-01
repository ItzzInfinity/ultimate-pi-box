from __future__ import annotations

from ..base import BaseComponent
from ...rendering import draw_message
from ...system import get_hostname, get_ip_address, get_wifi_networks


class MyIPComponent(BaseComponent):
    key = "my_ip"
    label = "MyIP"

    def render(self, app) -> None:
        networks = get_wifi_networks()
        draw_message(
            app.hardware,
            self.label,
            [
                f"Host: {get_hostname()}",
                f"IP: {get_ip_address()}",
                f"WiFi networks: {len(networks)}",
                "Press to refresh",
            ],
            "Long press to exit",
        )

    def on_short_press(self, app) -> None:
        self.render(app)
