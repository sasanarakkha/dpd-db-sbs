"""Characterization tests for update_ru_db_from_csv.py auto-update and diff logic."""

import json
from pathlib import Path

from scripts.change_in_db.update_ru_db_from_csv import (
    _auto_update_meaning,
    _has_lit_diff,
    _has_meaning_diff,
)
from tools.tsv_read_write import dotdict

FIXTURE_PATH = (
    Path(__file__).resolve().parent / "test_update_ru_db_from_csv_fixtures.json"
)


def _should_skip_processed(csv_row: dotdict) -> bool:
    return csv_row.get("processed") == "ok"


class TestAutoUpdate:
    def test_empty_meaning_auto_update(self) -> None:
        f = load_fixture("empty_meaning_auto_update")
        row = dotdict(f["csv_row"])
        new_meaning, updated = _auto_update_meaning(row, f["current_meaning"])
        assert updated == f["auto_updated"]
        assert new_meaning == f["new_meaning"]

    def test_same_meaning_no_diff(self) -> None:
        f = load_fixture("same_meaning_no_diff")
        row = dotdict(f["csv_row"])
        new_meaning, updated = _auto_update_meaning(row, f["current_meaning"])
        assert updated == f["auto_updated"]
        assert new_meaning == f["new_meaning"]

    def test_different_meaning_has_diff(self) -> None:
        f = load_fixture("different_meaning_has_diff")
        row = dotdict(f["csv_row"])
        new_meaning, updated = _auto_update_meaning(row, f["current_meaning"])
        assert updated == f["auto_updated"]
        assert new_meaning == f["new_meaning"]

    def test_lit_correction_meaning_no_diff(self) -> None:
        f = load_fixture("lit_correction_meaning_no_diff")
        row = dotdict(f["csv_row"])
        new_meaning, updated = _auto_update_meaning(row, f["current_meaning"])
        assert updated == f["auto_updated"]
        assert new_meaning == f["new_meaning"]

    def test_empty_corrections_nothing(self) -> None:
        f = load_fixture("empty_corrections_nothing")
        row = dotdict(f["csv_row"])
        new_meaning, updated = _auto_update_meaning(row, f["current_meaning"])
        assert updated == f["auto_updated"]
        assert new_meaning == f["new_meaning"]

    def test_whitespace_only_correction(self) -> None:
        f = load_fixture("whitespace_only_correction")
        row = dotdict(f["csv_row"])
        new_meaning, updated = _auto_update_meaning(row, f["current_meaning"])
        assert updated == f["auto_updated"]
        assert new_meaning == f["new_meaning"]


class TestHasDiff:
    def test_empty_meaning_auto_update_has_no_diff(self) -> None:
        f = load_fixture("empty_meaning_auto_update")
        row = dotdict(f["csv_row"])
        assert not _has_meaning_diff(row, f["new_meaning"])
        assert not _has_lit_diff(row, f["current_meaning_lit"])

    def test_different_meaning_has_diff(self) -> None:
        f = load_fixture("different_meaning_has_diff")
        row = dotdict(f["csv_row"])
        meaning_diff = _has_meaning_diff(row, f["current_meaning"])
        lit_diff = _has_lit_diff(row, f["current_meaning_lit"])
        assert (meaning_diff, lit_diff) == tuple(f["has_diff"])

    def test_lit_correction_has_lit_diff(self) -> None:
        f = load_fixture("lit_correction_meaning_no_diff")
        row = dotdict(f["csv_row"])
        meaning_diff = _has_meaning_diff(row, f["current_meaning"])
        lit_diff = _has_lit_diff(row, f["current_meaning_lit"])
        assert (meaning_diff, lit_diff) == tuple(f["has_diff"])

    def test_both_fields_have_diff(self) -> None:
        f = load_fixture("both_fields_have_diff")
        row = dotdict(f["csv_row"])
        meaning_diff = _has_meaning_diff(row, f["current_meaning"])
        lit_diff = _has_lit_diff(row, f["current_meaning_lit"])
        assert (meaning_diff, lit_diff) == tuple(f["has_diff"])


class TestSkipProcessed:
    def test_processed_ok_skip(self) -> None:
        f = load_fixture("already_processed_skip")
        row = dotdict(f["csv_row"])
        assert _should_skip_processed(row) is True
        assert f["should_skip"] is True

    def test_not_processed_no_skip(self) -> None:
        f = load_fixture("empty_meaning_auto_update")
        row = dotdict(f["csv_row"])
        assert _should_skip_processed(row) is False


def load_fixture(key: str) -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))[key]
