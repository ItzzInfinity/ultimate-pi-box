from __future__ import annotations

from ..base import BaseComponent
from ...rendering import draw_message


class DLNAUPnPComponent(BaseComponent):
    key = "dlna_upnp"
    label = "DLNA/UPnP"

    def render(self, app) -> None:
        draw_message(
            app.hardware,
            self.label,
            [
                "Directory reserved.",
                "Feature not wired",
                "into the menu yet.",
            ],
            "Long press to exit",
        )
