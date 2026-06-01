#!/usr/bin/env python3

"""Shared helpers for loading sync registry and accepted upstream sync metadata."""

import json
from pathlib import Path

from kamma.upstream_sync.scripts.sync_schema import (
    AcceptedSyncState as AcceptedSyncStateSchema,
)
from kamma.upstream_sync.scripts.sync_schema import PrepManifest as PrepManifestSchema
from kamma.upstream_sync.scripts.sync_schema import RegistryData


type AcceptedSyncState = dict[str, str]
type PrepManifest = dict[str, object]


def get_registry_path() -> Path:
    """Return the canonical path to registry.json."""
    return Path("kamma/upstream_sync/registry.json")


def get_accepted_sync_path() -> Path:
    """Return the canonical path to accepted_sync.json."""
    return Path("kamma/upstream_sync/accepted_sync.json")


def load_registry() -> dict[str, object]:
    """Load, validate, and return the registry as a dict."""
    path = get_registry_path()

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    RegistryData.from_raw(data)
    return data  # type: ignore[no-any-return]


def load_accepted_sync_state(path: Path | None = None) -> AcceptedSyncState:
    """Load and validate accepted upstream sync metadata."""
    sync_path = path or get_accepted_sync_path()
    if not sync_path.exists():
        raise FileNotFoundError(sync_path)

    with sync_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return AcceptedSyncStateSchema.from_raw(data).to_json()


def get_prep_manifest_path(thread_dir: Path | str) -> Path:
    """Return the canonical manifest path for a sync thread."""
    return Path(thread_dir) / "prep_manifest.json"


def load_prep_manifest(path: Path) -> PrepManifest:
    """Load and validate a Stage 1 prep manifest."""
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return PrepManifestSchema.from_raw(data).to_json()


def build_accepted_sync_state(
    manifest: PrepManifest,
    upstream_commit_date: str,
    notes: str = "",
) -> AcceptedSyncState:
    """Build the next accepted sync state from a verified manifest."""
    parsed_manifest = PrepManifestSchema.from_raw(manifest)
    if not upstream_commit_date.strip():
        raise ValueError("upstream commit date must be a non-empty string")

    state: AcceptedSyncState = {
        "last_accepted_upstream_sha": parsed_manifest.to_upstream_sha,
        "last_accepted_upstream_date": upstream_commit_date,
        "last_accepted_upstream_ref": parsed_manifest.target_upstream_ref,
    }
    if notes:
        state["notes"] = notes
    return state


def write_accepted_sync_state(path: Path, state: AcceptedSyncState) -> None:
    """Write accepted sync state as canonical JSON."""
    validated = AcceptedSyncStateSchema.from_raw(state).to_json()
    path.write_text(json.dumps(validated, indent=2) + "\n", encoding="utf-8")


def get_modified_upstream_paths(data: dict[str, object]) -> list[str]:
    """Extract path strings from modified_upstream_files (handles string or object entries)."""
    entries = data.get("modified_upstream_files", [])
    paths: list[str] = []
    for entry in entries:  # type: ignore[union-attr]
        if isinstance(entry, str):
            paths.append(entry)
        elif isinstance(entry, dict):
            path_val = entry.get("path")
            if isinstance(path_val, str):
                paths.append(path_val)
    return paths


def get_inspired_by_upstream_paths(data: dict[str, object]) -> list[str]:
    """Return the list of local paths in the inspired_by_upstream category."""
    inspired = data.get("inspired_by_upstream", {})
    if not isinstance(inspired, dict):
        return []
    return list(inspired.keys())


def get_inspired_by_upstream_mapping(data: dict[str, object]) -> dict[str, str]:
    """Return local_path -> upstream_path mapping for inspired entries."""
    inspired = data.get("inspired_by_upstream", {})
    if not isinstance(inspired, dict):
        return {}
    mapping: dict[str, str] = {}
    for local_path, entry in inspired.items():
        if isinstance(entry, dict):
            upstream = entry.get("upstream")
            if isinstance(upstream, str):
                mapping[local_path] = upstream
    return mapping


def get_string_mapping(data: dict[str, object], key: str) -> dict[str, str]:
    """Return a string-to-string registry mapping, ignoring malformed values."""
    value = data.get(key, {})
    if not isinstance(value, dict):
        return {}
    return {
        local_path: upstream_path
        for local_path, upstream_path in value.items()
        if isinstance(local_path, str) and isinstance(upstream_path, str)
    }


def get_strict_shadow_mappings(data: dict[str, object]) -> dict[str, str]:
    """Return combined strict shadow mappings for every localized category."""
    russian = get_string_mapping(data, "russian_copies")
    sbs = get_string_mapping(data, "sbs_copies")
    dps = get_string_mapping(data, "dps_copies")
    tamil = get_string_mapping(data, "tamil_copies")
    return {**russian, **sbs, **dps, **tamil}


def get_shadow_mappings_by_category(
    data: dict[str, object],
) -> dict[str, dict[str, str]]:
    """Return strict-shadow mappings grouped by logical category."""
    return {
        "russian_copies": get_string_mapping(data, "russian_copies"),
        "sbs_copies": get_string_mapping(data, "sbs_copies"),
        "dps_copies": get_string_mapping(data, "dps_copies"),
        "tamil_copies": get_string_mapping(data, "tamil_copies"),
    }


def get_skip_sync_patterns(data: dict[str, object]) -> list[str]:
    """Return the list of patterns to skip during sync."""
    patterns = data.get("skip_sync_patterns", [])
    if not isinstance(patterns, list):
        return []
    return [p for p in patterns if isinstance(p, str)]
