#!/usr/bin/env python3

"""Robustly execute selective sync from upstream ref, applying run-specific exclusions."""

import argparse
import subprocess
from pathlib import Path

from kamma.upstream_sync.scripts.registry_helper import (
    get_modified_upstream_paths,
    get_strict_shadow_mappings,
    load_accepted_sync_state,
    load_registry,
)
from kamma.upstream_sync.scripts.sync_runtime import verify_manifest
from kamma.upstream_sync.scripts.sync_schema import validate_repo_relative_paths
from tools.printer import printer as pr


class GitError(Exception):
    """Custom error for Git operations."""


class GitContext:
    """Manage Git state and ensure recovery on failure."""

    def __init__(self):
        self.original_branch = self._get_current_branch()
        self.is_dirty = self._check_if_dirty()

    def _get_current_branch(self) -> str:
        """Get the current branch name."""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def _check_if_dirty(self) -> bool:
        """Check if the current working tree has uncommitted changes.

        Submodule-internal modifications and untracked files are ignored
        (``--ignore-submodules=dirty``): they cannot be cleaned by a
        superproject commit and are irrelevant to protecting uncommitted
        edits to upstream-tracked files. Gitlink (recorded-commit) changes
        are still reported.
        """
        result = subprocess.run(
            ["git", "status", "--porcelain", "--ignore-submodules=dirty"],
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())

    def restore_original_state(self):
        """Try to restore the repository to its original branch."""
        current = self._get_current_branch()
        if current != self.original_branch:
            pr.amber(f"Restoring to original branch: {self.original_branch}")
            subprocess.run(["git", "checkout", self.original_branch], check=False)


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    try:
        return subprocess.run(args, capture_output=True, text=True, check=check)
    except subprocess.CalledProcessError as e:
        pr.red(f"Git command failed: {' '.join(args)}")
        if e.stderr:
            pr.red(f"Error output: {e.stderr.strip()}")
        raise GitError(f"Command failed: {' '.join(args)}") from e


def get_protected_paths(run_exclusions: list[str] | None = None) -> set[str]:
    """Build the full protected set for the deletion pass from the registry."""
    registry = load_registry()
    protected: set[str] = set()
    protected.update(registry.no_sync_files)
    protected.update(get_modified_upstream_paths(registry))
    protected.update(get_strict_shadow_mappings(registry).keys())
    protected.update(registry.unique_paths)
    protected.update(registry.inspired_by_upstream.keys())
    if run_exclusions:
        protected.update(run_exclusions)
    return protected


def _is_protected(candidate: str, protected: set[str]) -> bool:
    """Return True if candidate equals or is nested under any protected entry."""
    if candidate in protected:
        return True
    candidate_path = Path(candidate)
    for entry in protected:
        entry_path = Path(entry)
        try:
            candidate_path.relative_to(entry_path)
            return True
        except ValueError:
            pass
    return False


