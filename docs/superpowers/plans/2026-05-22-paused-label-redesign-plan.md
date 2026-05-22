# Paused Label Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the bottom-left paused label so its click affordance and time meaning are immediately readable, by replacing the 7×7 orange dot with a 24×24 orange play button and shortening the text to just `MM:SS`.

**Architecture:** Pure visual + text change confined to `overlay.py`'s paused-label code path. Constants enlarge the affordance, a new polygon draw call adds the play triangle inside the existing oval, and the wrapping text becomes the bare `MM:SS` string. The time-up overlay, lifecycle management in `standup_timer.StandUpApp`, and click-to-resume behaviour are untouched.

**Tech Stack:** Python 3.10+, Tkinter, pytest

**Spec:** `docs/superpowers/specs/2026-05-22-paused-label-redesign-design.md`

---

### Task 1: Update size/padding constants for the new play button

**Files:**
- Modify: `overlay.py:33-46` (paused-label constants)
- Modify: `tests/test_overlay.py` (layout assertions for new dimensions)

- [ ] **Step 1: Write the failing test (constants update)**

Add a new test to `tests/test_overlay.py` that locks in the redesigned dimensions. Add the import for the new symbols first.

```python
# In tests/test_overlay.py, extend the existing import block
from overlay import (
    _compute_layout,
    _compute_paused_label_layout,
    _compute_position,
    _panel_bounds,
    ACCENT_COLOUR,
    CHINESE_HANDWRITING_FONT_FAMILY,
    HINT_LINE_FONT,
    LATIN_HANDWRITING_FONT_FAMILY,
    MARGIN,
    PAUSED_LABEL_DOT_LEFT_PADDING,
    PAUSED_LABEL_DOT_SIZE,
    PAUSED_LABEL_DOT_TEXT_GAP,
    PAUSED_LABEL_HEIGHT,
    PAUSED_LABEL_MIN_WIDTH,
    PAUSED_LABEL_DOT_FILL,
    PAUSED_LABEL_FONT,
    PAUSED_LABEL_TEXT_RIGHT_PADDING,
    PAUSED_LABEL_TEXT_SAFETY_PADDING,
    PANEL_INSET,
    PRIMARY_LINE_FONT,
    SECONDARY_LINE_FONT,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


def test_paused_label_constants_match_redesigned_play_button():
    assert PAUSED_LABEL_DOT_SIZE == 24
    assert PAUSED_LABEL_HEIGHT == 44
    assert PAUSED_LABEL_MIN_WIDTH == 96
    assert PAUSED_LABEL_DOT_LEFT_PADDING == 8
    assert PAUSED_LABEL_DOT_TEXT_GAP == 10
    assert PAUSED_LABEL_TEXT_RIGHT_PADDING == 14
    assert PAUSED_LABEL_TEXT_SAFETY_PADDING == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_overlay.py::test_paused_label_constants_match_redesigned_play_button -v`
Expected: FAIL with assertion errors (e.g. `assert 7 == 24`).

- [ ] **Step 3: Update the constants in overlay.py**

Replace lines 33-46 of `overlay.py`. Keep the existing colour and font constants; only the size/padding values change.

```python
PAUSED_LABEL_MIN_WIDTH = 96
PAUSED_LABEL_HEIGHT = 44
PAUSED_LABEL_PANEL_INSET = 3
PAUSED_LABEL_RADIUS = 13
PAUSED_LABEL_DOT_SIZE = 24
PAUSED_LABEL_DOT_LEFT_PADDING = 8
PAUSED_LABEL_DOT_TEXT_GAP = 10
PAUSED_LABEL_TEXT_SAFETY_PADDING = 0
PAUSED_LABEL_TEXT_RIGHT_PADDING = 14
PAUSED_LABEL_FONT = (LATIN_HANDWRITING_FONT_FAMILY, 10, "normal")
PAUSED_LABEL_FILL = "#1b2227"
PAUSED_LABEL_OUTLINE = "#344148"
PAUSED_LABEL_DOT_FILL = "#f29a4a"
PAUSED_LABEL_TEXT_FILL = "#edf4f5"
```

- [ ] **Step 4: Update the existing `test_paused_label_layout_is_compact` test**

The existing test at `tests/test_overlay.py:92-106` asserts `layout.text_width >= measured_text_width + PAUSED_LABEL_TEXT_SAFETY_PADDING`. With safety padding dropped to 0, also tighten the test to confirm the larger dot fits its new bounds.

