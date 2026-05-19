import ctypes
import ctypes.wintypes
import tkinter as tk
from typing import Callable

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 90
MARGIN = 24
TRANSPARENT_COLOUR = "magenta"

PRIMARY_LINE_FONT = ("Microsoft JhengHei UI", 22, "bold")
SECONDARY_LINE_FONT = ("Microsoft JhengHei UI", 12, "normal")


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


def show(on_dismiss: Callable[[], None], duration_minutes: int, parent: tk.Tk) -> tk.Toplevel:
    """Show the reminder overlay. Calls on_dismiss() when clicked, then destroys.

    Returns the Toplevel so callers can track / destroy it externally (e.g. if a
    new alert fires before the previous overlay was dismissed).
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

    primary = "站起來動一動"
    secondary = f"已坐 {duration_minutes} 分鐘"

    # Shadow (drawn first, offset by +2,+2 in dark grey)
    canvas.create_text(
        12 + 2, 18 + 2, anchor="nw", text=primary,
        font=PRIMARY_LINE_FONT, fill="#202020",
    )
    canvas.create_text(
        12 + 2, 58 + 2, anchor="nw", text=secondary,
        font=SECONDARY_LINE_FONT, fill="#202020",
    )
    # Main text
    canvas.create_text(
        12, 18, anchor="nw", text=primary,
        font=PRIMARY_LINE_FONT, fill="#ffffff",
    )
    canvas.create_text(
        12, 58, anchor="nw", text=secondary,
        font=SECONDARY_LINE_FONT, fill="#dddddd",
    )

    def dismiss(_event=None):
        on_dismiss()
        win.destroy()

    canvas.bind("<Button-1>", dismiss)
    win.bind("<Button-1>", dismiss)
    return win
