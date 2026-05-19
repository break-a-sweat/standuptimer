from PIL import Image

from icon import make_icon
from timer import State

# Sample coordinate: (7, 32) is inside the outer filled circle (4,4)-(60,60)
# but outside the inner white face ellipse (10,10)-(54,54), so it lands on
# the body colour rather than the white clock face or crossing hands.
_SAMPLE = (7, 32)


def test_make_icon_returns_image_64x64():
    img = make_icon(State.IDLE)
    assert isinstance(img, Image.Image)
    assert img.size == (64, 64)


def test_make_icon_idle_uses_grey():
    img = make_icon(State.IDLE)
    # Sample a pixel on the body — should be the body colour (grey-ish)
    r, g, b, _ = img.convert("RGBA").getpixel(_SAMPLE)
    assert r == g == b  # grey has equal channels
    assert 100 < r < 200


def test_make_icon_running_is_distinct_from_idle():
    idle_pixel = make_icon(State.IDLE).convert("RGBA").getpixel(_SAMPLE)
    running_pixel = make_icon(State.RUNNING).convert("RGBA").getpixel(_SAMPLE)
    assert running_pixel != idle_pixel


def test_make_icon_paused_is_distinct_from_running():
    paused_pixel = make_icon(State.PAUSED).convert("RGBA").getpixel(_SAMPLE)
    running_pixel = make_icon(State.RUNNING).convert("RGBA").getpixel(_SAMPLE)
    assert paused_pixel != running_pixel


def test_make_icon_finished_matches_idle():
    """FINISHED state shows the same icon as IDLE per spec."""
    idle_pixel = make_icon(State.IDLE).convert("RGBA").getpixel(_SAMPLE)
    finished_pixel = make_icon(State.FINISHED).convert("RGBA").getpixel(_SAMPLE)
    assert idle_pixel == finished_pixel
