#!/usr/bin/env python3

"""Test that execute_sync propagates upstream deletions/renames to the worktree."""

import subprocess
from pathlib import Path

import pytest

from kamma.upstream_sync.scripts.execute_sync import propagate_upstream_deletions


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)


def _make_repo_with_two_upstream_commits(tmp_path: Path) -> tuple[Path, str, str]:
    """
    Build a minimal git repo with two upstream commits.

    Commit A (sha_a):
      - tools/foo.py          (plain upstream file — will be deleted in B)
      - tools/bar.py          (upstream file — will be renamed to baz in B)
      - protected/config.py   (in a no_sync directory 'protected/' — will be deleted upstream)

    Commit B (sha_b):
      - tools/baz.py          (bar renamed here; bar is absent = D under --no-renames)
      - protected/config.py   is ALSO deleted in commit B (to test prefix-aware protection)

    The worktree additionally has:
      - tools/foo.py          (present — should be removed by pass)
      - tools/bar.py          (present — should be removed by pass)
      - db/families/family_compound_ru.py   (shadow — should be preserved)
      - no_sync_file.txt      (no_sync entry — should be preserved)
      - modified_upstream.py  (modified_upstream entry — should be preserved)
      - protected/config.py   (under a protected directory entry — should be preserved)
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["git", "init"], cwd=repo)
    _git(["git", "config", "user.email", "test@test.com"], cwd=repo)
    _git(["git", "config", "user.name", "Test"], cwd=repo)
    _git(["git", "config", "diff.renames", "true"], cwd=repo)  # enable rename detection

    # Commit A
    (repo / "tools").mkdir()
    (repo / "tools" / "foo.py").write_text("# foo\n")
    (repo / "tools" / "bar.py").write_text("# bar\n")
    (repo / "protected").mkdir()
    (repo / "protected" / "config.py").write_text("# config\n")
    _git(["git", "add", "."], cwd=repo)
    _git(["git", "commit", "-m", "commit A"], cwd=repo)
    sha_a = _git(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

    # Commit B: delete foo.py, rename bar→baz (baz added, bar gone), delete protected/config.py
    _git(["git", "rm", "tools/foo.py", "tools/bar.py", "protected/config.py"], cwd=repo)
    # tools/ dir may be empty after rm — recreate before writing baz.py
    (repo / "tools").mkdir(exist_ok=True)
    (repo / "tools" / "baz.py").write_text("# baz\n")
    _git(["git", "add", "tools/baz.py"], cwd=repo)
    _git(["git", "commit", "-m", "commit B"], cwd=repo)
    sha_b = _git(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

    return repo, sha_a, sha_b


@pytest.fixture()
def sync_repo(tmp_path: Path) -> tuple[Path, str, str]:
    return _make_repo_with_two_upstream_commits(tmp_path)


def _setup_worktree(repo: Path) -> None:
    """Populate worktree as if execute_sync restore just ran (all upstream files present)."""
    # Upstream files present in worktree (as if restore ran from sha_b)
    (repo / "tools" / "foo.py").write_text("# foo\n")
    (repo / "tools" / "bar.py").write_text("# bar\n")
    # Protected / local files also present
    (repo / "db").mkdir(exist_ok=True)
    (repo / "db" / "families").mkdir(exist_ok=True)
    (repo / "db" / "families" / "family_compound_ru.py").write_text("# shadow\n")
    (repo / "no_sync_file.txt").write_text("no sync\n")
    (repo / "modified_upstream.py").write_text("# modified\n")
    (repo / "protected").mkdir(exist_ok=True)
    (repo / "protected" / "config.py").write_text("# config\n")


def _build_protected(repo: Path) -> set[str]:
    """Build the protected set covering shadows, no_sync, modified_upstream, and a directory."""
    return {
        "db/families/family_compound_ru.py",  # shadow
        "no_sync_file.txt",  # no_sync file
        "modified_upstream.py",  # modified_upstream entry
        "protected",  # directory entry — protects protected/config.py via prefix check
    }


def test_plain_deletion_removed(sync_repo: tuple[Path, str, str]) -> None:
    """upstream-deleted plain file (tools/foo.py) is removed from worktree."""
    repo, sha_a, sha_b = sync_repo
    _setup_worktree(repo)
    protected = _build_protected(repo)

    propagate_upstream_deletions(
        last_accepted_sha=sha_a,
        target_sha=sha_b,
        protected=protected,
        repo_root=repo,
    )

    assert not (repo / "tools" / "foo.py").exists(), "foo.py must be removed"


def test_renamed_away_removed(sync_repo: tuple[Path, str, str]) -> None:
    """upstream-renamed-away file (tools/bar.py) is removed; --no-renames ensures it."""
    repo, sha_a, sha_b = sync_repo
    _setup_worktree(repo)
    protected = _build_protected(repo)

    propagate_upstream_deletions(
        last_accepted_sha=sha_a,
        target_sha=sha_b,
        protected=protected,
        repo_root=repo,
    )

    assert not (repo / "tools" / "bar.py").exists(), (
        "bar.py (renamed away) must be removed"
    )


def test_shadow_preserved(sync_repo: tuple[Path, str, str]) -> None:
    """Local shadow file (family_compound_ru.py) is NOT removed."""
    repo, sha_a, sha_b = sync_repo
    _setup_worktree(repo)
    protected = _build_protected(repo)

    propagate_upstream_deletions(
        last_accepted_sha=sha_a,
        target_sha=sha_b,
        protected=protected,
        repo_root=repo,
    )

    assert (repo / "db" / "families" / "family_compound_ru.py").exists()


def test_no_sync_preserved(sync_repo: tuple[Path, str, str]) -> None:
    """no_sync file is NOT removed."""
    repo, sha_a, sha_b = sync_repo
    _setup_worktree(repo)
    protected = _build_protected(repo)

    propagate_upstream_deletions(
        last_accepted_sha=sha_a,
        target_sha=sha_b,
        protected=protected,
        repo_root=repo,
    )

    assert (repo / "no_sync_file.txt").exists()


def test_modified_upstream_preserved(sync_repo: tuple[Path, str, str]) -> None:
    """modified_upstream file is NOT removed."""
    repo, sha_a, sha_b = sync_repo
    _setup_worktree(repo)
    protected = _build_protected(repo)

    propagate_upstream_deletions(
        last_accepted_sha=sha_a,
        target_sha=sha_b,
        protected=protected,
        repo_root=repo,
    )

    assert (repo / "modified_upstream.py").exists()


def test_file_under_protected_directory_preserved(
    sync_repo: tuple[Path, str, str],
) -> None:
    """File under a protected directory entry is NOT removed (prefix-aware protection)."""
    repo, sha_a, sha_b = sync_repo
    _setup_worktree(repo)
    protected = _build_protected(repo)

    propagate_upstream_deletions(
        last_accepted_sha=sha_a,
        target_sha=sha_b,
        protected=protected,
        repo_root=repo,
    )

    assert (repo / "protected" / "config.py").exists(), (
        "protected/config.py must be preserved via directory prefix protection"
    )


def test_nothing_staged(sync_repo: tuple[Path, str, str]) -> None:
    """The deletion pass must not stage anything — index stays clean."""
    repo, sha_a, sha_b = sync_repo
    _setup_worktree(repo)
    protected = _build_protected(repo)

    # Stage the worktree files so there's a HEAD to diff against
    _git(["git", "add", "."], cwd=repo)
    _git(["git", "commit", "-m", "worktree snapshot"], cwd=repo)

    propagate_upstream_deletions(
        last_accepted_sha=sha_a,
        target_sha=sha_b,
        protected=protected,
        repo_root=repo,
    )

    # git diff --cached should show nothing (no staged changes)
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "", "nothing must be staged after deletion pass"


def test_missing_base_sha_aborts(sync_repo: tuple[Path, str, str]) -> None:
    """When the base SHA does not resolve, the pass aborts and removes nothing."""
    repo, sha_a, sha_b = sync_repo
    _setup_worktree(repo)
    protected = _build_protected(repo)

    bad_sha = "a" * 40

    with pytest.raises(SystemExit) as exc_info:
        propagate_upstream_deletions(
            last_accepted_sha=bad_sha,
            target_sha=sha_b,
            protected=protected,
            repo_root=repo,
        )

    assert exc_info.value.code != 0, "abort must exit non-zero"
    # Nothing should have been removed
    assert (repo / "tools" / "foo.py").exists(), "no files removed when base SHA is bad"
    assert (repo / "tools" / "bar.py").exists(), "no files removed when base SHA is bad"
