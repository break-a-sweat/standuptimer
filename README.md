# StandUp Timer

A lightweight Windows tray-icon countdown timer that reminds you to stand up.

## Run

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python standup_timer.py
```

## Test

```
pytest -v
```

## Package as exe

```
pip install pyinstaller
pyinstaller --noconsole --onefile --icon=icon.ico standup_timer.py
```
