#!/usr/bin/env python3

"""Provide manifest-verification helpers imported by the sync scripts."""

from pathlib import Path

from kamma.upstream_sync.scripts.registry_helper import (
    get_prep_manifest_path,
    load_prep_manifest,
    read_line_list,
)
from kamma.upstream_sync.scripts.sync_schema import AcceptedSyncState
from tools.printer import printer as pr


def _load_acknowledged_blockers(thread_dir: str | Path) -> list[str]:
    """Load acknowledged blocker paths from thread_dir/run_acknowledged_blockers.txt."""
    return read_line_list(Path(thread_dir) / "run_acknowledged_blockers.txt")


def effective_blocker_paths(
    thread_dir: str | Path, blocker_paths: list[str]
) -> list[str]:
    """Return blocker_paths minus any acknowledged in run_acknowledged_blockers.txt."""
    acknowledged = set(_load_acknowledged_blockers(thread_dir))
    return [p for p in blocker_paths if p not in acknowledged]


def verify_manifest(
    thread_dir: str | Path,
    accepted_sync_state: AcceptedSyncState | None = None,
    target_sha: str | None = None,
    allow_discuss: bool = True,
    allow_blockers: bool = True,
) -> int:
    """Verify a prep manifest exists and is valid."""
    manifest_path = get_prep_manifest_path(thread_dir)
    try:
        manifest = load_prep_manifest(manifest_path)
        if accepted_sync_state is not None:
            if (
                manifest.from_upstream_sha
                != accepted_sync_state.last_accepted_upstream_sha
            ):
                pr.red(
                    "Manifest from_upstream_sha does not match accepted_sync.json: "
                    f"{manifest.from_upstream_sha} != {accepted_sync_state.last_accepted_upstream_sha}"
                )
                return 1
            if (
                manifest.target_upstream_ref
                != accepted_sync_state.last_accepted_upstream_ref
            ):
                pr.red(
                    "Manifest target_upstream_ref does not match accepted_sync.json: "
                    f"{manifest.target_upstream_ref} != {accepted_sync_state.last_accepted_upstream_ref}"
                )
                return 1
        if target_sha is not None and manifest.to_upstream_sha != target_sha:
            pr.red(
                "Manifest to_upstream_sha is stale for current target ref: "
                f"{manifest.to_upstream_sha} != {target_sha}"
            )
            return 1
        if not allow_discuss and manifest.discuss_paths:
            pr.red("Manifest contains discuss paths. Stop before automated pull:")
            for path in manifest.discuss_paths:
                pr.red(f"  {path}")
            return 1
        acknowledged = _load_acknowledged_blockers(thread_dir)
        blocker_set = set(manifest.blocker_paths)
        for path in acknowledged:
            if path not in blocker_set:
                pr.red(
                    f"Stale acknowledgment: '{path}' is not in manifest blocker_paths"
                )
                return 1
        for path in acknowledged:
            pr.amber(f"Acknowledged blocker (still present in manifest): {path}")
        effective_blockers = effective_blocker_paths(thread_dir, manifest.blocker_paths)
        if not allow_blockers and effective_blockers:
            pr.red("Manifest contains blocker paths. Resolve before automated pull:")
            for path in effective_blockers:
                pr.red(f"  {path}")
            return 1
        pr.green(f"Manifest verified: {manifest.to_upstream_sha}")
        return 0
    except FileNotFoundError:
        pr.red(f"Manifest not found: {manifest_path}")
        return 1
    except ValueError as exc:
        pr.red(f"Manifest invalid: {exc}")
        return 1
