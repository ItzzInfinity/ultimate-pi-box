from __future__ import annotations

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
