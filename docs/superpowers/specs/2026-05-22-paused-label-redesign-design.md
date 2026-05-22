# Paused Label Redesign

**Date:** 2026-05-22
**Status:** Draft for user review

## Summary

Redesign the bottom-left paused label so its clickability and time meaning are immediately readable, without making the label visually heavier in a working environment.

The current label reads `Timer paused MM:SS` next to a small orange dot. Two issues drive the redesign:

1. **No click affordance.** The label looks like a passive notification; nothing communicates that clicking resumes the countdown.
2. **Ambiguous number.** `Timer paused 12:34` does not say whether `12:34` is remaining time, elapsed time, or the moment of pause.

The new label replaces the small orange dot with a circular orange play button, and shortens the text to just `MM:SS`. The play glyph carries the "click to resume" affordance, and by implication anchors the number as remaining countdown time. No instructional text is added; visual weight stays close to the current label.

Existing behaviour for lifecycle, positioning, click handling, and the time-up overlay is unchanged.

## Confirmed Decisions

| Decision | Choice |
|---|---|
| Affordance | Circular orange play button (filled), replacing the 7×7 orange dot |
| Text | `MM:SS` only — no `Timer paused`, no `剩`, no Chinese instruction line |
| Visual weight | Keep current dark pill panel, fill `#1b2227`, outline `#344148`, alpha 0.88 |
| Position | Bottom-left of primary monitor work area (unchanged) |
| Interaction | Click anywhere on the pill to resume (unchanged) |
| Update cadence | Per-second re-render while paused (unchanged) |
| Font | `LATIN_HANDWRITING_FONT_FAMILY`, size 10, normal (unchanged) |
| Out of scope | Hover state, animation, multi-monitor, language toggle |

## Visual Specification

The pill is structured left-to-right:

```
+----------------------------------+
|  ( ▶ )   12:34                   |
+----------------------------------+
```

- **Play button**: a 24×24 filled circle, fill `#f29a4a` (existing accent). Inside the circle, a right-pointing isoceles triangle drawn as a polygon, fill `#11181d` (matches the existing dark panel fill used for shadow tone). Triangle is sized to fit comfortably inside the circle (apex extends ~9 px horizontally from the vertical base; base is ~10 px tall). Optically centred: because a right-pointing triangle's geometric centre sits visually to the left of its perceived centre, nudge it 1 px right of geometric centre.
- **Time text**: `_format_mmss(remaining_seconds)` rendered with the existing `PAUSED_LABEL_FONT` and `PAUSED_LABEL_TEXT_FILL` (`#edf4f5`). No prefix, no suffix.
- **Spacing**: keep the current panel inset and panel radius. Increase `PAUSED_LABEL_DOT_LEFT_PADDING` slightly so the larger circle sits comfortably off the left edge (target: circle left edge ≈ 8 px inside the panel). Keep a gap of about 10 px between the circle's right edge and the text.
- **Pill width**: recompute via the existing `_compute_paused_label_layout` flow. Because the text shortens from `Timer paused 12:34` to `12:34`, the required width drops; the visible pill should shrink to fit the new content. Reduce `PAUSED_LABEL_MIN_WIDTH` so the pill is allowed to shrink (target minimum: around 96 px, enough to host the 24 px circle, gaps, paddings, and a five-character `MM:SS` even at maximum width).
- **Pill height**: increase `PAUSED_LABEL_HEIGHT` modestly to give the 24 px circle vertical breathing room (target: 40 → 44).

The dark pill panel, rounded corner radius (`PAUSED_LABEL_RADIUS = 13`), outline, and the transparent sentinel background colour all stay as today.

## Components

### `overlay.py`

Affected module. Changes are confined to the paused-label code paths; `show()` (the time-up overlay) is untouched.

Constant changes:

