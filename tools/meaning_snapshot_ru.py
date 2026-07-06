"""Snapshot storage and drift detection for the AI Russian meaning checker (issue #40): hashes of checked English content, with invalidation when the DB value changes."""

import hashlib
import json
from pathlib import Path

from sqlalchemy.orm import Session

from db.models import DpdHeadword


def normalize_text(value: str | None) -> str:
    """Strip and collapse all whitespace runs to single spaces."""
    if not value:
        return ""
    return " ".join(value.split())


def compute_field_hash(value: str | None) -> str:
    """16-hex-char SHA-256 of the normalized text. Never returns ''."""
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()[:16]


def compose_english_content(headword: DpdHeadword, mode: str) -> str:
    """Single source of truth for the English content sent to the AI per mode."""
    if mode in ("notes", "notes_raw"):
        return headword.notes or ""
    if mode in ("meaning_lit", "meaning_lit_list"):
        return headword.meaning_lit or ""
    # meaning, meaning_raw, russian_grammar_meaning_raw, meaning_raw_list
    if headword.meaning_lit:
        return f"{headword.meaning_1}; lit. {headword.meaning_lit}"
    return headword.meaning_1 or ""


def load_snapshot(path: Path) -> dict[int, str]:
    """Load v2 snapshot; auto-migrate v1 (plain list) to empty-hash entries."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if isinstance(data, list):  # v1: [12345, ...] -> sentinel "" = seed later
        return {int(i): "" for i in data}
    if isinstance(data, dict) and "checked" in data:
        return {int(k): str(v) for k, v in data["checked"].items()}
    return {}


def save_snapshot(path: Path, snapshot: dict[int, str]) -> None:
    """Write v2 format. Keys serialized as strings (JSON requirement)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format_version": 2,
        "checked": {str(k): v for k, v in sorted(snapshot.items())},
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def reconcile_snapshot(
    snapshot: dict[int, str], current_hashes: dict[int, str]
) -> tuple[int, int]:
    """Mutate snapshot in place against current DB hashes.

    Returns (n_invalidated, n_seeded).
    - stored == "" (sentinel): seed with current hash, count as seeded.
    - stored != current: delete from snapshot (will be re-checked), count as invalidated.
    - stored == current: keep.
    - id missing from current_hashes (deleted headword): delete, count as invalidated.
    """
    n_invalidated = 0
    n_seeded = 0
    for headword_id in list(snapshot.keys()):
        current = current_hashes.get(headword_id)
        if current is None:
            del snapshot[headword_id]
            n_invalidated += 1
        elif snapshot[headword_id] == "":
            snapshot[headword_id] = current
            n_seeded += 1
        elif snapshot[headword_id] != current:
            del snapshot[headword_id]
            n_invalidated += 1
    return n_invalidated, n_seeded


def invalidate_changed(
    snapshot: dict[int, str], db_session: Session, mode: str
) -> tuple[int, int]:
    """Query current English content for all snapshot IDs and reconcile."""
    if not snapshot:
        return 0, 0
    headwords = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.id.in_(list(snapshot.keys())))
        .all()
    )
    current_hashes = {
        hw.id: compute_field_hash(compose_english_content(hw, mode)) for hw in headwords
    }
    return reconcile_snapshot(snapshot, current_hashes)


def remove_ids_from_snapshot(path: Path, ids: set[int]) -> int:
    """Remove IDs from a snapshot file so they re-enter the check queue.

    Used by the translation generator after regenerating Russian content.
    Returns the number of IDs actually removed. No-op if the file is
    missing or none of the IDs are present.
    """
    snapshot = load_snapshot(path)
    if not snapshot:
        return 0
    removed = 0
    for headword_id in ids:
        if headword_id in snapshot:
            del snapshot[headword_id]
            removed += 1
    if removed:
        save_snapshot(path, snapshot)
    return removed
