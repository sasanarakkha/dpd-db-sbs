#!/usr/bin/env python3

"""Provide command-line helpers for runtime sync metadata used by shell automation."""

import argparse
import sys

from kamma.upstream_sync.scripts.registry_helper import (
    get_prep_manifest_path,
    load_accepted_sync_state,
    load_prep_manifest,
    load_registry,
    get_modified_upstream_paths,
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


def verify_manifest(thread_dir: str) -> int:
    """Verify a prep manifest exists and is valid."""
    manifest_path = get_prep_manifest_path(thread_dir)
    try:
        manifest = load_prep_manifest(manifest_path)
        pr.info(f"Manifest verified: {manifest.get('to_upstream_sha', 'unknown')}")
        return 0
    except FileNotFoundError:
        pr.error(f"Manifest not found: {manifest_path}")
        return 1
    except ValueError as exc:
        pr.error(f"Manifest invalid: {exc}")
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

    pr.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
