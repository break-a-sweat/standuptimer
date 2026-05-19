import logging
import os
import sys
import threading
import time
import ctypes
import tkinter as tk
from pathlib import Path

import pystray
from pystray import MenuItem as Item, Menu

import autostart
import icon as icon_module
import overlay
from config import Config
from timer import State, TimerState

PRESET_DURATIONS = [25, 30, 45, 60]
LOG_PATH = Path(os.environ.get("APPDATA", str(Path.home()))) / "standuptimer" / "standuptimer.log"


def _setup_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


class StandUpApp:
    def __init__(self):
        self.config = Config()
        self.timer = TimerState(duration_seconds=self.config.duration_minutes * 60)
        self.tray: pystray.Icon | None = None
        self.tk_root: tk.Tk | None = None
        self._stop = threading.Event()
        self._current_overlay: tk.Toplevel | None = None
        self._last_icon_state: State | None = None

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

    def on_select_preset(self, minutes: int):
        def handler(icon, item):
            self._change_duration(minutes)
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
            except OSError as e:
                logging.exception("Failed to disable autostart")
                self._notify("無法設定開機自啟")
        else:
            try:
                autostart.enable(exe_path=self._exe_path())
                self.config.auto_start = True
                self.config.save()
            except OSError as e:
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

    def _change_duration(self, minutes: int):
        self.config.duration_minutes = minutes
        self.config.save()
        self.timer.change_duration(minutes * 60)
        self._refresh_tray()

    def _show_custom_dialog(self):
        dialog = tk.Toplevel(self.tk_root)
        dialog.title("自訂時長")
        dialog.geometry("260x110")
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)

        tk.Label(dialog, text="分鐘 (1–999):").pack(pady=(12, 4))
        var = tk.IntVar(value=self.config.duration_minutes)
        spin = tk.Spinbox(dialog, from_=1, to=999, textvariable=var, width=10)
        spin.pack()

        def accept():
            value = var.get()
            if 1 <= value <= 999:
                self._change_duration(value)
            dialog.destroy()

        tk.Button(dialog, text="確定", command=accept, width=10).pack(pady=8)

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
        duration_minutes = self.timer.duration_seconds // 60
        # Schedule overlay creation on tk main thread
        if self.tk_root is not None:
            self.tk_root.after(0, lambda: self._show_overlay(duration_minutes))

    def _show_overlay(self, duration_minutes: int):
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

        self._current_overlay = overlay.show(
            on_dismiss=on_dismiss,
            duration_minutes=duration_minutes,
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

    def _format_remaining(self) -> str:
        m, s = divmod(max(self.timer.remaining_seconds, 0), 60)
        return f"{m:02d}:{s:02d}"

    def _build_menu(self) -> Menu:
        is_running = self.timer.state == State.RUNNING
        start_pause_label = "⏸ 暫停" if is_running else "▶ 開始"

        def make_preset(m):
            return Item(
                f"{m} 分鐘",
                self.on_select_preset(m),
                checked=lambda _i, _m=m: self.config.duration_minutes == _m,
                radio=True,
            )

        duration_submenu = Menu(
            *(make_preset(m) for m in PRESET_DURATIONS),
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
        if state != self._last_icon_state:
            self.tray.icon = icon_module.make_icon(state)
            self._last_icon_state = state
        self.tray.menu = self._build_menu()
        self.tray.title = self._tooltip_text()

    def _tooltip_text(self) -> str:
        if self.timer.state == State.RUNNING:
            return f"剩餘 {self._format_remaining()}"
        if self.timer.state == State.PAUSED:
            return f"已暫停 · 剩 {self._format_remaining()}"
        return f"{self.config.duration_minutes} 分鐘"

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
            icon=icon_module.make_icon(State.IDLE),
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
