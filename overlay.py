import ctypes
import ctypes.wintypes
import math
import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from typing import Callable

WINDOW_WIDTH = 380
WINDOW_HEIGHT = 126
MARGIN = 24
TRANSPARENT_COLOUR = "magenta"

PANEL_INSET = 8
PANEL_RADIUS = 14
ACCENT_COLOUR = "#63d5b3"
PANEL_FILL = "#11181d"
PANEL_OUTLINE = "#27343b"
SHADOW_FILL = "#050708"
TEXT_LEFT_OFFSET = 40
TEXT_RIGHT_PADDING = 18
PRIMARY_TOP_PADDING = 18
PRIMARY_SECONDARY_GAP = 6
SECONDARY_HINT_GAP = 4
BOTTOM_PADDING = 16

PRIMARY_LINE_FONT = ("Microsoft JhengHei UI", 22, "bold")
SECONDARY_LINE_FONT = ("Microsoft JhengHei UI", 12, "normal")
HINT_LINE_FONT = ("Microsoft JhengHei UI", 10, "normal")

PAUSED_LABEL_MIN_WIDTH = 132
PAUSED_LABEL_HEIGHT = 34
PAUSED_LABEL_PANEL_INSET = 3
PAUSED_LABEL_RADIUS = 13
PAUSED_LABEL_DOT_SIZE = 7
PAUSED_LABEL_DOT_LEFT_PADDING = 11
PAUSED_LABEL_DOT_TEXT_GAP = 8
PAUSED_LABEL_TEXT_RIGHT_PADDING = 11
PAUSED_LABEL_FONT = ("Microsoft JhengHei UI", 10, "normal")
PAUSED_LABEL_FILL = "#1b2227"
PAUSED_LABEL_OUTLINE = "#344148"
PAUSED_LABEL_DOT_FILL = "#f29a4a"
PAUSED_LABEL_TEXT_FILL = "#edf4f5"

PRIMARY_TEXT = "站起來動一動"
HINT_TEXT = "點一下暫停提醒"


@dataclass(frozen=True)
class OverlayLayout:
    width: int
    height: int
    panel_bounds: tuple[int, int, int, int]
    text_x: int
    text_width: int
    primary_y: int
    secondary_y: int
    hint_y: int


@dataclass(frozen=True)
class PausedLabelLayout:
    width: int
    height: int
    panel_bounds: tuple[int, int, int, int]
    dot_bounds: tuple[int, int, int, int]
    text_x: int
    text_y: int
    text_width: int


