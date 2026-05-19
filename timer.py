from enum import Enum


class State(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


class TimerState:
    def __init__(self, duration_seconds: int):
        self.duration_seconds = duration_seconds
        self.remaining_seconds = duration_seconds
        self.state = State.IDLE

    def start(self) -> None:
        if self.state in (State.IDLE, State.PAUSED):
            self.state = State.RUNNING
        elif self.state == State.FINISHED:
            self.remaining_seconds = self.duration_seconds
            self.state = State.RUNNING

    def pause(self) -> None:
        if self.state == State.RUNNING:
            self.state = State.PAUSED

    def reset(self) -> None:
        self.state = State.IDLE
        self.remaining_seconds = self.duration_seconds

    def tick(self) -> None:
        if self.state != State.RUNNING:
            return
        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self.remaining_seconds = 0
            self.state = State.FINISHED

    def change_duration(self, seconds: int) -> None:
        self.duration_seconds = seconds
        self.remaining_seconds = seconds
        # state preservation:
        # IDLE -> stays IDLE, RUNNING -> stays RUNNING (restarts from full),
        # PAUSED -> stays PAUSED (new remaining), FINISHED -> goes back to IDLE
        if self.state == State.FINISHED:
            self.state = State.IDLE

    def dismiss(self) -> None:
        """Called when the user clicks the reminder overlay."""
        if self.state == State.FINISHED:
            self.state = State.IDLE
            self.remaining_seconds = self.duration_seconds
