from PIL import Image, ImageDraw

from timer import State

SIZE = 64

_COLOURS = {
    State.IDLE: (140, 140, 140),       # grey
    State.FINISHED: (140, 140, 140),   # same as idle per spec
    State.RUNNING: (74, 158, 255),     # blue
    State.PAUSED: (255, 165, 80),      # orange
}


def make_icon(state: State) -> Image.Image:
    body = _COLOURS[state]
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Filled circle
    draw.ellipse((4, 4, SIZE - 4, SIZE - 4), fill=body)
    # Inner clock face
    draw.ellipse((10, 10, SIZE - 10, SIZE - 10), outline=(255, 255, 255, 230), width=2)
    # Clock hands
    cx = cy = SIZE // 2
    draw.line((cx, cy, cx, cy - 16), fill=(255, 255, 255, 255), width=3)  # minute hand
    draw.line((cx, cy, cx + 10, cy), fill=(255, 255, 255, 255), width=3)  # hour hand
    return img
