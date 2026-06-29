"""Structural tests for copy_dpd_to_server.sh."""

import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "bash" / "copy_dpd_to_server.sh"


def test_script_exists_and_is_executable() -> None:
    assert SCRIPT.exists()
    assert SCRIPT.stat().st_mode & stat.S_IXUSR


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/bin/bash")


def test_no_hardcoded_home_path() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "$HOME" not in content


def test_ask_invoked_without_python() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "uv run tools/ask.py" in content
    assert "uv run python tools/ask.py" not in content


def test_distribute_invoked_with_python3() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "uv run python3 scripts/moving/distribute.py" in content


def test_both_copy_tasks_present() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "copy_dpdsbs_from_sbs2filesrv" in content
    assert "copy_rudpd_from_share2filesrv" in content
