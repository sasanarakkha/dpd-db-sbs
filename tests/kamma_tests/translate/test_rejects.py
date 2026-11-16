"""Reject memory (kamma/translate/rejects.json): counts, parking, reason lookup."""

import json
from datetime import datetime, timezone
from pathlib import Path

from kamma.translate.scripts.rejects import (
    load_rejects,
    parked_ids,
    record_reject,
    reject_reason,
)

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)


def test_first_reject_counts_one_and_stores_reason(tmp_path: Path):
    path = tmp_path / "rejects.json"
    assert record_reject(path, 7, "wrong sense", NOW) == 1
    assert load_rejects(path)["7"] == {
        "count": 1,
        "reason": "wrong sense",
        "last": "2026-11-16T12:00:00+00:00",
    }
    assert parked_ids(path) == []


def test_second_reject_parks_and_keeps_latest_reason(tmp_path: Path):
    path = tmp_path / "rejects.json"
    record_reject(path, 7, "first", NOW)
    assert record_reject(path, 7, "second", NOW) == 2
    assert parked_ids(path) == [7]
    assert reject_reason(path, 7) == "second"


def test_missing_or_malformed_file_is_empty(tmp_path: Path):
    assert load_rejects(tmp_path / "none.json") == {}
    bad = tmp_path / "bad.json"
    bad.write_text("{oops", encoding="utf-8")
    assert load_rejects(bad) == {}
    bad.write_text(json.dumps([1]), encoding="utf-8")
    assert load_rejects(bad) == {}
    assert reject_reason(tmp_path / "none.json", 1) == ""


def test_unparking_means_deleting_the_entry(tmp_path: Path):
    path = tmp_path / "rejects.json"
    record_reject(path, 7, "a", NOW)
    record_reject(path, 7, "b", NOW)
    path.write_text(json.dumps({}), encoding="utf-8")
    assert parked_ids(path) == []
