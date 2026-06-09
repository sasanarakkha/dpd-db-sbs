"""Tests for preview_dhp_changes formatting functions.

Fixtures were captured from the inline logic in the original main() before
extraction into sub-functions, so they act as a golden-master for the refactor.
"""

import json
from pathlib import Path

import pytest

from scripts.change_in_db.preview_dhp_changes import (
    ProposedChange,
    _build_proposed_changes_section,
    _build_speech_marks_section,
)

FIXTURE_PATH = Path(__file__).parent / "test_preview_dhp_changes_fixtures.json"


@pytest.fixture(scope="module")
def fixtures() -> dict[str, dict[str, object]]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


# --- _build_speech_marks_section ---


def test_speech_marks_empty(fixtures: dict[str, dict[str, object]]) -> None:
    data = fixtures["speech_marks_empty"]
    assert _build_speech_marks_section(data["input"]) == data["output"]  # type: ignore[arg-type]


def test_speech_marks_single_two_variants(
    fixtures: dict[str, dict[str, object]],
) -> None:
    data = fixtures["speech_marks_single_variant"]
    assert _build_speech_marks_section(data["input"]) == data["output"]  # type: ignore[arg-type]


def test_speech_marks_single_one_variant(
    fixtures: dict[str, dict[str, object]],
) -> None:
    data = fixtures["speech_marks_single_one_variant"]
    assert _build_speech_marks_section(data["input"]) == data["output"]  # type: ignore[arg-type]


def test_speech_marks_multi_words(fixtures: dict[str, dict[str, object]]) -> None:
    data = fixtures["speech_marks_multi_words"]
    assert _build_speech_marks_section(data["input"]) == data["output"]  # type: ignore[arg-type]


# --- _build_proposed_changes_section ---


def test_changes_empty(fixtures: dict[str, dict[str, object]]) -> None:
    data = fixtures["changes_empty"]
    assert _build_proposed_changes_section(data["input"]) == data["output"]  # type: ignore[arg-type]


def test_changes_new_single(fixtures: dict[str, dict[str, object]]) -> None:
    data = fixtures["changes_new_single"]
    rows: list[ProposedChange] = data["input"]  # type: ignore[assignment]
    assert _build_proposed_changes_section(rows) == data["output"]


def test_changes_skip_single(fixtures: dict[str, dict[str, object]]) -> None:
    data = fixtures["changes_skip_single"]
    rows: list[ProposedChange] = data["input"]  # type: ignore[assignment]
    assert _build_proposed_changes_section(rows) == data["output"]


def test_changes_multi_rows(fixtures: dict[str, dict[str, object]]) -> None:
    data = fixtures["changes_multi_rows"]
    rows: list[ProposedChange] = data["input"]  # type: ignore[assignment]
    assert _build_proposed_changes_section(rows) == data["output"]
