"""Golden-master tests for tools/sbs_table_functions.py, captured from real shared_data/sbs_csvs files."""

import json
from pathlib import Path

import pytest

from tools import sbs_table_functions
from tools.sbs_table_functions import SBS_table_tools, paragraphs_are_similar_sbs

FIXTURE_PATH = Path(__file__).parent / "test_sbs_table_functions_fixtures.json"
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def tools() -> SBS_table_tools:
    return SBS_table_tools()


def test_load_chant_index_map(tools: SBS_table_tools) -> None:
    assert tools.load_chant_index_map() == FIXTURES["chant_index_map"]


def test_load_chant_link_map(tools: SBS_table_tools) -> None:
    assert tools.load_chant_link_map() == FIXTURES["chant_link_map"]


def test_load_valid_chants(tools: SBS_table_tools) -> None:
    assert tools.load_valid_chants() == FIXTURES["valid_chants"]


def test_load_valid_mappings(tools: SBS_table_tools) -> None:
    mappings = sorted(tuple(m) for m in tools.load_valid_mappings())
    expected = sorted(tuple(m) for m in FIXTURES["valid_mappings"])
    assert mappings == expected


def test_load_class_link_map(tools: SBS_table_tools) -> None:
    expected = {int(k): v for k, v in FIXTURES["class_link_map"].items()}
    assert tools.load_class_link_map() == expected


@pytest.mark.parametrize("chant", list(FIXTURES["fetch_results"].keys()))
def test_fetch_sbs_index(tools: SBS_table_tools, chant: str) -> None:
    result = tools.fetch_sbs_index(chant)
    expected = FIXTURES["fetch_results"][chant]
    assert (list(result) if result else result) == expected


def test_find_closest_chant_exact(tools: SBS_table_tools) -> None:
    valid_chants = FIXTURES["valid_chants"]
    result = tools.find_closest_chant(valid_chants[0], threshold=0.8)
    expected = FIXTURES["closest_results"]["exact"]
    assert (list(result) if result else result) == expected


def test_find_closest_chant_near(tools: SBS_table_tools) -> None:
    valid_chants = FIXTURES["valid_chants"]
    close_match_input = valid_chants[0][:-1]
    result = tools.find_closest_chant(close_match_input, threshold=0.8)
    expected = FIXTURES["closest_results"]["near"]
    assert (list(result) if result else result) == expected


def test_find_closest_chant_no_match(tools: SBS_table_tools) -> None:
    result = tools.find_closest_chant("xyz completely wrong", threshold=0.8)
    assert result == FIXTURES["closest_results"]["no_match"]


@pytest.mark.parametrize("lemma", list(FIXTURES["audio_results"].keys()))
def test_generate_sbs_audio(tools: SBS_table_tools, lemma: str) -> None:
    assert tools.generate_sbs_audio(lemma) == FIXTURES["audio_results"][lemma]


def test_paragraphs_are_similar_sbs_identical() -> None:
    assert (
        paragraphs_are_similar_sbs("hello world", "hello world", 0.8)
        == FIXTURES["paragraph_results"]["identical"]
    )


def test_paragraphs_are_similar_sbs_different() -> None:
    assert (
        paragraphs_are_similar_sbs("hello world", "completely unrelated text", 0.8)
        == FIXTURES["paragraph_results"]["different"]
    )


def test_paragraphs_are_similar_sbs_close() -> None:
    assert (
        paragraphs_are_similar_sbs("hello world foo", "hello world bar", 0.5)
        == FIXTURES["paragraph_results"]["close"]
    )


def test_get_dhp_translation_hit(
    tools: SBS_table_tools, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        sbs_table_functions,
        "_load_dhp_translations_map",
        lambda: {
            "DHP1": {
                "source": "DHP1",
                "translation": "figurative text",
                "literal_translation": "literal text",
            }
        },
    )
    assert (
        tools.get_dhp_translation("DHP1")
        == "Literal: literal text<br>Figurative: figurative text"
    )


def test_get_dhp_translation_miss(
    tools: SBS_table_tools, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sbs_table_functions, "_load_dhp_translations_map", dict)
    assert tools.get_dhp_translation("DHP999") == ""


def test_get_dhp_translation_falsy_source(tools: SBS_table_tools) -> None:
    assert tools.get_dhp_translation("") == ""
