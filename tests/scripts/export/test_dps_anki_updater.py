"""Tests for dps_anki_updater.py — pure logic functions."""

from __future__ import annotations

from scripts.export.dps_anki_updater import deck_selector, make_search_query


class FakeSBS:
    """Minimal stand-in for db.models.SBS — only exposes the attrs deck_selector reads."""

    def __init__(self) -> None:
        self.sbs_chapter_1: str | None = None
        self.sbs_chapter_2: str | None = None
        self.dhp_example: str | None = None
        self.pat_example: str | None = None
        self.vib_example: str | None = None
        self.class_anki: str | None = None
        self.discourses_example: str | None = None


class FakeHeadword:
    """Minimal stand-in for db.models.DpdHeadword — only exposes the attrs deck_selector reads."""

    def __init__(self) -> None:
        self.sbs: FakeSBS | None = None


def test_make_search_query_single_deck() -> None:
    assert make_search_query(["Pali"]) == 'deck:"Pali"'


def test_make_search_query_multiple_decks() -> None:
    assert make_search_query(["Pali", "SBS"]) == 'deck:"Pali" or deck:"SBS"'


def test_deck_selector_returns_pali_when_sbs_chapter_1() -> None:
    i = FakeHeadword()
    i.sbs = FakeSBS()
    i.sbs.sbs_chapter_1 = "Chapter 1"
    assert deck_selector(i) == "Pali"


def test_deck_selector_returns_pali_when_sbs_chapter_2() -> None:
    i = FakeHeadword()
    i.sbs = FakeSBS()
    i.sbs.sbs_chapter_2 = "Chapter 2"
    assert deck_selector(i) == "Pali"


def test_deck_selector_returns_pali_when_dhp_example() -> None:
    i = FakeHeadword()
    i.sbs = FakeSBS()
    i.sbs.dhp_example = "DHP ex"
    assert deck_selector(i) == "Pali"


def test_deck_selector_returns_pali_when_pat_example() -> None:
    i = FakeHeadword()
    i.sbs = FakeSBS()
    i.sbs.pat_example = "PAT ex"
    assert deck_selector(i) == "Pali"


def test_deck_selector_returns_pali_when_vib_example() -> None:
    i = FakeHeadword()
    i.sbs = FakeSBS()
    i.sbs.vib_example = "VIB ex"
    assert deck_selector(i) == "Pali"


def test_deck_selector_returns_pali_when_class_anki() -> None:
    i = FakeHeadword()
    i.sbs = FakeSBS()
    i.sbs.class_anki = "Class"
    assert deck_selector(i) == "Pali"


def test_deck_selector_returns_pali_when_discourses_example() -> None:
    i = FakeHeadword()
    i.sbs = FakeSBS()
    i.sbs.discourses_example = "Disc ex"
    assert deck_selector(i) == "Pali"


def test_deck_selector_returns_none_when_no_sbs() -> None:
    i = FakeHeadword()
    i.sbs = None
    assert deck_selector(i) is None


def test_deck_selector_returns_none_when_sbs_has_no_content() -> None:
    i = FakeHeadword()
    i.sbs = FakeSBS()
    assert deck_selector(i) is None
