# Paused Reminder Label Design

**Date:** 2026-05-21
**Status:** Draft for user review

## Summary

Add a subtle desktop reminder for any paused timer state. The reminder is a small bottom-left label, not a full notification. It exists because the user often hides the Windows taskbar and may pause the timer for a short break, then forget to restart it when returning.

The existing full reminder overlay remains the time-up alert. After the user clicks that overlay, the timer becomes paused at `00:00`, so the same small paused label appears and can start the next countdown.

## Confirmed Decisions

| Decision | Choice |
|---|---|
| When to show | Any `PAUSED` state |
| Visual style | Minimal pill label, matching mockup option C |
| Placement | Bottom-left of the primary monitor work area |
| Interaction | Click the label to start or resume the countdown |
| Auto-dismiss | No auto-dismiss; it stays while paused |
| Time-up overlay | Keep the existing larger overlay for `FINISHED` |
| Text content | Show paused state and remaining time, for example `Timer paused 24:12` |

## Behaviour

The label is tied directly to timer state:

- `RUNNING`: no paused label.
- `PAUSED`: show the paused label.
- `FINISHED`: show the existing full reminder overlay, not the paused label.
- `IDLE`: no paused label.

Clicking the paused label calls the same start action as clicking the tray icon:

- If paused with remaining time above zero, it resumes from that remaining time.
- If paused at `00:00` after dismissing the time-up overlay, it starts a fresh full-duration countdown.
- Once the timer is running, the label disappears.

Duration changes follow existing timer behaviour:

- Changing duration while paused with remaining time keeps the timer paused and updates the label text to the new remaining time.
- Changing duration after a dismissed time-up reminder may start a new countdown through the existing `TimerState.change_duration()` behaviour; in that case the label disappears.

## Components

### `TimerState`

No new timer state is needed. The feature uses the existing `PAUSED` state and existing `start()` semantics.

### `standup_timer.StandUpApp`

`StandUpApp` owns the lifecycle of the paused label, similar to how it already tracks `_current_overlay`.

Responsibilities:

- Track the current paused label window.
- Reconcile the paused label whenever the timer state changes or the tray refreshes.
- Show the label when state is `PAUSED`.
- Destroy the label when state is not `PAUSED`.
- Handle label click by calling `timer.start()`, hiding the label, and refreshing the tray.
- Destroy the label on quit.

### `overlay.py`

The existing full reminder overlay stays as-is. Add a second overlay-style function for the paused label, or a small helper class if that keeps the geometry and drawing isolated.

The paused label should reuse the same work-area positioning helpers where practical, but use smaller dimensions and lighter visual weight:

- Small rounded pill.
- Semi-transparent dark fill.
- Subtle orange dot.
- Short text with remaining time.
- Topmost, borderless `tk.Toplevel`.
- Transparent sentinel background, matching the existing overlay approach.

## Data Flow

1. User pauses from the tray icon or hidden start/pause menu action.
2. `TimerState.pause()` transitions `RUNNING` to `PAUSED`.
3. `StandUpApp` refreshes UI state.
4. Paused label is shown at bottom-left.
5. User clicks the paused label.
6. `TimerState.start()` resumes or restarts depending on remaining time.
7. `StandUpApp` destroys the label and refreshes the tray icon/title.

For time-up:

1. Timer reaches zero and transitions to `FINISHED`.
2. Existing full reminder overlay appears.
3. User clicks the full reminder.
4. `TimerState.dismiss()` transitions to `PAUSED` with `remaining_seconds == 0`.
5. Paused label appears.
6. User clicks the paused label to start the next full countdown.

## Error Handling

If creating or destroying the paused label raises a `tk.TclError`, the app should log the exception and continue running. The timer state must remain authoritative even if the visual label fails.

If the label already exists when a paused refresh occurs, the app should update or recreate it rather than stacking multiple labels.

## Testing

Add tests around behaviour before implementation:

- Pausing a running timer schedules or shows the paused label.
- Starting from paused hides the paused label.
- Dismissing the finished overlay transitions to paused and shows the paused label.
- Clicking the paused label starts the timer and hides the label.
- Refreshing while still paused does not create duplicate labels.
- Overlay layout tests cover the compact label bounds and bottom-left positioning.

GUI tests should stay focused on pure helpers and app lifecycle hooks. Direct tkinter rendering remains manually verified.

## Out of Scope

- Multi-monitor support.
- Sound, flashing, or Windows toast notifications.
- User-configurable label text, color, opacity, or position.
- Snooze controls.
- Persisting paused/running state across app restarts.
