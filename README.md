# StandUp Timer

A lightweight Windows tray-icon countdown timer. When the countdown finishes, a semi-transparent reminder appears at the bottom-left of the screen until you click to dismiss it.

## Features

- System tray icon **displays the remaining time as `MM:SS` text**
- Minimal right-click menu: 自訂時間 / 開機啟動 / 退出
- Custom duration down to 1 second
- Click-to-dismiss reminder overlay (no auto-disappear)
- Optional "Start with Windows" toggle (per-user, no admin needed)

## Install (development)

Requires Python 3.10 or newer (uses PEP 604 union syntax).

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

Double-click `start.pyw` — Windows launches it with `pythonw.exe` (no console window).

You can also run from a terminal:

```
python standup_timer.py
```

Right-click the tray icon to access the menu. On Windows 11 you may need to drag the icon from the overflow panel onto the visible tray.

## Test

```
pytest -v
```

The autostart tests touch the real `HKCU` registry under a uniquely-named test value, so they require Windows. They skip cleanly on other platforms.

## Config

Settings live at `%APPDATA%\standuptimer\config.json`. The file is created on first run and rewritten whenever you change settings from the tray menu.

```json
{
  "duration_seconds": 1500,
  "auto_start": false
}
```

## Logs

Errors are written to `%APPDATA%\standuptimer\standuptimer.log`.

## Out of scope (current version)

- Sound alerts
- Multi-monitor (overlay shows on primary monitor only)
- Session history / statistics
- Snooze button on the overlay
