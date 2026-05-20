import ctypes
import ctypes.wintypes
import tkinter as tk
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

PRIMARY_LINE_FONT = ("Microsoft JhengHei UI", 22, "bold")
SECONDARY_LINE_FONT = ("Microsoft JhengHei UI", 12, "normal")
HINT_LINE_FONT = ("Microsoft JhengHei UI", 10, "normal")

PRIMARY_TEXT = "站起來動一動"
HINT_TEXT = "點一下暫停提醒"


def _get_work_area() -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) of primary monitor work area in pixels."""
    SPI_GETWORKAREA = 0x0030
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
    return rect.left, rect.top, rect.right, rect.bottom


def _compute_position(work_area: tuple[int, int, int, int]) -> tuple[int, int]:
    """Bottom-left of work area, with margin."""
    left, _, _, bottom = work_area
    x = left + MARGIN
    y = bottom - WINDOW_HEIGHT - MARGIN
    return x, y


def _panel_bounds() -> tuple[int, int, int, int]:
    """Return the rounded panel bounds inside the transparent overlay window."""
    return (
        PANEL_INSET,
        PANEL_INSET,
        WINDOW_WIDTH - PANEL_INSET,
        WINDOW_HEIGHT - PANEL_INSET,
    )


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

    x, y = _compute_position(_get_work_area())
    win.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    canvas = tk.Canvas(
        win,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        bg=TRANSPARENT_COLOUR,
        highlightthickness=0,
    )
    canvas.pack()

    panel_bounds = _panel_bounds()
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

    text_x = x0 + 32
    text_width = x1 - text_x - 18
    canvas.create_text(
        text_x,
        y0 + 18,
        anchor="nw",
        text=PRIMARY_TEXT,
        font=PRIMARY_LINE_FONT,
        fill="#ffffff",
        width=text_width,
    )
    canvas.create_text(
        text_x,
        y0 + 55,
        anchor="nw",
        text=secondary_text,
        font=SECONDARY_LINE_FONT,
        fill="#cfd8dc",
        width=text_width,
    )
    canvas.create_text(
        text_x,
        y0 + 82,
        anchor="nw",
        text=HINT_TEXT,
        font=HINT_LINE_FONT,
        fill="#8fa1aa",
        width=text_width,
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
