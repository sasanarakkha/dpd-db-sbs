"""Golden-master tests for the AI-response cleanup helper in family_set_ru_update."""

import json
from pathlib import Path

import pytest

from db.families.family_set_ru_update import _clean_translated_lines

FIXTURE_PATH = Path(__file__).parent / "family_set_ru_update_fixtures.json"


@pytest.fixture(scope="module")
def fixtures() -> dict[str, dict[str, str]]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "case",
    [
        "numbered_dot",
        "numbered_dot_space",
        "dash_prefix",
        "star_prefix",
        "bold_markdown",
        "bold_inline",
        "clean_line",
        "numbered_no_content",
        "leading_trailing_spaces",
        "combined_numbered_bold",
        "combined_dash_bold",
        "combined_star_bold",
        "not_numbered_mid",
        "not_dash_mid",
        "unicode_pali",
    ],
)
def test_clean_translated_lines_golden_master(
    fixtures: dict[str, dict[str, str]], case: str
) -> None:
    data = fixtures[case]
    result = _clean_translated_lines([data["input"]])
    assert result == [data["output"]], (
        f"Case {case!r}: input={data['input']!r} expected={data['output']!r} got={result[0]!r}"
    )


def test_clean_translated_lines_batch() -> None:
    """All lines in a batch are cleaned consistently."""
    inputs = ["1. слово", "- другое", "* третье"]
    result = _clean_translated_lines(inputs)
    assert result == ["слово", "другое", "третье"]


def test_clean_translated_lines_empty() -> None:
    assert _clean_translated_lines([]) == []
