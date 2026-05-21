from PIL import Image

from icon import _FONT_CANDIDATES, _FONT_SIZE, make_icon, SIZE
from timer import State


_BACKGROUND_SAMPLE = (32, 6)


def test_make_icon_returns_image_64x64():
    img = make_icon(State.IDLE, "30:00")
    assert isinstance(img, Image.Image)
    assert img.size == (SIZE, SIZE)


def test_make_icon_has_transparent_background():
    img = make_icon(State.RUNNING, "30:00")
    assert img.getpixel(_BACKGROUND_SAMPLE) == (0, 0, 0, 0)


def test_make_icon_uses_only_black_text_pixels():
    img = make_icon(State.PAUSED, "30:00")
    visible_pixels = [pixel for pixel in img.getdata() if pixel[3] > 0]

    assert visible_pixels
    assert all(pixel[:3] == (0, 0, 0) for pixel in visible_pixels)


def test_make_icon_same_label_same_pixels_across_states():
    running = make_icon(State.RUNNING, "30:00")
    paused = make_icon(State.PAUSED, "30:00")
    finished = make_icon(State.FINISHED, "30:00")

    assert list(running.getdata()) == list(paused.getdata())
    assert list(running.getdata()) == list(finished.getdata())


def test_icon_font_prefers_handwriting_font():
    first_candidate = _FONT_CANDIDATES[0]

    assert first_candidate.name == "Segoe Print"
    assert first_candidate.filename == "segoepr.ttf"
    assert _FONT_SIZE >= 20


def test_make_icon_text_stays_inside_canvas_with_margin():
    img = make_icon(State.RUNNING, "00:00")
    visible_points = [
        (x, y)
        for y in range(img.height)
        for x in range(img.width)
        if img.getpixel((x, y))[3] > 0
    ]
    left = min(x for x, _y in visible_points)
    right = max(x for x, _y in visible_points)

    assert left >= 2
    assert right <= SIZE - 3


def test_make_icon_different_labels_produce_different_images():
    """Different label text must actually be rendered onto the image."""
    a = make_icon(State.RUNNING, "12:34")
    b = make_icon(State.RUNNING, "56:78")
    assert list(a.getdata()) != list(b.getdata())


def test_make_icon_same_label_same_state_is_deterministic():
    a = make_icon(State.RUNNING, "12:34")
    b = make_icon(State.RUNNING, "12:34")
    assert list(a.getdata()) == list(b.getdata())