def propagate_upstream_deletions(
    last_accepted_sha: str,
    target_sha: str,
    protected: set[str],
    repo_root: Path | None = None,
) -> None:
    """Remove worktree files that upstream deleted or renamed away since last_accepted_sha.

    Candidates come from git diff --no-renames --diff-filter=D, which decomposes renames into
    add+delete so renamed-away paths appear as deleted. Protected files are never removed.
    Removals are worktree-only (Path.unlink); the index is never touched.

    Raises SystemExit(1) if last_accepted_sha does not resolve in the object store.
    """
    cwd = repo_root  # None = subprocess uses process CWD

    # Guard missing base SHA before diffing
    check = subprocess.run(
        ["git", "cat-file", "-e", f"{last_accepted_sha}^{{commit}}"],
        capture_output=True,
        cwd=cwd,
        check=False,
    )
    if check.returncode != 0:
        pr.red(
            f"P0 deletion pass aborted: base SHA '{last_accepted_sha}' does not resolve "
            "in the object store. Verify accepted_sync.json or re-run git fetch upstream."
        )
        raise SystemExit(1)

    result = subprocess.run(
        [
            "git",
            "diff",
            "--no-renames",
            "--name-only",
            "--diff-filter=D",
            f"{last_accepted_sha}..{target_sha}",
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
        check=False,
    )
    if result.returncode != 0:
        pr.red(f"P0 deletion diff failed: {result.stderr.strip()}")
        raise SystemExit(1)

    candidates = [p for p in result.stdout.splitlines() if p.strip()]
    removed = 0
    for candidate in candidates:
        if _is_protected(candidate, protected):
            continue
        target = (repo_root / candidate) if repo_root else Path(candidate)
        if target.exists():
            target.unlink()
            pr.amber(f"  P0 removed: {candidate}")
            removed += 1

    pr.yes(
        f"P0 deletion pass: {removed} upstream-deleted file(s) removed from worktree"
    )


def get_permanent_exclusions() -> list[str]:
    """Load permanent exclusions from registry.json."""
    registry = load_registry()
    exclusions = get_modified_upstream_paths(registry)
    exclusions.extend(registry.no_sync_files)
    return validate_repo_relative_paths(exclusions, "permanent exclusions")


def get_run_specific_exclusions(thread_dir: str | None) -> list[str]:
    """Load run-specific exclusions from thread_dir/run_exclusions.txt."""
    if not thread_dir:
        return []

    exclusions_path = Path(thread_dir) / "run_exclusions.txt"
    if not exclusions_path.exists():
        return []

    exclusions = []
    with exclusions_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n\r")
            if line.strip() and not line.lstrip().startswith("#"):
                exclusions.append(line)
    return validate_repo_relative_paths(exclusions, "run-specific exclusions")


def run_sync_assertions(previous_sha: str) -> int:
    """Run lightweight post-sync assertions without leaving the Python workflow."""
    pr.green_title("post-sync assertions")

    pr.green(f"diff summary since {previous_sha}")
    diff_stat = run_git(["git", "diff", "--stat", previous_sha]).stdout.strip()
    if diff_stat:
        pr.cyan(diff_stat)
    else:
        pr.yes("no file changes")

    changed_files = [
        path
        for path in run_git(
            ["git", "diff", "--name-only", previous_sha]
        ).stdout.splitlines()
        if path.strip()
    ]
    pr.green("checking db schema changes")
    if "db/models.py" in changed_files:
        pr.amber(
            "db/models.py changed; verify SBS, Russian, Tamil, and Sinhala schema "
            "extensions during Stage 2."
        )
    else:
        pr.yes("no db/models.py change")

    new_files = [
        path
        for path in run_git(
            ["git", "diff", "--name-only", "--diff-filter=A", previous_sha]
        ).stdout.splitlines()
        if path.strip()
    ]
    new_templates = [path for path in new_files if "templates/" in path]

    pr.green("checking new upstream templates")
    if new_templates:
        pr.amber("new template files detected:")
        for path in new_templates:
            pr.amber(f"  {path}")
    else:
        pr.yes("no new templates")

    return 0


def execute_sync(
    thread_dir: str | None, dry_run: bool = False, stage: bool = False
) -> int:
    """Orchestrate the selective sync process."""
    pr.green_title("execute_sync.py")

    if not thread_dir:
        pr.red("Thread directory is required so prep_manifest.json can be verified.")
        return 1

    context = GitContext()
    if context.is_dirty:
        pr.red("Working tree is dirty. Commit or stash changes before sync.")
        return 1

    if context.original_branch != "sbs-ru":
        pr.red(
            f"Sync must start from sbs-ru, not {context.original_branch}. "
            "Switch branches before running execute_sync.py."
        )
        return 1

    try:
        # 1. Discover target ref
        pr.green("discovering target ref")
        state = load_accepted_sync_state()
        target_ref = state.last_accepted_upstream_ref
        run_git(["git", "fetch", "upstream"])
        target_sha = run_git(["git", "rev-parse", target_ref]).stdout.strip()
        pr.yes(f"{target_ref} -> {target_sha}")

        # 2. Verify manifest if thread_dir is provided
        if thread_dir:
            pr.green("verifying manifest")
            if (
                verify_manifest(
                    thread_dir,
                    accepted_sync_state=state,
                    target_sha=target_sha,
                    allow_discuss=False,
                    allow_blockers=False,
                )
                != 0
            ):
                pr.red("Manifest verification failed. Stop before checkout.")
                return 1
            else:
                pr.yes("ok")

        # 3. Gather exclusions
        pr.green("gathering exclusions")
        permanent = get_permanent_exclusions()
        run_specific = get_run_specific_exclusions(thread_dir)
        all_exclusions = sorted(set(permanent + run_specific))
        pr.yes(f"{len(all_exclusions)} paths")
        if run_specific:
            pr.green(f"Included {len(run_specific)} run-specific exclusions.")

        if dry_run:
            pr.green("Dry run: skipping actual git operations.")
            return 0

        # 4. Record original state and pin as_upstream without branch switching
        pr.green("recording original sbs-ru sha")
        sbs_ru_original_sha = run_git(["git", "rev-parse", "HEAD"]).stdout.strip()
        pr.yes(sbs_ru_original_sha)

        pr.green("updating as_upstream")
        run_git(["git", "update-ref", "refs/heads/as_upstream", target_sha])
        pr.yes("ok")

        # 5. Sync upstream-tracked paths into the current sbs-ru worktree (worktree only — leaves index unchanged so changes remain unstaged for review)
        pr.green("performing restore from as_upstream")
        run_git(["git", "restore", "--source", "as_upstream", "--worktree", "--", "."])
        pr.yes("ok")

        # 6. Restore excluded files
        pr.green("restoring excluded files")
        restored_count = 0
        removed_count = 0

        # Batch restore for existing files
        for path in all_exclusions:
            # Check if file existed in original sbs-ru state
            check_result = subprocess.run(
                ["git", "rev-parse", "--verify", f"{sbs_ru_original_sha}:{path}"],
                capture_output=True,
                check=False,
            )

            if check_result.returncode == 0:
                # File existed, restore it
                # If it is a directory, clean it first to remove untracked upstream additions
                if Path(path).is_dir():
                    run_git(["git", "clean", "-f", "-d", "--", path])

                run_git(
                    [
                        "git",
                        "restore",
                        "--source",
                        sbs_ru_original_sha,
                        "--staged",
                        "--worktree",
                        "--",
                        path,
                    ]
                )
                restored_count += 1
            else:
                # File did not exist in sbs-ru, if it exists now (from as_upstream), remove it
                if Path(path).exists():
                    run_git(
                        [
                            "git",
                            "rm",
                            "-r",
                            "--cached",
                            "--ignore-unmatch",
                            "--",
                            path,
                        ]
                    )
                    # If it's a directory, rm -rf
                    if Path(path).is_dir():
                        import shutil

                        shutil.rmtree(path)
                    else:
                        Path(path).unlink(missing_ok=True)
                    removed_count += 1

        pr.yes(f"restored {restored_count}, removed {removed_count}")

        # 6b. Propagate upstream deletions (files upstream removed/renamed since last sync)
        pr.green("propagating upstream deletions")
        protected = get_protected_paths(run_specific)
        propagate_upstream_deletions(
            last_accepted_sha=state.last_accepted_upstream_sha,
            target_sha=target_sha,
            protected=protected,
        )

        # 7. Optional staging
        if stage:
            pr.green("staging all changes")
            run_git(["git", "add", "."])
            pr.yes("ok")
        else:
            pr.amber("leaving changes unstaged; review before manual staging")

        # 8. Run assertions
        if run_sync_assertions(sbs_ru_original_sha) != 0:
            pr.red("Sync assertions failed. Check output above.")
            return 1

        pr.green("✅ Sync execution complete. Ready for Stage 2 (Analysis).")
        return 0

    except Exception as e:  # noqa: BLE001
        pr.red(f"Sync failed: {e}")
        context.restore_original_state()
        return 1


def main() -> int:
    """Parse CLI arguments and execute the sync."""
    parser = argparse.ArgumentParser(
        description="Execute selective sync from upstream."
    )
    parser.add_argument(
        "thread_dir", nargs="?", help="Path to the current sync thread directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without modifying the repository",
    )
    parser.add_argument(
        "--stage",
        action="store_true",
        help="Stage all sync changes after execution.",
    )

    args = parser.parse_args()
    return execute_sync(args.thread_dir, dry_run=args.dry_run, stage=args.stage)


if __name__ == "__main__":
    raise SystemExit(main())
