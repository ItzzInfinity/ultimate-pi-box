from __future__ import annotations

import datetime as dt
import math
import time

from PIL import Image, ImageDraw

from .system import get_ip_address, get_volume_percent, wifi_signal_bars


def make_canvas(hardware):
    image = Image.new("1", (hardware.width, hardware.height), 0)
    return image, ImageDraw.Draw(image)


def text_size(draw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def format_seconds(value: int) -> str:
    total = max(0, int(value))
    minutes, seconds = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def trim_text(draw, text: str, font, max_width: int) -> str:
    if not text:
        return ""
    current = text
    while current and text_size(draw, current, font)[0] > max_width:
        current = current[:-1]
    return current if current == text else current[:-1] + "..."


def _draw_marquee(draw, x: int, y: int, width: int, text: str, font, fill: int, seed: int) -> None:
    text_width, _ = text_size(draw, text, font)
    if text_width <= width:
        draw.text((x, y), text, font=font, fill=fill)
        return

    padded_text = f"{text}   "
    padded_width, _ = text_size(draw, padded_text, font)
    cycle = max(1, padded_width)
    offset = seed % cycle
    draw.text((x - offset, y), padded_text, font=font, fill=fill)
    draw.text((x - offset + padded_width, y), padded_text, font=font, fill=fill)


def draw_menu(hardware, title: str, items: list[str], selected_index: int, subtitle: str = "") -> None:
    image, draw = make_canvas(hardware)
    fonts = hardware.fonts

    draw.text((2, 0), title, font=fonts.title, fill=255)
    if subtitle:
        draw.text((70, 0), trim_text(draw, subtitle, fonts.small, 56), font=fonts.small, fill=255)

    max_visible = 4
    scroll_offset = 0
    if selected_index >= max_visible:
        scroll_offset = selected_index - max_visible + 1

    for line, item_index in enumerate(range(scroll_offset, min(scroll_offset + max_visible, len(items)))):
        y = 14 + line * 12
        label = trim_text(draw, items[item_index], fonts.body, hardware.width - 10)
        if item_index == selected_index:
            draw.rectangle((0, y - 1, hardware.width, y + 9), fill=255)
            _draw_marquee(draw, 4, y - 1, hardware.width - 8, items[item_index], fonts.body, 0, int(time.time() * 12))
        else:
            draw.text((4, y - 1), label, font=fonts.body, fill=255)

    hardware.display(image)


def draw_message(hardware, title: str, lines: list[str], footer: str = "") -> None:
    image, draw = make_canvas(hardware)
    fonts = hardware.fonts

    draw.text((2, 0), trim_text(draw, title, fonts.title, hardware.width - 4), font=fonts.title, fill=255)
    y = 16
    max_body_lines = 3 if footer else 4
    for line in lines[:max_body_lines]:
        draw.text((2, y), trim_text(draw, line, fonts.body, hardware.width - 4), font=fonts.body, fill=255)
        y += 12
    if footer:
        draw.text((2, hardware.height - 9), trim_text(draw, footer, fonts.small, hardware.width - 4), font=fonts.small, fill=255)

    hardware.display(image)


def _draw_equalizer(draw, width: int, height: int, seed: int) -> None:
    for index, x in enumerate((2, 8, width - 12, width - 6)):
        level = 4 + int(abs(math.sin((seed + index) / 2.0)) * 10)
        draw.rectangle((x, height - 4 - level, x + 2, height - 4), fill=255)


def _draw_signal_bars(draw, width: int, signal_text: str) -> None:
    levels = {
        "....": [2, 2, 2, 2],
        "|...": [3, 2, 2, 2],
        "||..": [3, 5, 2, 2],
        "|||.": [3, 5, 7, 2],
        "||||": [3, 5, 7, 9],
    }.get(signal_text, [3, 5, 7, 9])
    start_x = width - 16
    for index, bar_height in enumerate(levels):
        x = start_x + (index * 4)
        base_y = 10
        draw.rectangle((x, base_y - bar_height, x + 2, base_y), fill=255)


def draw_player(
    hardware,
    title: str,
    subtitle: str,
    progress: float,
    elapsed_text: str,
    total_text: str,
    controls: list[str],
    selected_control: int,
    footer_left: str = "",
    footer_right: str = "",
    seed: int = 0,
) -> None:
    image, draw = make_canvas(hardware)
    fonts = hardware.fonts

    _draw_marquee(draw, 2, 0, hardware.width - 4, title, fonts.title, 255, seed)
    draw.text((2, 14), trim_text(draw, subtitle, fonts.body, hardware.width - 4), font=fonts.body, fill=255)

    bar_top = 30
    draw.rectangle((2, bar_top, hardware.width - 3, bar_top + 5), outline=255)
    filled = int((hardware.width - 6) * max(0.0, min(progress, 1.0)))
    if filled > 0:
        draw.rectangle((3, bar_top + 1, 3 + filled, bar_top + 4), fill=255)

    draw.text((2, 38), elapsed_text, font=fonts.small, fill=255)
    total_width, _ = text_size(draw, total_text, fonts.small)
    draw.text((hardware.width - total_width - 2, 38), total_text, font=fonts.small, fill=255)

    start_x = 6
    for index, icon in enumerate(controls):
        x = start_x + index * 24
        if index == selected_control:
            draw.rectangle((x - 2, 49, x + 18, 61), fill=255)
            draw.text((x + 2, 50), icon, font=fonts.body, fill=0)
        else:
            draw.text((x + 2, 50), icon, font=fonts.body, fill=255)

    if footer_left:
        draw.text((2, 24), trim_text(draw, footer_left, fonts.small, 52), font=fonts.small, fill=255)
    if footer_right:
        right = trim_text(draw, footer_right, fonts.small, 52)
        right_width, _ = text_size(draw, right, fonts.small)
        draw.text((hardware.width - right_width - 2, 24), right, font=fonts.small, fill=255)

    _draw_equalizer(draw, hardware.width, hardware.height, seed)
    hardware.display(image)


def draw_volume(hardware, volume: int, muted: bool = False) -> None:
    image, draw = make_canvas(hardware)
    fonts = hardware.fonts

    title = "Muted" if muted else f"Volume {volume}%"
    draw.text((2, 0), title, font=fonts.title, fill=255)
    draw.text((2, 16), "Rotate to adjust", font=fonts.body, fill=255)
    draw.text((2, 28), "Press to mute", font=fonts.body, fill=255)

    draw.rectangle((4, 46, hardware.width - 5, 58), outline=255)
    fill_width = int((hardware.width - 10) * (max(0, min(volume, 100)) / 100.0))
    if fill_width > 0:
        draw.rectangle((5, 47, 5 + fill_width, 57), fill=255)

    hardware.display(image)


def draw_idle_clock(hardware, now: dt.datetime | None = None) -> None:
    current = now or dt.datetime.now()
    image, draw = make_canvas(hardware)
    fonts = hardware.fonts

    ip_text = get_ip_address()
    volume_text = f"VOL {get_volume_percent()}%"
    bars = wifi_signal_bars(100 if ip_text != "No Network" else 0)

    draw.text((2, 0), trim_text(draw, ip_text, fonts.small, 80), font=fonts.small, fill=255)
    _draw_signal_bars(draw, hardware.width, bars)
    volume_width, _ = text_size(draw, volume_text, fonts.small)
    draw.text((hardware.width - volume_width - 20, 0), volume_text, font=fonts.small, fill=255)

    time_text = current.strftime("%H:%M")
    time_width, _ = text_size(draw, time_text, fonts.large)
    draw.text(((hardware.width - time_width) // 2, 16), time_text, font=fonts.large, fill=255)

    date_text = current.strftime("%d-%m-%Y")
    date_width, _ = text_size(draw, date_text, fonts.body)
    draw.text(((hardware.width - date_width) // 2, 52), date_text, font=fonts.body, fill=255)

    hardware.display(image)
