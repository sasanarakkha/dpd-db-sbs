"""Tests for copy_dpd_for_classes.safe_copy file/directory copy logic."""

from pathlib import Path

import pytest

from scripts.moving.copy_dpd_for_classes import safe_copy


def test_safe_copy_file_to_new_dest(tmp_path: Path) -> None:
    src = tmp_path / "src.db"
    src.write_text("db contents")
    dest = tmp_path / "dest.db"

    safe_copy(src, dest)

    assert dest.read_text() == "db contents"


def test_safe_copy_file_overwrites_existing_dest(tmp_path: Path) -> None:
    src = tmp_path / "src.db"
    src.write_text("new contents")
    dest = tmp_path / "dest.db"
    dest.write_text("old contents")

    safe_copy(src, dest)

    assert dest.read_text() == "new contents"


def test_safe_copy_dir_to_new_dest(tmp_path: Path) -> None:
    src = tmp_path / "src_dir"
    src.mkdir()
    (src / "file.txt").write_text("hello")
    dest = tmp_path / "dest_dir"

    safe_copy(src, dest)

    assert (dest / "file.txt").read_text() == "hello"


def test_safe_copy_dir_overwrites_existing_dest_dir(tmp_path: Path) -> None:
    src = tmp_path / "src_dir"
    src.mkdir()
    (src / "new.txt").write_text("new")
    dest = tmp_path / "dest_dir"
    dest.mkdir()
    (dest / "stale.txt").write_text("stale")

    safe_copy(src, dest)

    assert (dest / "new.txt").read_text() == "new"
    assert not (dest / "stale.txt").exists()


def test_safe_copy_logs_red_on_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "src.db"
    src.write_text("db contents")
    # dest's parent does not exist -> shutil.copy2 raises OSError
    dest = tmp_path / "missing_parent" / "dest.db"

    safe_copy(src, dest)

    captured = capsys.readouterr()
    assert "Failed to copy" in captured.out
    assert not dest.exists()
