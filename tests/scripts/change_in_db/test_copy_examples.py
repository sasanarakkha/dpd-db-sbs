"""Tests for the _copy_dpd_fields helper in scripts/change_in_db/copy_examples.py."""

import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from db.models import SBS, DpdHeadword
from scripts.change_in_db.copy_examples import _SOURCE_FIELDS, _copy_dpd_fields

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


def _make_sbs(attrs: dict[str, Any] | None = None) -> SBS:
    defaults: dict[str, Any] = {"vib_source": "", "vib_sutta": "", "vib_example": ""}
    if attrs:
        defaults.update(attrs)
    return cast(SBS, SimpleNamespace(**defaults))


def _load_fixtures() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


# ---- Original tests for _copy_dpd_fields ----


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


# ---- Processing logic tests (synthetic cases from fixtures) ----


def _process_row_refactored(
    word: DpdHeadword,
    sbs: SBS | None,
    source_value: str,
    target_prefix: str,
) -> tuple[str, list[tuple[str, str]]]:
    """Run the refactored priority-based processing on a single word+sbs pair.

    Returns (action, changes) where:
      action is "already" | "from_sbs" | "from_dpd" | "new_row" | "none"
      changes is [(field, value), ...] of attributes set on SBS.
    """
    changes: list[tuple[str, str]] = []

    if sbs and sbs.vib_source == source_value:
        return ("already", changes)

    if sbs:
        for idx in range(1, 3):
            sbs_source = getattr(sbs, f"sbs_source_{idx}")
            if sbs_source and re.search(source_value, sbs_source):
                for field in _SOURCE_FIELDS:
                    src_val = getattr(sbs, f"sbs_{field}_{idx}")
                    setattr(sbs, f"{target_prefix}_{field}", src_val)
                    changes.append((f"{target_prefix}_{field}", src_val))
                return ("from_sbs", changes)
        # No SBS source matched — try DPD
        if _copy_dpd_fields(word, sbs, source_value, target_prefix):
            for field in _SOURCE_FIELDS:
                changes.append(
                    (
                        f"{target_prefix}_{field}",
                        getattr(sbs, f"{target_prefix}_{field}"),
                    )
                )
            return ("from_dpd", changes)
    else:
        # No SBS row — create one and try DPD
        sbs_obj = _make_sbs({"vib_source": "", "vib_sutta": "", "vib_example": ""})
        word.sbs = sbs_obj
        if _copy_dpd_fields(word, sbs_obj, source_value, target_prefix):
            for field in _SOURCE_FIELDS:
                changes.append(
                    (
                        f"{target_prefix}_{field}",
                        getattr(sbs_obj, f"{target_prefix}_{field}"),
                    )
                )
            return ("new_row", changes)

    return ("none", changes)


def _make_sbs_for_case(case_sbs: dict[str, Any] | None) -> SBS | None:
    """Create an SBS object from a fixture case's sbs dict, or None."""
    if case_sbs is None:
        return None
    attrs: dict[str, Any] = {}
    for key, val in case_sbs.items():
        attrs[key] = val
    return _make_sbs(attrs)


def test_synthetic_already_have() -> None:
    fixtures = _load_fixtures()
    case = fixtures["synthetic_cases"]["already_have"]
    word = _make_word(case["word"])
    sbs = _make_sbs_for_case(case["sbs"])

    action, _changes = _process_row_refactored(
        word, sbs, fixtures["source_value"], fixtures["target"]
    )

    assert action == "already"
    assert _changes == []


def test_synthetic_from_sbs_source1() -> None:
    fixtures = _load_fixtures()
    case = fixtures["synthetic_cases"]["from_sbs_source1"]
    word = _make_word(case["word"])
    sbs = _make_sbs_for_case(case["sbs"])

    action, _changes = _process_row_refactored(
        word, sbs, fixtures["source_value"], fixtures["target"]
    )

    assert action == "from_sbs"
    expected = case["expected_changes"]
    for field, val in expected.items():
        assert getattr(sbs, field) == val


def test_synthetic_from_sbs_source2() -> None:
    fixtures = _load_fixtures()
    case = fixtures["synthetic_cases"]["from_sbs_source2"]
    word = _make_word(case["word"])
    sbs = _make_sbs_for_case(case["sbs"])

    action, _changes = _process_row_refactored(
        word, sbs, fixtures["source_value"], fixtures["target"]
    )

    assert action == "from_sbs"
    expected = case["expected_changes"]
    for field, val in expected.items():
        assert getattr(sbs, field) == val


def test_synthetic_from_dpd_existing_sbs() -> None:
    fixtures = _load_fixtures()
    case = fixtures["synthetic_cases"]["from_dpd_existing_sbs"]
    word = _make_word(case["word"])
    sbs = _make_sbs_for_case(case["sbs"])

    action, _changes = _process_row_refactored(
        word, sbs, fixtures["source_value"], fixtures["target"]
    )

    assert action == "from_dpd"
    expected = case["expected_changes"]
    for field, val in expected.items():
        assert getattr(sbs, field) == val


