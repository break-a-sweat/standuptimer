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
import single_instance
from config import Config
from timer import State, TimerState

PRESET_MINUTES = [25, 30, 45, 60]
CUSTOM_DIALOG_MIN_WIDTH = 520
CUSTOM_DIALOG_MIN_HEIGHT = 240
CUSTOM_DIALOG_SCREEN_MARGIN = 32
LOG_PATH = Path(os.environ.get("APPDATA", str(Path.home()))) / "standuptimer" / "standuptimer.log"
PID_PATH = LOG_PATH.with_suffix(".pid")


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


def _center_geometry(screen_width: int, screen_height: int, width: int, height: int) -> str:
    max_width = max(1, screen_width - (CUSTOM_DIALOG_SCREEN_MARGIN * 2))
    max_height = max(1, screen_height - (CUSTOM_DIALOG_SCREEN_MARGIN * 2))
    width = min(max(width, CUSTOM_DIALOG_MIN_WIDTH), max_width)
    height = min(max(height, CUSTOM_DIALOG_MIN_HEIGHT), max_height)
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)
    return f"{width}x{height}+{x}+{y}"


def _dialog_min_size(screen_width: int, screen_height: int) -> tuple[int, int]:
    max_width = max(1, screen_width - (CUSTOM_DIALOG_SCREEN_MARGIN * 2))
    max_height = max(1, screen_height - (CUSTOM_DIALOG_SCREEN_MARGIN * 2))
    return (
        min(CUSTOM_DIALOG_MIN_WIDTH, max_width),
        min(CUSTOM_DIALOG_MIN_HEIGHT, max_height),
    )


def _parse_duration_fields(minutes_text: str, seconds_text: str) -> int:
    minutes_text = minutes_text.strip()
    seconds_text = seconds_text.strip()
    try:
        minutes = int(minutes_text) if minutes_text else 0
        seconds = int(seconds_text) if seconds_text else 0
    except ValueError as exc:
        raise ValueError("請輸入數字") from exc
    if minutes < 0:
        raise ValueError("分鐘不可小於 0")
    if not 0 <= seconds <= 59:
        raise ValueError("秒數需介於 0 到 59")
    return (minutes * 60) + seconds


def _duration_preview_text(minutes_text: str, seconds_text: str) -> str:
    try:
        total = _parse_duration_fields(minutes_text, seconds_text)
    except ValueError as exc:
        return str(exc)
    if total < 1:
        return "請輸入至少 1 秒"
    return f"將設定為 {_format_mmss(total)}"


