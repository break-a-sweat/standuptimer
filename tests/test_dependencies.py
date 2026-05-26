from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _requirement_lines(path: str) -> list[str]:
    return [
        line.strip()
        for line in (ROOT / path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def test_runtime_requirements_only_contain_app_dependencies():
    requirements = _requirement_lines("requirements.txt")

    assert requirements == ["pystray==0.19.5", "Pillow==10.4.0"]


def test_dev_requirements_extend_runtime_dependencies():
    requirements = _requirement_lines("requirements-dev.txt")

    assert "-r requirements.txt" in requirements
    assert "pytest==8.3.3" in requirements
    assert any(line.startswith("pyinstaller==") for line in requirements)
