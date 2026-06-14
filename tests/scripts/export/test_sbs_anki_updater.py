"""Tests for normalize_anki_text, _natural_sort_key, and deck_selector."""

from types import SimpleNamespace
from typing import cast

import pytest

from db.models import DpdHeadword
from scripts.export.sbs_anki_updater import (
    _natural_sort_key,
    deck_selector,
    normalize_anki_text,
)


# ── normalize_anki_text ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "value, expected",
    [
        ("hello", "hello"),
        (None, ""),
        (42, "42"),
        ("", ""),
        ("  spaces  ", "  spaces  "),
        (3.14, "3.14"),
    ],
)
def test_normalize_anki_text(value: object, expected: str) -> None:
    assert normalize_anki_text(value) == expected


# ── _natural_sort_key ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "items, expected",
    [
        (["DHP10", "DHP2", "DHP1"], ["DHP1", "DHP2", "DHP10"]),
        (["source20", "source3", "source1"], ["source1", "source3", "source20"]),
        (["MN10", "MN2", "DN1"], ["DN1", "MN2", "MN10"]),
    ],
)
def test_natural_sort_key_ordering(items: list[str], expected: list[str]) -> None:
    assert sorted(items, key=_natural_sort_key) == expected


def test_natural_sort_key_empty_string() -> None:
    assert _natural_sort_key("") == [""]


# ── deck_selector helpers ─────────────────────────────────────────────────────


def _make_sbs(**kwargs: object) -> SimpleNamespace:
    defaults: dict[str, object] = dict(
        sbs_index=None,
        dhp_source=None,
        sbs_chant_pali_1=None,
        sbs_chant_pali_2=None,
        vib_source=None,
        class_anki=None,
        discourses_example=None,
        discourses_source=None,
        vib_example=None,
        pat_example=None,
        dhp_example=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_hw(
    *,
    sbs: SimpleNamespace | None = None,
    rt: object = None,
    phonetic: object = None,
) -> DpdHeadword:
    return cast(DpdHeadword, SimpleNamespace(sbs=sbs, rt=rt, phonetic=phonetic))


# ── deck_selector tests ───────────────────────────────────────────────────────


def test_deck_selector_no_sbs() -> None:
    assert deck_selector(_make_hw()) == []


def test_deck_selector_sbs_index() -> None:
    result = deck_selector(_make_hw(sbs=_make_sbs(sbs_index=1)))
    assert "SBS Pali-English Vocab" in result
    assert "Пали Словарь" in result


def test_deck_selector_dhp_source() -> None:
    result = deck_selector(_make_hw(sbs=_make_sbs(dhp_source="DHP1")))
    assert "Pali DHP vocab" in result


def test_deck_selector_chant_pali_1() -> None:
    result = deck_selector(
        _make_hw(sbs=_make_sbs(sbs_chant_pali_1="Karaṇīya-metta-sutta"))
    )
    assert "Pali Parittas" in result


def test_deck_selector_chant_pali_2() -> None:
    result = deck_selector(_make_hw(sbs=_make_sbs(sbs_chant_pali_2="Ratana-sutta")))
    assert "Pali Parittas" in result


def test_deck_selector_vib_source() -> None:
    result = deck_selector(_make_hw(sbs=_make_sbs(vib_source="Vib1")))
    assert "Pali Bhikkhu Vibhanga" in result


def test_deck_selector_class_anki_numbered() -> None:
    result = deck_selector(_make_hw(sbs=_make_sbs(class_anki=5)))
    assert "Vocab Pali Class::05.Class" in result
    assert "Пали Словарь" in result


def test_deck_selector_class_anki_out_of_range() -> None:
    result = deck_selector(_make_hw(sbs=_make_sbs(class_anki=30)))
    assert "Vocab Pali Class" in result
    assert "Vocab Pali Class::30.Class" not in result


def test_deck_selector_class_anki_with_rt() -> None:
    result = deck_selector(_make_hw(sbs=_make_sbs(class_anki=3), rt=object()))
    assert "Roots Pali Class" in result


def test_deck_selector_class_anki_with_phonetic() -> None:
    result = deck_selector(_make_hw(sbs=_make_sbs(class_anki=3), phonetic="some"))
    assert "Phonetic Changes Pali Class" in result


def test_deck_selector_discourses_no_source() -> None:
    result = deck_selector(_make_hw(sbs=_make_sbs(discourses_example="text")))
    assert "Suttas Advanced Pali Class" in result


def test_deck_selector_no_duplicates() -> None:
    result = deck_selector(
        _make_hw(
            sbs=_make_sbs(sbs_index=1, class_anki=5, dhp_source="DHP1"),
            rt=object(),
            phonetic="p",
        )
    )
    assert len(result) == len(set(result))
