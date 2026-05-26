import ctypes
import os
import sys
from pathlib import Path

LATIN_HANDWRITING_FONT_FAMILY = "Segoe Print"
CHINESE_HANDWRITING_FONT_FAMILY = "LXGW WenKai TC"
CHINESE_HANDWRITING_FONT_FILENAME = "LXGWWenKaiTC-Regular.ttf"
BUNDLED_FONT_DIR = Path("assets") / "fonts"


def _resource_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _bundled_font_paths() -> tuple[Path, ...]:
    return (_resource_root() / BUNDLED_FONT_DIR / CHINESE_HANDWRITING_FONT_FILENAME,)


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


def _load_font_resources(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    loaded = []
    for path in paths:
        if path.exists() and _add_font_resource(path):
            loaded.append(path)
    return tuple(loaded)


def load_user_fonts() -> tuple[Path, ...]:
    for paths in (_bundled_font_paths(), _user_font_paths()):
        loaded = _load_font_resources(paths)
        if loaded:
            return loaded
    return ()
