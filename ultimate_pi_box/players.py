from __future__ import annotations

import re
import socket
import subprocess
import time


class VlcRcProcess:
    def __init__(self, host: str = "127.0.0.1", port: int = 4212) -> None:
        self.host = host
        self.port = port
        self.process = None

    def _base_args(self) -> list[str]:
        return [
            "cvlc",
            "--intf",
            "rc",
            "--rc-host",
            f"{self.host}:{self.port}",
            "--no-video",
            "--quiet",
        ]

    def play_args(self, extra_args: list[str]) -> None:
        self.stop()
        self.process = subprocess.Popen(
            self._base_args() + extra_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        time.sleep(0.6)

    def play_path(self, path: str) -> None:
        self.play_args([path])

    def play_url(self, url: str) -> None:
        self.play_args([url])

    def play_shell(self, shell_command: str) -> None:
        self.stop()
        command = f'{shell_command} | {" ".join(self._base_args())} -'
        self.process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        time.sleep(0.6)

    def stop(self) -> None:
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=1.0)
            except Exception:
                subprocess.run(
                    ["killall", "vlc"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            self.process = None

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def command(self, command: str) -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                sock.connect((self.host, self.port))
                time.sleep(0.05)
                try:
                    sock.recv(4096)
                except Exception:
                    pass
                sock.sendall(f"{command}\n".encode())
                time.sleep(0.05)
                return sock.recv(4096).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def toggle_pause(self) -> None:
        self.command("pause")

    def next(self) -> None:
        self.command("next")

    def previous(self) -> None:
        self.command("prev")

    def get_time(self) -> int:
        return self._extract_int(self.command("get_time"))

    def get_length(self) -> int:
        return self._extract_int(self.command("get_length"))

    @staticmethod
    def _extract_int(value: str) -> int:
        matches = re.findall(r"\d+", value or "")
        return int(matches[0]) if matches else 0
