from PIL import Image

from icon import make_icon, SIZE
from timer import State


# Top-center pixel: inside the rounded body rectangle, above the centered label.
# Reliably lands on the state colour.
_BG_SAMPLE = (32, 6)


def test_make_icon_returns_image_64x64():
    img = make_icon(State.IDLE, "30:00")
    assert isinstance(img, Image.Image)
    assert img.size == (SIZE, SIZE)


def test_make_icon_running_background_matches_idle_gray():
    p_idle = make_icon(State.IDLE, "30:00").getpixel(_BG_SAMPLE)
    p_running = make_icon(State.RUNNING, "30:00").getpixel(_BG_SAMPLE)
    assert p_running == p_idle


def test_make_icon_paused_background_distinct_from_running():
    p_paused = make_icon(State.PAUSED, "30:00").getpixel(_BG_SAMPLE)
    p_running = make_icon(State.RUNNING, "30:00").getpixel(_BG_SAMPLE)
    assert p_paused != p_running


def test_make_icon_finished_background_matches_idle():
    p_idle = make_icon(State.IDLE, "30:00").getpixel(_BG_SAMPLE)
    p_finished = make_icon(State.FINISHED, "30:00").getpixel(_BG_SAMPLE)
    assert p_idle == p_finished


def test_make_icon_different_labels_produce_different_images():
    """Different label text must actually be rendered onto the image."""
    a = make_icon(State.RUNNING, "12:34")
    b = make_icon(State.RUNNING, "56:78")
    assert list(a.getdata()) != list(b.getdata())


def test_make_icon_same_label_same_state_is_deterministic():
    a = make_icon(State.RUNNING, "12:34")
    b = make_icon(State.RUNNING, "12:34")
    assert list(a.getdata()) == list(b.getdata())
