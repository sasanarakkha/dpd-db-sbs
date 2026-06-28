"""Structural tests for upload_study_tools.sh.

Captured against unedited code, then augmented after echo→ask.py conversion.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "bash" / "upload_study_tools.sh"


def test_script_exists() -> None:
    assert SCRIPT.exists()


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/bin/bash")


def test_set_eu_present() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "set -eu" in content
    assert "set -u\n" not in content


def test_has_description_comment() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Create or append" in content


def test_no_echo_for_output() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("echo"):
            assert False, f"echo found on line: {stripped}"


def test_ask_used_for_all_messages() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.count("uv run tools/ask.py --print") == 5


def test_pipefail_present() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "set -o pipefail" in content


def test_targets_correct_repo() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "sasanarakkha/study-tools" in content


def test_asset_dir() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "temp/study_tools_release" in content


def test_calls_for_release_py() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "scripts/export/for_release.py" in content


def test_calls_gh_release_create() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "gh release create" in content


def test_calls_gh_release_upload() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "gh release upload" in content


def test_calls_gh_release_view() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "gh release view" in content


def test_calls_gh_release_list() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "gh release list" in content


def test_uses_draft_flag() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "--draft" in content


def test_uses_clobber_flag() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "--clobber" in content
