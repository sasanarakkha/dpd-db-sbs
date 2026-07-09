"""Unit tests for precommit_gate.py"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "kamma/improve/scripts/precommit_gate.py"


def _run_gate(*args: str) -> tuple[str, int]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)] + list(args),
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    return (
        result.stdout.strip() + "\n" + result.stderr.strip()
    ).strip(), result.returncode


def test_no_test_flag_fails():
    """Without --test, gate must fail with a clear message."""
    output, exit_code = _run_gate("kamma/improve/scripts/archive_check.py")
    assert exit_code != 0
    assert "--test" in output


def test_missing_file_fails():
    """Non-existent source file must produce FAIL."""
    output, exit_code = _run_gate(
        "nonexistent/file.py",
        "--test",
        "tests/kamma_tests/improve/test_archive_check.py",
    )
    assert exit_code != 0
    assert "not found" in output.lower()


def test_missing_test_file_fails():
    """Non-existent test file must produce FAIL."""
    output, exit_code = _run_gate(
        "kamma/improve/scripts/archive_check.py", "--test", "tests/nonexistent/test.py"
    )
    assert exit_code != 0
    assert "not found" in output.lower()


def test_no_source_files_fails():
    """Zero source files must produce FAIL."""
    output, exit_code = _run_gate()
    assert exit_code != 0
    assert "No source files" in output


def test_missing_test_flag_does_not_run_quality_tools():
    """Missing --test must fail before running ruff/pyright/pyrefly."""
    from kamma.improve.scripts import precommit_gate

    with (
        patch.object(
            sys, "argv", ["precommit_gate.py", "gui2/dps_process_corrections.py"]
        ),
        patch.object(precommit_gate, "_run") as run_tool,
        pytest.raises(SystemExit) as exc_info,
    ):
        precommit_gate.main()

    assert exc_info.value.code == 1
    run_tool.assert_not_called()
