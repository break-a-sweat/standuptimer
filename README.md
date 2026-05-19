# StandUp Timer

A lightweight Windows tray-icon countdown timer. When the countdown finishes, a semi-transparent reminder appears at the bottom-left of the screen until you click to dismiss it.

## Features

- System tray icon with right-click menu
- Preset durations (25 / 30 / 45 / 60 min) plus custom
- Start / Pause / Reset controls
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

```
python standup_timer.py
```

Right-click the tray icon to access the menu. On Windows 11 you may need to drag the icon from the overflow panel onto the visible tray.

## Test

```
pytest -v
```

The autostart tests touch the real `HKCU` registry under a uniquely-named test value, so they require Windows. They skip cleanly on other platforms.

## Package as a single .exe

```
pip install pyinstaller
pyinstaller --noconsole --onefile --name StandUpTimer standup_timer.py
```

The exe lands in `dist\StandUpTimer.exe`. Place it anywhere; the registry auto-start entry uses its absolute path.

## Config

Settings live at `%APPDATA%\standuptimer\config.json`. The file is created on first run and rewritten whenever you change settings from the tray menu.

```json
{
  "duration_minutes": 30,
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
