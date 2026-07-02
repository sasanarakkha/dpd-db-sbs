"""Golden-master tests for SBS example cleanup logic."""

import json
from pathlib import Path

import pytest

from scripts.change_in_db.example_cleanup import clean_example

FIXTURE_PATH = Path(__file__).parent / "test_example_cleanup_fixtures.json"


@pytest.fixture
def fixtures() -> list[dict]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_clean_example_golden_master(fixtures: list[dict]) -> None:
    for case in fixtures:
        result = clean_example(case["input"])
        assert result == case["expected"], (
            f"id={case['id']} input={case['input']!r} → expected={case['expected']!r}, got {result!r}"
        )
