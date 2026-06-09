"""Tests for the _copy_dpd_fields helper in scripts/change_in_db/copy_examples.py."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from db.models import DpdHeadword, SBS
from scripts.change_in_db.copy_examples import _copy_dpd_fields

FIXTURE_PATH = Path(__file__).parent / "test_copy_examples_fixtures.json"


def _make_word(data: dict[str, Any]) -> DpdHeadword:
    return cast(
        DpdHeadword,
        SimpleNamespace(
            source_1=data.get("source_1", ""),
            source_2=data.get("source_2", ""),
            sutta_1=data.get("sutta_1", ""),
            sutta_2=data.get("sutta_2", ""),
            example_1=data.get("example_1", ""),
            example_2=data.get("example_2", ""),
        ),
    )


def _make_sbs() -> SBS:
    return cast(SBS, SimpleNamespace(vib_source="", vib_sutta="", vib_example=""))


def _load_fixtures() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_match_source1() -> None:
    fixtures = _load_fixtures()
    case = fixtures["match_source1"]
    word = _make_word(case)
    sbs = _make_sbs()

    result = _copy_dpd_fields(word, sbs, case["source_value"], "vib")

    assert result is True
    assert sbs.vib_source == case["expected_target_source"]
    assert sbs.vib_sutta == case["expected_target_sutta"]
    assert sbs.vib_example == case["expected_target_example"]


def test_match_source2_only() -> None:
    """source_1 is empty; match falls through to source_2."""
    fixtures = _load_fixtures()
    case = fixtures["match_source2_only"]
    word = _make_word(case)
    sbs = _make_sbs()

    result = _copy_dpd_fields(word, sbs, case["source_value"], "vib")

    assert result is True
    assert sbs.vib_source == case["expected_target_source"]
    assert sbs.vib_sutta == case["expected_target_sutta"]
    assert sbs.vib_example == case["expected_target_example"]


def test_match_source2_fallback() -> None:
    """source_1 exists but doesn't match; source_2 matches."""
    fixtures = _load_fixtures()
    case = fixtures["match_source2_fallback"]
    word = _make_word(case)
    sbs = _make_sbs()

    result = _copy_dpd_fields(word, sbs, case["source_value"], "vib")

    assert result is True
    assert sbs.vib_source == case["expected_target_source"]
    assert sbs.vib_sutta == case["expected_target_sutta"]
    assert sbs.vib_example == case["expected_target_example"]


def test_no_match() -> None:
    """Neither source field matches — function returns False, sbs untouched."""
    fixtures = _load_fixtures()
    case = fixtures["no_match"]
    word = _make_word(case)
    sbs = _make_sbs()

    result = _copy_dpd_fields(word, sbs, case["source_value"], "vib")

    assert result is False
    assert sbs.vib_source == ""
    assert sbs.vib_sutta == ""
    assert sbs.vib_example == ""


def test_source1_empty_no_source2() -> None:
    """Both sources empty — returns False."""
    word = _make_word(
        {
            "source_1": "",
            "source_2": "",
            "sutta_1": "",
            "sutta_2": "",
            "example_1": "",
            "example_2": "",
        }
    )
    sbs = _make_sbs()

    result = _copy_dpd_fields(word, sbs, "anything", "vib")

    assert result is False
