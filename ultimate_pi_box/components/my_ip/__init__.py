from __future__ import annotations

from ..base import BaseComponent
from ...rendering import draw_menu, draw_message, draw_search
from ...system import connect_wifi, get_hostname, get_ip_address, get_wifi_networks

PASSWORD_CHARSET = (
    list("abcdefghijklmnopqrstuvwxyz")
    + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    + list("0123456789")
    + list("@#$%_-.!& ")
    + ["<DEL>", "<OK>"]
)


class MyIPComponent(BaseComponent):
    key = "my_ip"
    label = "MyIP"

    def __init__(self) -> None:
        self.mode = "info"  # info | networks | password | result
        self.networks: list[dict[str, str]] = []
        self.net_index = 0
        self.password = ""
        self.char_index = 0
        self.target_ssid = ""
        self.result_lines: list[str] = []

    def enter(self, app) -> None:
        self.mode = "info"
        self.render(app)

    def render(self, app) -> None:
        if self.mode == "networks":
            if not self.networks:
                draw_message(
                    app.hardware,
                    "WiFi Networks",
                    ["No networks found.", "Press to rescan."],
                    "Long press to go back",
                )
                return
            labels = [
                f"{'*' if net['active'] == 'yes' else ' '}{net['ssid']} {net['signal']}%"
                for net in self.networks
            ]
            draw_menu(app.hardware, "WiFi Networks", labels, self.net_index, f"{len(labels)} found")
            return

        if self.mode == "password":
            draw_search(
                app.hardware,
                f"Pass: {self.target_ssid}"[:20],
                self.password,
                PASSWORD_CHARSET[self.char_index],
                masked=True,
                hint="Press=add  Long=connect",
            )
            return

        if self.mode == "result":
            draw_message(app.hardware, "WiFi", self.result_lines, "Long press to exit")
            return

        networks = get_wifi_networks()
        draw_message(
            app.hardware,
            self.label,
            [
                f"Host: {get_hostname()}",
                f"IP: {get_ip_address()}",
                f"WiFi networks: {len(networks)}",
                "Press: connect / refresh",
            ],
            "Long press to exit",
        )

    def on_rotate(self, app, direction: int) -> None:
        if self.mode == "networks":
            if self.networks:
                self.net_index = (self.net_index + direction) % len(self.networks)
        elif self.mode == "password":
            self.char_index = (self.char_index + direction) % len(PASSWORD_CHARSET)
        self.render(app)

    def on_short_press(self, app) -> None:
        if self.mode == "info":
            self.networks = get_wifi_networks()
            self.net_index = 0
            self.mode = "networks"
            self.render(app)
            return

        if self.mode == "networks":
            if not self.networks:
                self.networks = get_wifi_networks()
                self.render(app)
                return
            net = self.networks[self.net_index]
            self.target_ssid = net["ssid"]
            security = (net.get("security") or "").upper()
            if security in {"", "OPEN", "--"}:
                self._connect(app, "")
            else:
                self.password = ""
                self.char_index = 0
                self.mode = "password"
                self.render(app)
            return

        if self.mode == "password":
            char = PASSWORD_CHARSET[self.char_index]
            if char == "<DEL>":
                self.password = self.password[:-1]
            elif char == "<OK>":
                self._connect(app, self.password)
                return
            else:
                self.password += char
            self.render(app)
            return

        if self.mode == "result":
            self.mode = "info"
            self.render(app)

    def _connect(self, app, password: str) -> None:
        self.mode = "result"
        self.result_lines = [f"Connecting to", self.target_ssid, "please wait..."]
        self.render(app)
        success, message = connect_wifi(self.target_ssid, password)
        if success:
            self.result_lines = ["Connected to", self.target_ssid, f"IP: {get_ip_address()}"]
        else:
            self.result_lines = ["Failed to connect", self.target_ssid, message[:40]]
        self.render(app)

    def on_long_press(self, app) -> None:
        if self.mode == "password":
            self.mode = "networks"
            self.render(app)
            return
        if self.mode in {"networks", "result"}:
            self.mode = "info"
            self.render(app)
            return
        super().on_long_press(app)

    def get_web_state(self, app) -> dict[str, object]:
        return {
            "key": self.key,
            "label": self.label,
            "items": [get_ip_address()],
            "selected_index": 0,
            "current_item": get_ip_address(),
            "hostname": get_hostname(),
        }
