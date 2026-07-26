from __future__ import annotations

import csv
import re
import sqlite3

from ..base import BaseComponent
from ...players import VlcRcProcess
from ...rendering import draw_menu, draw_message, draw_player, draw_search, format_seconds
from ...system import resolve_youtube_stream, search_youtube

SEARCH_CHARSET = list("abcdefghijklmnopqrstuvwxyz0123456789 ") + ["<DEL>", "<OK>"]
_SAFE_TABLE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class YoutubeOnlineComponent(BaseComponent):
    key = "youtube_online"
    label = "Youtube Online"
    media_screen = True

    def __init__(self) -> None:
        self.selected_index = 0
        self.items: list[dict[str, str]] = []
        self.results: list[dict[str, str]] = []
        self.result_index = 0
        self.action_index = 0
        self.action_target: dict[str, str] | None = None
        self.mode = "list"  # list | search | results | action | player
        self.player: VlcRcProcess | None = None
        self.playing = False
        self.paused = False
        self.control_index = 1
        self.now_playing: dict[str, str] | None = None
        self.status_line = ""
        self.seed = 0
        self.search_query = ""
        self.search_char_index = 0

    # ---- lifecycle -------------------------------------------------------
    def enter(self, app) -> None:
        self.items = self._load_items(app)
        self.selected_index = 0
        self.mode = "list"
        self.playing = False
        self.paused = False
        self.status_line = ""
        if self.player is None:
            self.player = VlcRcProcess(app.config.vlc_host, app.config.vlc_port)
        self.render(app)

    def exit(self, app) -> None:
        if self.player is not None:
            self.player.stop()
        app.mpd_oled.stop_if_owned_by(self.key)
        self.playing = False
        self.paused = False

    # ---- data loading ----------------------------------------------------
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
                table_name = table[0]
                # Guard against SQL injection: only allow plain identifiers, and
                # quote the identifier when interpolating it into the query.
                if not _SAFE_TABLE.match(table_name):
                    return []
                cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 100')
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

    def _save_favorite(self, app, item: dict[str, str]) -> bool:
        path = app.config.youtube_csv
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            write_header = not path.exists() or path.stat().st_size == 0
            with path.open("a", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                if write_header:
                    writer.writerow(["Title", "Video ID", "URL"])
                writer.writerow([item.get("title", ""), item.get("id", ""), item.get("url", "")])
        except OSError:
            return False
        # Refresh favorites so the new entry shows on return (only when CSV-backed).
        if not app.config.youtube_db.exists():
            self.items = self._load_items(app)
        return True

    # ---- playback --------------------------------------------------------
    def _play_item(self, app, item: dict[str, str]) -> None:
        if self.player is None:
            return
        self.status_line = "Resolving stream..."
        self.now_playing = item
        self.render(app)
        stream = resolve_youtube_stream(item.get("id", ""), item.get("url", ""))
        if not stream:
            self.status_line = "Could not resolve stream"
            self.mode = "list"
            self.playing = False
            self.render(app)
            return
        self.player.play_url(stream)
        self.playing = True
        self.paused = False
        self.control_index = 1
        self.mode = "player"
        self.seed = 0
        app.mpd_oled.start(self.key)
        self.render(app)

    def _stop(self, app) -> None:
        if self.player is not None:
            self.player.stop()
        self.playing = False
        self.paused = False
        self.mode = "list"
        app.mpd_oled.stop_if_owned_by(self.key)

    # ---- rendering -------------------------------------------------------
    def render(self, app) -> None:
        if self.mode == "search":
            draw_search(
                app.hardware,
                "Search YouTube",
                self.search_query,
                SEARCH_CHARSET[self.search_char_index],
            )
            return

        if self.mode == "results":
            if not self.results:
                draw_message(
                    app.hardware,
                    self.label,
                    ["No results found.", self.status_line or "Try another query."],
                    "Long press to go back",
                )
                return
            labels = [item["title"] for item in self.results]
            draw_menu(app.hardware, "Results", labels, self.result_index, f"{len(labels)} hits")
            return

        if self.mode == "action" and self.action_target is not None:
            options = ["Play", "Save to favorites", "Back"]
            draw_menu(app.hardware, self.action_target["title"][:18] or "Item", options, self.action_index, "Choose")
            return

        if self.mode == "player" and self.playing:
            if app.mpd_oled.is_owned_by(self.key):
                return
            title = self.now_playing["title"] if self.now_playing else "YouTube"
            elapsed = self.player.get_time() if self.player is not None else 0
            total = self.player.get_length() if self.player is not None else 0
            progress = (elapsed / total) if total > 0 else 0.0
            controls = ["<<", "||" if not self.paused else ">", ">>", "St"]
            draw_player(
                app.hardware,
                title,
                "YouTube Online",
                progress,
                format_seconds(elapsed),
                format_seconds(total) if total > 0 else "LIVE",
                controls,
                self.control_index,
                footer_left="YT",
                footer_right="stream",
                seed=self.seed,
            )
            return

        # default: favorites list
        if not self.items:
            source = "youtube.db" if app.config.youtube_db.exists() else "youtube_favorites.csv"
            draw_message(
                app.hardware,
                self.label,
                [
                    self.status_line or "No saved favorites.",
                    "Select [Search] to find",
                    "and save songs.",
                    f"Source: {source}",
                ],
                "Long press to exit",
            )
            return
        labels = ["[Search YouTube]"] + [item["title"] for item in self.items]
        subtitle = self.status_line or f"{len(self.items)} saved"
        draw_menu(app.hardware, self.label, labels, self.selected_index, subtitle)

    # ---- search entry ----------------------------------------------------
    def _confirm_search_char(self, app) -> None:
        char = SEARCH_CHARSET[self.search_char_index]
        if char == "<DEL>":
            self.search_query = self.search_query[:-1]
        elif char == "<OK>":
            self.status_line = "Searching..."
            self.mode = "results"
            self.render(app)
            self.results = search_youtube(self.search_query, limit=10)
            self.result_index = 0
            self.status_line = "" if self.results else "No results."
        else:
            self.search_query += char
        self.render(app)

    # ---- input handling --------------------------------------------------
    def on_rotate(self, app, direction: int) -> None:
        if self.mode == "search":
            self.search_char_index = (self.search_char_index + direction) % len(SEARCH_CHARSET)
        elif self.mode == "results":
            if self.results:
                self.result_index = (self.result_index + direction) % len(self.results)
        elif self.mode == "action":
            self.action_index = (self.action_index + direction) % 3
        elif self.mode == "player":
            self.control_index = (self.control_index + direction) % 4
        else:  # list
            self.selected_index = (self.selected_index + direction) % (len(self.items) + 1)
        self.render(app)

    def on_short_press(self, app) -> None:
        if self.mode == "search":
            self._confirm_search_char(app)
            return
        if self.mode == "results":
            if self.results:
                self.action_target = self.results[self.result_index]
                self.action_index = 0
                self.mode = "action"
            self.render(app)
            return
        if self.mode == "action" and self.action_target is not None:
            if self.action_index == 0:
                self._play_item(app, self.action_target)
            elif self.action_index == 1:
                ok = self._save_favorite(app, self.action_target)
                self.status_line = "Saved to favorites" if ok else "Save failed"
                self.mode = "results"
                self.render(app)
            else:
                self.mode = "results"
                self.render(app)
            return
        if self.mode == "player":
            if self.control_index == 0:
                self._skip(app, -1)
            elif self.control_index == 1 and self.player is not None:
                self.player.toggle_pause()
                self.paused = not self.paused
            elif self.control_index == 2:
                self._skip(app, 1)
            elif self.control_index == 3:
                self._stop(app)
            self.render(app)
            return
        # list mode
        if self.selected_index == 0:
            self.mode = "search"
            self.search_query = ""
            self.search_char_index = 0
            self.status_line = ""
            self.render(app)
            return
        if self.items:
            self.status_line = ""
            self._play_item(app, self.items[self.selected_index - 1])

    def _skip(self, app, step: int) -> None:
        if not self.items:
            return
        # Skip within the saved favourites list.
        base = max(0, self.selected_index - 1)
        self.selected_index = ((base + step) % len(self.items)) + 1
        self._play_item(app, self.items[self.selected_index - 1])

    def on_long_press(self, app) -> None:
        if self.mode == "search":
            self.mode = "list"
            self.render(app)
            return
        if self.mode == "action":
            self.mode = "results"
            self.render(app)
            return
        if self.mode == "results":
            self.mode = "list"
            self.status_line = ""
            self.render(app)
            return
        if self.mode == "player":
            self._stop(app)
            self.render(app)
            return
        super().on_long_press(app)

    def tick(self, app) -> None:
        if self.mode != "player" or not self.playing or self.player is None:
            return
        self.seed += 2
        if not self.paused and not self.player.is_running():
            self._stop(app)
        self.render(app)

    # ---- web -------------------------------------------------------------
    def get_web_state(self, app) -> dict[str, object]:
        self.items = self._load_items(app)
        current_item = self.now_playing["title"] if self.now_playing and self.playing else None
        return {
            "key": self.key,
            "label": self.label,
            "items": [item["title"] for item in self.items[:100]],
            "selected_index": max(0, self.selected_index - 1),
            "playing": self.playing,
            "paused": self.paused,
            "current_item": current_item,
        }

    def web_command(self, app, command: str, value: str | None = None) -> bool:
        self.items = self._load_items(app)
        if command == "search" and value:
            self.results = search_youtube(value, limit=10)
            return True
        if command == "open" and value is not None and self.items:
            try:
                index = max(0, min(int(value), len(self.items) - 1))
            except ValueError:
                return False
            self.selected_index = index + 1
            self._play_item(app, self.items[index])
            return True
        if command == "play_pause":
            if not self.playing and self.items:
                self._play_item(app, self.items[max(0, self.selected_index - 1)])
            elif self.player is not None:
                self.player.toggle_pause()
                self.paused = not self.paused
                self.render(app)
            return True
        if command == "next":
            self._skip(app, 1)
            return True
        if command == "previous":
            self._skip(app, -1)
            return True
        if command == "stop":
            self._stop(app)
            self.render(app)
            return True
        return False
