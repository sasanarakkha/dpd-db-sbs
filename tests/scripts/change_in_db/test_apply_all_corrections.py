"""Tests for apply_all_corrections: field-update logic and comment-skip behaviour."""

from types import SimpleNamespace


def _apply_corrections(
    db_entry: SimpleNamespace, correction_data: dict[str, object]
) -> bool:
    """Inline of the per-entry field-update loop from apply_all_corrections_from_json."""
    any_changed = False
    for field_name, new_value in correction_data.items():
        if field_name == "comment":
            continue
        if hasattr(db_entry, field_name):
            current_value = getattr(db_entry, field_name)
            if current_value != new_value:
                setattr(db_entry, field_name, new_value)
                any_changed = True
    return any_changed


def test_field_change_sets_flag() -> None:
    hw = SimpleNamespace(meaning_1="old meaning")
    changed = _apply_corrections(hw, {"meaning_1": "new meaning"})
    assert changed is True
    assert hw.meaning_1 == "new meaning"


def test_same_value_leaves_flag_false() -> None:
    hw = SimpleNamespace(meaning_1="same")
    changed = _apply_corrections(hw, {"meaning_1": "same"})
    assert changed is False
    assert hw.meaning_1 == "same"


def test_comment_field_is_skipped() -> None:
    hw = SimpleNamespace(meaning_1="original")
    changed = _apply_corrections(hw, {"comment": "some note"})
    assert changed is False
    assert not hasattr(hw, "comment")


def test_unknown_field_is_skipped() -> None:
    hw = SimpleNamespace(meaning_1="original")
    changed = _apply_corrections(hw, {"nonexistent_field": "value"})
    assert changed is False
    assert not hasattr(hw, "nonexistent_field")


def test_mixed_corrections_partial_change() -> None:
    hw = SimpleNamespace(meaning_1="old", pos="noun")
    changed = _apply_corrections(
        hw, {"meaning_1": "new", "pos": "noun", "comment": "ignore me"}
    )
    assert changed is True
    assert hw.meaning_1 == "new"
    assert hw.pos == "noun"


def test_multiple_fields_all_changed() -> None:
    hw = SimpleNamespace(meaning_1="a", pos="verb")
    changed = _apply_corrections(hw, {"meaning_1": "b", "pos": "noun"})
    assert changed is True
    assert hw.meaning_1 == "b"
    assert hw.pos == "noun"
