from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from timer import State

SIZE = 64
_FONT_SIZE = 22


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


def _text_size(label: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    scratch = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(scratch)
    left, top, right, bottom = draw.textbbox((0, 0), label, font=font)
    return right - left, bottom - top


def _font_for_label(label: str) -> ImageFont.ImageFont:
    max_width = SIZE - 4
    max_height = SIZE - 4
    for font_size in range(_FONT_SIZE, 11, -1):
        font = _load_font(font_size)
        width, height = _text_size(label, font)
        if width <= max_width and height <= max_height:
            return font
    return _load_font(12)


def make_icon(state: State, label: str) -> Image.Image:
    del state
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text(
        (SIZE // 2, SIZE // 2),
        label,
        font=_font_for_label(label),
        fill=(0, 0, 0, 255),
        anchor="mm",
    )
    return img
