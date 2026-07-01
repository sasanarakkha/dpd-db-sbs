"""Structural tests for scripts/cl_dps/decks."""

import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "cl_dps" / "decks"


def test_script_exists_and_is_executable() -> None:
    assert SCRIPT.exists()
    mode = SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/bin/bash")


def test_set_e() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "set -euo pipefail" in content


def test_refs_update_decks() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "update_decks.sh" in content


def test_uses_ask_py() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "tools/ask.py" in content


def test_direct_ask_py_invocation() -> None:
    """Uses uv run tools/ask.py not uv run python ... tools/ask.py."""
    content = SCRIPT.read_text(encoding="utf-8")
    assert "uv run tools/ask.py" in content
    assert "uv run python" not in content


def test_aborts_on_q() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    count = content.count("|| exit 1")
    assert count >= 2, f"expected at least 2 '|| exit 1' guards, found {count}"


def test_refs_mnt_and_umnt() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "mnt" in content
    assert "umnt" in content


def test_has_project_dir() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "PROJECT_DIR" in content or "PROJECT_ROOT" in content
