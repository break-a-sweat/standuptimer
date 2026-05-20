import standup_timer


def test_center_geometry_expands_to_custom_dialog_minimum():
    geometry = standup_timer._center_geometry(1920, 1080, 280, 140)
    assert geometry == "520x190+700+445"


def test_center_geometry_keeps_larger_requested_size():
    geometry = standup_timer._center_geometry(1920, 1080, 640, 300)
    assert geometry == "640x300+640+390"
