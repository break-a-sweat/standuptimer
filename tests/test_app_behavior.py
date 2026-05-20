from types import SimpleNamespace

import standup_timer
from timer import State


def test_app_initializes_timer_running(monkeypatch):
    monkeypatch.setattr(
        standup_timer,
        "Config",
        lambda: SimpleNamespace(duration_seconds=1500, auto_start=False),
    )

    app = standup_timer.StandUpApp()

    assert app.timer.state == State.RUNNING
    assert app.timer.remaining_seconds == 1500


def test_tray_menu_has_only_requested_items(monkeypatch):
    monkeypatch.setattr(
        standup_timer,
        "Config",
        lambda: SimpleNamespace(duration_seconds=1500, auto_start=False),
    )

    app = standup_timer.StandUpApp()
    menu = app._build_menu()

    assert [item.text for item in menu.items] == [
        "自訂時間",
        "重新計時",
        "開機啟動",
    ]
    assert all(item.submenu is None for item in menu.items)
