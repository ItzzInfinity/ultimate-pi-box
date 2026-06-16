from __future__ import annotations

import json
import threading
import time
from collections import deque
from pathlib import Path

from .config import build_config
from .hardware import create_hardware
from .mpd_oled import MpdOledController
from .rendering import draw_idle_clock, draw_menu
from .components.bt_settings import BTSettingsComponent
from .components.connect_phone import ConnectPhoneComponent
from .components.dlna_upnp import DLNAUPnPComponent
from .components.internet_radio import InternetRadioComponent
from .components.my_ip import MyIPComponent
from .components.my_music import MyMusicComponent
from .components.shutdown import ShutdownComponent
from .components.system_volume import SystemVolumeComponent
from .components.youtube_online import YoutubeOnlineComponent
from .web import create_web_app


class UltimatePiBoxApp:
    def __init__(self, root_dir: Path | None = None) -> None:
        self.config = build_config(root_dir)
        self.hardware = create_hardware(self.config)
        self.mpd_oled = MpdOledController(self.config)
        self.event_queue: deque[tuple[str, int | None]] = deque()
        self.menu_items = self._load_menu()
        self.selected_index = 0
        self.current_component = None
        self.components = self._build_components()
        self.last_encoder_steps = getattr(self.hardware.encoder, "steps", 0)
        self.button_pressed_at = None
        self.last_interaction_at = time.monotonic()
        self.last_idle_draw_at = 0.0
        self.web_thread = None
        self.web_app = create_web_app(self)

    def _load_menu(self) -> list[dict[str, str]]:
        with self.config.menu_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _build_components(self) -> dict[str, object]:
        return {
            "my_music": MyMusicComponent(),
            "youtube_online": YoutubeOnlineComponent(),
            "connect_phone": ConnectPhoneComponent(),
            "internet_radio": InternetRadioComponent(),
            "my_ip": MyIPComponent(),
            "bt_settings": BTSettingsComponent(),
            "system_volume": SystemVolumeComponent(),
            "dlna_upnp": DLNAUPnPComponent(),
            "shutdown": ShutdownComponent(),
        }

    def bind_inputs(self) -> None:
        if hasattr(self.hardware.encoder, "when_rotated"):
            self.hardware.encoder.when_rotated = self._handle_encoder_rotation
        if hasattr(self.hardware.button, "when_pressed"):
            self.hardware.button.when_pressed = self._handle_button_press
        if hasattr(self.hardware.button, "when_released"):
            self.hardware.button.when_released = self._handle_button_release

    def _handle_encoder_rotation(self) -> None:
        current_steps = getattr(self.hardware.encoder, "steps", 0)
        delta = current_steps - self.last_encoder_steps
        self.last_encoder_steps = current_steps
        direction = 1 if delta > 0 else -1
        for _ in range(abs(delta) or 1):
            self.event_queue.append(("rotate", direction))

    def _handle_button_press(self) -> None:
        self.button_pressed_at = time.monotonic()

    def _handle_button_release(self) -> None:
        start = self.button_pressed_at or time.monotonic()
        held_for = time.monotonic() - start
        event_name = "long_press" if held_for >= self.config.long_press_seconds else "short_press"
        self.event_queue.append((event_name, None))
        self.button_pressed_at = None

    def run(self) -> None:
        self.bind_inputs()
        self.start_web_server()
        self.render_home(force=True)
        try:
            while True:
                self.process_events()
                if self.current_component is not None:
                    self.current_component.tick(self)
                else:
                    self.render_home()
                time.sleep(self.config.poll_interval_seconds)
        except KeyboardInterrupt:
            self.hardware.clear()

    def start_web_server(self) -> None:
        if self.web_thread is not None or self.web_app is None:
            return
        self.web_thread = threading.Thread(
            target=lambda: self.web_app.run(
                host=self.config.web_host,
                port=self.config.web_port,
                debug=False,
                use_reloader=False,
            ),
            daemon=True,
        )
        self.web_thread.start()

    def process_events(self) -> None:
        while self.event_queue:
            event_name, value = self.event_queue.popleft()
            self.last_interaction_at = time.monotonic()
            if event_name == "rotate":
                self.handle_rotation(value or 1)
            elif event_name == "short_press":
                self.handle_short_press()
            elif event_name == "long_press":
                self.handle_long_press()

    def handle_rotation(self, direction: int) -> None:
        self.last_interaction_at = time.monotonic()
        self.mpd_oled.stop_if_owned_by("idle")
        if self.current_component is None:
            self.selected_index = (self.selected_index + direction) % len(self.menu_items)
            self.render_home(force=True)
            return
        self.current_component.on_rotate(self, direction)

    def handle_short_press(self) -> None:
        self.last_interaction_at = time.monotonic()
        self.mpd_oled.stop_if_owned_by("idle")
        if self.current_component is None:
            self.open_selected_component()
            return
        self.current_component.on_short_press(self)

    def handle_long_press(self) -> None:
        self.last_interaction_at = time.monotonic()
        self.mpd_oled.stop_if_owned_by("idle")
        if self.current_component is None:
            self.render_home(force=True)
            return
        self.current_component.on_long_press(self)

    def open_selected_component(self) -> None:
        key = self.menu_items[self.selected_index]["key"]
        self.open_component_by_key(key)

    def open_component_by_key(self, key: str) -> bool:
        component = self.components.get(key)
        if component is None:
            return False
        if self.current_component is not None and self.current_component is not component:
            self.current_component.exit(self)
        self.last_interaction_at = time.monotonic()
        self.current_component = component
        self.current_component.enter(self)
        return True

    def show_menu(self) -> None:
        if self.current_component is not None:
            self.current_component.exit(self)
        self.current_component = None
        self.mpd_oled.stop()
        self.render_home(force=True)

    def render_home(self, force: bool = False) -> None:
        inactive_for = time.monotonic() - self.last_interaction_at
        if inactive_for >= self.config.idle_timeout_seconds:
            if self.mpd_oled.start("idle"):
                self.last_idle_draw_at = time.monotonic()
                return
            if force or (time.monotonic() - self.last_idle_draw_at) >= 1.0:
                draw_idle_clock(self.hardware)
                self.last_idle_draw_at = time.monotonic()
            return

        self.mpd_oled.stop_if_owned_by("idle")
        subtitle = "mock mode" if self.hardware.mock_mode else "ready"
        labels = [item["label"] for item in self.menu_items]
        draw_menu(self.hardware, "Ultimate Pi Box", labels, self.selected_index, subtitle)

    def snapshot_state(self) -> dict[str, object]:
        current_key = None
        current_label = None
        current_state: dict[str, object] | None = None
        if self.current_component is not None:
            current_key = getattr(self.current_component, "key", "")
            current_label = getattr(self.current_component, "label", "")
            current_state = self.current_component.get_web_state(self)
        return {
            "menu_items": self.menu_items,
            "selected_index": self.selected_index,
            "current_component_key": current_key,
            "current_component_label": current_label,
            "current_component_state": current_state,
            "components": {
                key: component.get_web_state(self)
                for key, component in self.components.items()
            },
            "mpd_oled": self.mpd_oled.status(),
            "mock_mode": self.hardware.mock_mode,
            "web_port": self.config.web_port,
        }

    def dispatch_web_command(self, component_key: str, command: str, value: str | None = None) -> bool:
        component = self.components.get(component_key)
        if component is None:
            return False
        if self.current_component is not component:
            self.open_component_by_key(component_key)
        handled = component.web_command(self, command, value)
        if handled:
            self.last_interaction_at = time.monotonic()
        return handled


def run() -> None:
    UltimatePiBoxApp().run()
