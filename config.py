import json
import os
from pathlib import Path

DEFAULT_DURATION_MINUTES = 30
DEFAULT_AUTO_START = False


def default_config_path() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        appdata = str(Path.home() / "AppData" / "Roaming")
    return Path(appdata) / "standuptimer" / "config.json"


class Config:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else default_config_path()
        self.duration_minutes = DEFAULT_DURATION_MINUTES
        self.auto_start = DEFAULT_AUTO_START
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(data, dict):
            return
        duration = data.get("duration_minutes")
        if isinstance(duration, int) and duration > 0:
            self.duration_minutes = duration
        auto = data.get("auto_start")
        if isinstance(auto, bool):
            self.auto_start = auto

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "duration_minutes": self.duration_minutes,
            "auto_start": self.auto_start,
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
