import overlay
from overlay import (
    _compute_layout,
    _compute_paused_label_layout,
    _compute_position,
    _panel_bounds,
    _play_triangle_points,
    ACCENT_COLOUR,
    CHINESE_HANDWRITING_FONT_FAMILY,
    HINT_LINE_FONT,
    LATIN_HANDWRITING_FONT_FAMILY,
    MARGIN,
    PAUSED_LABEL_DOT_LEFT_PADDING,
    PAUSED_LABEL_DOT_SIZE,
    PAUSED_LABEL_DOT_TEXT_GAP,
    PAUSED_LABEL_HEIGHT,
    PAUSED_LABEL_MIN_WIDTH,
    PAUSED_LABEL_DOT_FILL,
    PAUSED_LABEL_FONT,
    PAUSED_LABEL_TEXT_RIGHT_PADDING,
    PAUSED_LABEL_TEXT_SAFETY_PADDING,
    PAUSED_LABEL_TRIANGLE_FILL,
    PAUSED_LABEL_TRIANGLE_HEIGHT,
    PAUSED_LABEL_TRIANGLE_OPTICAL_NUDGE,
    PAUSED_LABEL_TRIANGLE_WIDTH,
    PANEL_INSET,
    PRIMARY_LINE_FONT,
    SECONDARY_LINE_FONT,
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


def test_paused_label_constants_match_redesigned_play_button():
    assert PAUSED_LABEL_DOT_SIZE == 24
    assert PAUSED_LABEL_HEIGHT == 44
    assert PAUSED_LABEL_MIN_WIDTH == 96
    assert PAUSED_LABEL_DOT_LEFT_PADDING == 8
    assert PAUSED_LABEL_DOT_TEXT_GAP == 10
    assert PAUSED_LABEL_TEXT_RIGHT_PADDING == 14
    assert PAUSED_LABEL_TEXT_SAFETY_PADDING == 0


def test_paused_label_layout_is_compact():
    measured_text_width = 60  # roughly the width of "MM:SS" at size 10
    layout = _compute_paused_label_layout(
        work_area=(0, 0, 1920, 1040),
        text_width=measured_text_width,
        text_height=18,
    )

    assert layout.width >= PAUSED_LABEL_MIN_WIDTH
    assert layout.height == PAUSED_LABEL_HEIGHT
    assert layout.panel_bounds[0] >= 0
    assert layout.panel_bounds[2] <= layout.width
    dot_width = layout.dot_bounds[2] - layout.dot_bounds[0]
    dot_height = layout.dot_bounds[3] - layout.dot_bounds[1]
    assert dot_width == PAUSED_LABEL_DOT_SIZE
    assert dot_height == PAUSED_LABEL_DOT_SIZE
    assert layout.dot_bounds[0] > layout.panel_bounds[0]
    assert layout.text_x > layout.dot_bounds[2]
    assert layout.text_width >= measured_text_width


def test_paused_label_layout_collapses_when_text_is_empty():
    layout = _compute_paused_label_layout(
        work_area=(0, 0, 1920, 1040),
        text_width=0,
        text_height=18,
    )

    assert layout.width < PAUSED_LABEL_MIN_WIDTH
    assert layout.height == PAUSED_LABEL_HEIGHT
    assert layout.dot_bounds[0] > layout.panel_bounds[0]
    assert layout.dot_bounds[2] < layout.panel_bounds[2]
    assert layout.text_width == 0


def test_paused_label_layout_keeps_handwriting_text_away_from_window_edges():
    measured_text_width = 140
    measured_text_height = 23

    layout = _compute_paused_label_layout(
        work_area=(0, 0, 1920, 1040),
        text_width=measured_text_width,
        text_height=measured_text_height,
    )

    assert layout.height >= measured_text_height + 14
    assert layout.text_y >= 7
    assert layout.text_y + measured_text_height <= layout.height - 7


def test_paused_label_layout_caps_width_to_available_work_area():
    layout = _compute_paused_label_layout(
        work_area=(0, 0, 160, 600),
        text_width=400,
        text_height=18,
    )

    assert layout.width <= 160 - (MARGIN * 2)
    assert layout.text_width > 0
    assert layout.text_x < layout.width


def test_finished_reminder_uses_larger_layout_than_paused_label():
    finished = _compute_layout(
        work_area=(0, 0, 1920, 1040),
        primary_text_width=220,
        secondary_text_width=130,
        hint_text_width=130,
        primary_line_height=32,
        secondary_line_height=20,
        hint_line_height=18,
    )
    paused = _compute_paused_label_layout(
        work_area=(0, 0, 1920, 1040),
        text_width=140,
        text_height=18,
    )

    assert finished.width > paused.width
    assert finished.height > paused.height


def test_finished_reminder_accent_matches_paused_orange():
    assert ACCENT_COLOUR == PAUSED_LABEL_DOT_FILL


def test_overlay_fonts_use_handwriting_family():
    assert LATIN_HANDWRITING_FONT_FAMILY == "Segoe Print"
    assert CHINESE_HANDWRITING_FONT_FAMILY == "LXGW WenKai TC"
    assert PRIMARY_LINE_FONT[0] == CHINESE_HANDWRITING_FONT_FAMILY
    assert SECONDARY_LINE_FONT[0] == CHINESE_HANDWRITING_FONT_FAMILY
    assert HINT_LINE_FONT[0] == CHINESE_HANDWRITING_FONT_FAMILY
    assert PAUSED_LABEL_FONT[0] == LATIN_HANDWRITING_FONT_FAMILY


def test_show_uses_full_finished_reminder_renderer(monkeypatch):
    class FakeWindow:
        def overrideredirect(self, *_args):
            return None

        def attributes(self, *_args):
            return None

        def configure(self, **_kwargs):
            return None

        def geometry(self, *_args):
            return None

        def bind(self, *_args):
            return None

        def winfo_exists(self):
            return True

        def destroy(self):
            return None

    class FakeCanvas:
        lines = []

        def __init__(self, *_args, **_kwargs):
            return None

        def pack(self):
            return None

        def create_polygon(self, *_args, **_kwargs):
            return None

        def create_line(self, *_args, **kwargs):
            self.lines.append(kwargs)

        def create_text(self, *_args, **_kwargs):
            return None

        def bind(self, *_args):
            return None

    def fail_compact_renderer(**_kwargs):
        raise AssertionError("finished reminder should not use compact label renderer")

    fake_window = FakeWindow()
    monkeypatch.setattr(overlay, "_show_status_label", fail_compact_renderer)
    monkeypatch.setattr(overlay.tk, "Toplevel", lambda _parent: fake_window)
    monkeypatch.setattr(overlay.tk, "Canvas", FakeCanvas)
    monkeypatch.setattr(overlay, "_get_work_area", lambda: (0, 0, 1920, 1040))
    monkeypatch.setattr(overlay, "_font_measurements", lambda *_args: (120, 20))

    result = overlay.show(
        on_dismiss=lambda: None,
        secondary_text="elapsed 00:05",
        parent=object(),
    )

    assert result is fake_window
    assert any(line.get("fill") == ACCENT_COLOUR for line in FakeCanvas.lines)


def test_show_paused_label_uses_bare_mmss_text(monkeypatch):
    captured = {}

    def fake_status_label(*, on_click, text, parent, destroy_before_callback=False):
        captured["text"] = text
        captured["on_click"] = on_click
        captured["parent"] = parent
        captured["destroy_before_callback"] = destroy_before_callback
        return object()

    monkeypatch.setattr(overlay, "_show_status_label", fake_status_label)

    sentinel_parent = object()
    overlay.show_paused_label(
        on_click=lambda: None,
        remaining_seconds=754,  # 12:34
        parent=sentinel_parent,
    )

    assert captured["text"] == "12:34"
    assert captured["parent"] is sentinel_parent


def test_show_paused_label_can_render_play_button_only(monkeypatch):
    captured = {}

    def fake_status_label(*, on_click, text, parent, destroy_before_callback=False):
        captured["text"] = text
        captured["on_click"] = on_click
        captured["parent"] = parent
        captured["destroy_before_callback"] = destroy_before_callback
        return object()

    monkeypatch.setattr(overlay, "_show_status_label", fake_status_label)

    sentinel_parent = object()
    overlay.show_paused_label(
        on_click=lambda: None,
        remaining_seconds=None,
        parent=sentinel_parent,
    )

    assert captured["text"] == ""
    assert captured["parent"] is sentinel_parent


def _show_paused_label_geometry(
    monkeypatch,
    *,
    work_area,
    screen_bounds,
    taskbar_info,
    text_width=60,
    text_height=18,
):
    class FakeWindow:
        def __init__(self):
            self.geometry_calls = []

        def overrideredirect(self, *_args):
            return None

        def attributes(self, *_args):
            return None

        def configure(self, **_kwargs):
            return None

        def geometry(self, value):
            self.geometry_calls.append(value)

        def bind(self, *_args):
            return None

        def winfo_exists(self):
            return True

        def destroy(self):
            return None

    class FakeCanvas:
        def __init__(self, *_args, **_kwargs):
            return None

        def pack(self):
            return None

        def create_polygon(self, *_args, **_kwargs):
            return None

        def create_oval(self, *_args, **_kwargs):
            return None

        def create_text(self, *_args, **_kwargs):
            return None

        def bind(self, *_args):
            return None

    fake_window = FakeWindow()

    monkeypatch.setattr(overlay.tk, "Toplevel", lambda _parent: fake_window)
    monkeypatch.setattr(overlay.tk, "Canvas", FakeCanvas)
    monkeypatch.setattr(overlay, "_get_work_area", lambda: work_area)
    monkeypatch.setattr(overlay, "_get_primary_screen_bounds", lambda: screen_bounds, raising=False)
    monkeypatch.setattr(overlay, "_get_taskbar_info", lambda: taskbar_info, raising=False)
    monkeypatch.setattr(overlay, "_font_measurements", lambda *_args: (text_width, text_height))

    overlay.show_paused_label(
        on_click=lambda: None,
        remaining_seconds=754,
        parent=object(),
    )

    return fake_window.geometry_calls


def test_show_paused_label_touches_work_area_bottom(monkeypatch):
    work_area = (0, 0, 1920, 1040)
    text_width = 60
    text_height = 18
    expected_layout = _compute_paused_label_layout(work_area, text_width, text_height)
    expected_y = work_area[3] - expected_layout.height

    geometry_calls = _show_paused_label_geometry(
        monkeypatch,
        work_area=work_area,
        screen_bounds=(0, 0, 1920, 1080),
        taskbar_info=None,
        text_width=text_width,
        text_height=text_height,
    )

    assert geometry_calls == [
        f"{expected_layout.width}x{expected_layout.height}+{MARGIN}+{expected_y}"
    ]


def test_show_paused_label_sits_above_auto_hidden_bottom_taskbar(monkeypatch):
    work_area = (0, 0, 1920, 1080)
    effective_work_area = (0, 0, 1920, 996)
    text_width = 60
    text_height = 18
    expected_layout = _compute_paused_label_layout(effective_work_area, text_width, text_height)
    expected_y = effective_work_area[3] - expected_layout.height

    geometry_calls = _show_paused_label_geometry(
        monkeypatch,
        work_area=work_area,
        screen_bounds=(0, 0, 1920, 1080),
        taskbar_info=overlay.TaskbarInfo(
            rect=(0, 1078, 1920, 1162),
            auto_hide=True,
        ),
        text_width=text_width,
        text_height=text_height,
    )

    assert geometry_calls == [
        f"{expected_layout.width}x{expected_layout.height}+{MARGIN}+{expected_y}"
    ]


def test_effective_work_area_reserves_auto_hidden_bottom_taskbar_height():
    work_area = (0, 0, 1920, 1080)
    screen_bounds = (0, 0, 1920, 1080)
    taskbar_info = overlay.TaskbarInfo(
        rect=(0, 1078, 1920, 1162),
        auto_hide=True,
    )

    assert overlay._effective_work_area(work_area, screen_bounds, taskbar_info) == (
        0,
        0,
        1920,
        996,
    )


def test_effective_work_area_keeps_normal_work_area_when_taskbar_is_not_auto_hidden():
    work_area = (0, 0, 1920, 996)
    screen_bounds = (0, 0, 1920, 1080)
    taskbar_info = overlay.TaskbarInfo(
        rect=(0, 996, 1920, 1080),
        auto_hide=False,
    )

    assert overlay._effective_work_area(work_area, screen_bounds, taskbar_info) == work_area


def test_play_triangle_points_fit_inside_circle_and_nudge_right():
    dot_bounds = (10, 10, 34, 34)  # 24x24 circle at (10,10)
    points = _play_triangle_points(dot_bounds)

    assert len(points) == 6  # 3 (x, y) pairs
    xs = points[0::2]
    ys = points[1::2]

    circle_left, circle_top, circle_right, circle_bottom = dot_bounds
    for x, y in zip(xs, ys):
        assert circle_left <= x <= circle_right
        assert circle_top <= y <= circle_bottom

    # Right-pointing isoceles triangle: two points share the smaller x (vertical base),
    # one point sits at the larger x (apex).
    base_x = min(xs)
    apex_x = max(xs)
    assert xs.count(base_x) == 2
    assert xs.count(apex_x) == 1
    assert apex_x - base_x == PAUSED_LABEL_TRIANGLE_WIDTH

    # Base is shifted right of the circle's geometric centre by the optical nudge.
    circle_center_x = (circle_left + circle_right) // 2
    expected_base_x = (
        circle_center_x
        + PAUSED_LABEL_TRIANGLE_OPTICAL_NUDGE
        - (PAUSED_LABEL_TRIANGLE_WIDTH // 2)
    )
    assert base_x == expected_base_x

    # The two base points are vertically separated by TRIANGLE_HEIGHT and
    # mirrored around the circle's vertical centre.
    base_ys = sorted(y for x, y in zip(xs, ys) if x == base_x)
    assert base_ys[1] - base_ys[0] == PAUSED_LABEL_TRIANGLE_HEIGHT
    circle_center_y = (circle_top + circle_bottom) // 2
    assert (base_ys[0] + base_ys[1]) // 2 == circle_center_y

    # Apex sits on the circle's horizontal centreline.
    apex_y = next(y for x, y in zip(xs, ys) if x == apex_x)
    assert apex_y == circle_center_y