class StandUpApp:
    def __init__(self):
        self.config = Config()
        self.timer = TimerState(duration_seconds=self.config.duration_seconds)
        self.timer.start()
        self.tray: pystray.Icon | None = None
        self.tk_root: tk.Tk | None = None
        self._stop = threading.Event()
        self._current_overlay: tk.Toplevel | None = None
        self._current_paused_label: tk.Toplevel | None = None
        self._paused_label_remaining_seconds: int | None = None
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
        self._destroy_paused_label()
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
        dialog.title("自訂倒數時長")
        dialog.resizable(False, False)
        dialog.minsize(
            *_dialog_min_size(dialog.winfo_screenwidth(), dialog.winfo_screenheight())
        )
        dialog.attributes("-topmost", True)

        style = ttk.Style(dialog)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        main = ttk.Frame(dialog, padding=(22, 18, 22, 18))
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)

        initial_min, initial_sec = divmod(self.config.duration_seconds, 60)
        min_var = tk.StringVar(value=str(initial_min))
        sec_var = tk.StringVar(value=str(initial_sec))

        ttk.Label(
            main,
            text="設定倒數時長",
            font=("Microsoft JhengHei UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        input_frame = ttk.LabelFrame(main, text="輸入", padding=(14, 10))
        input_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 14))
        input_frame.columnconfigure(0, weight=1)
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="分鐘").grid(row=0, column=0, sticky="w")
        min_spin = ttk.Spinbox(
            input_frame,
            from_=0,
            to=999,
            width=8,
            justify="center",
            textvariable=min_var,
        )
        min_spin.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(6, 0))

        ttk.Label(input_frame, text="秒").grid(row=0, column=1, sticky="w")
        sec_spin = ttk.Spinbox(
            input_frame,
            from_=0,
            to=59,
            width=8,
            justify="center",
            textvariable=sec_var,
        )
        sec_spin.grid(row=1, column=1, sticky="ew", pady=(6, 0))

        ttk.Label(
            input_frame,
            text="空白欄位會自動視為 0",
            foreground="#666666",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 0))

        preview_frame = ttk.LabelFrame(main, text="預覽", padding=(14, 10))
        preview_frame.grid(row=1, column=1, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)

        preview_var = tk.StringVar(
            value=_duration_preview_text(min_var.get(), sec_var.get())
        )
        ttk.Label(
            preview_frame,
            textvariable=preview_var,
            font=("Microsoft JhengHei UI", 13, "bold"),
            anchor="center",
            justify="center",
            wraplength=150,
        ).grid(row=0, column=0, sticky="ew", pady=(8, 10))

        ttk.Label(
            preview_frame,
            text=f"目前 {_format_mmss(self.config.duration_seconds)}",
            foreground="#666666",
            anchor="center",
        ).grid(row=1, column=0, sticky="ew")

        def update_preview(*_args):
            preview_var.set(_duration_preview_text(min_var.get(), sec_var.get()))

        min_var.trace_add("write", update_preview)
        sec_var.trace_add("write", update_preview)

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(18, 0), sticky="e")

        def accept():
            try:
                total = _parse_duration_fields(min_var.get(), sec_var.get())
            except ValueError as exc:
                preview_var.set(str(exc))
                return
            if total < 1:
                preview_var.set("請輸入至少 1 秒")
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
        geometry = _center_geometry(
            dialog.winfo_screenwidth(),
            dialog.winfo_screenheight(),
            dialog.winfo_width(),
            dialog.winfo_height(),
        )
        dialog.geometry(geometry)

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
        self._destroy_paused_label()
        # If a previous overlay still exists, destroy it first
        if self._current_overlay is not None:
            try:
                self._current_overlay.destroy()
            except tk.TclError:
                pass
            self._current_overlay = None

        def on_dismiss():
            self.timer.dismiss(force=self.timer.state == State.IDLE)
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

    def _on_paused_label_click(self):
        self.timer.start()
        self._sync_paused_label()
        self._refresh_tray()

    def _destroy_paused_label(self):
        if self._current_paused_label is None:
            self._paused_label_remaining_seconds = None
            return
        try:
            self._current_paused_label.destroy()
        except tk.TclError:
            logging.exception("Failed to destroy paused label")
        self._current_paused_label = None
        self._paused_label_remaining_seconds = None

    def _sync_paused_label(self):
        if self.timer.state != State.PAUSED:
            self._destroy_paused_label()
            return
        if self.tk_root is None:
            return
        if (
            self._current_paused_label is not None
            and self._paused_label_remaining_seconds == self.timer.remaining_seconds
        ):
            return
        self._destroy_paused_label()
        try:
            self._current_paused_label = overlay.show_paused_label(
                on_click=self._on_paused_label_click,
                remaining_seconds=self.timer.remaining_seconds,
                parent=self.tk_root,
            )
            self._paused_label_remaining_seconds = self.timer.remaining_seconds
        except tk.TclError:
            logging.exception("Failed to show paused label")

    def _schedule_paused_label_sync(self):
        if self.tk_root is not None and hasattr(self.tk_root, "after"):
            self.tk_root.after(0, self._sync_paused_label)
        else:
            self._sync_paused_label()

    def _icon_label(self) -> str:
        if self.timer.state in (State.RUNNING, State.PAUSED):
            return _format_mmss(self.timer.remaining_seconds)
        return _format_mmss(self.config.duration_seconds)

    def _build_menu(self) -> Menu:
        return Menu(
            Item("開始/暫停", self.on_start_pause, default=True, visible=False),
            Item("自訂時間", self.on_custom_duration),
            Item(
                "開機啟動",
                self.on_toggle_autostart,
                checked=lambda _i: self.config.auto_start,
            ),
            Item("退出", self.on_quit),
        )

    def _refresh_tray(self):
        self._schedule_paused_label_sync()
        if self.tray is None:
            return
        state = self.timer.state
        label = self._icon_label()
        key = (state, label)
        if key != self._last_icon_key:
            self.tray.icon = icon_module.make_icon(state, label)
            self._last_icon_key = key
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
    single_instance.replace_existing_instance(PID_PATH)
    try:
        StandUpApp().run()
    except Exception:
        logging.exception("Fatal error")
        raise
    finally:
        single_instance.release_instance(PID_PATH)


if __name__ == "__main__":
    main()
