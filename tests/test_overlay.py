import overlay
from overlay import (
    _compute_finished_label_layout,
    _compute_layout,
    _compute_paused_label_layout,
    _compute_position,
    _finished_label_text,
    _panel_bounds,
    MARGIN,
    PAUSED_LABEL_HEIGHT,
    PAUSED_LABEL_MIN_WIDTH,
    PANEL_INSET,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


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


def test_layout_expands_height_for_scaled_fonts_without_overlap():
    layout = _compute_layout(
        work_area=(0, 0, 1920, 1040),
        primary_text_width=260,
        secondary_text_width=130,
        hint_text_width=150,
        primary_line_height=58,
        secondary_line_height=32,
        hint_line_height=26,
    )

    assert layout.secondary_y >= layout.primary_y + 58 + 6
    assert layout.hint_y >= layout.secondary_y + 32 + 4
    assert layout.height >= layout.hint_y + 26 + 16 + PANEL_INSET


def test_layout_caps_width_to_available_work_area():
    layout = _compute_layout(
        work_area=(0, 0, 320, 600),
        primary_text_width=700,
        secondary_text_width=320,
        hint_text_width=260,
        primary_line_height=42,
        secondary_line_height=24,
        hint_line_height=20,
    )

    assert layout.width <= 320 - (MARGIN * 2)
    assert layout.text_width > 0


def test_layout_fits_very_narrow_work_area():
    layout = _compute_layout(
        work_area=(0, 0, 180, 600),
        primary_text_width=700,
        secondary_text_width=320,
        hint_text_width=260,
        primary_line_height=42,
        secondary_line_height=24,
        hint_line_height=20,
    )

    assert layout.width <= 180 - (MARGIN * 2)
    assert layout.text_width > 0


def test_paused_label_layout_is_compact():
    layout = _compute_paused_label_layout(
        work_area=(0, 0, 1920, 1040),
        text_width=120,
        text_height=18,
    )

    assert layout.width >= PAUSED_LABEL_MIN_WIDTH
    assert layout.height == PAUSED_LABEL_HEIGHT
    assert layout.panel_bounds[0] >= 0
    assert layout.panel_bounds[2] <= layout.width
    assert layout.dot_bounds[0] > layout.panel_bounds[0]
    assert layout.text_x > layout.dot_bounds[2]


def test_paused_label_layout_caps_width_to_available_work_area():
    layout = _compute_paused_label_layout(
        work_area=(0, 0, 160, 600),
        text_width=400,
        text_height=18,
    )

    assert layout.width <= 160 - (MARGIN * 2)
    assert layout.text_width > 0
    assert layout.text_x < layout.width


def test_finished_label_uses_same_compact_layout_as_paused_label():
    finished = _compute_finished_label_layout(
        work_area=(0, 0, 1920, 1040),
        text_width=140,
        text_height=18,
    )
    paused = _compute_paused_label_layout(
        work_area=(0, 0, 1920, 1040),
        text_width=140,
        text_height=18,
    )

    assert finished == paused


def test_finished_label_text_is_compact_status_text():
    assert _finished_label_text() == "Timer finished 00:00"


def test_show_uses_compact_status_label_renderer(monkeypatch):
    calls = []
    expected_window = object()

    def fake_status_label(**kwargs):
        calls.append(kwargs)
        return expected_window

    monkeypatch.setattr(overlay, "_show_status_label", fake_status_label, raising=False)

    def dismiss():
        return None

    parent = object()
    result = overlay.show(
        on_dismiss=dismiss,
        secondary_text="elapsed 00:05",
        parent=parent,
    )

    assert result is expected_window
    assert calls == [
        {
            "on_click": dismiss,
            "text": "Timer finished 00:00",
            "parent": parent,
            "destroy_before_callback": True,
        }
    ]
