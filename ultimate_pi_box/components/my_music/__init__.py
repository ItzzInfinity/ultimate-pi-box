from __future__ import annotations

import random
from pathlib import Path

from ..base import BaseComponent
from ...players import VlcRcProcess
from ...rendering import draw_menu, draw_message, draw_player, draw_search, format_seconds
from ...system import estimate_bitrate_kbps

SEARCH_CHARSET = list("abcdefghijklmnopqrstuvwxyz0123456789 ") + ["<DEL>", "<OK>"]


class MyMusicComponent(BaseComponent):
    key = "my_music"
    label = "My Music"
    media_screen = True

    def __init__(self) -> None:
        self.tracks: list[Path] = []
        self.filtered: list[int] = []
        self.browse_index = 0
        self.current_index = 0
        self.control_index = 1
        self.player: VlcRcProcess | None = None
        self.playing = False
        self.paused = False
        self.repeat_mode = False
        self.shuffle_mode = False
        self.seed = 0
        self.search_mode = False
        self.search_query = ""
        self.search_char_index = 0

    def enter(self, app) -> None:
        self.tracks = self._load_tracks(app)
        self.filtered = list(range(len(self.tracks)))
        self.browse_index = 0
        self.current_index = 0
        self.control_index = 1
        self.playing = False
        self.paused = False
        self.search_mode = False
        self.search_query = ""
        self.seed = 0
        if self.player is None:
            self.player = VlcRcProcess(app.config.vlc_host, app.config.vlc_port)
        self.render(app)

    def exit(self, app) -> None:
        if self.player is not None:
            self.player.stop()
        app.mpd_oled.stop_if_owned_by(self.key)
        self.playing = False
        self.paused = False

    def _load_tracks(self, app) -> list[Path]:
        tracks: list[Path] = []
        if not app.config.music_dir.exists():
            return tracks
        for extension in app.config.audio_extensions:
            tracks.extend(sorted(app.config.music_dir.rglob(f"*.{extension}")))
        return sorted(set(tracks))

    def _apply_search(self) -> None:
        query = self.search_query.strip().lower()
        if not query:
            self.filtered = list(range(len(self.tracks)))
        else:
            self.filtered = [
                index for index, track in enumerate(self.tracks) if query in track.stem.lower()
            ]
        self.browse_index = 0
        self.current_index = 0

    def _play_current(self, app) -> None:
        if not self.filtered or self.player is None:
            return
        track = self.tracks[self.filtered[self.current_index]]
        self.player.play_path(str(track))
        self.playing = True
        self.paused = False
        self.seed = 0
        app.mpd_oled.start(self.key)

    def _play_browsed(self, app) -> None:
        if not self.filtered:
            return
        self.current_index = self.browse_index - 1
        self._play_current(app)

    def _advance(self, app, step: int) -> None:
        if not self.filtered:
            return
        if self.shuffle_mode and len(self.filtered) > 1:
            choices = [i for i in range(len(self.filtered)) if i != self.current_index]
            self.current_index = random.choice(choices)
        else:
            self.current_index = (self.current_index + step) % len(self.filtered)
        self._play_current(app)

    def render(self, app) -> None:
        if not self.tracks:
            draw_message(
                app.hardware,
                self.label,
                [
                    "No music files found.",
                    "Put songs under",
                    str(app.config.music_dir),
                ],
                "Long press to exit",
            )
            return

        if self.search_mode:
            draw_search(app.hardware, "Search Music", self.search_query, SEARCH_CHARSET[self.search_char_index])
            return

        if not self.playing:
            query_label = f"[Search: {self.search_query}]" if self.search_query else "[Search]"
            labels = [query_label] + [self.tracks[index].stem for index in self.filtered]
            subtitle = f"{len(self.filtered)}/{len(self.tracks)} tracks"
            draw_menu(app.hardware, self.label, labels, self.browse_index, subtitle)
            return

        if app.mpd_oled.is_owned_by(self.key):
            return

        track = self.tracks[self.filtered[self.current_index]]
        elapsed = self.player.get_time() if self.player is not None else 0
        total = self.player.get_length() if self.player is not None else 0
        progress = (elapsed / total) if total > 0 else 0.0
        bitrate = estimate_bitrate_kbps(track, total) if total > 0 else 0
        mode_icon = "S" if self.shuffle_mode else ("R" if self.repeat_mode else "-")
        controls = ["<<", "||" if not self.paused else ">", ">>", mode_icon]
        draw_player(
            app.hardware,
            track.stem,
            track.parent.name or "Local Music",
            progress,
            format_seconds(elapsed),
            format_seconds(total),
            controls,
            self.control_index,
            footer_left="LOCAL",
            footer_right=f"{bitrate}kbps" if bitrate else "",
            seed=self.seed,
        )

    def _rotate_search(self, app, direction: int) -> None:
        self.search_char_index = (self.search_char_index + direction) % len(SEARCH_CHARSET)
        self.render(app)

    def _confirm_search_char(self, app) -> None:
        char = SEARCH_CHARSET[self.search_char_index]
        if char == "<DEL>":
            self.search_query = self.search_query[:-1]
        elif char == "<OK>":
            self._apply_search()
            self.search_mode = False
        else:
            self.search_query += char
        self.render(app)

    def on_rotate(self, app, direction: int) -> None:
        if not self.tracks:
            return
        if self.search_mode:
            self._rotate_search(app, direction)
            return
        if not self.playing:
            self.browse_index = (self.browse_index + direction) % (len(self.filtered) + 1)
        else:
            self.control_index = (self.control_index + direction) % 4
        self.render(app)

    def on_short_press(self, app) -> None:
        if not self.tracks:
            self.render(app)
            return
        if self.search_mode:
            self._confirm_search_char(app)
            return
        if not self.playing:
            if self.browse_index == 0:
                self.search_mode = True
                self.search_char_index = 0
            else:
                self._play_browsed(app)
            self.render(app)
            return

        if self.control_index == 0:
            self._advance(app, -1)
        elif self.control_index == 1 and self.player is not None:
            self.player.toggle_pause()
            self.paused = not self.paused
        elif self.control_index == 2:
            self._advance(app, 1)
        elif self.control_index == 3:
            if self.shuffle_mode:
                self.shuffle_mode = False
                self.repeat_mode = True
            elif self.repeat_mode:
                self.repeat_mode = False
            else:
                self.shuffle_mode = True
        self.render(app)

    def on_long_press(self, app) -> None:
        if self.search_mode:
            self.search_mode = False
            self.render(app)
            return
        super().on_long_press(app)

    def tick(self, app) -> None:
        if not self.playing or self.player is None:
            return
        self.seed += 2
        if not self.paused and not self.player.is_running():
            if self.repeat_mode:
                self._play_current(app)
            else:
                self._advance(app, 1)
        self.render(app)

    def get_web_state(self, app) -> dict[str, object]:
        self.tracks = self._load_tracks(app)
        if not self.filtered:
            self.filtered = list(range(len(self.tracks)))
        current_track = (
            self.tracks[self.filtered[self.current_index]].stem if self.filtered else None
        )
        return {
            "key": self.key,
            "label": self.label,
            "items": [self.tracks[index].stem for index in self.filtered[:100]],
            "selected_index": self.current_index,
            "playing": self.playing,
            "paused": self.paused,
            "shuffle": self.shuffle_mode,
            "repeat": self.repeat_mode,
            "current_item": current_track,
            "source_path": str(app.config.music_dir),
        }

    def web_command(self, app, command: str, value: str | None = None) -> bool:
        self.tracks = self._load_tracks(app)
        if not self.filtered:
            self.filtered = list(range(len(self.tracks)))
        if command == "open" and value is not None and self.filtered:
            try:
                self.current_index = max(0, min(int(value), len(self.filtered) - 1))
            except ValueError:
                return False
            self._play_current(app)
            self.render(app)
            return True
        if not self.filtered:
            return False
        if command == "play_pause":
            if not self.playing:
                self._play_current(app)
            elif self.player is not None:
                self.player.toggle_pause()
                self.paused = not self.paused
            self.render(app)
            return True
        if command == "next":
            self._advance(app, 1)
            self.render(app)
            return True
        if command == "previous":
            self._advance(app, -1)
            self.render(app)
            return True
        if command == "stop" and self.player is not None:
            self.player.stop()
            self.playing = False
            self.paused = False
            app.mpd_oled.stop_if_owned_by(self.key)
            self.render(app)
            return True
        return False
