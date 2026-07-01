"""Structural golden-master tests for scripts/cl_dps/dpd-makedict.

Invariant checks that pass against both old (inline while/echo) and new
(prompt_and_run/ask.py) versions of the script.
"""

import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "cl_dps" / "dpd-makedict"


def test_script_exists_and_is_executable() -> None:
    assert SCRIPT.exists()
    mode = SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/bin/bash")


def test_project_root_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "PROJECT_ROOT" in content


def test_master_script_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "MASTER_SCRIPT" in content
    assert "run_and_log.sh" in content


def test_log_base_name() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert 'LOG_BASE_NAME="make_dpd"' in content


def test_target_script_make_dpd() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "TARGET_SCRIPT_PATH" in content
    assert "make_dpd.sh" in content


def test_target_script_make_ru_dpd() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "TARGET_SCRIPT_PATH_RU" in content
    assert "make_ru_dpd.sh" in content


def test_target_script_copy_to_server() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "TARGET_SCRIPT_PATH_COPY" in content
    assert "copy_dpd_to_server.sh" in content


def test_target_script_distribute() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "TARGET_SCRIPT_PATH_COPY_TPR" in content
    assert "distribute.py" in content


def test_command_arrays_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "COMMAND_TO_EXECUTE" in content
    assert "COMMAND_TO_EXECUTE_RU" in content
    assert "COMMAND_TO_EXECUTE_COPY" in content
    assert "COMMAND_TO_EXECUTE_COPY_TPR" in content


def test_mnt_and_umnt_called() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "mnt" in content
    assert "umnt" in content
