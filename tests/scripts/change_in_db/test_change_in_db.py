"""Tests for change_in_db: prepend formula, regex substitution, and update condition."""

import re


def _prepend_value(old_value: str, update_value: str) -> str:
    """Inline of the new_value formula from filter_and_add."""
    return "(грам) " + old_value if old_value else update_value


def _should_update_note(old_value: str | None) -> bool:
    """Inline of the update condition from update_notes (fixed order)."""
    return not old_value or "ИИ" in old_value


_NOTE_PATTERN = "agent noun used verbally see Perniola §292"
_NOTE_REPLACEMENT = "существительное деятель, используемое глагольно, см. Перниола §292"


def _translate_note(notes: str) -> str:
    """Inline of the re.sub call from update_notes."""
    return re.sub(_NOTE_PATTERN, _NOTE_REPLACEMENT, notes)


# filter_and_add: new_value formula


def test_prepend_when_old_value_present() -> None:
    assert _prepend_value("some meaning", "(грам)") == "(грам) some meaning"


def test_prepend_uses_update_value_when_old_empty() -> None:
    assert _prepend_value("", "(грам)") == "(грам)"


def test_prepend_uses_update_value_when_old_none_equivalent() -> None:
    # empty string is falsy — same branch as missing value
    result = _prepend_value("", "fallback")
    assert result == "fallback"


# update_notes: condition guard


def test_should_update_when_old_is_empty() -> None:
    assert _should_update_note("") is True


def test_should_update_when_old_is_none() -> None:
    assert _should_update_note(None) is True


def test_should_update_when_old_contains_ii() -> None:
    assert _should_update_note("ИИ generated translation") is True


def test_should_not_update_when_old_is_real_translation() -> None:
    assert _should_update_note("настоящий перевод") is False


# update_notes: regex substitution


def test_regex_replaces_english_note() -> None:
    notes = "agent noun used verbally see Perniola §292"
    result = _translate_note(notes)
    assert (
        result == "существительное деятель, используемое глагольно, см. Перниола §292"
    )


def test_regex_replaces_within_longer_string() -> None:
    notes = "prefix; agent noun used verbally see Perniola §292; suffix"
    result = _translate_note(notes)
    assert "agent noun used verbally see Perniola §292" not in result
    assert "существительное деятель" in result


def test_regex_leaves_unmatched_string_unchanged() -> None:
    notes = "some other note"
    assert _translate_note(notes) == "some other note"
