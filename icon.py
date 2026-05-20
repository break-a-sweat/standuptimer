from PIL import Image, ImageDraw, ImageFont

from timer import State

SIZE = 64
_FONT_SIZE = 22

_COLOURS = {
    State.IDLE: (140, 140, 140),       # grey
    State.FINISHED: (140, 140, 140),   # same as idle
    State.RUNNING: (140, 140, 140),    # grey while counting down
    State.PAUSED: (255, 165, 80),      # bright orange to prompt action
}


def _load_font() -> ImageFont.ImageFont:
    for name in ("arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, _FONT_SIZE)
        except OSError:
            continue
    return ImageFont.load_default()


_FONT = _load_font()


def make_icon(state: State, label: str) -> Image.Image:
    body = _COLOURS[state]
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Filled rounded rectangle covers most of the icon; corners stay transparent.
    draw.rounded_rectangle((2, 2, SIZE - 2, SIZE - 2), radius=10, fill=body)
    # Centered label with a subtle shadow for legibility against the body colour.
    draw.text((SIZE // 2 + 1, SIZE // 2 + 1), label, font=_FONT, fill=(0, 0, 0, 160), anchor="mm")
    draw.text((SIZE // 2, SIZE // 2), label, font=_FONT, fill=(255, 255, 255, 255), anchor="mm")
    return img
