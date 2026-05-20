import pytest

from timer import TimerState, State


def test_initial_state_is_idle_with_full_remaining():
    t = TimerState(duration_seconds=1800)
    assert t.state == State.IDLE
    assert t.remaining_seconds == 1800


def test_start_from_idle_transitions_to_running():
    t = TimerState(duration_seconds=1800)
    t.start()
    assert t.state == State.RUNNING
    assert t.remaining_seconds == 1800


def test_pause_from_running_transitions_to_paused():
    t = TimerState(duration_seconds=1800)
    t.start()
    t.tick()
    t.pause()
    assert t.state == State.PAUSED
    assert t.remaining_seconds == 1799


def test_start_from_paused_resumes_running():
    t = TimerState(duration_seconds=1800)
    t.start()
    t.tick()
    t.pause()
    t.start()
    assert t.state == State.RUNNING
    assert t.remaining_seconds == 1799


def test_reset_returns_to_idle_with_full_remaining():
    t = TimerState(duration_seconds=1800)
    t.start()
    for _ in range(100):
        t.tick()
    t.reset()
    assert t.state == State.IDLE
    assert t.remaining_seconds == 1800


def test_tick_when_running_decrements_remaining():
    t = TimerState(duration_seconds=10)
    t.start()
    t.tick()
    assert t.remaining_seconds == 9


def test_tick_when_not_running_is_noop():
    t = TimerState(duration_seconds=10)
    t.tick()  # IDLE
    assert t.remaining_seconds == 10
    t.start()
    t.pause()
    t.tick()  # PAUSED
    assert t.remaining_seconds == 10


def test_tick_to_zero_transitions_to_finished():
    t = TimerState(duration_seconds=2)
    t.start()
    t.tick()
    assert t.state == State.RUNNING
    t.tick()
    assert t.state == State.FINISHED
    assert t.remaining_seconds == 0


def test_change_duration_while_idle_updates_remaining():
    t = TimerState(duration_seconds=1800)
    t.change_duration(2700)
    assert t.duration_seconds == 2700
    assert t.remaining_seconds == 2700
    assert t.state == State.IDLE


def test_change_duration_while_running_resets_and_restarts():
    t = TimerState(duration_seconds=1800)
    t.start()
    t.tick()
    t.change_duration(600)
    assert t.duration_seconds == 600
    assert t.remaining_seconds == 600
    assert t.state == State.RUNNING


def test_change_duration_while_paused_keeps_paused_with_new_remaining():
    t = TimerState(duration_seconds=1800)
    t.start()
    t.pause()
    t.change_duration(600)
    assert t.state == State.PAUSED
    assert t.remaining_seconds == 600


def test_dismiss_from_finished_pauses_at_zero():
    t = TimerState(duration_seconds=10)
    t.start()
    for _ in range(10):
        t.tick()
    assert t.state == State.FINISHED
    t.dismiss()
    assert t.state == State.PAUSED
    assert t.remaining_seconds == 0


def test_start_from_paused_at_zero_restarts_full_countdown():
    t = TimerState(duration_seconds=10)
    t.state = State.PAUSED
    t.remaining_seconds = 0
    t.start()
    assert t.state == State.RUNNING
    assert t.remaining_seconds == 10


def test_tick_after_finished_stays_at_zero_and_finished():
    """Calling tick() repeatedly after FINISHED must not underflow or change state."""
    t = TimerState(duration_seconds=2)
    t.start()
    t.tick()
    t.tick()
    assert t.state == State.FINISHED
    assert t.remaining_seconds == 0
    t.tick()
    t.tick()
    assert t.state == State.FINISHED
    assert t.remaining_seconds == 0


def test_start_from_finished_resets_remaining_and_runs():
    """start() from FINISHED restarts a fresh countdown (re-anchors remaining)."""
    t = TimerState(duration_seconds=5)
    t.start()
    for _ in range(5):
        t.tick()
    assert t.state == State.FINISHED
    t.start()
    assert t.state == State.RUNNING
    assert t.remaining_seconds == 5
