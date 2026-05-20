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

    assert [item.text for item in menu] == [
        "自訂時間",
        "開機啟動",
        "退出",
    ]
    assert all(item.submenu is None for item in menu)
    assert all(item.enabled for item in menu)


def test_tray_menu_visible_items_are_not_default_actions(monkeypatch):
    monkeypatch.setattr(
        standup_timer,
        "Config",
        lambda: SimpleNamespace(duration_seconds=1500, auto_start=False),
    )

    app = standup_timer.StandUpApp()
    menu = app._build_menu()

    assert all(not item.default for item in menu)


def test_tray_left_click_uses_hidden_start_pause_action(monkeypatch):
    monkeypatch.setattr(
        standup_timer,
        "Config",
        lambda: SimpleNamespace(duration_seconds=1500, auto_start=False),
    )

    app = standup_timer.StandUpApp()
    app.timer.pause()

    menu = app._build_menu()
    menu(None)

    assert app.timer.state == State.RUNNING


def test_refresh_tray_does_not_rebuild_unchanged_menu(monkeypatch):
    monkeypatch.setattr(
        standup_timer,
        "Config",
        lambda: SimpleNamespace(duration_seconds=1500, auto_start=False),
    )

    class FakeTray:
        def __init__(self, menu):
            self._menu = menu
            self.menu_assignments = 0
            self.icon = None
            self.title = ""

        @property
        def menu(self):
            return self._menu

        @menu.setter
        def menu(self, value):
            self.menu_assignments += 1
            self._menu = value

    app = standup_timer.StandUpApp()
    tray = FakeTray(app._build_menu())
    app.tray = tray

    app._refresh_tray()
    app._refresh_tray()

    assert tray.menu_assignments == 0
