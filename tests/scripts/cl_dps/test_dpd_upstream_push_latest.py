"""Structural tests for scripts/cl_dps/dpd-upstream-push-latest."""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "cl_dps" / "dpd-upstream-push-latest"


def test_bash_syntax() -> None:
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"bash syntax error:\n{result.stderr}"


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/usr/bin/env bash")


def test_uses_ask_not_echo() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    echo_lines = [
        l.strip()
        for l in content.splitlines()
        if l.strip().startswith("echo ") and ">" not in l
    ]
    assert len(echo_lines) == 0, f"found echo terminal statements: {echo_lines}"
    assert "uv run tools/ask.py" in content


def test_handles_as_upstream_check() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert '"$CURRENT_BRANCH" == "as_upstream"' in content


def test_handles_empty_commit() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "FILES[@] -eq 0" in content or "${#FILES[@]}" in content


def test_handles_deleted_files() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "git cat-file -e" in content


def test_has_confirmation_before_push() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    push_line = [i for i, l in enumerate(content.splitlines()) if "git push" in l]
    ask_lines = [i for i, l in enumerate(content.splitlines()) if "tools/ask.py" in l]
    assert len(push_line) == 1
    assert any(a > push_line[0] for a in ask_lines), "ask.py not found after git push"


def test_returns_to_original_branch() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert (
        'git checkout "$CURRENT_BRANCH"' in content
        or "git checkout $CURRENT_BRANCH" in content
    )
