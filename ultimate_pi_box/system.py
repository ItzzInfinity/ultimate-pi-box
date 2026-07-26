from __future__ import annotations

import json
import shlex
import socket
import subprocess


def run_command(command: list[str], timeout: float = 5.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def quote(value: str) -> str:
    return shlex.quote(value)


def get_ip_address() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip_address = sock.getsockname()[0]
        sock.close()
        return ip_address
    except Exception:
        return "No Network"


def get_hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "raspberrypi"


def get_volume_percent() -> int:
    try:
        output = run_command(["amixer", "get", "Master"]).stdout
        for line in output.splitlines():
            if "Playback" in line and "%" in line:
                return int(line.split("[")[1].split("%")[0])
    except Exception:
        return 0
    return 0


def set_volume_percent(volume: int) -> None:
    safe_volume = max(0, min(100, volume))
    subprocess.run(
        ["amixer", "set", "Master", f"{safe_volume}%"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def toggle_mute() -> None:
    subprocess.run(
        ["amixer", "set", "Master", "toggle"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def get_wifi_networks() -> list[dict[str, str]]:
    try:
        output = run_command(
            ["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL,SECURITY", "device", "wifi", "list", "--rescan", "yes"],
            timeout=10.0,
        ).stdout
    except Exception:
        return []

    networks = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(":")
        if len(parts) < 4:
            continue
        active, ssid, signal, security = parts[0], parts[1], parts[2], ":".join(parts[3:])
        if not ssid:
            continue
        networks.append(
            {
                "active": active,
                "ssid": ssid,
                "signal": signal,
                "security": security or "OPEN",
            }
        )
    return networks


def connect_wifi(ssid: str, password: str = "") -> tuple[bool, str]:
    if password:
        result = run_command(["nmcli", "device", "wifi", "connect", ssid, "password", password], timeout=20.0)
    else:
        result = run_command(["nmcli", "device", "wifi", "connect", ssid], timeout=20.0)
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip() or "No output from nmcli."


def get_bluetooth_show() -> dict[str, str]:
    output = run_command(["bluetoothctl", "show"]).stdout
    data: dict[str, str] = {}
    for line in output.splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def get_paired_devices() -> list[dict[str, str]]:
    output = run_command(["bluetoothctl", "paired-devices"]).stdout
    devices = []
    for line in output.splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3:
            devices.append({"mac": parts[1], "name": parts[2]})
    return devices


def is_device_connected(mac_address: str) -> bool:
    output = run_command(["bluetoothctl", "info", mac_address]).stdout
    return "Connected: yes" in output


def bluetooth_toggle_power(enabled: bool) -> None:
    run_command(["bluetoothctl", "power", "on" if enabled else "off"])


def bluetooth_toggle_discoverable(enabled: bool) -> None:
    run_command(["bluetoothctl", "discoverable", "on" if enabled else "off"])


def bluetooth_connect(mac_address: str) -> None:
    run_command(["bluetoothctl", "connect", mac_address], timeout=15.0)


def bluetooth_disconnect(mac_address: str) -> None:
    run_command(["bluetoothctl", "disconnect", mac_address], timeout=15.0)


def estimate_bitrate_kbps(file_path, duration_seconds: int) -> int:
    if duration_seconds <= 0:
        return 0
    try:
        size_bytes = file_path.stat().st_size
    except OSError:
        return 0
    return int((size_bytes * 8) / duration_seconds / 1000)


def youtube_watch_url(video_id: str, url: str = "") -> str:
    if url:
        return url
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return ""


def resolve_youtube_stream(video_id: str = "", url: str = "") -> str | None:
    """Resolve a YouTube video id/url to a direct audio stream URL via yt-dlp.

    Uses the argv form of subprocess (never shell=True) so the id/url cannot be
    used for shell injection. Returns None when yt-dlp is unavailable or fails.
    """
    target = youtube_watch_url(video_id, url)
    if not target:
        return None
    try:
        result = run_command(
            ["yt-dlp", "-f", "bestaudio/best", "--no-playlist", "-g", target],
            timeout=30.0,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("http"):
            return line
    return None


def search_youtube(query: str, limit: int = 10) -> list[dict[str, str]]:
    """Search YouTube via yt-dlp and return [{title, id, url}] result rows."""
    query = query.strip()
    if not query:
        return []
    try:
        result = run_command(
            [
                "yt-dlp",
                "--flat-playlist",
                "--dump-json",
                "--no-warnings",
                f"ytsearch{max(1, int(limit))}:{query}",
            ],
            timeout=30.0,
        )
    except Exception:
        return []
    if result.returncode != 0:
        return []
    items: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        video_id = str(record.get("id") or "")
        items.append(
            {
                "title": str(record.get("title") or "Untitled"),
                "id": video_id,
                "url": str(record.get("url") or youtube_watch_url(video_id)),
            }
        )
    return items


def _bluez_media_player(bus):
    """Return the first org.bluez.MediaPlayer1 (object_path, props) or (None, {})."""
    try:
        import dbus
    except Exception:
        return None, {}
    try:
        manager = dbus.Interface(
            bus.get_object("org.bluez", "/"), "org.freedesktop.DBus.ObjectManager"
        )
        objects = manager.GetManagedObjects()
    except Exception:
        return None, {}
    for path, interfaces in objects.items():
        if "org.bluez.MediaPlayer1" in interfaces:
            return str(path), dict(interfaces["org.bluez.MediaPlayer1"])
    return None, {}


def get_bt_media_info() -> dict[str, str]:
    """Fetch now-playing metadata from the connected phone via BlueZ MediaPlayer1."""
    try:
        import dbus
    except Exception:
        return {}
    try:
        bus = dbus.SystemBus()
    except Exception:
        return {}
    path, props = _bluez_media_player(bus)
    if path is None:
        return {}
    track = props.get("Track", {}) or {}
    return {
        "title": str(track.get("Title", "") or ""),
        "artist": str(track.get("Artist", "") or ""),
        "album": str(track.get("Album", "") or ""),
        "status": str(props.get("Status", "") or ""),
    }


def bt_media_control(action: str) -> bool:
    """Send a transport command (Next/Previous/Play/Pause) to the connected phone."""
    action = action.capitalize()
    if action not in {"Next", "Previous", "Play", "Pause", "Stop"}:
        return False
    try:
        import dbus
    except Exception:
        return False
    try:
        bus = dbus.SystemBus()
    except Exception:
        return False
    path, _ = _bluez_media_player(bus)
    if path is None:
        return False
    try:
        player = dbus.Interface(
            bus.get_object("org.bluez", path), "org.bluez.MediaPlayer1"
        )
        getattr(player, action)()
        return True
    except Exception:
        return False


def bluetooth_scan(duration: int = 8) -> list[dict[str, str]]:
    """Scan for nearby Bluetooth devices and return [{mac, name}] entries."""
    try:
        run_command(
            ["bluetoothctl", "--timeout", str(max(1, int(duration))), "scan", "on"],
            timeout=duration + 5.0,
        )
    except Exception:
        pass
    output = run_command(["bluetoothctl", "devices"]).stdout
    devices = []
    for line in output.splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3 and parts[0] == "Device":
            devices.append({"mac": parts[1], "name": parts[2]})
    return devices


def bluetooth_pair(mac_address: str) -> tuple[bool, str]:
    """Pair (and trust) a device by MAC address via bluetoothctl."""
    pair_result = run_command(["bluetoothctl", "pair", mac_address], timeout=30.0)
    output = (pair_result.stdout or "") + (pair_result.stderr or "")
    success = pair_result.returncode == 0 or "successful" in output.lower()
    if success:
        run_command(["bluetoothctl", "trust", mac_address], timeout=10.0)
    return success, output.strip() or "No output from bluetoothctl."


def wifi_signal_bars(signal: int) -> str:
    if signal >= 80:
        return "||||"
    if signal >= 60:
        return "|||."
    if signal >= 40:
        return "||.."
    if signal >= 20:
        return "|..."
    return "...."
