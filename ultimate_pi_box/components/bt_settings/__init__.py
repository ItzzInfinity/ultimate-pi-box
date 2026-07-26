from __future__ import annotations

from ..base import BaseComponent
from ...rendering import draw_menu, draw_message
from ...system import (
    bluetooth_pair,
    bluetooth_scan,
    bluetooth_toggle_discoverable,
    bluetooth_toggle_power,
    get_bluetooth_show,
    get_paired_devices,
)


class BTSettingsComponent(BaseComponent):
    key = "bt_settings"
    label = "BT Settings"

    def __init__(self) -> None:
        self.mode = "menu"  # menu | scan
        self.menu_index = 0
        self.state: dict[str, str] = {}
        self.found: list[dict[str, str]] = []
        self.scan_index = 0
        self.status_line = ""

    def enter(self, app) -> None:
        self.mode = "menu"
        self.menu_index = 0
        self.status_line = ""
        self._refresh_state()
        self.render(app)

    def _refresh_state(self) -> None:
        self.state = get_bluetooth_show()

    def _menu_options(self) -> list[str]:
        powered = self.state.get("Powered", "unknown")
        discoverable = self.state.get("Discoverable", "unknown")
        paired = len(get_paired_devices())
        return [
            f"Power: {powered} (toggle)",
            f"Visible: {discoverable} (toggle)",
            f"Paired: {paired} device(s)",
            "Scan & pair new device",
            "Refresh status",
        ]

    def render(self, app) -> None:
        if self.mode == "scan":
            if not self.found:
                draw_message(
                    app.hardware,
                    "Scan & Pair",
                    [
                        self.status_line or "No devices found.",
                        "Make phone visible,",
                        "then press to rescan.",
                    ],
                    "Long press to go back",
                )
                return
            labels = [device["name"] for device in self.found]
            subtitle = self.status_line or f"{len(labels)} found"
            draw_menu(app.hardware, "Scan & Pair", labels, self.scan_index, subtitle)
            return

        options = self._menu_options()
        subtitle = self.status_line or "Rotate + press"
        draw_menu(app.hardware, self.label, options, self.menu_index, subtitle)

    def on_rotate(self, app, direction: int) -> None:
        if self.mode == "scan":
            if self.found:
                self.scan_index = (self.scan_index + direction) % len(self.found)
        else:
            self.menu_index = (self.menu_index + direction) % len(self._menu_options())
        self.render(app)

    def on_short_press(self, app) -> None:
        if self.mode == "scan":
            if not self.found:
                self._run_scan(app)
            else:
                self._pair_selected(app)
            self.render(app)
            return

        self.status_line = ""
        if self.menu_index == 0:
            powered = self.state.get("Powered", "no") == "yes"
            bluetooth_toggle_power(not powered)
            self._refresh_state()
            self.status_line = "Power toggled"
        elif self.menu_index == 1:
            visible = self.state.get("Discoverable", "no") == "yes"
            bluetooth_toggle_discoverable(not visible)
            self._refresh_state()
            self.status_line = "Visibility toggled"
        elif self.menu_index == 2:
            self._refresh_state()
            self.status_line = "Refreshed"
        elif self.menu_index == 3:
            self.mode = "scan"
            self.scan_index = 0
            self.found = []
            self._run_scan(app)
        elif self.menu_index == 4:
            self._refresh_state()
            self.status_line = "Refreshed"
        self.render(app)

    def _run_scan(self, app) -> None:
        self.status_line = "Scanning..."
        self.render(app)
        found = bluetooth_scan(duration=8)
        paired_macs = {device["mac"] for device in get_paired_devices()}
        self.found = [device for device in found if device["mac"] not in paired_macs]
        self.scan_index = 0
        self.status_line = "" if self.found else "No new devices."

    def _pair_selected(self, app) -> None:
        device = self.found[self.scan_index]
        self.status_line = f"Pairing {device['name'][:12]}..."
        self.render(app)
        success, _ = bluetooth_pair(device["mac"])
        self.status_line = "Paired!" if success else "Pair failed"
        if success:
            self.found = [d for d in self.found if d["mac"] != device["mac"]]
            self.scan_index = 0

    def on_long_press(self, app) -> None:
        if self.mode == "scan":
            self.mode = "menu"
            self.status_line = ""
            self.render(app)
            return
        super().on_long_press(app)

    def get_web_state(self, app) -> dict[str, object]:
        self._refresh_state()
        return {
            "key": self.key,
            "label": self.label,
            "items": [device["name"] for device in get_paired_devices()],
            "selected_index": 0,
            "current_item": None,
            "powered": self.state.get("Powered", "unknown"),
            "discoverable": self.state.get("Discoverable", "unknown"),
        }

    def web_command(self, app, command: str, value: str | None = None) -> bool:
        if command == "toggle_power":
            self._refresh_state()
            bluetooth_toggle_power(self.state.get("Powered", "no") != "yes")
            return True
        if command == "toggle_visible":
            self._refresh_state()
            bluetooth_toggle_discoverable(self.state.get("Discoverable", "no") != "yes")
            return True
        return False
