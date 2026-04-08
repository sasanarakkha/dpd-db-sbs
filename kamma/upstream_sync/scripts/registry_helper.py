#!/usr/bin/env python3

"""Shared helpers for loading and querying the upstream sync registry."""

from pathlib import Path


def get_registry_path() -> Path:
    """Return the canonical path to registry.json."""
    return Path("kamma/upstream_sync/registry.json")


def load_registry() -> dict[str, object]:
    """Load and return the registry as a dict."""
    path = get_registry_path()
    import json

    with path.open("r") as f:
        return json.load(f)  # type: ignore[no-any-return]


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
    """Return combined russian_copies and sbs_copies mappings."""
    russian: dict[str, str] = data.get("russian_copies", {})  # type: ignore[assignment]
    sbs: dict[str, str] = data.get("sbs_copies", {})  # type: ignore[assignment]
    return {**russian, **sbs}


def get_skip_sync_patterns(data: dict[str, object]) -> list[str]:
    """Return the list of patterns to skip during sync."""
    patterns = data.get("skip_sync_patterns", [])
    if not isinstance(patterns, list):
        return []
    return [p for p in patterns if isinstance(p, str)]
