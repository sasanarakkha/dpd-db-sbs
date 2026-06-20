#!/usr/bin/env python3

"""Derive whether a Stage 1 prep manifest touches nothing localized, enabling the Stage 1 -> Stage 5 fast-path."""

import json
import sys
from pathlib import Path

from tools.printer import printer as pr

LOCALIZED_CATEGORIES = {
    "modified_upstream_files",
    "russian_copies",
    "sbs_copies",
    "dps_copies",
    "tamil_copies",
    "inspired_by_upstream",
}

NONEMPTY_BLOCKER_FIELDS = (
    "discuss_paths",
    "needs_classification_paths",
    "blocker_paths",
    "unregistered_local_paths",
    "upstream_deleted_orphans",
)


def is_localized_noop(manifest: dict[str, object]) -> bool:
    """Return True iff the manifest's upstream range touches nothing localized."""
    mapped_actions = manifest.get("mapped_actions", {})
    if isinstance(mapped_actions, dict):
        for actions in mapped_actions.values():
            if not isinstance(actions, list):
                continue
            for action in actions:
                if (
                    isinstance(action, dict)
                    and action.get("category") in LOCALIZED_CATEGORIES
                ):
                    return False

    for field in NONEMPTY_BLOCKER_FIELDS:
        if manifest.get(field):
            return False

    changed_upstream_paths = manifest.get("changed_upstream_paths", [])
    if isinstance(changed_upstream_paths, list):
        for path in changed_upstream_paths:
            if isinstance(path, str) and path.startswith("docs/"):
                return False

    return True


def main() -> None:
    pr.tic()
    pr.green_title("sync_triage.py")

    if len(sys.argv) != 2:
        pr.red("Usage: sync_triage.py <thread_dir>")
        sys.exit(1)

    manifest_path = Path(sys.argv[1]) / "prep_manifest.json"
    if not manifest_path.exists():
        pr.red(f"Manifest not found at {manifest_path}")
        sys.exit(1)

    manifest: dict[str, object] = json.loads(manifest_path.read_text(encoding="utf-8"))

    if is_localized_noop(manifest):
        pr.summary("verdict", "fast-path: no localized impact in this upstream range")
        pr.toc()
        sys.exit(0)
    else:
        pr.summary("verdict", "no fast-path: localized impact detected, run Stages 2-4")
        pr.toc()
        sys.exit(1)


if __name__ == "__main__":
    main()
