"""Golden-master tests for tools/ai_related.py against fixtures captured pre-refactor."""

import json
from pathlib import Path

from tools.ai_related import (
    generate_messages_for_meaning,
    generate_messages_for_meaning_lit,
    generate_messages_for_meaning_ta,
    generate_messages_for_notes,
    load_translation_examples,
    replace_abbreviations,
)
from tools.paths_dps import DPSPaths

FIXTURE_PATH = Path(__file__).parent / "test_ai_related_fixtures.json"
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

dpspth = DPSPaths()


def test_load_translation_examples_ru() -> None:
    assert (
        load_translation_examples(dpspth, lang="ru")
        == FIXTURES["load_translation_examples_ru"]
    )


def test_load_translation_examples_ta() -> None:
    assert (
        load_translation_examples(dpspth, lang="ta")
        == FIXTURES["load_translation_examples_ta"]
    )


def test_replace_abbreviations() -> None:
    for case, expected in FIXTURES["replace_abbreviations"].items():
        assert replace_abbreviations(case) == expected


def test_generate_messages_for_meaning() -> None:
    result = generate_messages_for_meaning(
        "dhamma", "masc, nom sg", "phenomenon; nature; teaching", "Dhammā anattā."
    )
    assert result == FIXTURES["generate_messages_for_meaning"]


def test_generate_messages_for_meaning_synonyms() -> None:
    result = generate_messages_for_meaning(
        "dhamma",
        "masc, nom sg",
        "phenomenon; nature; teaching",
        "",
        synonyms=True,
    )
    assert result == FIXTURES["generate_messages_for_meaning_synonyms"]


def test_generate_messages_for_meaning_with_example() -> None:
    result = generate_messages_for_meaning(
        "dhamma",
        "masc, nom sg",
        "phenomenon",
        "context here",
        translation_example="example here",
    )
    assert result == FIXTURES["generate_messages_for_meaning_with_example"]


def test_generate_messages_for_notes() -> None:
    result = generate_messages_for_notes("dhamma", "masc, nom sg", "see also adhamma")
    assert result == FIXTURES["generate_messages_for_notes"]


def test_generate_messages_for_meaning_ta() -> None:
    result = generate_messages_for_meaning_ta(
        "dhamma", "masc, nom sg", "phenomenon; nature; teaching", "Dhammā anattā."
    )
    assert result == FIXTURES["generate_messages_for_meaning_ta"]


def test_generate_messages_for_meaning_lit() -> None:
    result = generate_messages_for_meaning_lit(
        "dhamma", "masc, nom sg", "that which is held", "феномен"
    )
    assert result == FIXTURES["generate_messages_for_meaning_lit"]


def test_generate_messages_for_meaning_lit_no_ru() -> None:
    result = generate_messages_for_meaning_lit(
        "dhamma", "masc, nom sg", "that which is held"
    )
    assert result == FIXTURES["generate_messages_for_meaning_lit_no_ru"]


def test_generate_messages_for_meaning_with_root_examples() -> None:
    result = generate_messages_for_meaning(
        "accagamā 1",
        "verb, aorist",
        "went beyond",
        "",
        root_examples=[
            ("samannāgata", "endowed with", "наделённый"),
            ("gacchati 2", "goes", "идёт"),
        ],
        root_key="√gam",
        root_ru_meaning="идти",
    )
    assert result == FIXTURES["generate_messages_for_meaning_with_root_examples"]
    assert "√√" not in result[1]["content"]


def test_generate_messages_for_meaning_lit_with_construction() -> None:
    result = generate_messages_for_meaning_lit(
        "accagamā 1",
        "verb, aorist",
        "went beyond",
        "переступил",
        construction="ati > aty > acc + a + √gam + ā",
    )
    assert result == FIXTURES["generate_messages_for_meaning_lit_with_construction"]


def test_generate_messages_for_meaning_lit_with_root_examples() -> None:
    result = generate_messages_for_meaning_lit(
        "accagamā 1",
        "verb, aorist",
        "went beyond",
        "переступил",
        construction="ati > aty > acc + a + √gam + ā",
        root_examples=[
            ("sugata 1", "su + √gam + ta", "well gone", "хорошо ушедший"),
            ("agata 1", "na > a + √gam + ta", "", "не ушедший"),
        ],
        root_key="√gam",
        root_ru_meaning="идти",
    )
    assert result == FIXTURES["generate_messages_for_meaning_lit_with_root_examples"]
    assert "√√" not in result[1]["content"]
