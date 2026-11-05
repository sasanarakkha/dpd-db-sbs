"""Unit tests for find_orphans in tests/test_shadow_cleanup.py (orphan selection logic)."""

import subprocess
from pathlib import Path

import pytest

from tests.test_shadow_cleanup import find_orphans, run_git


def _registry() -> dict[str, object]:
    return {
        "no_sync_files": ["kamma/"],
        "unique_paths": ["scripts/unique_tool.py"],
        "skip_sync_patterns": ["scripts/archive/", "*.pyc"],
        "russian_copies": {"scripts/a_ru.py": {"upstream": "scripts/a.py"}},
        "sbs_copies": {},
        "dps_copies": {"scripts/dpsdir/": {"upstream": "scripts/dpsorig/"}},
        "tamil_copies": {},
        "inspired_by_upstream": {
            "scripts/inspired.py": {"upstream": "scripts/orig.py"},
            "scripts/inspired_dir/": {"upstream": "scripts/orig_dir/"},
        },
    }


def test_skip_sync_prefix_is_not_orphan() -> None:
    assert find_orphans(["scripts/archive/old.py"], set(), _registry()) == []


def test_skip_sync_glob_is_not_orphan() -> None:
    assert find_orphans(["scripts/x.pyc"], set(), _registry()) == []


def test_inspired_by_upstream_key_is_not_orphan() -> None:
    assert find_orphans(["scripts/inspired.py"], set(), _registry()) == []


def test_file_under_inspired_dir_key_is_not_orphan() -> None:
    assert find_orphans(["scripts/inspired_dir/x.py"], set(), _registry()) == []


def test_shadow_dir_and_unique_are_not_orphans() -> None:
    files = ["scripts/dpsdir/x.py", "scripts/unique_tool.py", "scripts/a_ru.py"]
    assert find_orphans(files, set(), _registry()) == []


def test_unregistered_file_absent_from_upstream_is_orphan() -> None:
    assert find_orphans(["scripts/stray.py"], set(), _registry()) == [
        "scripts/stray.py"
    ]


def test_file_present_in_upstream_is_not_orphan() -> None:
    assert find_orphans(["scripts/up.py"], {"scripts/up.py"}, _registry()) == []


def test_run_git_returns_unquoted_non_ascii_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-ASCII tracked paths must come back unquoted so prefix exclusions match."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "scripts" / "archive").mkdir(parents=True)
    (tmp_path / "scripts" / "archive" / "kathā.py").write_text("# x\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)

    files = run_git(["ls-files", "--", "scripts/"])

    assert files == ["scripts/archive/kathā.py"]
    assert find_orphans(files, set(), _registry()) == []
