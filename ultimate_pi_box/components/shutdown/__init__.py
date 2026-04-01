from __future__ import annotations

import subprocess

from ..base import BaseComponent
from ...rendering import draw_menu, draw_message


class ShutdownComponent(BaseComponent):
    key = "shutdown"
    label = "ShutDown"

    def __init__(self) -> None:
        self.options = ["Cancel", "Shutdown", "Reboot"]
        self.selected_index = 0

    def enter(self, app) -> None:
        self.selected_index = 0
        self.render(app)

    def render(self, app) -> None:
        draw_menu(app.hardware, self.label, self.options, self.selected_index, "Confirm action")

    def on_rotate(self, app, direction: int) -> None:
        self.selected_index = (self.selected_index + direction) % len(self.options)
        self.render(app)

    def on_short_press(self, app) -> None:
        choice = self.options[self.selected_index]
        if choice == "Cancel":
            app.show_menu()
            return
        if app.hardware.mock_mode:
            draw_message(
                app.hardware,
                self.label,
                [
                    f"Mock mode active.",
                    f"{choice} skipped.",
                    "This will run only",
                    "on the Raspberry Pi.",
                ],
                "Long press to exit",
            )
            return
        if choice == "Shutdown":
            subprocess.run(["sudo", "shutdown", "now"], check=False)
        elif choice == "Reboot":
            subprocess.run(["sudo", "reboot"], check=False)
