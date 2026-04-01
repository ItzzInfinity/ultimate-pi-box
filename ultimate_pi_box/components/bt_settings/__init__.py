from __future__ import annotations

from ..base import BaseComponent
from ...rendering import draw_message
from ...system import get_bluetooth_show, get_paired_devices


class BTSettingsComponent(BaseComponent):
    key = "bt_settings"
    label = "BT Settings"

    def render(self, app) -> None:
        state = get_bluetooth_show()
        paired_devices = get_paired_devices()
        draw_message(
            app.hardware,
            self.label,
            [
                f"Power: {state.get('Powered', 'unknown')}",
                f"Visible: {state.get('Discoverable', 'unknown')}",
                f"Paired: {len(paired_devices)} device(s)",
                "Press to refresh",
            ],
            "Long press to exit",
        )

    def on_short_press(self, app) -> None:
        self.render(app)
