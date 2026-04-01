from __future__ import annotations

from ..base import BaseComponent
from ...rendering import draw_volume
from ...system import get_volume_percent, set_volume_percent, toggle_mute


class SystemVolumeComponent(BaseComponent):
    key = "system_volume"
    label = "System Volume"

    def __init__(self) -> None:
        self.volume = 0
        self.muted = False

    def enter(self, app) -> None:
        self.volume = get_volume_percent()
        self.render(app)

    def render(self, app) -> None:
        draw_volume(app.hardware, self.volume, self.muted)

    def on_rotate(self, app, direction: int) -> None:
        self.volume = max(0, min(100, self.volume + (direction * 2)))
        self.muted = False
        set_volume_percent(self.volume)
        self.render(app)

    def on_short_press(self, app) -> None:
        toggle_mute()
        self.muted = not self.muted
        self.render(app)
