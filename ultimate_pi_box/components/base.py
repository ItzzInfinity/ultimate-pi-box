from __future__ import annotations


class BaseComponent:
    key = ""
    label = ""

    def enter(self, app) -> None:
        self.render(app)

    def exit(self, app) -> None:
        return None

    def render(self, app) -> None:
        return None

    def on_rotate(self, app, direction: int) -> None:
        return None

    def on_short_press(self, app) -> None:
        return None

    def on_long_press(self, app) -> None:
        app.show_menu()

    def tick(self, app) -> None:
        return None
