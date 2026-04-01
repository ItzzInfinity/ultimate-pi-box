from __future__ import annotations

from ..base import BaseComponent
from ...rendering import draw_message


class YoutubeOnlineComponent(BaseComponent):
    key = "youtube_online"
    label = "Youtube Online"

    def render(self, app) -> None:
        source = "youtube.db" if app.config.youtube_db.exists() else "youtube_favorites.csv"
        draw_message(
            app.hardware,
            self.label,
            [
                "Source file expected:",
                source,
                "Streaming logic",
                "will be added next.",
            ],
            "Long press to exit",
        )
