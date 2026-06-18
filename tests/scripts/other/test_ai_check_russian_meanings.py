from scripts.other.ai_check_russian_meanings import _MODE_NOTES

_ALL_MODES = {
    "meaning",
    "meaning_raw",
    "meaning_ru_raw",
    "meaning_raw_list",
    "meaning_lit",
    "meaning_lit_list",
    "notes",
    "notes_raw",
}


def test_mode_notes_keys_are_known_modes() -> None:
    assert _MODE_NOTES.keys() <= _ALL_MODES


def test_default_mode_has_no_note() -> None:
    assert "meaning" not in _MODE_NOTES


def test_every_non_default_mode_has_a_note() -> None:
    assert set(_MODE_NOTES.keys()) == _ALL_MODES - {"meaning"}


def test_mode_notes_are_non_empty_strings() -> None:
    assert all(isinstance(v, str) and v for v in _MODE_NOTES.values())
