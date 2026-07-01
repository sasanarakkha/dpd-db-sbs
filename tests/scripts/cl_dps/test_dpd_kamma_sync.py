"""Structural golden-master tests for dpd-kamma-sync.

Captured against unedited code, then augmented after echo→ask.py conversion.
"""

import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "cl_dps" / "dpd-kamma-sync"


def test_script_exists_and_is_executable() -> None:
    assert SCRIPT.exists()
    mode = SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/bin/bash")


def test_set_euo_pipefail() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "set -euo pipefail" in content


def test_branch_guard_present() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "sbs-ru" in content
    assert "CURRENT_BRANCH" in content


def test_staged_changes_guard_present() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "git diff --cached" in content


def test_backup_script_path_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "BACKUP_SCRIPT" in content
    assert "db/backup_tsv/backup_dps.py" in content


def test_init_script_path_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "INIT_SCRIPT" in content
    assert "init_sync_thread.py" in content


def test_backup_files_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    for f in ["russian.tsv", "sbs.tsv", "tamil.tsv", "ru_roots.tsv"]:
        assert f in content


def test_backup_commit_message_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "BACKUP_COMMIT_MESSAGE" in content


def test_project_dir_uses_home_dpd_db() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "PROJECT_DIR" in content
    assert "Documents/dpd-db" in content


def test_file_existence_guard_count() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.count('-f "') == 2  # BACKUP_SCRIPT and INIT_SCRIPT


def test_uv_run_python3_usage() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "uv run python3" in content


def test_ask_used_for_all_output() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.count("uv run tools/ask.py") == 6


def test_ask_red_for_errors() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("uv run tools/ask.py --print -c red"):
            assert "Error:" in stripped


def test_ask_green_for_success() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "uv run tools/ask.py --print -c green" in content


def test_no_raw_echo_for_output() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("echo"):
            assert False, f"echo found on line: {stripped}"
