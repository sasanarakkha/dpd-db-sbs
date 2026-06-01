#!/usr/bin/env python3
"""Check whether strict shadow copies were updated when their upstream sources changed."""

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from kamma.upstream_sync.scripts.registry_helper import get_shadow_mappings_by_category
from kamma.upstream_sync.scripts.sync_schema import (
    FULL_SHA_RE,
    validate_repo_relative_paths,
)
from tools.printer import printer as pr

REGISTRY_PATH = Path("kamma/upstream_sync/registry.json")
NOOP_LEDGER_PATH = Path("kamma/upstream_sync/reviewed_shadow_noops.json")


@dataclass(frozen=True)
class ReviewedShadowNoop:
    """A reviewed upstream shadow change that intentionally needs no local edit."""

    sync_commit: str
    source: str
    shadow: str
    changed_paths: frozenset[str]
    reason: str


def get_modified_files(command: list[str]) -> set[str]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return set(filter(None, result.stdout.split("\n")))


def get_last_sync_commit() -> str:
    result = subprocess.run(
        [
            "git",
            "log",
            "--grep=#sync: upstream pull",
            "--format=%H",
            "-n",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        match = FULL_SHA_RE.match(result.stdout.strip())
        if match:
            return result.stdout.strip()
    return "HEAD^"


def require_string(entry: dict[str, object], field: str, label: str) -> str:
    """Read a required non-empty string field from a no-op ledger entry."""
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: field '{field}' must be a non-empty string")
    return value


def require_string_list(entry: dict[str, object], field: str, label: str) -> list[str]:
    """Read a required non-empty string list field from a no-op ledger entry."""
    value = entry.get(field)
    if not isinstance(value, list):
        raise ValueError(f"{label}: field '{field}' must be a list")

    paths: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"{label}: field '{field}[{index}]' must be a non-empty string"
            )
        paths.append(item)

    if not paths:
        raise ValueError(f"{label}: field '{field}' must not be empty")
    if len(set(paths)) != len(paths):
        raise ValueError(f"{label}: field '{field}' must not contain duplicates")
    return paths


def load_reviewed_shadow_noops(
    path: Path = NOOP_LEDGER_PATH,
) -> list[ReviewedShadowNoop]:
    """Load and validate reviewed shadow no-op entries."""
    if not path.exists():
        return []

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("reviewed shadow no-op ledger must be a JSON list")

    noops: list[ReviewedShadowNoop] = []
    seen: set[tuple[str, str, str, frozenset[str]]] = set()
    for index, item in enumerate(raw):
        label = f"reviewed_shadow_noops[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{label}: entry must be an object")

        entry: dict[str, object] = item
        sync_commit = require_string(entry, "sync_commit", label)
        source = require_string(entry, "source", label)
        shadow = require_string(entry, "shadow", label)
        changed_paths = frozenset(require_string_list(entry, "changed_paths", label))
        reason = require_string(entry, "reason", label)
        if not FULL_SHA_RE.fullmatch(sync_commit):
            raise ValueError(
                f"{label}: field 'sync_commit' must be a full 40-character lowercase git SHA"
            )
        validate_repo_relative_paths([source], f"{label}.source")
        validate_repo_relative_paths([shadow], f"{label}.shadow")
        validate_repo_relative_paths(
            list(changed_paths),
            f"{label}.changed_paths",
        )

        key = (sync_commit, source, shadow, changed_paths)
        if key in seen:
            raise ValueError(f"{label}: duplicate reviewed no-op entry")
        seen.add(key)

        noops.append(
            ReviewedShadowNoop(
                sync_commit=sync_commit,
                source=source,
                shadow=shadow,
                changed_paths=changed_paths,
                reason=reason,
            )
        )
    return noops


def is_reviewed_noop(
    noops: list[ReviewedShadowNoop],
    sync_commit: str,
    source: str,
    shadow: str,
    changed_paths: list[str],
) -> bool:
    """Return True only when a reviewed no-op exactly matches this warning."""
    changed_path_set = frozenset(changed_paths)
    return any(
        noop.sync_commit == sync_commit
        and noop.source == source
        and noop.shadow == shadow
        and noop.changed_paths == changed_path_set
        for noop in noops
    )


def check_shadows() -> None:
    if not REGISTRY_PATH.exists():
        pr.red(f"Error: Registry not found at {REGISTRY_PATH}")
        sys.exit(1)

    registry: dict[str, object] = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    try:
        reviewed_noops = load_reviewed_shadow_noops(NOOP_LEDGER_PATH)
    except ValueError as exc:
        pr.red(f"Error: {NOOP_LEDGER_PATH}: {exc}")
        sys.exit(1)

    sync_commit = get_last_sync_commit()
    pr.green(f"Checking modifications relative to sync commit: {sync_commit}")

    # 1. Upstream sources modified in the sync commit
    upstream_modified = get_modified_files(
        ["git", "show", "--name-only", "--format=", sync_commit]
    )

    # 2. Shadows modified since the sync commit (including uncommitted)
    local_modified = get_modified_files(
        ["git", "diff", f"{sync_commit}^", "--name-only"]
    )

    all_mappings: list[tuple[str, str, str]] = []
    category_labels = {
        "russian_copies": "Russian",
        "sbs_copies": "SBS",
        "dps_copies": "DPS",
        "tamil_copies": "Tamil",
    }
    for category, mappings in get_shadow_mappings_by_category(registry).items():
        for shadow, source in mappings.items():
            all_mappings.append((category_labels[category], shadow, source))

    unmodified_shadows = []

    for category, shadow, source in all_mappings:
        # Determine if source was modified
        modified_source_files = []
        if source.endswith("/"):
            for uf in upstream_modified:
                if uf.startswith(source):
                    modified_source_files.append(uf)
        else:
            if source in upstream_modified:
                modified_source_files.append(source)

        if modified_source_files:
            # Check if any corresponding shadow was modified
            shadow_is_modified = False
            if shadow.endswith("/"):
                for lf in local_modified:
                    if lf.startswith(shadow):
                        shadow_is_modified = True
                        break
            else:
                if shadow in local_modified:
                    shadow_is_modified = True

            if not shadow_is_modified and not is_reviewed_noop(
                reviewed_noops,
                sync_commit=sync_commit,
                source=source,
                shadow=shadow,
                changed_paths=modified_source_files,
            ):
                unmodified_shadows.append(
                    {
                        "category": category,
                        "source": source,
                        "shadow": shadow,
                        "details": modified_source_files,
                    }
                )

    if unmodified_shadows:
        pr.red(
            "WARNING: The following upstream sources were modified, but their shadow copies have NOT been updated:"
        )
        for item in unmodified_shadows:
            pr.amber(f"  [{item['category']}]")
            pr.amber(f"  Source: {item['source']}")
            pr.amber(f"  Shadow: {item['shadow']}")
            pr.amber("  Modified upstream files in this path:")
            for f in item["details"][:10]:
                pr.amber(f"    - {f}")
            if len(item["details"]) > 10:
                pr.amber(f"    - ... and {len(item['details']) - 10} more")

        pr.red(f"Total missing shadow updates: {len(unmodified_shadows)}")
        sys.exit(1)
    else:
        pr.green(
            "SUCCESS: All shadow copies of modified upstream sources have been updated."
        )
        sys.exit(0)


if __name__ == "__main__":
    check_shadows()
