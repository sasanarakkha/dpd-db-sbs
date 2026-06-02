"""Tests for deck update shell helper behavior."""

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
UPDATE_DECKS = REPO_ROOT / "scripts" / "bash" / "update_decks.sh"
PALI_COURSE_PUSH = REPO_ROOT / "scripts" / "bash" / "pali_vocab_push.sh"


def write_fake_git(fake_bin: Path) -> None:
    """Write a fake git executable that records calls and returns controlled status."""
    fake_git = fake_bin / "git"
    fake_git.write_text(
        """#!/bin/sh
printf '%s\\n' "$*" >> "$GIT_LOG"
case "$*" in
  "status --porcelain"*)
    printf '%s' "$GIT_STATUS_OUTPUT"
    ;;
  "diff --cached --quiet"*)
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
    status_output: str,
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
        "GIT_STATUS_OUTPUT": status_output,
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


def test_update_decks_uses_pali_course_push_helper() -> None:
    """The vocab branch must push courses changes without leaving dpd-db."""
    script = UPDATE_DECKS.read_text()
    helper_call = 'bash "$PROJECT_DIR/scripts/bash/pali_vocab_push.sh"'
    vocab_prompt = '"need to push vocab for classes?"'
    grammar_prompt = '"need to make updated grammar.csv?"'

    assert "git-push" not in script
    assert helper_call in script
    assert script.index(vocab_prompt) < script.index(helper_call)
    assert script.index(helper_call) < script.index(grammar_prompt)
    assert (
        'cd "$PROJECT_DIR"'
        in script[script.index(helper_call) : script.index(grammar_prompt)]
    )


def test_pali_course_push_commits_and_pushes_generated_changes(tmp_path: Path) -> None:
    """Generated course changes are staged, committed, and pushed."""
    generated_paths = "-- docs/generated/vocab docs/generated/abbreviations.md"
    result, git_commands = run_course_push(
        tmp_path,
        status_output=" M vocab/class-02.md\n?? vocab/index.md\n",
        diff_exit=1,
    )

    assert result.returncode == 0, result.stderr
    assert git_commands == [
        f"status --porcelain {generated_paths}",
        f"status --short {generated_paths}",
        f"add {generated_paths}",
        f"diff --cached --quiet {generated_paths}",
        f"commit -m update pali course vocab {generated_paths}",
        "push",
    ]


def test_pali_course_push_skips_clean_course_repo(tmp_path: Path) -> None:
    """A clean course repo should not create an empty commit or push."""
    generated_paths = "-- docs/generated/vocab docs/generated/abbreviations.md"
    result, git_commands = run_course_push(
        tmp_path,
        status_output="",
        diff_exit=0,
    )

    assert result.returncode == 0, result.stderr
    assert git_commands == [f"status --porcelain {generated_paths}"]
    assert "No generated vocab changes to push." in result.stdout


def test_patimokkha_download_clears_inherited_virtual_env() -> None:
    """Cross-project uv runs should not warn about the dpd-db virtualenv."""
    script = UPDATE_DECKS.read_text()
    assert "env -u VIRTUAL_ENV uv run bash scripts/download_patimokkha.sh" in script
