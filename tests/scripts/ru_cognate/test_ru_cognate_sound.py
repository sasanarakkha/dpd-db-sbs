"""Tests for the code-side sound label used by the ru_cognate verify step."""

import pytest

from scripts.ru_cognate.ru_cognate_sound import skeleton, sound_label, sources


@pytest.mark.parametrize(
    ("unit_key", "sanskrit", "word", "expected"),
    [
        ("√agg", "ag", "огонь", "close"),
        ("√akkh", "akṣ", "око", "close"),
        ("√ad", "ad", "еда", "close"),
        ("√is", "iṣ", "искать", "close"),
        ("√kās 2", "kās", "кашель", "close"),
        ("bhātar", "bhrātṛ", "брат", "close"),
        ("mātar", "mātar, mātṛ", "мать", "close"),
        ("dvi", "dvi, dva", "два", "close"),
        ("ti", "tri", "три", "close"),
        ("nava1", "nava", "новый", "close"),
        ("√dvar", "dvṛ", "дверь", "close"),
        ("√budh", "budh", "будить", "close"),
        ("√ñā", "jñā", "знать", "close"),
        ("bhū", "bhrū", "бровь", "close"),
        ("cha", "ṣaḍ, ṣaṭka < ṣaṣ", "шесть", "close"),
        ("dhava", "vidhavā", "вдова", "close"),
        ("√ud", "ud", "вода", "weak"),
        ("√an", "an", "вонь", "weak"),
        ("√i 1", "i", "идти", "weak"),
        ("aṭṭha", "aṣṭan", "восемь", "weak"),
        ("nāma", "nāma, nāman", "имя", "weak"),
        ("√ad", "ad", "медведь", "weak"),
        ("√kath", "kath", "кой", "weak"),
        ("√ad", "ad", "есть", "none"),
    ],
)
def test_sound_label(unit_key: str, sanskrit: str, word: str, expected: str) -> None:
    assert sound_label(unit_key, sanskrit, word) == expected


def test_skeleton_collapses_and_skips_aspirate() -> None:
    assert skeleton("akkh") == ["K"]


def test_skeleton_keeps_first_two_classes() -> None:
    assert skeleton("bhātar") == ["B", "T"]


def test_skeleton_vowel_only_is_empty() -> None:
    assert skeleton("i") == []


def test_sources_strip_root_sign_and_homonym_number() -> None:
    assert sources("√kus 2", "kuṣ √kus") == ["kus", "kuṣ", "kus"]
