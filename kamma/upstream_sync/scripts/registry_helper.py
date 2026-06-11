#!/usr/bin/env python3

"""Shared helpers for loading sync registry and accepted upstream sync metadata."""

import json
from pathlib import Path

from kamma.upstream_sync.scripts.sync_schema import (
    AcceptedSyncState,
    PrepManifest,
    RegistryData,
)


def get_registry_path() -> Path:
    """Return the canonical path to registry.json."""
    return Path("kamma/upstream_sync/registry.json")


def get_accepted_sync_path() -> Path:
    """Return the canonical path to accepted_sync.json."""
    return Path("kamma/upstream_sync/accepted_sync.json")


def load_registry() -> RegistryData:
    """Load, validate, and return the registry as a typed RegistryData object."""
    path = get_registry_path()

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return RegistryData.from_raw(data)


def load_accepted_sync_state(path: Path | None = None) -> AcceptedSyncState:
    """Load and validate accepted upstream sync metadata."""
    sync_path = path or get_accepted_sync_path()
    if not sync_path.exists():
        raise FileNotFoundError(sync_path)

    with sync_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return AcceptedSyncState.from_raw(data)


def get_prep_manifest_path(thread_dir: Path | str) -> Path:
    """Return the canonical manifest path for a sync thread."""
    return Path(thread_dir) / "prep_manifest.json"


def load_prep_manifest(path: Path) -> PrepManifest:
    """Load and validate a Stage 1 prep manifest."""
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return PrepManifest.from_raw(data)


def build_accepted_sync_state(
    manifest: PrepManifest,
    upstream_commit_date: str,
    notes: str = "",
) -> AcceptedSyncState:
    """Build the next accepted sync state from a verified manifest."""
    if not upstream_commit_date.strip():
        raise ValueError("upstream commit date must be a non-empty string")

    return AcceptedSyncState(
        last_accepted_upstream_sha=manifest.to_upstream_sha,
        last_accepted_upstream_date=upstream_commit_date,
        last_accepted_upstream_ref=manifest.target_upstream_ref,
        notes=notes if notes else None,
    )


def write_accepted_sync_state(path: Path, state: AcceptedSyncState) -> None:
    """Write accepted sync state as canonical JSON."""
    path.write_text(json.dumps(state.to_json(), indent=2) + "\n", encoding="utf-8")


def get_modified_upstream_paths(registry: RegistryData) -> list[str]:
    """Extract path strings from modified_upstream_files."""
    return [entry.path for entry in registry.modified_upstream_files]


def get_inspired_by_upstream_paths(registry: RegistryData) -> list[str]:
    """Return the list of local paths in the inspired_by_upstream category."""
    return list(registry.inspired_by_upstream.keys())


def get_inspired_by_upstream_mapping(registry: RegistryData) -> dict[str, str]:
    """Return local_path -> upstream_path mapping for inspired entries."""
    return {
        local_path: entry.upstream
        for local_path, entry in registry.inspired_by_upstream.items()
    }


def get_strict_shadow_mappings(registry: RegistryData) -> dict[str, str]:
    """Return combined strict shadow mappings for every localized category."""
    return {
        **registry.russian_copies,
        **registry.sbs_copies,
        **registry.dps_copies,
        **registry.tamil_copies,
    }


def get_shadow_mappings_by_category(
    registry: RegistryData,
) -> dict[str, dict[str, str]]:
    """Return strict-shadow mappings grouped by logical category."""
    return {
        "russian_copies": registry.russian_copies,
        "sbs_copies": registry.sbs_copies,
        "dps_copies": registry.dps_copies,
        "tamil_copies": registry.tamil_copies,
    }


def get_skip_sync_patterns(registry: RegistryData) -> list[str]:
    """Return the list of patterns to skip during sync."""
    return registry.skip_sync_patterns


def get_no_sync_files(registry: RegistryData) -> list[str]:
    """Return the list of permanent no-sync infrastructure paths."""
    return registry.no_sync_files
