import sys
from pathlib import Path
from typing import Any

import pytest

from kamma.translate.scripts import ai_check_russian_meanings
from kamma.translate.scripts.ai_check_russian_meanings import _MODE_NOTES

_ALL_MODES = {
    "meaning",
    "meaning_raw",
    "russian_grammar_meaning_raw",
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


class _FakeChecker:
    def __init__(self, **_kwargs: Any) -> None:
        self.checked_ids_file = Path("unused")

    def apply_invalidation(self, _session: Any) -> tuple[int, int]:
        return 0, 0

    def get_total_count_with_session(self, _session: Any) -> int:
        return 9

    def run_analysis(self, **_kwargs: Any) -> int:
        return 7


def test_main_prints_checked_line_with_verdict_count(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["ai_check_russian_meanings.py", "--limit", "9"])
    monkeypatch.setattr(
        ai_check_russian_meanings, "get_db_session", lambda _p: object()
    )
    monkeypatch.setattr(
        ai_check_russian_meanings, "RussianMeaningChecker", _FakeChecker
    )
    ai_check_russian_meanings.main()
    lines = capsys.readouterr().out.splitlines()
    assert "checked 7" in [line.strip() for line in lines]
