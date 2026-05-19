import sys
import uuid

import pytest

if sys.platform != "win32":
    pytest.skip("autostart is Windows-only", allow_module_level=True)

import winreg

from autostart import is_enabled, enable, disable, RUN_KEY_PATH


@pytest.fixture
def test_value_name():
    name = f"StandUpTimerTest_{uuid.uuid4().hex[:8]}"
    yield name
    # Cleanup: remove the value if a test left it behind
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, name)
    except FileNotFoundError:
        pass


def test_is_enabled_returns_false_when_not_set(test_value_name):
    assert is_enabled(test_value_name) is False


def test_enable_writes_registry_value(test_value_name):
    enable(test_value_name, exe_path=r"C:\fake\path\standup_timer.exe")
    assert is_enabled(test_value_name) is True
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH) as k:
        value, _ = winreg.QueryValueEx(k, test_value_name)
    assert value == r"C:\fake\path\standup_timer.exe"


def test_disable_removes_registry_value(test_value_name):
    enable(test_value_name, exe_path=r"C:\fake\standup_timer.exe")
    disable(test_value_name)
    assert is_enabled(test_value_name) is False


def test_disable_when_not_set_is_idempotent(test_value_name):
    disable(test_value_name)  # should not raise
    assert is_enabled(test_value_name) is False


def test_enable_overwrites_existing_value(test_value_name):
    enable(test_value_name, exe_path=r"C:\old\path.exe")
    enable(test_value_name, exe_path=r"C:\new\path.exe")
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH) as k:
        value, _ = winreg.QueryValueEx(k, test_value_name)
    assert value == r"C:\new\path.exe"
