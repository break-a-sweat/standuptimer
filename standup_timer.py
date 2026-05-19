import logging
import os
import sys
import threading
import time
import ctypes
import tkinter as tk
from tkinter import ttk
from pathlib import Path

import pystray
from pystray import MenuItem as Item, Menu

import autostart
import icon as icon_module
import overlay
from config import Config
from timer import State, TimerState

PRESET_MINUTES = [25, 30, 45, 60]
LOG_PATH = Path(os.environ.get("APPDATA", str(Path.home()))) / "standuptimer" / "standuptimer.log"


def _setup_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def _format_mmss(seconds: int) -> str:
    m, s = divmod(max(seconds, 0), 60)
    return f"{m:02d}:{s:02d}"


def _format_duration_friendly(seconds: int) -> str:
    if seconds >= 60 and seconds % 60 == 0:
        return f"{seconds // 60} 分鐘"
    return _format_mmss(seconds)


class StandUpApp:
    def __init__(self):
        self.config = Config()
        self.timer = TimerState(duration_seconds=self.config.duration_seconds)
        self.tray: pystray.Icon | None = None
        self.tk_root: tk.Tk | None = None
        self._stop = threading.Event()
        self._current_overlay: tk.Toplevel | None = None
        self._last_icon_key: tuple[State, str] | None = None

    # ---------- tray actions ----------

    def on_start_pause(self, icon, item):
        if self.timer.state == State.RUNNING:
            self.timer.pause()
        else:
            self.timer.start()
        self._refresh_tray()

    def on_reset(self, icon, item):
        self.timer.reset()
        self._refresh_tray()

    def on_select_preset(self, seconds: int):
        def handler(icon, item):
            self._change_duration(seconds)
        return handler

    def on_custom_duration(self, icon, item):
        # Schedule a tkinter modal on the main thread
        self.tk_root.after(0, self._show_custom_dialog)

    def on_toggle_autostart(self, icon, item):
        if self.config.auto_start:
            try:
                autostart.disable()
                self.config.auto_start = False
                self.config.save()
            except OSError:
                logging.exception("Failed to disable autostart")
                self._notify("無法設定開機自啟")
        else:
            try:
                autostart.enable(exe_path=self._exe_path())
                self.config.auto_start = True
                self.config.save()
            except OSError:
                logging.exception("Failed to enable autostart")
                self._notify("無法設定開機自啟")
        self._refresh_tray()

    def on_quit(self, icon, item):
        self._stop.set()
        if self.tray:
            self.tray.stop()
        if self.tk_root:
            self.tk_root.after(0, self.tk_root.quit)

    # ---------- duration changes ----------

    def _change_duration(self, seconds: int):
        self.config.duration_seconds = seconds
        self.config.save()
        self.timer.change_duration(seconds)
        self._refresh_tray()

    def _show_custom_dialog(self):
        dialog = tk.Toplevel(self.tk_root)
        dialog.title("自訂時長")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)

        style = ttk.Style(dialog)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        main = ttk.Frame(dialog, padding=20)
        main.pack()

        initial_min, initial_sec = divmod(self.config.duration_seconds, 60)
        min_var = tk.IntVar(value=initial_min)
        sec_var = tk.IntVar(value=initial_sec)

        ttk.Label(main, text="設定倒數時長").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

        ttk.Label(main, text="分").grid(row=1, column=0, padx=(0, 6))
        min_spin = ttk.Spinbox(main, from_=0, to=999, width=6, textvariable=min_var)
        min_spin.grid(row=1, column=1, padx=(0, 18))

        ttk.Label(main, text="秒").grid(row=1, column=2, padx=(0, 6))
        sec_spin = ttk.Spinbox(main, from_=0, to=59, width=6, textvariable=sec_var)
        sec_spin.grid(row=1, column=3)

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=(20, 0), sticky="e")

        def accept():
            try:
                m = int(min_var.get())
                s = int(sec_var.get())
            except (tk.TclError, ValueError):
                return
            total = m * 60 + s
            if total < 1:
                return
            self._change_duration(total)
            dialog.destroy()

        def cancel():
            dialog.destroy()

        ttk.Button(btn_frame, text="取消", command=cancel, width=8).pack(side="right", padx=(8, 0))
        ttk.Button(btn_frame, text="確定", command=accept, width=8).pack(side="right")

        dialog.protocol("WM_DELETE_WINDOW", cancel)
        dialog.bind("<Return>", lambda _e: accept())
        dialog.bind("<Escape>", lambda _e: cancel())

        # Center on screen
        dialog.update_idletasks()
        w = dialog.winfo_width()
        h = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() - w) // 2
        y = (dialog.winfo_screenheight() - h) // 2
        dialog.geometry(f"+{x}+{y}")

        min_spin.focus()

    # ---------- timer loop ----------

    def _timer_loop(self):
        while not self._stop.is_set():
            time.sleep(1)
            previous = self.timer.state
            self.timer.tick()
            if previous == State.RUNNING and self.timer.state == State.FINISHED:
                self._on_finished()
            if self.tray is not None:
                self._refresh_tray()

    def _on_finished(self):
        duration_seconds = self.timer.duration_seconds
        # Schedule overlay creation on tk main thread
        if self.tk_root is not None:
            self.tk_root.after(0, lambda: self._show_overlay(duration_seconds))

    def _show_overlay(self, duration_seconds: int):
        # If a previous overlay still exists, destroy it first
        if self._current_overlay is not None:
            try:
                self._current_overlay.destroy()
            except tk.TclError:
                pass
            self._current_overlay = None

        def on_dismiss():
            self.timer.dismiss()
            self._current_overlay = None
            self._refresh_tray()

        secondary = f"已坐 {_format_duration_friendly(duration_seconds)}"
        self._current_overlay = overlay.show(
            on_dismiss=on_dismiss,
            secondary_text=secondary,
            parent=self.tk_root,
        )

    # ---------- tray helpers ----------

    def _exe_path(self) -> str:
        # If frozen (PyInstaller), sys.executable is the exe itself
        if getattr(sys, "frozen", False):
            return sys.executable
        # Otherwise, point at the script via `pythonw script.py`
        script = os.path.abspath(sys.argv[0])
        return f'"{sys.executable}" "{script}"'

    def _notify(self, message: str) -> None:
        if self.tray is not None:
            try:
                self.tray.notify(message, title="StandUp Timer")
            except Exception:
                logging.exception("Failed to show tray notification")

    def _icon_label(self) -> str:
        if self.timer.state in (State.RUNNING, State.PAUSED):
            return _format_mmss(self.timer.remaining_seconds)
        return _format_mmss(self.config.duration_seconds)

    def _build_menu(self) -> Menu:
        is_running = self.timer.state == State.RUNNING
        start_pause_label = "⏸ 暫停" if is_running else "▶ 開始"

        def make_preset(minutes):
            secs = minutes * 60
            return Item(
                f"{minutes} 分鐘",
                self.on_select_preset(secs),
                checked=lambda _i, _s=secs: self.config.duration_seconds == _s,
                radio=True,
            )

        duration_submenu = Menu(
            *(make_preset(m) for m in PRESET_MINUTES),
            Item("自訂…", self.on_custom_duration),
        )

        return Menu(
            Item(start_pause_label, self.on_start_pause, default=True),
            Item("↻ 重設", self.on_reset),
            Menu.SEPARATOR,
            Item("時長", duration_submenu),
            Menu.SEPARATOR,
            Item(
                "開機自動啟動",
                self.on_toggle_autostart,
                checked=lambda _i: self.config.auto_start,
            ),
            Menu.SEPARATOR,
            Item("✕ 離開", self.on_quit),
        )

    def _refresh_tray(self):
        if self.tray is None:
            return
        state = self.timer.state
        label = self._icon_label()
        key = (state, label)
        if key != self._last_icon_key:
            self.tray.icon = icon_module.make_icon(state, label)
            self._last_icon_key = key
        self.tray.menu = self._build_menu()
        self.tray.title = self._tooltip_text()

    def _tooltip_text(self) -> str:
        if self.timer.state == State.RUNNING:
            return f"剩餘 {_format_mmss(self.timer.remaining_seconds)}"
        if self.timer.state == State.PAUSED:
            return f"已暫停 · 剩 {_format_mmss(self.timer.remaining_seconds)}"
        return _format_duration_friendly(self.config.duration_seconds)

    # ---------- entry point ----------

    def run(self):
        # DPI awareness for accurate overlay positioning
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self.tk_root = tk.Tk()
        self.tk_root.withdraw()  # invisible root; overlay/dialog are Toplevels

        self.tray = pystray.Icon(
            "StandUpTimer",
            icon=icon_module.make_icon(State.IDLE, self._icon_label()),
            title=self._tooltip_text(),
            menu=self._build_menu(),
        )
        self.tray.run_detached()

        timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        timer_thread.start()

        self.tk_root.mainloop()
        self._stop.set()


def main():
    _setup_logging()
    try:
        StandUpApp().run()
    except Exception:
        logging.exception("Fatal error")
        raise


if __name__ == "__main__":
    main()
