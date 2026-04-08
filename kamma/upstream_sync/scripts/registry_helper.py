#!/usr/bin/env python3

"""Shared helpers for loading sync registry and accepted upstream sync metadata."""

import json
from pathlib import Path


type AcceptedSyncState = dict[str, str]
type PrepManifest = dict[str, object]


def get_registry_path() -> Path:
    """Return the canonical path to registry.json."""
    return Path("kamma/upstream_sync/registry.json")


def get_accepted_sync_path() -> Path:
    """Return the canonical path to accepted_sync.json."""
    return Path("kamma/upstream_sync/accepted_sync.json")


def load_registry() -> dict[str, object]:
    """Load and return the registry as a dict."""
    path = get_registry_path()

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def load_accepted_sync_state(path: Path | None = None) -> AcceptedSyncState:
    """Load and validate accepted upstream sync metadata."""
    sync_path = path or get_accepted_sync_path()
    if not sync_path.exists():
        raise FileNotFoundError(sync_path)

    with sync_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("accepted sync state must be a JSON object")

    required_fields = [
        "last_accepted_upstream_sha",
        "last_accepted_upstream_date",
        "last_accepted_upstream_ref",
    ]
    validated: AcceptedSyncState = {}

    for field in required_fields:
        if field not in data:
            raise ValueError(f"missing required field '{field}'")
        value = data[field]
        if not isinstance(value, str):
            raise ValueError(f"field '{field}' must be a string")
        if not value.strip():
            raise ValueError(f"field '{field}' must be a non-empty string")
        validated[field] = value

    notes = data.get("notes")
    if notes is not None:
        if not isinstance(notes, str):
            raise ValueError("field 'notes' must be a string")
        validated["notes"] = notes

    return validated


def get_prep_manifest_path(thread_dir: Path | str) -> Path:
    """Return the canonical manifest path for a sync thread."""
    return Path(thread_dir) / "prep_manifest.json"


def load_prep_manifest(path: Path) -> PrepManifest:
    """Load and validate a Stage 1 prep manifest."""
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("prep manifest must be a JSON object")

    required_string_fields = [
        "from_upstream_sha",
        "to_upstream_sha",
        "target_upstream_ref",
        "generated_at",
    ]
    required_list_fields = [
        "changed_upstream_paths",
        "deleted_upstream_paths",
        "discuss_paths",
    ]
    for field in required_string_fields:
        if field not in data:
            raise ValueError(f"missing required field '{field}'")
        value = data[field]
        if not isinstance(value, str):
            raise ValueError(f"field '{field}' must be a string")
        if not value.strip():
            raise ValueError(f"field '{field}' must be a non-empty string")

    for field in required_list_fields:
        if field not in data:
            raise ValueError(f"missing required field '{field}'")
        value = data[field]
        if not isinstance(value, list):
            raise ValueError(f"field '{field}' must be a list")

    mapped_actions = data.get("mapped_actions")
    if not isinstance(mapped_actions, dict):
        raise ValueError("field 'mapped_actions' must be an object")

    return data


def build_accepted_sync_state(
    manifest: PrepManifest,
    upstream_commit_date: str,
    notes: str = "",
) -> AcceptedSyncState:
    """Build the next accepted sync state from a verified manifest."""
    to_sha = manifest.get("to_upstream_sha")
    target_ref = manifest.get("target_upstream_ref")
    if not isinstance(to_sha, str) or not to_sha.strip():
        raise ValueError("manifest field 'to_upstream_sha' must be a non-empty string")
    if not isinstance(target_ref, str) or not target_ref.strip():
        raise ValueError(
            "manifest field 'target_upstream_ref' must be a non-empty string"
        )
    if not upstream_commit_date.strip():
        raise ValueError("upstream commit date must be a non-empty string")

    state: AcceptedSyncState = {
        "last_accepted_upstream_sha": to_sha,
        "last_accepted_upstream_date": upstream_commit_date,
        "last_accepted_upstream_ref": target_ref,
    }
    if notes:
        state["notes"] = notes
    return state


def write_accepted_sync_state(path: Path, state: AcceptedSyncState) -> None:
    """Write accepted sync state as canonical JSON."""
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


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


def get_strict_shadow_mappings(data: dict[str, object]) -> dict[str, str]:
    """Return combined russian_copies, sbs_copies, and dps_copies mappings."""
    russian: dict[str, str] = data.get("russian_copies", {})  # type: ignore[assignment]
    sbs: dict[str, str] = data.get("sbs_copies", {})  # type: ignore[assignment]
    dps: dict[str, str] = data.get("dps_copies", {})  # type: ignore[assignment]
    return {**russian, **sbs, **dps}


def get_shadow_mappings_by_category(
    data: dict[str, object],
) -> dict[str, dict[str, str]]:
    """Return strict-shadow mappings grouped by logical category."""
    return {
        "russian_copy": data.get("russian_copies", {}),  # type: ignore[dict-item]
        "sbs_copy": data.get("sbs_copies", {}),  # type: ignore[dict-item]
        "dps_copy": data.get("dps_copies", {}),  # type: ignore[dict-item]
    }


def get_skip_sync_patterns(data: dict[str, object]) -> list[str]:
    """Return the list of patterns to skip during sync."""
    patterns = data.get("skip_sync_patterns", [])
    if not isinstance(patterns, list):
        return []
    return [p for p in patterns if isinstance(p, str)]