Replace the existing function body:

```python
def test_paused_label_layout_is_compact():
    measured_text_width = 60  # roughly the width of "MM:SS" at size 10
    layout = _compute_paused_label_layout(
        work_area=(0, 0, 1920, 1040),
        text_width=measured_text_width,
        text_height=18,
    )

    assert layout.width >= PAUSED_LABEL_MIN_WIDTH
    assert layout.height == PAUSED_LABEL_HEIGHT
    assert layout.panel_bounds[0] >= 0
    assert layout.panel_bounds[2] <= layout.width
    dot_width = layout.dot_bounds[2] - layout.dot_bounds[0]
    dot_height = layout.dot_bounds[3] - layout.dot_bounds[1]
    assert dot_width == PAUSED_LABEL_DOT_SIZE
    assert dot_height == PAUSED_LABEL_DOT_SIZE
    assert layout.dot_bounds[0] > layout.panel_bounds[0]
    assert layout.text_x > layout.dot_bounds[2]
    assert layout.text_width >= measured_text_width
```

- [ ] **Step 5: Run the full overlay test file to verify nothing else broke**

Run: `pytest tests/test_overlay.py -v`
Expected: All tests PASS. (`test_paused_label_layout_keeps_handwriting_text_away_from_window_edges` still passes — with the new HEIGHT=44, `text_y = max(3, (44-23)//2) = 10`, satisfying `text_y >= 7` and `text_y + 23 <= 44 - 7 = 37`.)

- [ ] **Step 6: Commit**

```bash
git add overlay.py tests/test_overlay.py
git commit -m "$(cat <<'EOF'
refactor: enlarge paused-label affordance and trim safety padding

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Draw a play triangle inside the orange circle

**Files:**
- Modify: `overlay.py` (add constants, helper, drawing call)
- Modify: `tests/test_overlay.py` (helper test)

- [ ] **Step 1: Write the failing test for the triangle helper**

Add this test and import to `tests/test_overlay.py`:

```python
# Add to the import block
from overlay import (
    # ... existing imports ...
    _play_triangle_points,
    PAUSED_LABEL_TRIANGLE_FILL,
    PAUSED_LABEL_TRIANGLE_HEIGHT,
    PAUSED_LABEL_TRIANGLE_OPTICAL_NUDGE,
    PAUSED_LABEL_TRIANGLE_WIDTH,
)


