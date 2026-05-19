from overlay import _compute_position, WINDOW_HEIGHT, MARGIN


def test_compute_position_places_at_bottom_left_with_margin():
    work_area = (0, 0, 1920, 1040)  # 1080p with taskbar
    x, y = _compute_position(work_area)
    assert x == MARGIN
    assert y == 1040 - WINDOW_HEIGHT - MARGIN


def test_compute_position_respects_non_zero_left():
    work_area = (100, 50, 1920, 1040)
    x, y = _compute_position(work_area)
    assert x == 100 + MARGIN
    assert y == 1040 - WINDOW_HEIGHT - MARGIN
