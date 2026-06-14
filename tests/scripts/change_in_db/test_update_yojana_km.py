"""Golden-master tests for update_yojana_km pure functions.

Fixtures captured from real DB data (yojana entries with kilometre values)
using old_base=14, new_base=12 to exercise real transformations.
"""

import json
from pathlib import Path

import pytest

from scripts.change_in_db.update_yojana_km import (
    _format_ru_km_value,
    format_ru_km,
    recalculate_meaning_en,
    recalculate_meaning_ru,
    words_to_num,
)

FIXTURE_PATH = Path(__file__).parent / "test_update_yojana_km_fixtures.json"


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_words_to_num_all_real_db_phrases(fixtures: dict) -> None:
    """All English word-number phrases from real yojana DB entries parse correctly."""
    cases = fixtures["words_to_num"]
    assert cases, "fixture is empty"
    for phrase, expected in cases.items():
        assert words_to_num(phrase) == expected, (
            f"words_to_num({phrase!r}): expected {expected}, got {words_to_num(phrase)}"
        )


def test_recalculate_meaning_en_all_real_entries(fixtures: dict) -> None:
    """English km recalculation matches golden output for all real yojana entries."""
    cases = fixtures["recalculate_meaning_en"]
    old_base: int = fixtures["old_base"]
    new_base: int = fixtures["new_base"]
    assert cases, "fixture is empty"
    for meaning, expected in cases.items():
        result = recalculate_meaning_en(meaning, old_base, new_base)
        assert result == expected, (
            f"recalculate_meaning_en({meaning!r}): expected {expected!r}, got {result!r}"
        )


def test_recalculate_meaning_ru_all_real_entries(fixtures: dict) -> None:
    """Russian km recalculation matches golden output for all real yojana entries."""
    cases = fixtures["recalculate_meaning_ru"]
    old_base: int = fixtures["old_base"]
    new_base: int = fixtures["new_base"]
    assert cases, "fixture is empty"
    for meaning, expected in cases.items():
        result = recalculate_meaning_ru(meaning, old_base, new_base)
        assert result == expected, (
            f"recalculate_meaning_ru({meaning!r}): expected {expected!r}, got {result!r}"
        )


def test_format_ru_km_representative_values(fixtures: dict) -> None:
    """Russian km formatting matches golden output for representative km values."""
    cases = fixtures["format_ru_km"]
    assert cases, "fixture is empty"
    for km_str, expected in cases.items():
        result = format_ru_km(int(km_str))
        assert result == expected, (
            f"format_ru_km({km_str}): expected {expected!r}, got {result!r}"
        )


def test_format_ru_km_value_representative_values(fixtures: dict) -> None:
    """Internal _format_ru_km_value matches golden output for representative km values."""
    cases = fixtures["_format_ru_km_value"]
    assert cases, "fixture is empty"
    for km_str, expected in cases.items():
        result = _format_ru_km_value(int(km_str))
        assert result == expected, (
            f"_format_ru_km_value({km_str}): expected {expected!r}, got {result!r}"
        )
