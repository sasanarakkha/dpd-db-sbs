"""Unit tests for Russian meaning checker snapshot hashing and migration."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from tools.ai_meaning_checker import RussianMeaningChecker
from tools.meaning_snapshot_ru import (
    compose_english_content,
    compute_field_hash,
    load_snapshot,
    normalize_text,
    reconcile_snapshot,
    remove_ids_from_snapshot,
    save_snapshot,
)


def _headword(
    meaning_1: str | None = "m1",
    meaning_lit: str | None = "",
    notes: str | None = "notes",
) -> Any:
    """Create a minimal headword-like object for composition tests."""
    return SimpleNamespace(
        id=1,
        meaning_1=meaning_1,
        meaning_lit=meaning_lit,
        notes=notes,
    )


def _checker(
    checked_ids_file: Path,
    snapshot: dict[int, str],
    checked_ids: set[int],
    english_by_id: dict[int, str],
) -> RussianMeaningChecker:
    """Create a checker with only save_checked_ids dependencies populated."""
    checker = RussianMeaningChecker.__new__(RussianMeaningChecker)
    checker.checked_ids_file = checked_ids_file
    checker.snapshot = snapshot
    checker.checked_ids = checked_ids
    checker.english_by_id = english_by_id
    return checker


def test_normalize_collapses_whitespace() -> None:
    assert normalize_text(" a \n b\t c ") == "a b c"
    assert normalize_text(None) == ""
    assert normalize_text("") == ""


def test_hash_stable_and_whitespace_invariant() -> None:
    result = compute_field_hash("a  b\n")

    assert result == compute_field_hash("a b")
    assert len(result) == 16
    assert compute_field_hash("") != ""
    assert compute_field_hash("a") != compute_field_hash("b")


def test_compose_meaning_mode_with_and_without_lit() -> None:
    assert compose_english_content(_headword(meaning_lit="x"), "meaning") == (
        "m1; lit. x"
    )
    assert compose_english_content(_headword(meaning_lit=""), "meaning") == "m1"
    assert compose_english_content(_headword(meaning_lit=None), "meaning") == "m1"


def test_compose_lit_and_notes_modes() -> None:
    assert compose_english_content(_headword(meaning_lit="x"), "meaning_lit") == "x"
    assert compose_english_content(_headword(notes="n1"), "notes") == "n1"


def test_load_missing_and_corrupt_file(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    assert load_snapshot(path) == {}

    path.write_text("{", encoding="utf-8")
    assert load_snapshot(path) == {}


def test_v1_migration(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")

    assert load_snapshot(path) == {1: "", 2: "", 3: ""}


def test_v2_roundtrip_int_keys(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"

    save_snapshot(path, {12345: "abcd"})

    assert load_snapshot(path) == {12345: "abcd"}
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["format_version"] == 2
    assert raw["checked"] == {"12345": "abcd"}


def test_reconcile_seeds_empty_hashes() -> None:
    snapshot = {1: ""}

    assert reconcile_snapshot(snapshot, {1: "h1"}) == (0, 1)
    assert snapshot == {1: "h1"}


def test_reconcile_invalidates_changed() -> None:
    snapshot = {1: "old"}

    assert reconcile_snapshot(snapshot, {1: "new"}) == (1, 0)
    assert snapshot == {}


def test_reconcile_keeps_unchanged() -> None:
    snapshot = {1: "h1"}

    assert reconcile_snapshot(snapshot, {1: "h1"}) == (0, 0)
    assert snapshot == {1: "h1"}


def test_reconcile_drops_deleted_headwords() -> None:
    snapshot = {1: "h1"}

    assert reconcile_snapshot(snapshot, {}) == (1, 0)
    assert snapshot == {}


def test_remove_ids_from_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    save_snapshot(path, {1: "a", 2: "b"})

    assert remove_ids_from_snapshot(path, {2, 99}) == 1
    assert load_snapshot(path) == {1: "a"}

    missing_path = tmp_path / "missing.json"
    assert remove_ids_from_snapshot(missing_path, {1}) == 0
    assert not missing_path.exists()


def test_save_checked_ids_hashes_new_ids(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    checker = _checker(
        checked_ids_file=path,
        snapshot={},
        checked_ids={1},
        english_by_id={1: "dog"},
    )

    checker.save_checked_ids()

    assert load_snapshot(path)[1] == compute_field_hash("dog")


def test_save_checked_ids_unknown_english_gets_sentinel(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    checker = _checker(
        checked_ids_file=path,
        snapshot={},
        checked_ids={2},
        english_by_id={},
    )

    checker.save_checked_ids()

    assert load_snapshot(path)[2] == ""


def test_save_checked_ids_keeps_existing_hashes(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    checker = _checker(
        checked_ids_file=path,
        snapshot={3: "keep"},
        checked_ids={3},
        english_by_id={3: "changed"},
    )

    checker.save_checked_ids()

    assert load_snapshot(path)[3] == "keep"