def _get_work_area() -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) of primary monitor work area in pixels."""
    SPI_GETWORKAREA = 0x0030
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
    return rect.left, rect.top, rect.right, rect.bottom


def _compute_position(
    work_area: tuple[int, int, int, int],
    window_width: int = WINDOW_WIDTH,
    window_height: int = WINDOW_HEIGHT,
) -> tuple[int, int]:
    """Bottom-left of work area, with margin."""
    left, top, right, bottom = work_area
    del window_width, right
    x = left + MARGIN
    y = max(top + MARGIN, bottom - window_height - MARGIN)
    return x, y


def _panel_bounds(
    window_width: int = WINDOW_WIDTH,
    window_height: int = WINDOW_HEIGHT,
) -> tuple[int, int, int, int]:
    """Return the rounded panel bounds inside the transparent overlay window."""
    return (
        PANEL_INSET,
        PANEL_INSET,
        window_width - PANEL_INSET,
        window_height - PANEL_INSET,
    )


def _rounded_points(bounds: tuple[int, int, int, int], radius: int) -> tuple[int, ...]:
    x0, y0, x1, y1 = bounds
    radius = min(radius, (x1 - x0) // 2, (y1 - y0) // 2)
    return (
        x0 + radius,
        y0,
        x1 - radius,
        y0,
        x1,
        y0,
        x1,
        y0 + radius,
        x1,
        y1 - radius,
        x1,
        y1,
        x1 - radius,
        y1,
        x0 + radius,
        y1,
        x0,
        y1,
        x0,
        y1 - radius,
        x0,
        y0 + radius,
        x0,
        y0,
    )


def _wrapped_line_count(text_width: int, available_width: int) -> int:
    return max(1, math.ceil(max(1, text_width) / max(1, available_width)))


def _compute_layout(
    work_area: tuple[int, int, int, int],
    primary_text_width: int,
    secondary_text_width: int,
    hint_text_width: int,
    primary_line_height: int,
    secondary_line_height: int,
    hint_line_height: int,
) -> OverlayLayout:
    left, _, right, _ = work_area
    available_width = max(1, (right - left) - (MARGIN * 2))
    widest_text = max(primary_text_width, secondary_text_width, hint_text_width)
    required_width = widest_text + TEXT_LEFT_OFFSET + TEXT_RIGHT_PADDING + PANEL_INSET
    width = min(max(WINDOW_WIDTH, required_width), available_width)

    panel_bounds = _panel_bounds(width, WINDOW_HEIGHT)
    panel_left, panel_top, panel_right, _ = panel_bounds
    text_x = panel_left + TEXT_LEFT_OFFSET - PANEL_INSET
    text_width = max(1, panel_right - text_x - TEXT_RIGHT_PADDING)

    primary_block_height = (
        _wrapped_line_count(primary_text_width, text_width) * primary_line_height
    )
    secondary_block_height = (
        _wrapped_line_count(secondary_text_width, text_width) * secondary_line_height
    )
    hint_block_height = _wrapped_line_count(hint_text_width, text_width) * hint_line_height

    primary_y = panel_top + PRIMARY_TOP_PADDING
    secondary_y = primary_y + primary_block_height + PRIMARY_SECONDARY_GAP
    hint_y = secondary_y + secondary_block_height + SECONDARY_HINT_GAP
    height = max(WINDOW_HEIGHT, hint_y + hint_block_height + BOTTOM_PADDING + PANEL_INSET)

    return OverlayLayout(
        width=width,
        height=height,
        panel_bounds=_panel_bounds(width, height),
        text_x=text_x,
        text_width=text_width,
        primary_y=primary_y,
        secondary_y=secondary_y,
        hint_y=hint_y,
    )


def _compute_paused_label_layout(
    work_area: tuple[int, int, int, int],
    text_width: int,
    text_height: int,
) -> PausedLabelLayout:
    left, _, right, _ = work_area
    available_width = max(1, (right - left) - (MARGIN * 2))
    required_width = (
        PAUSED_LABEL_PANEL_INSET
        + PAUSED_LABEL_DOT_LEFT_PADDING
        + PAUSED_LABEL_DOT_SIZE
        + PAUSED_LABEL_DOT_TEXT_GAP
        + text_width
        + PAUSED_LABEL_TEXT_RIGHT_PADDING
        + PAUSED_LABEL_PANEL_INSET
    )
    width = min(max(PAUSED_LABEL_MIN_WIDTH, required_width), available_width)
    height = PAUSED_LABEL_HEIGHT
    panel_bounds = (
        PAUSED_LABEL_PANEL_INSET,
        PAUSED_LABEL_PANEL_INSET,
        width - PAUSED_LABEL_PANEL_INSET,
        height - PAUSED_LABEL_PANEL_INSET,
    )
    panel_left, _, panel_right, _ = panel_bounds
    dot_left = panel_left + PAUSED_LABEL_DOT_LEFT_PADDING
    dot_top = (height - PAUSED_LABEL_DOT_SIZE) // 2
    dot_bounds = (
        dot_left,
        dot_top,
        dot_left + PAUSED_LABEL_DOT_SIZE,
        dot_top + PAUSED_LABEL_DOT_SIZE,
    )
    text_x = dot_bounds[2] + PAUSED_LABEL_DOT_TEXT_GAP
    text_y = max(PAUSED_LABEL_PANEL_INSET, (height - text_height) // 2)
    label_text_width = max(1, panel_right - text_x - PAUSED_LABEL_TEXT_RIGHT_PADDING)

    return PausedLabelLayout(
        width=width,
        height=height,
        panel_bounds=panel_bounds,
        dot_bounds=dot_bounds,
        text_x=text_x,
        text_y=text_y,
        text_width=label_text_width,
    )


def _font_measurements(parent: tk.Misc, font_spec: tuple[str, int, str], text: str) -> tuple[int, int]:
    font = tkfont.Font(parent, font=font_spec)
    return font.measure(text), font.metrics("linespace")


def _format_mmss(seconds: int) -> str:
    minutes, seconds = divmod(max(seconds, 0), 60)
    return f"{minutes:02d}:{seconds:02d}"


def show(on_dismiss: Callable[[], None], secondary_text: str, parent: tk.Tk) -> tk.Toplevel:
    """Show the reminder overlay. Calls on_dismiss() when clicked, then destroys.

    `secondary_text` is the second line under the main heading. The caller
    formats it, for example "已坐 30 分鐘" or "已坐 00:05".

    Returns the Toplevel so callers can track or destroy it externally.
    """
    win = tk.Toplevel(parent)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.attributes("-transparentcolor", TRANSPARENT_COLOUR)
    win.configure(bg=TRANSPARENT_COLOUR)

    work_area = _get_work_area()
    primary_width, primary_height = _font_measurements(win, PRIMARY_LINE_FONT, PRIMARY_TEXT)
    secondary_width, secondary_height = _font_measurements(win, SECONDARY_LINE_FONT, secondary_text)
    hint_width, hint_height = _font_measurements(win, HINT_LINE_FONT, HINT_TEXT)
    layout = _compute_layout(
        work_area=work_area,
        primary_text_width=primary_width,
        secondary_text_width=secondary_width,
        hint_text_width=hint_width,
        primary_line_height=primary_height,
        secondary_line_height=secondary_height,
        hint_line_height=hint_height,
    )

    x, y = _compute_position(work_area, layout.width, layout.height)
    win.geometry(f"{layout.width}x{layout.height}+{x}+{y}")

    canvas = tk.Canvas(
        win,
        width=layout.width,
        height=layout.height,
        bg=TRANSPARENT_COLOUR,
        highlightthickness=0,
    )
    canvas.pack()

    panel_bounds = layout.panel_bounds
    shadow_bounds = (
        panel_bounds[0] + 2,
        panel_bounds[1] + 3,
        panel_bounds[2] + 2,
        panel_bounds[3] + 3,
    )

    for bounds, fill, outline, width in (
        (shadow_bounds, SHADOW_FILL, "", 1),
        (panel_bounds, PANEL_FILL, PANEL_OUTLINE, 1),
    ):
        x0, y0, x1, y1 = bounds
        radius = min(PANEL_RADIUS, (x1 - x0) // 2, (y1 - y0) // 2)
        rounded_points = (
            x0 + radius,
            y0,
            x1 - radius,
            y0,
            x1,
            y0,
            x1,
            y0 + radius,
            x1,
            y1 - radius,
            x1,
            y1,
            x1 - radius,
            y1,
            x0 + radius,
            y1,
            x0,
            y1,
            x0,
            y1 - radius,
            x0,
            y0 + radius,
            x0,
            y0,
        )
        canvas.create_polygon(
            rounded_points,
            smooth=True,
            fill=fill,
            outline=outline,
            width=width,
        )

    x0, y0, x1, y1 = panel_bounds
    canvas.create_line(
        x0 + 14,
        y0 + 18,
        x0 + 14,
        y1 - 18,
        fill=ACCENT_COLOUR,
        width=4,
        capstyle=tk.ROUND,
    )

    canvas.create_text(
        layout.text_x,
        layout.primary_y,
        anchor="nw",
        text=PRIMARY_TEXT,
        font=PRIMARY_LINE_FONT,
        fill="#ffffff",
        width=layout.text_width,
    )
    canvas.create_text(
        layout.text_x,
        layout.secondary_y,
        anchor="nw",
        text=secondary_text,
        font=SECONDARY_LINE_FONT,
        fill="#cfd8dc",
        width=layout.text_width,
    )
    canvas.create_text(
        layout.text_x,
        layout.hint_y,
        anchor="nw",
        text=HINT_TEXT,
        font=HINT_LINE_FONT,
        fill="#8fa1aa",
        width=layout.text_width,
    )

    def dismiss(_event=None):
        if not win.winfo_exists():
            return
        try:
            on_dismiss()
        finally:
            win.destroy()

    canvas.bind("<Button-1>", dismiss)
    win.bind("<Button-1>", dismiss)
    return win


def show_paused_label(
    on_click: Callable[[], None],
    remaining_seconds: int,
    parent: tk.Tk,
) -> tk.Toplevel:
    win = tk.Toplevel(parent)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.attributes("-transparentcolor", TRANSPARENT_COLOUR)
    try:
        win.attributes("-alpha", 0.88)
    except tk.TclError:
        pass
    win.configure(bg=TRANSPARENT_COLOUR)

    text = f"Timer paused {_format_mmss(remaining_seconds)}"
    work_area = _get_work_area()
    text_width, text_height = _font_measurements(win, PAUSED_LABEL_FONT, text)
    layout = _compute_paused_label_layout(work_area, text_width, text_height)
    x, y = _compute_position(work_area, layout.width, layout.height)
    win.geometry(f"{layout.width}x{layout.height}+{x}+{y}")

    canvas = tk.Canvas(
        win,
        width=layout.width,
        height=layout.height,
        bg=TRANSPARENT_COLOUR,
        highlightthickness=0,
    )
    canvas.pack()
    canvas.create_polygon(
        _rounded_points(layout.panel_bounds, PAUSED_LABEL_RADIUS),
        smooth=True,
        fill=PAUSED_LABEL_FILL,
        outline=PAUSED_LABEL_OUTLINE,
        width=1,
    )
    canvas.create_oval(
        *layout.dot_bounds,
        fill=PAUSED_LABEL_DOT_FILL,
        outline=PAUSED_LABEL_DOT_FILL,
    )
    canvas.create_text(
        layout.text_x,
        layout.text_y,
        anchor="nw",
        text=text,
        font=PAUSED_LABEL_FONT,
        fill=PAUSED_LABEL_TEXT_FILL,
        width=layout.text_width,
    )

    def click(_event=None):
        if not win.winfo_exists():
            return
        try:
            on_click()
        finally:
            if win.winfo_exists():
                win.destroy()

    canvas.bind("<Button-1>", click)
    win.bind("<Button-1>", click)
    return win
