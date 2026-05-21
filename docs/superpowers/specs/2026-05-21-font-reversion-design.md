# Font Reversion Design

## Purpose
To ensure visual stability and prevent font-missing issues across different Windows environments by strictly using built-in, system-safe fonts. We are reverting custom or handwriting Chinese fonts back to "Microsoft JhengHei UI".

## Architecture & Data Flow
This is a purely aesthetic change modifying presentation constants and TKinter UI configuration. No architectural or logical data flows are altered.

## Component Changes

### 1. Overlay Display (`overlay.py`)
- The constant `CHINESE_HANDWRITING_FONT_FAMILY` will be updated from its current value ("少女手寫體") to **"Microsoft JhengHei UI"**.
- `LATIN_HANDWRITING_FONT_FAMILY` will remain **"Segoe Print"** to preserve the casual feel for numbers and English text where supported.

### 2. Custom Time Dialog (`standup_timer.py`)
- All occurrences of the font tuple explicitly specifying "少女手寫體" for labels and preview text will be reverted to **"Microsoft JhengHei UI"**.

### 3. Testing (`tests/test_overlay.py`)
- The test suite `test_overlay_fonts_use_handwriting_family` will be updated to assert that `CHINESE_HANDWRITING_FONT_FAMILY` is equal to "Microsoft JhengHei UI".

## Error Handling
No new error handling is required. Reverting to universally available system fonts intrinsically removes the potential errors associated with missing fonts.

## Testing Strategy
- Run `pytest` to ensure all tests, particularly those validating overlay constants, pass successfully.
- Verify UI logic loads correctly without missing font exceptions.
