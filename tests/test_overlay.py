import overlay
from overlay import (
    _compute_layout,
    _compute_paused_label_layout,
    _compute_position,
    _panel_bounds,
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
