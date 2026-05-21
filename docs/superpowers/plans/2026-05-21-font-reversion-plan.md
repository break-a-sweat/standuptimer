# Font Reversion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Revert custom handwriting fonts to system-safe "Microsoft JhengHei UI" to prevent font-missing issues.

**Architecture:** Pure UI aesthetic update changing constants and `font=` parameters in TKinter components.

**Tech Stack:** Python, TKinter, pytest

---

### Task 1: Update Overlay Fonts

**Files:**
- Modify: `overlay.py`
- Modify: `tests/test_overlay.py`

- [ ] **Step 1: Write the failing test**

```python
# In tests/test_overlay.py
# Modify the existing test `test_overlay_fonts_use_handwriting_family`
def test_overlay_fonts_use_handwriting_family():
    assert LATIN_HANDWRITING_FONT_FAMILY == "Segoe Print"
    assert CHINESE_HANDWRITING_FONT_FAMILY == "Microsoft JhengHei UI"
    assert PRIMARY_LINE_FONT[0] == CHINESE_HANDWRITING_FONT_FAMILY
    assert SECONDARY_LINE_FONT[0] == CHINESE_HANDWRITING_FONT_FAMILY
    assert HINT_LINE_FONT[0] == CHINESE_HANDWRITING_FONT_FAMILY
    assert PAUSED_LABEL_FONT[0] == LATIN_HANDWRITING_FONT_FAMILY
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_overlay.py::test_overlay_fonts_use_handwriting_family -v`
Expected: FAIL due to assertion error ("少女手寫體" != "Microsoft JhengHei UI")

- [ ] **Step 3: Write minimal implementation**

```python
# In overlay.py
# Update the constant
CHINESE_HANDWRITING_FONT_FAMILY = "Microsoft JhengHei UI"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_overlay.py::test_overlay_fonts_use_handwriting_family -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add overlay.py tests/test_overlay.py
git commit -m "style: revert overlay fonts to system-safe Microsoft JhengHei UI"
```

---

### Task 2: Update Custom Time Dialog Fonts

**Files:**
- Modify: `standup_timer.py`

- [ ] **Step 1: Write minimal implementation (Visual/UI update)**

```python
# In standup_timer.py
# Find occurrences of "少女手寫體" and change them back to "Microsoft JhengHei UI"
# Replace at line ~191:
        ttk.Label(
            main,
            text="設定倒數時長",
            font=("Microsoft JhengHei UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

# Replace at line ~237:
        ttk.Label(
            preview_frame,
            textvariable=preview_var,
            font=("Microsoft JhengHei UI", 13, "bold"),
            anchor="center",
            justify="center",
            wraplength=150,
        ).grid(row=0, column=0, sticky="ew", pady=(8, 10))
```

- [ ] **Step 2: Run test to verify app behavior is intact**

Run: `pytest tests/test_app_behavior.py -v`
Expected: PASS (confirming the dialog updates didn't break core app test coverage)

- [ ] **Step 3: Commit**

```bash
git add standup_timer.py
git commit -m "style: revert dialog fonts to system-safe Microsoft JhengHei UI"
```
