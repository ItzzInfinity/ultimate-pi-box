from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageFont

try:
    from gpiozero import Button, RotaryEncoder
    from luma.core.interface.serial import i2c
    from luma.oled.device import sh1106
except Exception as exc:  # pragma: no cover - depends on Raspberry Pi runtime
    Button = None
    RotaryEncoder = None
    i2c = None
    sh1106 = None
    HARDWARE_IMPORT_ERROR = str(exc)
else:
    HARDWARE_IMPORT_ERROR = ""


@dataclass
class FontSet:
    small: object
    body: object
    title: object
    large: object


class MockOLED:
    width = 128
    height = 64

    def __init__(self) -> None:
        self.last_image = None

    def display(self, image: Image.Image) -> None:
        self.last_image = image

    def clear(self) -> None:
        self.last_image = Image.new("1", (self.width, self.height), 0)


class MockEncoder:
    def __init__(self) -> None:
        self.steps = 0
        self.when_rotated = None


class MockButton:
    def __init__(self) -> None:
        self.when_pressed = None
        self.when_released = None


@dataclass
class HardwareBundle:
    oled: object
    encoder: object
    button: object
    fonts: FontSet
    mock_mode: bool
    mock_reason: str = ""

    @property
    def width(self) -> int:
        return self.oled.width

    @property
    def height(self) -> int:
        return self.oled.height

    def display(self, image: Image.Image) -> None:
        self.oled.display(image)

    def clear(self) -> None:
        self.oled.clear()


def _load_font(font_path: str, size: int) -> object:
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()


def load_fonts(config) -> FontSet:
    return FontSet(
        small=_load_font(config.default_font_path, 9),
        body=_load_font(config.default_font_path, 10),
        title=_load_font(config.title_font_path, 11),
        large=_load_font(config.title_font_path, 24),
    )


def create_hardware(config) -> HardwareBundle:
    fonts = load_fonts(config)
    if Button is None or RotaryEncoder is None or i2c is None or sh1106 is None:
        return HardwareBundle(
            oled=MockOLED(),
            encoder=MockEncoder(),
            button=MockButton(),
            fonts=fonts,
            mock_mode=True,
            mock_reason=HARDWARE_IMPORT_ERROR or "Hardware libraries not available.",
        )

    serial = i2c(port=config.oled_port, address=config.oled_address)
    oled = sh1106(serial)
    encoder = RotaryEncoder(
        config.encoder_clk_pin,
        config.encoder_dt_pin,
        max_steps=config.encoder_max_steps,
    )
    button = Button(config.encoder_button_pin)
    return HardwareBundle(oled=oled, encoder=encoder, button=button, fonts=fonts, mock_mode=False)
