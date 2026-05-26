from pathlib import Path

import font_config


def test_user_font_loader_registers_installed_lxgw_wenkai_font(monkeypatch, tmp_path):
    installed_font = (
        tmp_path
        / "Microsoft"
        / "Windows"
        / "Fonts"
        / "LXGWWenKaiTC-Regular.ttf"
    )
    installed_font.parent.mkdir(parents=True)
    installed_font.write_bytes(b"font")
    calls = []

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(font_config, "_resource_root", lambda: tmp_path / "app", raising=False)
    monkeypatch.setattr(font_config, "_add_font_resource", lambda path: calls.append(path) or 1)

    assert font_config.load_user_fonts() == (installed_font,)
    assert calls == [installed_font]


def test_font_loader_prefers_bundled_lxgw_wenkai_font(monkeypatch, tmp_path):
    bundled_font = (
        tmp_path
        / "assets"
        / "fonts"
        / "LXGWWenKaiTC-Regular.ttf"
    )
    bundled_font.parent.mkdir(parents=True)
    bundled_font.write_bytes(b"font")
    installed_font = (
        tmp_path
        / "Microsoft"
        / "Windows"
        / "Fonts"
        / "LXGWWenKaiTC-Regular.ttf"
    )
    installed_font.parent.mkdir(parents=True)
    installed_font.write_bytes(b"font")
    calls = []

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(font_config, "_resource_root", lambda: tmp_path, raising=False)
    monkeypatch.setattr(font_config, "_add_font_resource", lambda path: calls.append(path) or 1)

    assert font_config.load_user_fonts() == (bundled_font,)
    assert calls == [bundled_font]


def test_user_font_loader_ignores_missing_font(monkeypatch, tmp_path):
    calls = []

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(font_config, "_resource_root", lambda: tmp_path, raising=False)
    monkeypatch.setattr(font_config, "_add_font_resource", lambda path: calls.append(path) or 1)

    assert font_config.load_user_fonts() == ()
    assert calls == []
