#!/usr/bin/env python3

"""Provide command-line helpers for runtime sync metadata used by shell automation."""

import argparse
import sys

from kamma.upstream_sync.scripts.registry_helper import (
    AcceptedSyncState,
    get_prep_manifest_path,
    get_modified_upstream_paths,
    load_accepted_sync_state,
    load_prep_manifest,
    load_registry,
)
from kamma.upstream_sync.scripts.sync_schema import (
    AcceptedSyncState as AcceptedSyncStateSchema,
)
from tools.printer import printer as pr


def print_exclusions() -> int:
    """Print newline-delimited paths that must be restored after automated sync."""
    registry = load_registry()
    no_sync_files = registry.get("no_sync_files", [])
    exclusions = get_modified_upstream_paths(registry)
    if isinstance(no_sync_files, list):
        exclusions.extend(path for path in no_sync_files if isinstance(path, str))

    for path in exclusions:
        sys.stdout.write(f"{path}\n")
    return 0


def print_target_ref() -> int:
    """Print the upstream ref used by the current accepted sync state."""
    state = load_accepted_sync_state()
    sys.stdout.write(f"{state['last_accepted_upstream_ref']}\n")
    return 0


def verify_manifest(
    thread_dir: str,
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
            expected_state = AcceptedSyncStateSchema.from_raw(accepted_sync_state)
            expected_from_sha = expected_state.last_accepted_upstream_sha
            expected_ref = expected_state.last_accepted_upstream_ref
            if manifest["from_upstream_sha"] != expected_from_sha:
                pr.red(
                    "Manifest from_upstream_sha does not match accepted_sync.json: "
                    f"{manifest['from_upstream_sha']} != {expected_from_sha}"
                )
                return 1
            if manifest["target_upstream_ref"] != expected_ref:
                pr.red(
                    "Manifest target_upstream_ref does not match accepted_sync.json: "
                    f"{manifest['target_upstream_ref']} != {expected_ref}"
                )
                return 1
        if target_sha is not None and manifest["to_upstream_sha"] != target_sha:
            pr.red(
                "Manifest to_upstream_sha is stale for current target ref: "
                f"{manifest['to_upstream_sha']} != {target_sha}"
            )
            return 1
        discuss_paths = manifest["discuss_paths"]
        if not isinstance(discuss_paths, list):
            pr.red("Manifest invalid: discuss_paths must be a list")
            return 1
        if not allow_discuss and discuss_paths:
            pr.red("Manifest contains discuss paths. Stop before automated pull:")
            for path in discuss_paths:
                pr.red(f"  {path}")
            return 1
        blocker_paths = manifest["blocker_paths"]
        if not isinstance(blocker_paths, list):
            pr.red("Manifest invalid: blocker_paths must be a list")
            return 1
        if not allow_blockers and blocker_paths:
            pr.red("Manifest contains blocker paths. Resolve before automated pull:")
            for path in blocker_paths:
                pr.red(f"  {path}")
            return 1
        pr.green(f"Manifest verified: {manifest.get('to_upstream_sha', 'unknown')}")
        return 0
    except FileNotFoundError:
        pr.red(f"Manifest not found: {manifest_path}")
        return 1
    except ValueError as exc:
        pr.red(f"Manifest invalid: {exc}")
        return 1


def main() -> int:
    """Parse CLI arguments and execute the requested runtime helper."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("print-exclusions")
    subparsers.add_parser("print-target-ref")

    verify_parser = subparsers.add_parser("verify-manifest")
    verify_parser.add_argument("thread_dir", help="Path to the sync thread directory")

    args = parser.parse_args()

    if args.command == "print-exclusions":
        return print_exclusions()
    if args.command == "print-target-ref":
        return print_target_ref()
    if args.command == "verify-manifest":
        return verify_manifest(args.thread_dir)

    pr.red(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
