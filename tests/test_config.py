import json
from pathlib import Path

import pytest

from config import Config, DEFAULT_DURATION_MINUTES


def test_load_with_no_file_returns_defaults(tmp_path):
    cfg = Config(tmp_path / "config.json")
    assert cfg.duration_minutes == DEFAULT_DURATION_MINUTES
    assert cfg.auto_start is False


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config(path)
    cfg.duration_minutes = 45
    cfg.auto_start = True
    cfg.save()

    cfg2 = Config(path)
    assert cfg2.duration_minutes == 45
    assert cfg2.auto_start is True


def test_load_malformed_json_returns_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{not valid json", encoding="utf-8")
    cfg = Config(path)
    assert cfg.duration_minutes == DEFAULT_DURATION_MINUTES
    assert cfg.auto_start is False


def test_save_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "dir" / "config.json"
    cfg = Config(path)
    cfg.duration_minutes = 25
    cfg.save()
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["duration_minutes"] == 25


def test_partial_config_uses_defaults_for_missing_keys(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"duration_minutes": 50}), encoding="utf-8")
    cfg = Config(path)
    assert cfg.duration_minutes == 50
    assert cfg.auto_start is False
