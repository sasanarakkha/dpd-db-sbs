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
