from __future__ import annotations

import xml.etree.ElementTree as ET

from ..base import BaseComponent
from ...players import VlcRcProcess
from ...rendering import draw_menu, draw_message, draw_player

try:
    import upnpclient
except Exception:  # pragma: no cover - depends on runtime dependency
    upnpclient = None


class DLNAUPnPComponent(BaseComponent):
    key = "dlna_upnp"
    label = "DLNA/UPnP"

    def __init__(self) -> None:
        self.devices = []
        self.selected_index = 0
        self.mode = "servers"
        self.items: list[dict[str, str]] = []
        self.browser_stack: list[tuple[object, str, str]] = []
        self.player: VlcRcProcess | None = None
        self.playing_item: str | None = None
        self.seed = 0

    def enter(self, app) -> None:
        self.selected_index = 0
        self.mode = "servers"
        self.items = []
        self.browser_stack = []
        self.playing_item = None
        if self.player is None:
            self.player = VlcRcProcess(app.config.vlc_host, app.config.vlc_port)
        self._discover()
        self.render(app)

    def exit(self, app) -> None:
        if self.player is not None:
            self.player.stop()
        self.playing_item = None

    def _discover(self) -> None:
        if upnpclient is None:
            self.devices = []
            return
        try:
            self.devices = upnpclient.discover()
        except Exception:
            self.devices = []

    def _content_directory(self, device):
        for service in getattr(device, "services", []):
            service_type = getattr(service, "service_type", "")
            if "ContentDirectory" in service_type:
                return service
        return None

    def _browse(self, device, object_id: str = "0") -> list[dict[str, str]]:
        service = self._content_directory(device)
        if service is None:
            return []
        try:
            response = service.Browse(
                ObjectID=object_id,
                BrowseFlag="BrowseDirectChildren",
                Filter="*",
                StartingIndex=0,
                RequestedCount=50,
                SortCriteria="",
            )
        except Exception:
            return []
        result_xml = response.get("Result", "")
        return self._parse_didl(result_xml)

    def _parse_didl(self, xml_text: str) -> list[dict[str, str]]:
        try:
            root = ET.fromstring(xml_text)
        except Exception:
            return []

        entries: list[dict[str, str]] = []
        for child in list(root):
            tag = child.tag.rsplit("}", 1)[-1]
            if tag not in {"item", "container"}:
                continue
            item_type = "container" if tag == "container" else "item"
            object_id = child.attrib.get("id", "")
            title = ""
            resource = ""
            item_class = ""
            for node in list(child):
                node_tag = node.tag.rsplit("}", 1)[-1]
                if node_tag == "title":
                    title = (node.text or "").strip()
                elif node_tag == "res":
                    resource = (node.text or "").strip()
                elif node_tag == "class":
                    item_class = (node.text or "").strip()
            if title:
                entries.append(
                    {
                        "title": title,
                        "type": item_type,
                        "id": object_id,
                        "resource": resource,
                        "class": item_class,
                    }
                )
        return entries

    def _open_selected_server(self) -> None:
        if not self.devices:
            return
        device = self.devices[self.selected_index]
        self.items = self._browse(device, "0")
        self.browser_stack = [(device, "0", getattr(device, "friendly_name", "DLNA Server"))]
        self.selected_index = 0
        self.mode = "items"

    def _open_selected_item(self) -> None:
        if not self.items or not self.browser_stack:
            return
        device, _, _ = self.browser_stack[-1]
        item = self.items[self.selected_index]
        if item["type"] == "container":
            self.items = self._browse(device, item["id"])
            self.browser_stack.append((device, item["id"], item["title"]))
            self.selected_index = 0
            return
        if item["resource"] and self.player is not None:
            self.player.play_url(item["resource"])
            self.playing_item = item["title"]

    def render(self, app) -> None:
        if upnpclient is None:
            draw_message(
                app.hardware,
                self.label,
                [
                    "upnpclient missing.",
                    "Install requirements",
                    "then retry DLNA.",
                ],
                "Long press to exit",
            )
            return

        if self.mode == "servers":
            if not self.devices:
                draw_message(
                    app.hardware,
                    self.label,
                    [
                        "No DLNA servers found.",
                        "Check same-network",
                        "devices and retry.",
                    ],
                    "Press to rescan",
                )
                return
            labels = [getattr(device, "friendly_name", "Unknown Server") for device in self.devices]
            draw_menu(app.hardware, self.label, labels, self.selected_index, f"{len(labels)} servers")
            return

        if self.playing_item:
            draw_player(
                app.hardware,
                self.playing_item,
                self.browser_stack[-1][2] if self.browser_stack else "DLNA/UPnP",
                0.0,
                "LIVE",
                "",
                ["<<", "[]", ">>", "BK"],
                self.selected_index % 4,
                footer_left="DLNA",
                footer_right="network",
                seed=self.seed,
            )
            return

        if not self.items:
            draw_message(
                app.hardware,
                self.label,
                [
                    "Empty DLNA folder.",
                    "Try another server",
                    "or container.",
                ],
                "Long press to go back",
            )
            return

        labels = [item["title"] for item in self.items]
        subtitle = self.browser_stack[-1][2] if self.browser_stack else "Browse"
        draw_menu(app.hardware, self.label, labels, self.selected_index, subtitle)

    def on_rotate(self, app, direction: int) -> None:
        entries = self.devices if self.mode == "servers" else self.items
        if not entries:
            return
        self.selected_index = (self.selected_index + direction) % len(entries)
        self.render(app)

    def on_short_press(self, app) -> None:
        if self.mode == "servers":
            if not self.devices:
                self._discover()
            else:
                self._open_selected_server()
            self.render(app)
            return

        if self.playing_item and self.player is not None:
            self.player.stop()
            self.playing_item = None
            self.selected_index = 0
            self.render(app)
            return

        self._open_selected_item()
        self.render(app)

    def on_long_press(self, app) -> None:
        if self.playing_item and self.player is not None:
            self.player.stop()
            self.playing_item = None
            self.render(app)
            return
        if self.mode == "items" and len(self.browser_stack) > 1:
            self.browser_stack.pop()
            device, object_id, _ = self.browser_stack[-1]
            self.items = self._browse(device, object_id)
            self.selected_index = 0
            self.render(app)
            return
        if self.mode == "items":
            self.mode = "servers"
            self.items = []
            self.browser_stack = []
            self.selected_index = 0
            self.render(app)
            return
        app.show_menu()

    def tick(self, app) -> None:
        if self.playing_item:
            self.seed += 2
            if self.player is not None and not self.player.is_running():
                self.playing_item = None
            self.render(app)

    def get_web_state(self, app) -> dict[str, object]:
        if not self.devices and upnpclient is not None:
            self._discover()
        return {
            "key": self.key,
            "label": self.label,
            "items": [getattr(device, "friendly_name", "Unknown Server") for device in self.devices[:50]],
            "selected_index": self.selected_index,
            "current_item": self.playing_item,
        }

    def web_command(self, app, command: str, value: str | None = None) -> bool:
        if command == "refresh":
            self._discover()
            self.mode = "servers"
            self.items = []
            self.browser_stack = []
            self.selected_index = 0
            self.render(app)
            return True
        return False
