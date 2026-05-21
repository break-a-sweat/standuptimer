import os

from single_instance import release_instance, replace_existing_instance


def test_replace_existing_instance_terminates_old_pid_and_writes_current_pid(tmp_path):
    pid_file = tmp_path / "standuptimer.pid"
    pid_file.write_text("12345", encoding="utf-8")
    terminated = []

    replace_existing_instance(
        pid_file,
        current_pid=67890,
        terminate_pid=lambda pid: terminated.append(pid),
    )

    assert terminated == [12345]
    assert pid_file.read_text(encoding="utf-8") == "67890"


def test_replace_existing_instance_ignores_current_pid(tmp_path):
    pid_file = tmp_path / "standuptimer.pid"
    current_pid = os.getpid()
    pid_file.write_text(str(current_pid), encoding="utf-8")
    terminated = []

    replace_existing_instance(
        pid_file,
        current_pid=current_pid,
        terminate_pid=lambda pid: terminated.append(pid),
    )

    assert terminated == []
    assert pid_file.read_text(encoding="utf-8") == str(current_pid)


def test_replace_existing_instance_ignores_invalid_pid_file(tmp_path):
    pid_file = tmp_path / "standuptimer.pid"
    pid_file.write_text("not-a-pid", encoding="utf-8")
    terminated = []

    replace_existing_instance(
        pid_file,
        current_pid=67890,
        terminate_pid=lambda pid: terminated.append(pid),
    )

    assert terminated == []
    assert pid_file.read_text(encoding="utf-8") == "67890"


def test_release_instance_removes_pid_file_only_for_current_pid(tmp_path):
    pid_file = tmp_path / "standuptimer.pid"
    pid_file.write_text("67890", encoding="utf-8")

    release_instance(pid_file, current_pid=67890)

    assert not pid_file.exists()


def test_release_instance_keeps_pid_file_for_different_pid(tmp_path):
    pid_file = tmp_path / "standuptimer.pid"
    pid_file.write_text("11111", encoding="utf-8")

    release_instance(pid_file, current_pid=67890)

    assert pid_file.read_text(encoding="utf-8") == "11111"
