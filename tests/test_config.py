import json
from pathlib import Path

import pytest

from config import Config, DEFAULT_DURATION_SECONDS


def test_load_with_no_file_returns_defaults(tmp_path):
    cfg = Config(tmp_path / "config.json")
    assert cfg.duration_seconds == DEFAULT_DURATION_SECONDS
    assert cfg.auto_start is False


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config(path)
    cfg.duration_seconds = 2700  # 45 min
    cfg.auto_start = True
    cfg.save()

    cfg2 = Config(path)
    assert cfg2.duration_seconds == 2700
    assert cfg2.auto_start is True


def test_round_trip_preserves_seconds_resolution(tmp_path):
    """5-second durations must survive a round trip — needed for test mode."""
    path = tmp_path / "config.json"
    cfg = Config(path)
    cfg.duration_seconds = 5
    cfg.save()

    cfg2 = Config(path)
    assert cfg2.duration_seconds == 5


def test_load_malformed_json_returns_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{not valid json", encoding="utf-8")
    cfg = Config(path)
    assert cfg.duration_seconds == DEFAULT_DURATION_SECONDS
    assert cfg.auto_start is False


def test_save_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "dir" / "config.json"
    cfg = Config(path)
    cfg.duration_seconds = 1500  # 25 min
    cfg.save()
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["duration_seconds"] == 1500


def test_partial_config_uses_defaults_for_missing_keys(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"duration_seconds": 3000}), encoding="utf-8")
    cfg = Config(path)
    assert cfg.duration_seconds == 3000
    assert cfg.auto_start is False
