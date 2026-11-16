import json
from pathlib import Path

from kamma.translate.scripts.ids_file import (
    read_ids_file,
    read_ids_scope,
    write_ids_file,
)


def test_write_then_read_round_trips_sorted_unique(tmp_path: Path):
    path = tmp_path / "sub" / "ids.json"
    write_ids_file(path, "ru", "meaning", [3, 1, 3, 2])
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "lang": "ru",
        "mode": "meaning",
        "ids": [1, 2, 3],
    }
    assert read_ids_file(path) == [1, 2, 3]


def test_read_accepts_legacy_bare_list(tmp_path: Path):
    path = tmp_path / "ids.json"
    path.write_text(json.dumps([4, 2]), encoding="utf-8")
    assert read_ids_file(path) == [4, 2]


def test_read_missing_malformed_or_wrong_shape_returns_empty(tmp_path: Path):
    assert read_ids_file(tmp_path / "nope.json") == []
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert read_ids_file(bad) == []
    odd = tmp_path / "odd.json"
    odd.write_text(json.dumps({"ids": "abc"}), encoding="utf-8")
    assert read_ids_file(odd) == []
    odd.write_text(json.dumps({"other": [1]}), encoding="utf-8")
    assert read_ids_file(odd) == []


def test_read_ids_scope(tmp_path: Path):
    path = tmp_path / "ids.json"
    assert read_ids_scope(path) is None
    write_ids_file(path, "ru", "lit", [1])
    assert read_ids_scope(path) == ("ru", "lit")
    path.write_text(json.dumps([1, 2]), encoding="utf-8")  # legacy bare list
    assert read_ids_scope(path) is None
    path.write_text("{not json", encoding="utf-8")
    assert read_ids_scope(path) is None
