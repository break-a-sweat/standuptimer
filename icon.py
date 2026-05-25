from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from timer import State

SIZE = 64
_FONT_SIZE = 29
_BLACK = (0, 0, 0, 255)
_RESET_COLOUR = (56, 70, 84, 255)
_RESET_FONT_SIZE = 52
_RESET_GLYPH = "\ue72c"


@dataclass(frozen=True)
class FontCandidate:
    name: str
    filename: str


_FONT_CANDIDATES = (
    FontCandidate("Segoe Print", "segoepr.ttf"),
    FontCandidate("Comic Sans MS", "comic.ttf"),
    FontCandidate("Arial", "arial.ttf"),
)


def _font_paths(candidate: FontCandidate) -> tuple[str, ...]:
    fonts_dir = Path("C:/Windows/Fonts")
    return (
        str(fonts_dir / candidate.filename),
        candidate.filename,
        candidate.name,
    )


@lru_cache(maxsize=None)
def _load_font(font_size: int = _FONT_SIZE) -> ImageFont.ImageFont:
    for candidate in _FONT_CANDIDATES:
        for path in _font_paths(candidate):
            try:
                return ImageFont.truetype(path, font_size)
            except OSError:
                continue
    return ImageFont.load_default()


@lru_cache(maxsize=None)
def _load_reset_font() -> ImageFont.ImageFont:
    fonts_dir = Path("C:/Windows/Fonts")
    for path in (str(fonts_dir / "segmdl2.ttf"), "segmdl2.ttf", "Segoe MDL2 Assets"):
        try:
            return ImageFont.truetype(path, _RESET_FONT_SIZE)
        except OSError:
            continue
    return _load_font(_RESET_FONT_SIZE)


def _text_size(label: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    scratch = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(scratch)
    left, top, right, bottom = draw.textbbox((0, 0), label, font=font)
    return right - left, bottom - top


def _split_label_lines(label: str) -> tuple[str, ...]:
    minutes, separator, seconds = label.partition(":")
    if separator:
        return minutes, seconds
    return (label,)


def _font_for_lines(lines: tuple[str, ...]) -> ImageFont.ImageFont:
    max_width = SIZE - 4
    line_gap = 0 if len(lines) == 1 else 2
    max_height = SIZE - 4 - (line_gap * (len(lines) - 1))
    for font_size in range(_FONT_SIZE + 8, 11, -1):
        font = _load_font(font_size)
        measurements = [_text_size(line, font) for line in lines]
        width = max(line_width for line_width, _line_height in measurements)
        height = sum(line_height for _line_width, line_height in measurements)
        if width <= max_width and height <= max_height:
            return font
    return _load_font(12)


def make_icon(state: State, label: str) -> Image.Image:
    del state
    lines = _split_label_lines(label)
    font = _font_for_lines(lines)
    measurements = [_text_size(line, font) for line in lines]
    line_gap = 0 if len(lines) == 1 else 2
    total_height = sum(height for _width, height in measurements) + (
        line_gap * (len(lines) - 1)
    )
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    y = (SIZE - total_height) / 2
    for line, (_width, height) in zip(lines, measurements):
        draw.text(
            (SIZE // 2, y + (height / 2)),
            line,
            font=font,
            fill=_BLACK,
            anchor="mm",
        )
        y += height + line_gap
    return img


def make_reset_icon() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_reset_font()
    left, top, right, bottom = draw.textbbox((0, 0), _RESET_GLYPH, font=font)
    width = right - left
    height = bottom - top
    draw.text(
        ((SIZE - width) / 2 - left, (SIZE - height) / 2 - top),
        _RESET_GLYPH,
        font=font,
        fill=_RESET_COLOUR,
    )
    return img
