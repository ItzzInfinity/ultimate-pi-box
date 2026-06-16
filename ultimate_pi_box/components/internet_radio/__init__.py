from __future__ import annotations

import csv

from ..base import BaseComponent
from ...players import VlcRcProcess
from ...rendering import draw_message, draw_menu, draw_player


class InternetRadioComponent(BaseComponent):
    key = "internet_radio"
    label = "Internet Radio"
    media_screen = True

    def __init__(self) -> None:
        self.selected_index = 0
        self.control_index = 1
        self.stations: list[tuple[str, str]] = []
        self.player: VlcRcProcess | None = None
        self.playing = False
        self.seed = 0

    def enter(self, app) -> None:
        self._load_stations(app)
        self.selected_index = 0
        self.control_index = 1
        self.playing = False
        self.seed = 0
        if self.player is None:
            self.player = VlcRcProcess(app.config.vlc_host, app.config.vlc_port)
        self.render(app)

    def exit(self, app) -> None:
        if self.player is not None:
            self.player.stop()
        app.mpd_oled.stop_if_owned_by(self.key)
        self.playing = False

    def _load_stations(self, app) -> None:
        self.stations = []
        if not app.config.radio_csv.exists():
            return
        with app.config.radio_csv.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                name = row.get("Station Name") or row.get("name") or row.get("Title") or ""
                url = row.get("Station URL") or row.get("url") or ""
                if name and url:
                    self.stations.append((name, url))

    def _play_selected(self, app) -> None:
        if not self.stations or self.player is None:
            return
        _, station_url = self.stations[self.selected_index]
        self.player.play_url(station_url)
        self.playing = True
        self.seed = 0
        app.mpd_oled.start(self.key)

    def _play_relative(self, app, step: int) -> None:
        if not self.stations:
            return
        self.selected_index = (self.selected_index + step) % len(self.stations)
        self._play_selected(app)

    def render(self, app) -> None:
        if not self.stations:
            draw_message(
                app.hardware,
                self.label,
                [
                    "No station data found.",
                    "Create data/radio_stations.csv",
                    "with Station Name and",
                    "Station URL columns.",
                ],
                "Long press to exit",
            )
            return
        if not self.playing:
            labels = [name for name, _ in self.stations]
            draw_menu(app.hardware, self.label, labels, self.selected_index, f"{len(labels)} stations")
            return
        if app.mpd_oled.is_owned_by(self.key):
            return
        station_name, station_url = self.stations[self.selected_index]
        controls = ["<<", "[]", ">>", "L"]
        draw_player(
            app.hardware,
            station_name,
            "Internet Radio",
            0.0,
            "LIVE",
            "",
            controls,
            self.control_index,
            footer_left="RADIO",
            footer_right=station_url.split("/")[2] if "://" in station_url else station_url[:12],
            seed=self.seed,
        )

    def on_rotate(self, app, direction: int) -> None:
        if not self.stations:
            return
        if not self.playing:
            self.selected_index = (self.selected_index + direction) % len(self.stations)
        else:
            self.control_index = (self.control_index + direction) % 4
        self.render(app)

    def on_short_press(self, app) -> None:
        if not self.stations:
            self.render(app)
            return
        if not self.playing:
            self._play_selected(app)
            self.render(app)
            return
        if self.control_index == 0:
            self._play_relative(app, -1)
        elif self.control_index == 1 and self.player is not None:
            self.player.stop()
            self.playing = False
            app.mpd_oled.stop_if_owned_by(self.key)
        elif self.control_index == 2:
            self._play_relative(app, 1)
        elif self.control_index == 3:
            self.playing = False
            app.mpd_oled.stop_if_owned_by(self.key)
        self.render(app)

    def tick(self, app) -> None:
        if not self.playing:
            return
        self.seed += 2
        if self.player is not None and not self.player.is_running():
            self.playing = False
        self.render(app)

    def get_web_state(self, app) -> dict[str, object]:
        self._load_stations(app)
        current_station = self.stations[self.selected_index][0] if self.stations else None
        return {
            "key": self.key,
            "label": self.label,
            "items": [name for name, _ in self.stations[:100]],
            "selected_index": self.selected_index,
            "playing": self.playing,
            "current_item": current_station,
        }

    def web_command(self, app, command: str, value: str | None = None) -> bool:
        self._load_stations(app)
        if command == "open" and value is not None and self.stations:
            try:
                self.selected_index = max(0, min(int(value), len(self.stations) - 1))
            except ValueError:
                return False
            self._play_selected(app)
            self.render(app)
            return True
        if not self.stations:
            return False
        if command == "play_pause":
            if not self.playing:
                self._play_selected(app)
            elif self.player is not None:
                self.player.stop()
                self.playing = False
                app.mpd_oled.stop_if_owned_by(self.key)
            self.render(app)
            return True
        if command == "next":
            self._play_relative(app, 1)
            self.render(app)
            return True
        if command == "previous":
            self._play_relative(app, -1)
            self.render(app)
            return True
        if command == "stop" and self.player is not None:
            self.player.stop()
            self.playing = False
            app.mpd_oled.stop_if_owned_by(self.key)
            self.render(app)
            return True
        return False
