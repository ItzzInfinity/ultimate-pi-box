from __future__ import annotations

from pathlib import Path

from ..base import BaseComponent
from ...players import VlcRcProcess
from ...rendering import draw_menu, draw_message, draw_player, format_seconds


class MyMusicComponent(BaseComponent):
    key = "my_music"
    label = "My Music"

    def __init__(self) -> None:
        self.selected_index = 0
        self.control_index = 1
        self.tracks: list[Path] = []
        self.player: VlcRcProcess | None = None
        self.playing = False
        self.paused = False
        self.repeat_mode = False
        self.seed = 0

    def enter(self, app) -> None:
        self.tracks = self._load_tracks(app)
        self.selected_index = 0
        self.control_index = 1
        self.playing = False
        self.paused = False
        self.seed = 0
        if self.player is None:
            self.player = VlcRcProcess(app.config.vlc_host, app.config.vlc_port)
        self.render(app)

    def exit(self, app) -> None:
        if self.player is not None:
            self.player.stop()
        self.playing = False
        self.paused = False

    def _load_tracks(self, app) -> list[Path]:
        tracks: list[Path] = []
        for extension in app.config.audio_extensions:
            tracks.extend(sorted(app.config.music_dir.rglob(f"*.{extension}")))
        return sorted(set(tracks))

    def _play_selected(self, app) -> None:
        if not self.tracks or self.player is None:
            return
        self.player.play_path(str(self.tracks[self.selected_index]))
        self.playing = True
        self.paused = False
        self.seed = 0

    def _play_next(self, app, step: int) -> None:
        if not self.tracks:
            return
        self.selected_index = (self.selected_index + step) % len(self.tracks)
        self._play_selected(app)

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

        if not self.playing:
            labels = [track.stem for track in self.tracks]
            draw_menu(app.hardware, self.label, labels, self.selected_index, f"{len(labels)} tracks")
            return

        track = self.tracks[self.selected_index]
        elapsed = self.player.get_time() if self.player is not None else 0
        total = self.player.get_length() if self.player is not None else 0
        progress = (elapsed / total) if total > 0 else 0.0
        controls = ["<<", "||" if not self.paused else ">", ">>", "R" if self.repeat_mode else "-"]
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
            footer_right=f"{len(self.tracks)} files",
            seed=self.seed,
        )

    def on_rotate(self, app, direction: int) -> None:
        if not self.tracks:
            return
        if not self.playing:
            self.selected_index = (self.selected_index + direction) % len(self.tracks)
        else:
            self.control_index = (self.control_index + direction) % 4
        self.render(app)

    def on_short_press(self, app) -> None:
        if not self.tracks:
            self.render(app)
            return
        if not self.playing:
            self._play_selected(app)
            self.render(app)
            return

        if self.control_index == 0:
            self._play_next(app, -1)
        elif self.control_index == 1 and self.player is not None:
            self.player.toggle_pause()
            self.paused = not self.paused
        elif self.control_index == 2:
            self._play_next(app, 1)
        elif self.control_index == 3:
            self.repeat_mode = not self.repeat_mode
        self.render(app)

    def tick(self, app) -> None:
        if not self.playing or self.player is None:
            return
        self.seed += 2
        if not self.paused and not self.player.is_running():
            if self.repeat_mode:
                self._play_selected(app)
            else:
                self._play_next(app, 1)
        self.render(app)
