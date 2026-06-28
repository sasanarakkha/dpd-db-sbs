"""Unit tests for archive_check.py"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "kamma/improve/scripts/archive_check.py"


def _run_archive_check(file_path: str) -> tuple[dict[str, Any], int]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), file_path],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    return json.loads(result.stdout), result.returncode


def test_json_shape():
    """Output must include all required keys with correct types."""
    data, exit_code = _run_archive_check("gui2/dps_process_corrections.py")
    assert exit_code == 0
    assert isinstance(data["file"], str)
    assert isinstance(data["docstring"], str)
    assert isinstance(data["size_lines"], int)
    assert isinstance(data["callers"], list)
    assert isinstance(data["in_registry"], bool)
    assert isinstance(data["registry_category"], str)
    assert isinstance(data["has_test"], bool)
    assert isinstance(data["has_entrypoint"], bool)
    assert isinstance(data["imports_from_repo"], list)


def test_missing_file():
    """Non-existent file must return error and exit 1."""
    data, exit_code = _run_archive_check("nonexistent/script.py")
    assert exit_code == 1
    assert "error" in data


def test_real_script_docstring():
    """A known script must return its module docstring."""
    data, _ = _run_archive_check("gui2/dps_process_corrections.py")
    assert "review correction comments" in data["docstring"].lower()


def test_real_script_size():
    """A known script must have a positive line count."""
    data, _ = _run_archive_check("gui2/dps_process_corrections.py")
    assert data["size_lines"] > 0


def test_registry_status_uses_repo_relative_paths():
    """Registry lookup must match repo-relative paths."""
    data, _ = _run_archive_check("gui2/dps_process_corrections.py")
    assert data["in_registry"] is True
    assert data["registry_category"] == "unique_paths"


def test_test_detection_uses_repo_relative_paths():
    """Mirrored tests under tests/ must be detected."""
    data, _ = _run_archive_check("scripts/moving/distribute.py")
    assert data["has_test"] is True


def test_has_entrypoint_true():
    """A script with __main__ guard must report has_entrypoint: true."""
    data, _ = _run_archive_check("gui2/dps_process_corrections.py")
    assert data["has_entrypoint"] is True


def test_no_entrypoint():
    """A module with no __main__ guard must report has_entrypoint: false."""
    data, _ = _run_archive_check("db/models.py")
    assert data["has_entrypoint"] is False


def test_imports_from_repo():
    """imports_from_repo must list local modules."""
    data, _ = _run_archive_check("gui2/dps_process_corrections.py")
    assert "tools" in data["imports_from_repo"]


def test_callers_is_list():
    """callers must always be a list (potentially empty)."""
    data, _ = _run_archive_check("gui2/dps_process_corrections.py")
    assert isinstance(data["callers"], list)