def test_synthetic_from_dpd_source2() -> None:
    fixtures = _load_fixtures()
    case = fixtures["synthetic_cases"]["from_dpd_source2"]
    word = _make_word(case["word"])
    sbs = _make_sbs_for_case(case["sbs"])

    action, _changes = _process_row_refactored(
        word, sbs, fixtures["source_value"], fixtures["target"]
    )

    assert action == "from_dpd"
    expected = case["expected_changes"]
    for field, val in expected.items():
        assert getattr(sbs, field) == val


def test_synthetic_from_dpd_new_sbs() -> None:
    fixtures = _load_fixtures()
    case = fixtures["synthetic_cases"]["from_dpd_new_sbs"]
    word = _make_word(case["word"])
    sbs = _make_sbs_for_case(case["sbs"])

    action, _changes = _process_row_refactored(
        word, sbs, fixtures["source_value"], fixtures["target"]
    )

    assert action == "new_row"
    # word.sbs was created by the function
    new_sbs = word.sbs
    assert new_sbs is not None
    expected = case["expected_changes"]
    for field, val in expected.items():
        assert getattr(new_sbs, field) == val


def test_synthetic_no_match() -> None:
    fixtures = _load_fixtures()
    case = fixtures["synthetic_cases"]["no_match"]
    word = _make_word(case["word"])
    sbs = _make_sbs_for_case(case["sbs"])

    action, changes = _process_row_refactored(
        word, sbs, fixtures["source_value"], fixtures["target"]
    )

    assert action == "none"
    assert changes == []


# ---- Query equivalence test (real DB, read-only) ----


def test_merged_query_equals_union_of_original_queries() -> None:
    """Verify the merged single query returns the same row IDs as the union of
    the three original queries.  Read-only DB test against golden fixtures."""
    from sqlalchemy import and_, not_, or_
    from sqlalchemy.orm import joinedload

    from db.db_helpers import get_db_session
    from db.models import SBS, DpdHeadword
    from tools.paths import ProjectPaths

    fixtures = _load_fixtures()
    source_value = fixtures["source_value"]

    pth = ProjectPaths()
    session = get_db_session(pth.dpd_db_path)

    try:
        # Original query 1: already have
        rows_already_have = (
            session.query(DpdHeadword)
            .options(joinedload(DpdHeadword.sbs))
            .outerjoin(SBS)
            .filter(SBS.vib_source == source_value)
            .all()
        )
        ids_already = [row.id for row in rows_already_have]

        # Original query 2: sbs_source match (excluding already-have)
        q2 = (
            session.query(DpdHeadword)
            .options(joinedload(DpdHeadword.sbs))
            .outerjoin(SBS)
            .filter(
                or_(
                    SBS.sbs_source_1 == source_value,
                    SBS.sbs_source_2 == source_value,
                ),
            )
        )
        if ids_already:
            q2 = q2.filter(not_(DpdHeadword.id.in_(ids_already)))
        rows_sbs = q2.all()
        ids_sbs = [row.id for row in rows_sbs]

        # Original query 3: dpd source match (excluding already-have + sbs)
        ids_exclude = ids_sbs + ids_already
        q3 = (
            session.query(DpdHeadword)
            .options(joinedload(DpdHeadword.sbs))
            .outerjoin(SBS)
            .filter(
                and_(
                    DpdHeadword.meaning_1 != "",
                    or_(
                        DpdHeadword.source_1 == source_value,
                        DpdHeadword.source_2 == source_value,
                    ),
                ),
            )
        )
        if ids_exclude:
            q3 = q3.filter(not_(DpdHeadword.id.in_(ids_exclude)))
        rows_dpd = q3.all()
        ids_dpd = [row.id for row in rows_dpd]

        # Merged query
        rows_merged = (
            session.query(DpdHeadword)
            .options(joinedload(DpdHeadword.sbs))
            .outerjoin(SBS)
            .filter(
                or_(
                    SBS.vib_source == source_value,
                    SBS.sbs_source_1 == source_value,
                    SBS.sbs_source_2 == source_value,
                    and_(
                        DpdHeadword.meaning_1 != "",
                        or_(
                            DpdHeadword.source_1 == source_value,
                            DpdHeadword.source_2 == source_value,
                        ),
                    ),
                ),
            )
            .all()
        )
        ids_merged = sorted([row.id for row in rows_merged])

        # Union of original queries
        all_ids = sorted(set(ids_already + ids_sbs + ids_dpd))

        assert ids_merged == all_ids, (
            f"Merged query returned {len(ids_merged)} rows, "
            f"union of original queries returned {len(all_ids)} rows"
        )

        # Cross-check against golden fixture
        assert ids_merged == sorted(fixtures["ids_merged"]), (
            "Merged query result changed from golden fixture"
        )
    finally:
        session.close()
