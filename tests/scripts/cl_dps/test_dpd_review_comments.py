"""Structural tests for scripts/cl_dps/dpd-review-comments."""

import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "cl_dps" / "dpd-review-comments"


def test_bash_syntax() -> None:
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"bash syntax error:\n{result.stderr}"


def test_script_exists_and_is_executable() -> None:
    assert SCRIPT.exists()
    mode = SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/bin/bash")


def test_set_e() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "set -e" in content


def test_refs_corrections_review() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "dps_process_corrections.py" in content


def test_refs_additions_review() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "dps_process_additions.py" in content


def test_uses_ask_py() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "tools/ask.py" in content


def test_direct_ask_py_invocation() -> None:
    """Uses uv run tools/ask.py not uv run python ... tools/ask.py."""
    content = SCRIPT.read_text(encoding="utf-8")
    assert "uv run tools/ask.py" in content
    assert "uv run python " not in content


def test_uses_python3() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "uv run python3" in content


def test_has_project_root() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "PROJECT_ROOT" in content
