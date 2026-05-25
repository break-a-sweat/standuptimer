from PIL import Image

import icon as icon_module
from icon import _FONT_CANDIDATES, _FONT_SIZE, _split_label_lines, make_icon, SIZE
from timer import State


_BACKGROUND_SAMPLE = (32, 6)


def _visible_points(img):
    return [
        (x, y)
        for y in range(img.height)
        for x in range(img.width)
        if img.getpixel((x, y))[3] > 0
    ]


def _visible_bounds(img):
    visible_points = _visible_points(img)
    return (
        min(x for x, _y in visible_points),
        min(y for _x, y in visible_points),
        max(x for x, _y in visible_points),
        max(y for _x, y in visible_points),
    )


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


def test_split_label_lines_splits_minutes_and_seconds():
    assert _split_label_lines("24:41") == ("24", "41")
    assert _split_label_lines("1:02") == ("1", "02")
    assert _split_label_lines("idle") == ("idle",)


def test_make_icon_text_stays_inside_canvas_with_margin():
    img = make_icon(State.RUNNING, "00:00")
    left, top, right, bottom = _visible_bounds(img)

    assert left >= 2
    assert right <= SIZE - 3
    assert top >= 2
    assert bottom <= SIZE - 3


def test_countdown_icon_numbers_use_larger_footprint():
    for label in ("24:41", "00:00", "59:59"):
        img = make_icon(State.RUNNING, label)
        left, top, right, bottom = _visible_bounds(img)

        assert left >= 2
        assert right <= SIZE - 3
        assert top >= 2
        assert bottom <= SIZE - 3
        assert right - left + 1 >= 40
        assert bottom - top + 1 >= 50


def test_make_icon_draws_minutes_above_seconds():
    img = make_icon(State.RUNNING, "24:41")
    visible_points = _visible_points(img)
    upper_pixels = [point for point in visible_points if point[1] < SIZE // 2]
    lower_pixels = [point for point in visible_points if point[1] > SIZE // 2]

    assert upper_pixels
    assert lower_pixels
    assert max(y for _x, y in upper_pixels) < min(y for _x, y in lower_pixels)


def test_make_icon_different_labels_produce_different_images():
    """Different label text must actually be rendered onto the image."""
    a = make_icon(State.RUNNING, "12:34")
    b = make_icon(State.RUNNING, "56:78")
    assert list(a.getdata()) != list(b.getdata())


def test_make_icon_same_label_same_state_is_deterministic():
    a = make_icon(State.RUNNING, "12:34")
    b = make_icon(State.RUNNING, "12:34")
    assert list(a.getdata()) == list(b.getdata())


def test_make_reset_icon_draws_visible_muted_shape():
    img = icon_module.make_reset_icon()
    visible_pixels = [pixel for pixel in img.getdata() if pixel[3] > 0]
    opaque_pixels = [pixel for pixel in img.getdata() if pixel[3] > 200]

    assert isinstance(img, Image.Image)
    assert img.size == (SIZE, SIZE)
    assert visible_pixels
    assert opaque_pixels
    assert all(50 <= pixel[0] <= 90 for pixel in opaque_pixels)
    assert all(pixel[0] <= pixel[1] <= pixel[2] for pixel in opaque_pixels)


def test_make_reset_icon_arrowhead_points_counterclockwise():
    img = icon_module.make_reset_icon()
    top_left_pixels = sum(
        1
        for y in range(0, 24)
        for x in range(0, 24)
        if img.getpixel((x, y))[3] > 0
    )
    top_right_pixels = sum(
        1
        for y in range(0, 24)
        for x in range(40, SIZE)
        if img.getpixel((x, y))[3] > 0
    )

    assert top_left_pixels > top_right_pixels


def test_make_reset_icon_matches_compact_refresh_footprint():
    img = icon_module.make_reset_icon()
    left, top, right, bottom = _visible_bounds(img)

    assert 6 <= left <= 16
    assert 5 <= top <= 16
    assert 46 <= right <= 58
    assert 46 <= bottom <= 58
    assert 34 <= right - left + 1 <= 54
    assert 34 <= bottom - top + 1 <= 54


def test_make_reset_icon_arrowhead_survives_tray_downscaling():
    tray_img = icon_module.make_reset_icon().resize((16, 16), Image.Resampling.LANCZOS)
    strong_pixels = [
        (x, y)
        for y in range(tray_img.height)
        for x in range(tray_img.width)
        if tray_img.getpixel((x, y))[3] > 120
    ]
    visible_pixels = [
        (x, y)
        for y in range(tray_img.height)
        for x in range(tray_img.width)
        if tray_img.getpixel((x, y))[3] > 80
    ]
    arrowhead_pixels = [
        (x, y)
        for y in range(2, 7)
        for x in range(2, 8)
        if tray_img.getpixel((x, y))[3] > 80
    ]

    assert 35 <= len(strong_pixels) <= 50
    assert len(visible_pixels) >= 55
    assert len(arrowhead_pixels) >= 11
