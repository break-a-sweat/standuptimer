from types import SimpleNamespace

import standup_timer
from timer import State


class FakeWindow:
    def __init__(self):
        self.destroyed = False

    def destroy(self):
        self.destroyed = True


def _config(duration_seconds=1500):
    return SimpleNamespace(
        duration_seconds=duration_seconds,
        auto_start=False,
        save=lambda: None,
    )


def _fake_tray():
    return SimpleNamespace(icon=None, title="")


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


def test_pausing_running_timer_shows_paused_label(monkeypatch):
    calls = []
    monkeypatch.setattr(standup_timer, "Config", lambda: _config())
    monkeypatch.setattr(
        standup_timer.overlay,
        "show_paused_label",
        lambda **kwargs: calls.append(kwargs) or FakeWindow(),
    )

    app = standup_timer.StandUpApp()
    app.tk_root = object()
    app.tray = _fake_tray()

    app.on_start_pause(None, None)

    assert app.timer.state == State.PAUSED
    assert len(calls) == 1
    assert calls[0]["remaining_seconds"] == 1500
    assert calls[0]["parent"] is app.tk_root


def test_refresh_while_paused_reuses_existing_paused_label(monkeypatch):
    calls = []
    monkeypatch.setattr(standup_timer, "Config", lambda: _config())
    monkeypatch.setattr(
        standup_timer.overlay,
        "show_paused_label",
        lambda **kwargs: calls.append(kwargs) or FakeWindow(),
    )

    app = standup_timer.StandUpApp()
    app.tk_root = object()
    app.tray = _fake_tray()
    app.timer.pause()

    app._refresh_tray()
    app._refresh_tray()

    assert len(calls) == 1


def test_starting_from_paused_hides_paused_label(monkeypatch):
    label = FakeWindow()
    monkeypatch.setattr(standup_timer, "Config", lambda: _config())
    monkeypatch.setattr(
        standup_timer.overlay,
        "show_paused_label",
        lambda **_kwargs: label,
    )

    app = standup_timer.StandUpApp()
    app.tk_root = object()
    app.tray = _fake_tray()
    app.timer.pause()
    app._refresh_tray()

    app.on_start_pause(None, None)

    assert app.timer.state == State.RUNNING
    assert label.destroyed
    assert app._current_paused_label is None


def test_dismissing_finished_overlay_shows_paused_label(monkeypatch):
    dismissed = {}
    paused_label_calls = []
    monkeypatch.setattr(standup_timer, "Config", lambda: _config(duration_seconds=1))
    monkeypatch.setattr(
        standup_timer.overlay,
        "show",
        lambda **kwargs: dismissed.update(on_dismiss=kwargs["on_dismiss"]) or FakeWindow(),
    )
    monkeypatch.setattr(
        standup_timer.overlay,
        "show_paused_label",
        lambda **kwargs: paused_label_calls.append(kwargs) or FakeWindow(),
    )

    app = standup_timer.StandUpApp()
    app.tk_root = object()
    app.tray = _fake_tray()
    app.timer.tick()
    app._show_overlay(duration_seconds=1)

    dismissed["on_dismiss"]()

    assert app.timer.state == State.PAUSED
    assert app.timer.remaining_seconds == 0
    assert len(paused_label_calls) == 1
    assert paused_label_calls[0]["remaining_seconds"] == 0


def test_dismissing_finished_overlay_after_duration_change_still_pauses(monkeypatch):
    dismissed = {}
    paused_label_calls = []
    monkeypatch.setattr(standup_timer, "Config", lambda: _config(duration_seconds=5))
    monkeypatch.setattr(
        standup_timer.overlay,
        "show",
        lambda **kwargs: dismissed.update(on_dismiss=kwargs["on_dismiss"]) or FakeWindow(),
    )
    monkeypatch.setattr(
        standup_timer.overlay,
        "show_paused_label",
        lambda **kwargs: paused_label_calls.append(kwargs) or FakeWindow(),
    )

    app = standup_timer.StandUpApp()
    app.tk_root = object()
    app.tray = _fake_tray()
    for _ in range(5):
        app.timer.tick()
    app._show_overlay(duration_seconds=5)

    app._change_duration(1500)
    dismissed["on_dismiss"]()

    assert app.config.duration_seconds == 1500
    assert app.timer.duration_seconds == 1500
    assert app.timer.state == State.PAUSED
    assert app.timer.remaining_seconds == 0
    assert len(paused_label_calls) == 1
    assert paused_label_calls[0]["remaining_seconds"] == 0


def test_showing_finished_overlay_destroys_existing_paused_label(monkeypatch):
    paused_label = FakeWindow()
    monkeypatch.setattr(standup_timer, "Config", lambda: _config(duration_seconds=5))
    monkeypatch.setattr(
        standup_timer.overlay,
        "show_paused_label",
        lambda **_kwargs: paused_label,
    )
    monkeypatch.setattr(
        standup_timer.overlay,
        "show",
        lambda **_kwargs: FakeWindow(),
    )

    app = standup_timer.StandUpApp()
    app.tk_root = object()
    app.tray = _fake_tray()
    app.timer.pause()
    app._refresh_tray()
    app.timer.state = State.FINISHED

    app._show_overlay(duration_seconds=5)

    assert paused_label.destroyed
    assert app._current_paused_label is None
    assert app.timer.state == State.FINISHED


def test_clicking_paused_label_starts_timer_and_hides_label(monkeypatch):
    clicked = {}
    label = FakeWindow()
    monkeypatch.setattr(standup_timer, "Config", lambda: _config())

    def show_paused_label(**kwargs):
        clicked["on_click"] = kwargs["on_click"]
        return label

    monkeypatch.setattr(standup_timer.overlay, "show_paused_label", show_paused_label)

    app = standup_timer.StandUpApp()
    app.tk_root = object()
    app.tray = _fake_tray()
    app.timer.pause()
    app._refresh_tray()

    clicked["on_click"]()

    assert app.timer.state == State.RUNNING
    assert label.destroyed
    assert app._current_paused_label is None


def test_paused_label_updates_when_paused_duration_changes(monkeypatch):
    windows = []
    calls = []
    monkeypatch.setattr(standup_timer, "Config", lambda: _config())

    def show_paused_label(**kwargs):
        calls.append(kwargs)
        window = FakeWindow()
        windows.append(window)
        return window

    monkeypatch.setattr(standup_timer.overlay, "show_paused_label", show_paused_label)

    app = standup_timer.StandUpApp()
    app.tk_root = object()
    app.tray = _fake_tray()
    app.timer.pause()
    app._refresh_tray()

    app._change_duration(600)

    assert [call["remaining_seconds"] for call in calls] == [1500, 600]
    assert windows[0].destroyed
    assert not windows[1].destroyed


def test_main_replaces_existing_instance_and_releases_pid_file(monkeypatch):
    calls = []

    class FakeApp:
        def run(self):
            calls.append("run")

    monkeypatch.setattr(standup_timer, "_setup_logging", lambda: calls.append("log"))
    monkeypatch.setattr(standup_timer, "StandUpApp", FakeApp)
    monkeypatch.setattr(
        standup_timer.single_instance,
        "replace_existing_instance",
        lambda pid_file: calls.append(("replace", pid_file)),
    )
    monkeypatch.setattr(
        standup_timer.single_instance,
        "release_instance",
        lambda pid_file: calls.append(("release", pid_file)),
    )

    standup_timer.main()

    assert calls == [
        "log",
        ("replace", standup_timer.PID_PATH),
        "run",
        ("release", standup_timer.PID_PATH),
    ]
