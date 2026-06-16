from __future__ import annotations

import csv
import sqlite3

from ..base import BaseComponent
from ...rendering import draw_menu, draw_message


class YoutubeOnlineComponent(BaseComponent):
    key = "youtube_online"
    label = "Youtube Online"
    media_screen = True

    def __init__(self) -> None:
        self.selected_index = 0
        self.items: list[dict[str, str]] = []

    def enter(self, app) -> None:
        self.items = self._load_items(app)
        self.selected_index = 0
        self.render(app)

    def _load_items(self, app) -> list[dict[str, str]]:
        if app.config.youtube_db.exists():
            return self._load_from_db(app)
        if app.config.youtube_csv.exists():
            return self._load_from_csv(app)
        return []

    def _load_from_csv(self, app) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        with app.config.youtube_csv.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                title = row.get("Title") or row.get("title") or row.get("Name") or "Untitled"
                items.append(
                    {
                        "title": title,
                        "id": row.get("Video ID") or row.get("id") or "",
                        "url": row.get("URL") or row.get("url") or "",
                    }
                )
        return items

    def _load_from_db(self, app) -> list[dict[str, str]]:
        try:
            with sqlite3.connect(app.config.youtube_db) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 1")
                table = cursor.fetchone()
                if not table:
                    return []
                cursor.execute(f"SELECT * FROM {table[0]} LIMIT 100")
                column_names = [entry[0] for entry in cursor.description or []]
                rows = cursor.fetchall()
        except Exception:
            return []

        items: list[dict[str, str]] = []
        for row in rows:
            record = dict(zip(column_names, row))
            items.append(
                {
                    "title": str(record.get("title") or record.get("name") or record.get("song") or "Untitled"),
                    "id": str(record.get("id") or record.get("video_id") or ""),
                    "url": str(record.get("url") or ""),
                }
            )
        return items

    def render(self, app) -> None:
        if not self.items:
            source = "youtube.db" if app.config.youtube_db.exists() else "youtube_favorites.csv"
            draw_message(
                app.hardware,
                self.label,
                [
                    "No YouTube source data.",
                    "Expected source:",
                    source,
                    "Playback not wired yet.",
                ],
                "Long press to exit",
            )
            return
        labels = [item["title"] for item in self.items]
        draw_menu(app.hardware, self.label, labels, self.selected_index, f"{len(labels)} items")

    def on_rotate(self, app, direction: int) -> None:
        if not self.items:
            return
        self.selected_index = (self.selected_index + direction) % len(self.items)
        self.render(app)

    def on_short_press(self, app) -> None:
        if not self.items:
            self.render(app)
            return
        item = self.items[self.selected_index]
        draw_message(
            app.hardware,
            self.label,
            [
                item["title"],
                item["id"] or "No video id",
                item["url"][:26] if item["url"] else "No url",
                "Playback next patch.",
            ],
            "Long press to exit",
        )

    def get_web_state(self, app) -> dict[str, object]:
        self.items = self._load_items(app)
        current_item = self.items[self.selected_index]["title"] if self.items else None
        return {
            "key": self.key,
            "label": self.label,
            "items": [item["title"] for item in self.items[:100]],
            "selected_index": self.selected_index,
            "current_item": current_item,
        }
