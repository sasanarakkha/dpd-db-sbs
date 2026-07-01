"""Structural tests for scripts/cl_dps/dpd-anki."""

import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "cl_dps" / "dpd-anki"


def test_script_exists_and_is_executable() -> None:
    assert SCRIPT.exists()
    mode = SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/usr/bin/env bash")


def test_refs_run_and_log() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "run_and_log.sh" in content


def test_refs_dps_anki_updater() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "dps_anki_updater.py" in content


def test_refs_update_sbs_chants() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "update_sbs_chants_in_db.py" in content


def test_refs_sbs_consistency_tests() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "sbs_consistency_tests.py" in content


def test_aborts_on_test_failure() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "exit 1" in content
    assert "FAILED" in content or "failed" in content


def test_handles_test_feedback_field_prompt() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "test" in content
    assert "feedback" in content
