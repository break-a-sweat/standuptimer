import standup_timer


def test_center_geometry_expands_to_custom_dialog_minimum():
    geometry = standup_timer._center_geometry(1920, 1080, 280, 140)
    assert geometry == "520x240+700+420"


def test_center_geometry_keeps_larger_requested_size():
    geometry = standup_timer._center_geometry(1920, 1080, 640, 300)
    assert geometry == "640x300+640+390"


def test_center_geometry_caps_size_to_small_screen():
    geometry = standup_timer._center_geometry(480, 320, 700, 500)
    assert geometry == "416x256+32+32"


def test_dialog_min_size_caps_to_small_screen():
    assert standup_timer._dialog_min_size(480, 320) == (416, 240)
    assert standup_timer._dialog_min_size(1920, 1080) == (520, 240)


def test_parse_duration_fields_treats_empty_values_as_zero():
    assert standup_timer._parse_duration_fields("", "5") == 5
    assert standup_timer._parse_duration_fields("2", "") == 120
    assert standup_timer._parse_duration_fields(" ", " ") == 0


def test_parse_duration_fields_rejects_invalid_numbers():
    try:
        standup_timer._parse_duration_fields("abc", "5")
    except ValueError as exc:
        assert str(exc) == "請輸入數字"
    else:
        raise AssertionError("expected ValueError")


def test_parse_duration_fields_rejects_seconds_outside_range():
    try:
        standup_timer._parse_duration_fields("0", "60")
    except ValueError as exc:
        assert str(exc) == "秒數需介於 0 到 59"
    else:
        raise AssertionError("expected ValueError")


def test_duration_preview_text_handles_empty_and_valid_inputs():
    assert standup_timer._duration_preview_text("", "5") == "將設定為 00:05"
    assert standup_timer._duration_preview_text("25", "") == "將設定為 25:00"
    assert standup_timer._duration_preview_text("", "") == "請輸入至少 1 秒"
