from overlay import _compute_position, _panel_bounds, WINDOW_HEIGHT, WINDOW_WIDTH, MARGIN


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


def test_panel_bounds_stay_inside_window():
    x0, y0, x1, y1 = _panel_bounds()

    assert 0 <= x0 < x1 <= WINDOW_WIDTH
    assert 0 <= y0 < y1 <= WINDOW_HEIGHT
