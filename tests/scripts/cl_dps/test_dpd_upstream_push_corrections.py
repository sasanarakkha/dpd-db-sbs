"""Structural tests for scripts/cl_dps/dpd-upstream-push-corrections."""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "cl_dps" / "dpd-upstream-push-corrections"


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


def test_has_confirmation_before_push() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "uv run tools/ask.py" in content
    assert "git push" in content
    push_line = [i for i, l in enumerate(content.splitlines()) if "git push" in l]
    ask_lines = [i for i, l in enumerate(content.splitlines()) if "tools/ask.py" in l]
    assert len(push_line) == 1
    assert any(a > push_line[0] for a in ask_lines), "ask.py not found after git push"


def test_clears_json_files() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "additions_deva.json" in content
    assert "corrections_deva.json" in content
    assert """echo '{}' >""" in content or "> gui2/data/additions_deva.json" in content
