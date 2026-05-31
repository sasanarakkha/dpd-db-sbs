#!/usr/bin/env python3

"""Robustly execute selective sync from upstream ref, applying run-specific exclusions."""

import argparse
import subprocess
from collections.abc import Iterable
from pathlib import Path, PurePosixPath

from kamma.upstream_sync.scripts.registry_helper import (
    get_modified_upstream_paths,
    load_accepted_sync_state,
    load_registry,
)
from kamma.upstream_sync.scripts.sync_runtime import verify_manifest
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
        """Check if the current working tree has uncommitted changes."""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
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


def validate_repo_relative_paths(paths: Iterable[str], label: str) -> list[str]:
    """Validate git pathspecs that may later be restored or removed."""
    validated: list[str] = []
    for index, path in enumerate(paths):
        item_label = f"{label}[{index}]"
        if not path.strip():
            raise ValueError(f"{item_label} must be a non-empty path")
        if path != path.strip():
            raise ValueError(f"{item_label} must not contain surrounding whitespace")
        if "\\" in path:
            raise ValueError(f"{item_label} must use forward slashes")
        posix_path = PurePosixPath(path)
        if posix_path.is_absolute() or path.startswith("~"):
            raise ValueError(f"{item_label} must be a repo-relative path")
        if ".." in posix_path.parts:
            raise ValueError(f"{item_label} must stay inside the repository")
        validated.append(path)
    return validated


def get_permanent_exclusions() -> list[str]:
    """Load permanent exclusions from registry.json."""
    registry = load_registry()
    no_sync_files = registry.get("no_sync_files", [])
    exclusions = get_modified_upstream_paths(registry)
    if isinstance(no_sync_files, list):
        exclusions.extend(path for path in no_sync_files if isinstance(path, str))
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
            line = line.strip()
            if line and not line.startswith("#"):
                exclusions.append(line)
    return validate_repo_relative_paths(exclusions, "run-specific exclusions")


def execute_sync(thread_dir: str | None, dry_run: bool = False) -> int:
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
        target_ref = state["last_accepted_upstream_ref"]
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
        all_exclusions = sorted(list(set(permanent + run_specific)))
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

        # 5. Sync upstream-tracked paths into the current sbs-ru worktree
        pr.green("performing checkout from as_upstream")
        run_git(["git", "checkout", "as_upstream", "--", "."])
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
                run_git(
                    [
                        "git",
                        "restore",
                        "--source",
                        sbs_ru_original_sha,
                        "--staged",
                        "--worktree",
                        path,
                    ]
                )
                restored_count += 1
            else:
                # File did not exist in sbs-ru, if it exists now (from as_upstream), remove it
                if Path(path).exists():
                    run_git(["git", "rm", "-r", "--cached", "--ignore-unmatch", path])
                    # If it's a directory, rm -rf
                    if Path(path).is_dir():
                        import shutil

                        shutil.rmtree(path)
                    else:
                        Path(path).unlink(missing_ok=True)
                    removed_count += 1

        pr.yes(f"restored {restored_count}, removed {removed_count}")

        # 7. Final staging
        pr.green("staging all changes")
        run_git(["git", "add", "."])
        pr.yes("ok")

        # 8. Run assertions
        assertions_script = Path("scripts/bash/dpd-sync-assertions.sh")
        if assertions_script.exists():
            pr.green("running sync assertions")
            try:
                subprocess.run(
                    ["bash", str(assertions_script), sbs_ru_original_sha], check=True
                )
                pr.yes("ok")
            except subprocess.CalledProcessError:
                pr.red("Sync assertions failed. Check output above.")
                return 1

        pr.green("✅ Sync execution complete. Ready for Stage 2 (Analysis).")
        return 0

    except Exception as e:
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

    args = parser.parse_args()
    return execute_sync(args.thread_dir, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
