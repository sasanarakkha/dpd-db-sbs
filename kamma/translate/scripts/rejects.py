"""Track Russian drafts the checker rejected (count + last reason) so repeat offenders are parked and the reason feeds regeneration."""

import json
from datetime import datetime
from pathlib import Path
from typing import TypedDict

REJECTS_PATH = Path(__file__).resolve().parents[1] / "rejects.json"
PARK_THRESHOLD = 2


class RejectEntry(TypedDict):
    """One rejected-draft record."""

    count: int
    reason: str
    last: str


def load_rejects(path: Path = REJECTS_PATH) -> dict[str, RejectEntry]:
    """Load the reject memory; a missing or malformed file yields {}."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def record_reject(
    path: Path, headword_id: int, reason: str, now: datetime | None = None
) -> int:
    """Increment the reject count for an id, store the latest reason, return the new count."""
    rejects = load_rejects(path)
    key = str(headword_id)
    previous = rejects.get(key)
    count = (previous["count"] if previous else 0) + 1
    stamp = (now or datetime.now().astimezone()).isoformat(timespec="seconds")
    rejects[key] = {"count": count, "reason": reason, "last": stamp}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(rejects, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return count


def parked_ids(path: Path = REJECTS_PATH, threshold: int = PARK_THRESHOLD) -> list[int]:
    """Ids rejected at least `threshold` times (excluded from the generate pool)."""
    return sorted(
        int(key)
        for key, entry in load_rejects(path).items()
        if entry.get("count", 0) >= threshold
    )


def reject_reason(path: Path, headword_id: int) -> str:
    """Latest rejection reason for an id, or '' when none."""
    entry = load_rejects(path).get(str(headword_id))
    return entry["reason"] if entry else ""
