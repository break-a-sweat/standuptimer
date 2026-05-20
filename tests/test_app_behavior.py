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
