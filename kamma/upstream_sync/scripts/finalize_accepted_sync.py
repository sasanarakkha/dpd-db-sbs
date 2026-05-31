#!/usr/bin/env python3

"""Advance accepted upstream sync metadata from a verified prep manifest."""

import argparse
import subprocess
from pathlib import Path

from kamma.upstream_sync.scripts.registry_helper import (
    build_accepted_sync_state,
    get_accepted_sync_path,
    get_prep_manifest_path,
    load_prep_manifest,
    write_accepted_sync_state,
)
from kamma.upstream_sync.scripts.sync_runtime import verify_manifest
from tools.printer import printer as pr


def resolve_commit_date(commit_sha: str) -> str:
    """Resolve the upstream commit date for the accepted target SHA."""
    result = subprocess.run(
        ["git", "show", "-s", "--format=%cI", commit_sha],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def finalize_accepted_sync(thread_dir: str, state_path: Path, notes: str) -> int:
    """Verify the prep manifest, then advance accepted upstream sync metadata."""
    pr.green_title("finalize_accepted_sync.py")
    pr.green("verifying prep manifest")
    if verify_manifest(thread_dir, allow_discuss=False) != 0:
        pr.red("Manifest verification failed. accepted_sync.json was not updated.")
        return 1
    pr.yes("ok")

    manifest_path = get_prep_manifest_path(thread_dir)

    pr.green("loading prep manifest")
    manifest = load_prep_manifest(manifest_path)
    pr.yes("ok")

    pr.green("resolving upstream date")
    commit_date = resolve_commit_date(str(manifest["to_upstream_sha"]))
    pr.yes("ok")

    pr.green("writing accepted sync")
    state = build_accepted_sync_state(
        manifest=manifest,
        upstream_commit_date=commit_date,
        notes=notes,
    )
    write_accepted_sync_state(state_path, state)
    pr.yes("ok")
    return 0


def main() -> int:
    """Parse arguments and update accepted sync metadata from a thread manifest."""
    parser = argparse.ArgumentParser()
    parser.add_argument("thread_dir")
    parser.add_argument("--notes", default="Accepted after Stage 3 verification.")
    parser.add_argument(
        "--state-path",
        default=str(get_accepted_sync_path()),
    )
    args = parser.parse_args()

    return finalize_accepted_sync(
        thread_dir=args.thread_dir,
        state_path=Path(args.state_path),
        notes=args.notes,
    )


if __name__ == "__main__":
    raise SystemExit(main())