def test_play_triangle_points_fit_inside_circle_and_nudge_right():
    dot_bounds = (10, 10, 34, 34)  # 24x24 circle at (10,10)
    points = _play_triangle_points(dot_bounds)

    assert len(points) == 6  # 3 (x, y) pairs
    xs = points[0::2]
    ys = points[1::2]

    circle_left, circle_top, circle_right, circle_bottom = dot_bounds
    for x, y in zip(xs, ys):
        assert circle_left <= x <= circle_right
        assert circle_top <= y <= circle_bottom

    # Right-pointing isoceles triangle: two points share the smaller x (vertical base),
    # one point sits at the larger x (apex).
    base_x = min(xs)
    apex_x = max(xs)
    assert xs.count(base_x) == 2
    assert xs.count(apex_x) == 1
    assert apex_x - base_x == PAUSED_LABEL_TRIANGLE_WIDTH

    # Base is shifted right of the circle's geometric centre by the optical nudge.
    circle_center_x = (circle_left + circle_right) // 2
    expected_base_x = (
        circle_center_x
        + PAUSED_LABEL_TRIANGLE_OPTICAL_NUDGE
        - (PAUSED_LABEL_TRIANGLE_WIDTH // 2)
    )
    assert base_x == expected_base_x

    # The two base points are vertically separated by TRIANGLE_HEIGHT and
    # mirrored around the circle's vertical centre.
    base_ys = sorted(y for x, y in zip(xs, ys) if x == base_x)
    assert base_ys[1] - base_ys[0] == PAUSED_LABEL_TRIANGLE_HEIGHT
    circle_center_y = (circle_top + circle_bottom) // 2
    assert (base_ys[0] + base_ys[1]) // 2 == circle_center_y

    # Apex sits on the circle's horizontal centreline.
    apex_y = next(y for x, y in zip(xs, ys) if x == apex_x)
    assert apex_y == circle_center_y
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_overlay.py::test_play_triangle_points_fit_inside_circle_and_nudge_right -v`
Expected: FAIL with `ImportError` / `AttributeError` on the new symbols.

- [ ] **Step 3: Add the triangle constants and helper to overlay.py**

Add the four new constants directly after the existing `PAUSED_LABEL_TEXT_FILL` line (~`overlay.py:46`):

```python
PAUSED_LABEL_TRIANGLE_FILL = "#11181d"
PAUSED_LABEL_TRIANGLE_WIDTH = 9
PAUSED_LABEL_TRIANGLE_HEIGHT = 10
PAUSED_LABEL_TRIANGLE_OPTICAL_NUDGE = 1
```

Then add the helper function. Place it near the other geometry helpers, just above `_compute_paused_label_layout` (~`overlay.py:189`):

```python
def _play_triangle_points(dot_bounds: tuple[int, int, int, int]) -> tuple[int, ...]:
    """Return polygon points for a right-pointing isoceles triangle, optically centred in dot_bounds."""
    circle_left, circle_top, circle_right, circle_bottom = dot_bounds
    circle_center_x = (circle_left + circle_right) // 2
    circle_center_y = (circle_top + circle_bottom) // 2
    geometric_center_x = circle_center_x + PAUSED_LABEL_TRIANGLE_OPTICAL_NUDGE
    half_width = PAUSED_LABEL_TRIANGLE_WIDTH // 2
    half_height = PAUSED_LABEL_TRIANGLE_HEIGHT // 2
    base_x = geometric_center_x - half_width
    apex_x = base_x + PAUSED_LABEL_TRIANGLE_WIDTH
    top_y = circle_center_y - half_height
    bottom_y = top_y + PAUSED_LABEL_TRIANGLE_HEIGHT
    return (
        base_x, top_y,
        base_x, bottom_y,
        apex_x, circle_center_y,
    )
```

Note: integer divisions are intentional — Tkinter accepts floats but using ints keeps the geometry deterministic and the test assertions clean. Vertical symmetry around `circle_center_y` holds because `PAUSED_LABEL_TRIANGLE_HEIGHT` is even (10); horizontal symmetry has a 0.5 px bias because `PAUSED_LABEL_TRIANGLE_WIDTH` is odd (9), which is invisible at this size and intentionally biases the apex one pixel further right of geometric centre — reinforcing the optical nudge.

- [ ] **Step 4: Run helper test to verify it passes**

Run: `pytest tests/test_overlay.py::test_play_triangle_points_fit_inside_circle_and_nudge_right -v`
Expected: PASS.

- [ ] **Step 5: Draw the triangle after the orange circle in `_show_status_label`**

In `overlay.py`, the current `_show_status_label` draws the circle at lines 285-289:

```python
    canvas.create_oval(
        *layout.dot_bounds,
        fill=PAUSED_LABEL_DOT_FILL,
        outline=PAUSED_LABEL_DOT_FILL,
    )
```

Add a `create_polygon` call immediately after, before the `create_text` call at line 290:

```python
    canvas.create_oval(
        *layout.dot_bounds,
        fill=PAUSED_LABEL_DOT_FILL,
        outline=PAUSED_LABEL_DOT_FILL,
    )
    canvas.create_polygon(
        _play_triangle_points(layout.dot_bounds),
        fill=PAUSED_LABEL_TRIANGLE_FILL,
        outline=PAUSED_LABEL_TRIANGLE_FILL,
    )
```

- [ ] **Step 6: Run the full overlay test suite**

Run: `pytest tests/test_overlay.py -v`
Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git add overlay.py tests/test_overlay.py
git commit -m "$(cat <<'EOF'
feat: draw play triangle inside paused-label affordance

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Drop the "Timer paused" prefix from the label text

**Files:**
- Modify: `overlay.py:424-433` (`show_paused_label`)
- Modify: `tests/test_overlay.py` (new behavioural test)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_overlay.py`. This test monkeypatches `_show_status_label` to capture what text it was called with, so we can assert the formatted string without rendering a real window.

```python
def test_show_paused_label_uses_bare_mmss_text(monkeypatch):
    captured = {}

    def fake_status_label(*, on_click, text, parent, destroy_before_callback=False):
        captured["text"] = text
        captured["on_click"] = on_click
        captured["parent"] = parent
        captured["destroy_before_callback"] = destroy_before_callback
        return object()

    monkeypatch.setattr(overlay, "_show_status_label", fake_status_label)

    sentinel_parent = object()
    overlay.show_paused_label(
        on_click=lambda: None,
        remaining_seconds=754,  # 12:34
        parent=sentinel_parent,
    )

    assert captured["text"] == "12:34"
    assert captured["parent"] is sentinel_parent
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_overlay.py::test_show_paused_label_uses_bare_mmss_text -v`
Expected: FAIL with `assert 'Timer paused 12:34' == '12:34'`.

- [ ] **Step 3: Strip the prefix in `show_paused_label`**

In `overlay.py:424-433`, change:

```python
def show_paused_label(
    on_click: Callable[[], None],
    remaining_seconds: int,
    parent: tk.Tk,
) -> tk.Toplevel:
    return _show_status_label(
        on_click=on_click,
        text=f"Timer paused {_format_mmss(remaining_seconds)}",
        parent=parent,
    )
```

to:

```python
def show_paused_label(
    on_click: Callable[[], None],
    remaining_seconds: int,
    parent: tk.Tk,
) -> tk.Toplevel:
    return _show_status_label(
        on_click=on_click,
        text=_format_mmss(remaining_seconds),
        parent=parent,
    )
```

- [ ] **Step 4: Run the new test to verify it passes**

Run: `pytest tests/test_overlay.py::test_show_paused_label_uses_bare_mmss_text -v`
Expected: PASS.

- [ ] **Step 5: Run the full test suite**

Run: `pytest -v`
Expected: All tests PASS. App-behaviour tests already stub `show_paused_label` rather than introspecting its text argument, so they remain unaffected.

- [ ] **Step 6: Commit**

```bash
git add overlay.py tests/test_overlay.py
git commit -m "$(cat <<'EOF'
refactor: drop 'Timer paused' prefix from paused label text

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Manual verification on Windows

**Files:** None modified. This task confirms the rendered result matches the spec.

- [ ] **Step 1: Launch the app**

Run: `python standup_timer.py`
Expected: The tray icon appears.

- [ ] **Step 2: Pause the timer from the tray**

Click the tray icon to trigger the default `開始/暫停` action while the timer is running.
Expected: The bottom-left pill appears.

- [ ] **Step 3: Verify visual against the spec**

Check each spec requirement:
- Left side shows a 24×24 solid orange circle (`#f29a4a`).
- A dark right-pointing triangle (`#11181d`) sits inside the circle, optically centred (a hair right of geometric centre).
- The text to the right of the circle is just `MM:SS` (no `Timer paused`, no Chinese instruction, no `剩`).
- The dark pill panel fill (`#1b2227`) and outline (`#344148`) are unchanged from before.
- The pill is shorter than the previous version (because text shrank).
- The pill sits at the bottom-left of the primary monitor work area with the same margin as before.

- [ ] **Step 4: Verify click behaviour**

Click the pill.
Expected: The countdown resumes and the pill disappears. The tray icon's `MM:SS` label continues counting down.

- [ ] **Step 5: Verify the time-up flow still uses the larger overlay**

Set a short duration (e.g. 1 second via `自訂時間`), let it expire.
Expected: The full reminder overlay (`站起來動一動` + `已坐 …` + `點一下暫停提醒`) appears — not the compact pill. Click to dismiss.
After dismiss: The compact paused pill appears at `00:00`. Click it to start a fresh countdown.

- [ ] **Step 6: Quit and stop**

Right-click tray icon → `退出`.

No commit — this task is verification only. If any check fails, return to the earlier task that produced the regression.

---

## Self-Review Notes

- **Spec coverage**: every Confirmed Decision in the spec maps to a step above. Constants table → Task 1. Triangle geometry + drawing → Task 2. Text simplification → Task 3. Manual visuals + click + finished overlay flow → Task 4.
- **Lifecycle and click behaviour**: spec confirms `StandUpApp` does not change. Task 4 step 4 verifies the existing click-to-resume path still works.
- **Out-of-scope items** (hover state, animation, language toggle, multi-monitor) are not in any task — correct.
- **Symbol consistency**: `PAUSED_LABEL_TRIANGLE_*` and `_play_triangle_points` are used identically in Tasks 2 and the helper test.