| Constant | Current | New |
|---|---|---|
| `PAUSED_LABEL_DOT_SIZE` | 7 | 24 |
| `PAUSED_LABEL_DOT_LEFT_PADDING` | 11 | 8 |
| `PAUSED_LABEL_DOT_TEXT_GAP` | 8 | 10 |
| `PAUSED_LABEL_TEXT_SAFETY_PADDING` | 28 | 0 (no longer needed once we control content) |
| `PAUSED_LABEL_TEXT_RIGHT_PADDING` | 11 | 14 |
| `PAUSED_LABEL_HEIGHT` | 40 | 44 |
| `PAUSED_LABEL_MIN_WIDTH` | 132 | 96 |

New constants:

- `PAUSED_LABEL_TRIANGLE_FILL = "#11181d"` — play glyph colour.
- `PAUSED_LABEL_TRIANGLE_WIDTH = 9` — horizontal extent (distance from vertical base to apex).
- `PAUSED_LABEL_TRIANGLE_HEIGHT = 10` — vertical extent (length of the vertical base).
- `PAUSED_LABEL_TRIANGLE_OPTICAL_NUDGE = 1` — pixels to shift right of geometric centre.

Drawing change in `_show_status_label`:

After the existing `canvas.create_oval(...)` for the dot (now a circle), add a `canvas.create_polygon(...)` for the play triangle. Triangle points are derived from `dot_bounds` and the constants above. Coordinates are integer-rounded.

Text change in `show_paused_label`:

Replace `text=f"Timer paused {_format_mmss(remaining_seconds)}"` with `text=_format_mmss(remaining_seconds)`. Keep the function signature and the caller contract.

`_compute_paused_label_layout` does not need structural changes — it already accepts the text dimensions from the caller and computes width from constants. The shorter text plus updated constants produce the new pill size automatically.

### `standup_timer.StandUpApp`

No changes. The paused label lifecycle (create on `PAUSED`, destroy on other states, click resumes the timer) is already handled and remains correct under the new visuals.

### `font_config`

No changes. The existing `LATIN_HANDWRITING_FONT_FAMILY` continues to render the `MM:SS` digits.

## Data Flow

Unchanged from the existing paused label feature:

1. User pauses (tray icon or hidden start/pause action).
2. `TimerState.pause()` → `PAUSED`.
3. `StandUpApp._sync_paused_label` creates a new label window via `overlay.show_paused_label(...)`.
4. Each tick re-renders the label so `MM:SS` stays current.
5. User clicks the label → `TimerState.start()` → `_destroy_paused_label` → tray refresh.

## Error Handling

Unchanged. `tk.TclError` during create or destroy is logged and the timer continues to operate from its authoritative state. The drawing changes are additive (one extra `create_polygon` call) and use the same canvas; no new failure modes are introduced.

## Testing

Existing tests for paused-label lifecycle and bottom-left positioning continue to apply.

Add or adjust layout tests for the new geometry:

- `_compute_paused_label_layout` returns a width that accommodates the new minimum (96 px) when text is the shortest plausible `00:00`.
- The computed `dot_bounds` is 24×24, vertically centred in the 44 px pill height.
- A helper for triangle coordinates (extracted if convenient) returns three integer points that fall inside the circle bounds for representative dot sizes.

Manual verification on Windows:

- Pause from the tray and confirm the pill shows a circular play button plus `MM:SS`, with no `Timer paused` text.
- Click the pill and confirm the countdown resumes.
- Trigger the time-up overlay, dismiss it, and confirm the new paused label appears at `00:00`. Click it and confirm a fresh countdown starts.
- Visually confirm the play triangle is centred (optically, not geometrically) inside the orange circle.

## Out of Scope

- Hover or pressed visual states for the play button.
- Animating the triangle (pulse, fade-in).
- Switching the paused label to Chinese or adding instructional text.
- Multi-monitor placement.
- Configurable label text, colour, opacity, or position.
- Changes to the time-up overlay (`overlay.show`).
- Changes to the tray icon, tooltip, or menu.
