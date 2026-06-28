"""Tests for pali_vocab_push.sh."""

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PALI_COURSE_PUSH = REPO_ROOT / "scripts" / "bash" / "pali_vocab_push.sh"

GENERATED_PATHS = "-- docs/generated/vocab docs/generated/abbreviations.md"


def write_fake_git(fake_bin: Path) -> None:
    """Write a fake git executable that records calls and returns controlled status."""
    fake_git = fake_bin / "git"
    fake_git.write_text(
        """#!/bin/sh
printf '%s\\n' "$*" >> "$GIT_LOG"
case "$*" in
  "diff --quiet"*)
    exit "$GIT_DIFF_EXIT"
    ;;
esac
exit 0
""",
    )
    fake_git.chmod(0o755)


def run_course_push(
    tmp_path: Path,
    *,
    diff_exit: int,
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    """Run the course push helper with fake git and return its command log."""
    home = tmp_path / "home"
    courses_dir = home / "Documents" / "dpd-pali-courses"
    courses_dir.mkdir(parents=True)

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    write_fake_git(fake_bin)

    git_log = tmp_path / "git.log"
    env = {
        **os.environ,
        "HOME": str(home),
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "GIT_LOG": str(git_log),
        "GIT_DIFF_EXIT": str(diff_exit),
    }

    result = subprocess.run(
        ["bash", str(PALI_COURSE_PUSH)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    git_commands = git_log.read_text().splitlines() if git_log.exists() else []
    return result, git_commands


def test_pali_course_push_commits_and_pushes_generated_changes(tmp_path: Path) -> None:
    """Generated course changes are staged, committed, and pushed."""
    result, git_commands = run_course_push(
        tmp_path,
        diff_exit=1,
    )

    assert result.returncode == 0, result.stderr
    assert git_commands == [
        f"status --short {GENERATED_PATHS}",
        f"diff --quiet {GENERATED_PATHS}",
        f"add {GENERATED_PATHS}",
        f"commit -m update pali course vocab {GENERATED_PATHS}",
        "push",
    ]


def test_pali_course_push_skips_clean_course_repo(tmp_path: Path) -> None:
    """A clean course repo should not create an empty commit or push."""
    result, git_commands = run_course_push(
        tmp_path,
        diff_exit=0,
    )

    assert result.returncode == 0, result.stderr
    assert git_commands == [
        f"status --short {GENERATED_PATHS}",
        f"diff --quiet {GENERATED_PATHS}",
    ]
