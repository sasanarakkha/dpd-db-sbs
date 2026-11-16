"""Read and write the translate-skill session ids file (`{lang, mode, ids}`, legacy bare list accepted)."""

import json
from pathlib import Path
from typing import Any


def read_ids_file(path: Path) -> list[int]:
    """Return the ids in an ids file; accepts the `{lang, mode, ids}` shape or a bare list.

    A missing, malformed, or unexpectedly shaped file yields [].
    """
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    raw: Any = data.get("ids") if isinstance(data, dict) else data
    if not isinstance(raw, list):
        return []
    try:
        return [int(i) for i in raw]
    except (TypeError, ValueError):
        return []


def read_ids_scope(path: Path) -> tuple[str, str] | None:
    """Return the file's `(lang, mode)`; None for a missing, malformed or legacy bare-list file."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    lang, mode = data.get("lang"), data.get("mode")
    if not isinstance(lang, str) or not isinstance(mode, str):
        return None
    return lang, mode


def write_ids_file(path: Path, lang: str, mode: str, ids: list[int]) -> None:
    """Write `{lang, mode, ids}` with sorted unique ids, creating parent folders."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"lang": lang, "mode": mode, "ids": sorted(set(ids))}
    path.write_text(json.dumps(payload), encoding="utf-8")
