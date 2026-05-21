import ctypes
import os
from pathlib import Path

LATIN_HANDWRITING_FONT_FAMILY = "Segoe Print"
CHINESE_HANDWRITING_FONT_FAMILY = "LXGW WenKai TC"
CHINESE_HANDWRITING_FONT_FILENAME = "LXGWWenKaiTC-Regular.ttf"


def _user_font_paths() -> tuple[Path, ...]:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        return ()
    return (
        Path(local_appdata)
        / "Microsoft"
        / "Windows"
        / "Fonts"
        / CHINESE_HANDWRITING_FONT_FILENAME,
    )


def _add_font_resource(path: Path) -> int:
    try:
        return ctypes.windll.gdi32.AddFontResourceExW(str(path), 0, 0)
    except (AttributeError, OSError):
        return 0


def load_user_fonts() -> tuple[Path, ...]:
    loaded = []
    for path in _user_font_paths():
        if path.exists() and _add_font_resource(path):
            loaded.append(path)
    return tuple(loaded)
