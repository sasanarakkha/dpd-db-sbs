#!/usr/bin/env python3

"""Golden-master tests for _find_dhp_source_idx in dhp_examples_copy.py."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.change_in_db.dhp_examples_copy import _find_dhp_source_idx

FIXTURE_PATH = Path(__file__).parent / "test_dhp_examples_copy_fixtures.json"


@pytest.fixture
def fixtures() -> list[dict]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _make_word(source_1: str, source_2: str) -> MagicMock:
    word = MagicMock()
    word.source_1 = source_1
    word.source_2 = source_2
    return word


def test_find_dhp_source_idx_golden_master(fixtures: list[dict]) -> None:
    for case in fixtures:
        word = _make_word(case["source_1"], case["source_2"])
        result = _find_dhp_source_idx(word)
        assert result == case["expected_idx"], (
            f"id={case['id']}: source_1={case['source_1']!r} source_2={case['source_2']!r}"
            f" → expected idx={case['expected_idx']}, got {result}"
        )


def test_covers_all_branches(fixtures: list[dict]) -> None:
    idxes = {c["expected_idx"] for c in fixtures}
    assert 1 in idxes, "need at least one case where source_1 matches"
    assert 2 in idxes, "need at least one case where only source_2 matches"
    assert None in idxes, "need at least one case where no source matches"
