"""Tests for apply_all_corrections: field-update logic with ALLOWED_FIELDS filtering."""

from types import SimpleNamespace

from db.models import DpdHeadword

ALLOWED_FIELDS: set[str] = set(DpdHeadword.__table__.columns.keys()) - {"id", "comment"}  # type: ignore[attr-defined]


def _apply_correction(
    db_entry: SimpleNamespace, correction_data: dict[str, object]
) -> bool:
    """Mirror of apply_all_corrections._apply_correction for isolated testing."""
    any_changed = False
    for field_name, new_value in correction_data.items():
        if field_name not in ALLOWED_FIELDS:
            continue
        current_value = getattr(db_entry, field_name)
        if current_value != new_value:
            setattr(db_entry, field_name, new_value)
            any_changed = True
    return any_changed


def test_field_change_sets_flag() -> None:
    hw = SimpleNamespace(meaning_1="old meaning")
    changed = _apply_correction(hw, {"meaning_1": "new meaning"})
    assert changed is True
    assert hw.meaning_1 == "new meaning"


def test_same_value_leaves_flag_false() -> None:
    hw = SimpleNamespace(meaning_1="same")
    changed = _apply_correction(hw, {"meaning_1": "same"})
    assert changed is False
    assert hw.meaning_1 == "same"


def test_comment_field_is_skipped() -> None:
    hw = SimpleNamespace(meaning_1="original")
    changed = _apply_correction(hw, {"comment": "some note"})
    assert changed is False
    assert not hasattr(hw, "comment")


def test_id_field_is_skipped() -> None:
    hw = SimpleNamespace()
    changed = _apply_correction(hw, {"id": 999})
    assert changed is False
    assert not hasattr(hw, "id")


def test_unknown_field_is_skipped() -> None:
    hw = SimpleNamespace(meaning_1="original")
    changed = _apply_correction(hw, {"nonexistent_field": "value"})
    assert changed is False
    assert not hasattr(hw, "nonexistent_field")


def test_mixed_corrections_partial_change() -> None:
    hw = SimpleNamespace(meaning_1="old", pos="noun")
    changed = _apply_correction(
        hw, {"meaning_1": "new", "pos": "noun", "comment": "ignore me"}
    )
    assert changed is True
    assert hw.meaning_1 == "new"
    assert hw.pos == "noun"


def test_multiple_fields_all_changed() -> None:
    hw = SimpleNamespace(meaning_1="a", pos="verb")
    changed = _apply_correction(hw, {"meaning_1": "b", "pos": "noun"})
    assert changed is True
    assert hw.meaning_1 == "b"
    assert hw.pos == "noun"


def test_allowed_fields_excludes_protected() -> None:
    assert "id" not in ALLOWED_FIELDS
    assert "comment" not in ALLOWED_FIELDS


def test_allowed_fields_includes_meaning() -> None:
    assert "meaning_1" in ALLOWED_FIELDS
    assert "pos" in ALLOWED_FIELDS
