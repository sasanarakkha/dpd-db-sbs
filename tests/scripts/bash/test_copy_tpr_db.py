"""Structural golden-master tests for copy_tpr_db.sh.

Captured against current code, then verified after echo→ask.py conversion.
"""

import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "bash" / "copy_tpr_db.sh"


def test_script_exists_and_is_executable() -> None:
    assert SCRIPT.exists()
    mode = SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/bin/bash")


def test_path_anchored_via_dirname() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert 'dirname "$0"' in content


def test_source_variables_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "SRC_DB" in content
    assert "SRC_DPD_DIR" in content


def test_destination_variables_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "DEST_DB" in content
    assert "DEST_DPD_DIR" in content


def test_source_existence_check() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert '[ ! -f "$SRC_DB" ]' in content
    assert '[ ! -d "$SRC_DPD_DIR" ]' in content


def test_exit_on_missing_source() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.count("exit 1") >= 2


def test_error_messages_mention_missing_source() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Missing source file:" in content
    assert "Missing source folder:" in content


def test_success_messages_mention_copy() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "copied successfully" in content
    assert "replaced successfully" in content


def test_failure_messages_mention_failed() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.count("Failed to copy") == 2
