import os
import subprocess
from pathlib import Path
from typing import Callable


def _read_pid(pid_file: Path) -> int | None:
    try:
        raw_pid = pid_file.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    try:
        return int(raw_pid)
    except ValueError:
        return None


def _terminate_pid(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
        return
    try:
        os.kill(pid, 15)
    except OSError:
        pass


def replace_existing_instance(
    pid_file: Path,
    *,
    current_pid: int | None = None,
    terminate_pid: Callable[[int], None] = _terminate_pid,
) -> None:
    current_pid = os.getpid() if current_pid is None else current_pid
    pid_file.parent.mkdir(parents=True, exist_ok=True)

    old_pid = _read_pid(pid_file)
    if old_pid is not None and old_pid != current_pid:
        terminate_pid(old_pid)

    pid_file.write_text(str(current_pid), encoding="utf-8")


def release_instance(pid_file: Path, *, current_pid: int | None = None) -> None:
    current_pid = os.getpid() if current_pid is None else current_pid
    if _read_pid(pid_file) != current_pid:
        return
    try:
        pid_file.unlink()
    except OSError:
        pass
