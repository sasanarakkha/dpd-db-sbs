"""Golden-master tests for anki_csv.py — pure/logic function outputs."""

import csv
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.export import anki_csv
from tools.paths_dps import DPSPaths

FIXTURE_PATH = Path(__file__).parent / "test_anki_csv_fixtures.json"
FIXTURES: dict = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_get_common_root_examples_fixtures() -> None:
    """Compare all fixture cases against actual function output."""
    cases = {
        "empty": ("", ""),
        "no_main_verb": ("kara, gaccha", ""),
        "with_main_verb": ("kara, gaccha, passa", "gaccha"),
        "single": ("kara", "gaccha"),
    }
    for key, (root_example, main_verb) in cases.items():
        expected = FIXTURES["get_common_root_examples"][key]
        assert anki_csv.get_common_root_examples(root_example, main_verb) == expected


def test_join() -> None:
    cases = FIXTURES["join"]
    for key, args in _join_args().items():
        assert anki_csv.join(*args) == cases[key], f"join failed for {key}"


def _join_args():
    return {
        "empty": (),
        "single": ("hello",),
        "multiple": ("foo", "bar", "baz"),
        "with_spaces": ("foo bar", "baz"),
        "with_none": ("foo", None, "baz"),
        "all_none": (None, None),
    }


def test_join_fixtures() -> None:
    cases = FIXTURES["join"]
    for key, args in _join_args().items():
        assert anki_csv.join(*args) == cases[key]


def test_none_to_empty() -> None:
    cases = FIXTURES["none_to_empty"]
    inputs = {
        "all_strings": ["a", "b", "c"],
        "all_none": [None, None],
        "mixed": ["a", None, "b", None],
        "empty_list": [],
    }
    for key in cases:
        assert anki_csv.none_to_empty(inputs[key]) == cases[key]


def test_get_feedback() -> None:
    cases = FIXTURES["get_feedback"]
    for deck in ("dps", "sbs", "dhp"):
        hw = MagicMock()
        hw.lemma_1 = "kamma"
        assert anki_csv.get_feedback(hw, deck) == cases[f"{deck}_deck"]


def test_get_root_info_with_rt() -> None:
    expected = FIXTURES["get_root_info"]["with_rt"]
    hw = MagicMock()
    hw.root_key = "√gam 1"
    hw.rt = MagicMock()
    hw.rt.sanskrit_root = "√gam"
    hw.rt.sanskrit_root_meaning = "to go"
    hw.rt.sanskrit_root_class = "1"
    hw.rt.root_has_verb = "･"
    hw.rt.root_group = "gaccha"
    hw.rt.root_meaning = "to go"
    hw.root_sign = "a"
    hw.root_base = "gam"
    assert list(anki_csv.get_root_info(hw)) == expected


def test_get_root_info_without_rt() -> None:
    """Test the branch that triggers NameError in original code."""
    expected = FIXTURES["get_root_info"]["without_rt"]
    hw = MagicMock()
    hw.root_key = "√kar 1"
    hw.rt = None
    hw.root_sign = ""
    hw.root_base = ""
    assert list(anki_csv.get_root_info(hw)) == expected


def test_get_grammar_and_meaning() -> None:
    cases = FIXTURES["get_grammar_and_meaning"]
    hw_m1 = MagicMock()
    hw_m1.grammar = "pr"
    hw_m1.neg = "neg"
    hw_m1.verb = "kar"
    hw_m1.trans = "act"
    hw_m1.plus_case = "acc"
    hw_m1.meaning_1 = "to do"
    hw_m1.meaning_2 = "to make"
    hw_m1.meaning_lit = "lit. to carry"
    assert list(anki_csv.get_grammar_and_meaning(hw_m1)) == cases["with_meaning_1"]

    hw_m2 = MagicMock()
    hw_m2.grammar = "pr"
    hw_m2.neg = "neg"
    hw_m2.verb = "kar"
    hw_m2.trans = "act"
    hw_m2.plus_case = "acc"
    hw_m2.meaning_1 = None
    hw_m2.meaning_2 = "alternative meaning"
    hw_m2.meaning_lit = None
    assert list(anki_csv.get_grammar_and_meaning(hw_m2)) == cases["with_meaning_2"]


def test_get_construction() -> None:
    cases = FIXTURES["get_construction"]

    hw = MagicMock()
    hw.construction = "kar + a"
    hw.derivative = "√"
    hw.suffix = "a"
    hw.phonetic = "kar + a → kara"
    hw.compound_type = "tappurisa"
    hw.compound_construction = "kamma + dha"
    assert list(anki_csv.get_construction(hw)) == cases["with_construction"]

    hw2 = MagicMock()
    hw2.construction = None
    hw2.derivative = ""
    hw2.suffix = ""
    hw2.phonetic = None
    hw2.compound_type = ""
    hw2.compound_construction = ""
    assert list(anki_csv.get_construction(hw2)) == cases["without_construction"]


def test_get_sbs_info() -> None:
    cases = FIXTURES["get_sbs_info"]

    hw = MagicMock()
    hw.sbs = MagicMock()
    hw.sbs.sbs_source_1 = "AN 1.1\nline2"
    hw.sbs.sbs_sutta_1 = "AN 1.1\ncontinuation"
    hw.sbs.sbs_example_1 = "Example text\nmore"
    hw.sbs.sbs_chant_pali_1 = "Karaṇīya-metta-sutta"
    hw.sbs.sbs_chant_eng_1 = "The Karaniya Sutta"
    hw.sbs.sbs_chapter_1 = "1"
    hw.sbs.sbs_source_2 = ""
    hw.sbs.sbs_sutta_2 = ""
    hw.sbs.sbs_example_2 = ""
    hw.sbs.sbs_chant_pali_2 = ""
    hw.sbs.sbs_chant_eng_2 = ""
    hw.sbs.sbs_chapter_2 = ""
    hw.antonym = ""
    hw.synonym = ""
    hw.variant = ""
    hw.commentary = ""
    hw.notes = "Some note\nwith newline"
    assert list(anki_csv.get_sbs_info(hw)) == cases["with_sbs_chapter"]

    hw2 = MagicMock()
    hw2.sbs = MagicMock()
    hw2.sbs.sbs_source_1 = None
    hw2.sbs.sbs_sutta_1 = None
    hw2.sbs.sbs_example_1 = None
    hw2.sbs.sbs_chant_pali_1 = None
    hw2.sbs.sbs_chant_eng_1 = None
    hw2.sbs.sbs_chapter_1 = None
    hw2.sbs.sbs_source_2 = None
    hw2.sbs.sbs_sutta_2 = None
    hw2.sbs.sbs_example_2 = None
    hw2.sbs.sbs_chant_pali_2 = None
    hw2.sbs.sbs_chant_eng_2 = None
    hw2.sbs.sbs_chapter_2 = None
    hw2.antonym = None
    hw2.synonym = None
    hw2.variant = None
    hw2.commentary = None
    hw2.notes = "Some note\nwith newline"
    assert list(anki_csv.get_sbs_info(hw2)) == cases["empty_sbs_fields"]

    hw3 = MagicMock()
    hw3.sbs = MagicMock()
    hw3.sbs.sbs_source_1 = None
    hw3.sbs.sbs_sutta_1 = None
    hw3.sbs.sbs_example_1 = None
    hw3.sbs.sbs_chant_pali_1 = None
    hw3.sbs.sbs_chant_eng_1 = None
    hw3.sbs.sbs_chapter_1 = None
    hw3.sbs.sbs_source_2 = None
    hw3.sbs.sbs_sutta_2 = None
    hw3.sbs.sbs_example_2 = None
    hw3.sbs.sbs_chant_pali_2 = None
    hw3.sbs.sbs_chant_eng_2 = None
    hw3.sbs.sbs_chapter_2 = None
    hw3.antonym = "opposite"
    hw3.synonym = "same"
    hw3.variant = "var"
    hw3.commentary = "com"
    hw3.notes = None
    assert list(anki_csv.get_sbs_info(hw3)) == cases["no_sbs"]


def test_get_paritta_source() -> None:
    cases = FIXTURES["get_paritta_source"]
    chant_names = ["Karaṇīya-metta-sutta", "Ratana-sutta", "Maṅgala-sutta"]

    def _check(key, hw):
        result = anki_csv.get_paritta_source(hw, chant_names)
        assert list(result) == cases[key], f"get_paritta_source failed for {key}"

    hw1 = MagicMock()
    hw1.sbs = MagicMock()
    hw1.sbs.sbs_source_1 = "Khp 1"
    hw1.sbs.sbs_sutta_1 = "Khp 1"
    hw1.sbs.sbs_example_1 = "Karaṇīya-metta-sutta example text"
    hw1.sbs.sbs_chant_pali_1 = "Karaṇīya-metta-sutta"
    hw1.sbs.sbs_chant_pali_2 = "Something else"
    _check("chant_in_first", hw1)

    hw2 = MagicMock()
    hw2.sbs = MagicMock()
    hw2.sbs.sbs_source_1 = "AN 1"
    hw2.sbs.sbs_sutta_1 = "AN 1.1"
    hw2.sbs.sbs_example_1 = "AN example"
    hw2.sbs.sbs_chant_pali_1 = "Not a chant sutta"
    hw2.sbs.sbs_source_2 = "Khp 5"
    hw2.sbs.sbs_sutta_2 = "Khp 5"
    hw2.sbs.sbs_example_2 = "Ratana-sutta example"
    hw2.sbs.sbs_chant_pali_2 = "Ratana-sutta"
    _check("chant_in_second", hw2)

    hw3 = MagicMock()
    hw3.sbs = MagicMock()
    hw3.sbs.sbs_source_1 = "AN 1"
    hw3.sbs.sbs_sutta_1 = "AN 1.1"
    hw3.sbs.sbs_example_1 = "AN example"
    hw3.sbs.sbs_chant_pali_1 = "Unrelated chant"
    hw3.sbs.sbs_chant_pali_2 = ""
    _check("no_chant_match", hw3)

    hw4 = MagicMock()
    hw4.sbs = MagicMock()
    hw4.sbs.sbs_source_1 = None
    hw4.sbs.sbs_sutta_1 = None
    hw4.sbs.sbs_example_1 = None
    hw4.sbs.sbs_chant_pali_1 = ""
    hw4.sbs.sbs_chant_pali_2 = ""
    _check("sbs_is_none", hw4)


def test_get_example_for_class() -> None:
    cases = FIXTURES["get_example_for_class"]

    def _check(key, sbs, hw):
        result = anki_csv.get_example_for_class(sbs, hw)
        assert list(result) == cases[key], f"get_example_for_class failed for {key}"

    hw = MagicMock()
    hw.sbs = MagicMock()
    hw.sbs.class_example = "class example text"
    hw.sbs.class_source = "Class Src"
    hw.sbs.class_sutta = "Class Sut"
    hw.sbs.sbs_example_1 = ""
    hw.sbs.sbs_example_2 = ""
    hw.sbs.dhp_example = ""
    hw.sbs.pat_example = ""
    hw.sbs.vib_example = ""
    hw.sbs.discourses_example = ""
    hw.source_1 = None
    hw.sutta_1 = None
    hw.example_1 = None
    _check("class_example_priority", hw.sbs, hw)

    hw2 = MagicMock()
    hw2.sbs = MagicMock()
    hw2.sbs.class_example = ""
    hw2.sbs.class_source = ""
    hw2.sbs.class_sutta = ""
    hw2.sbs.sbs_example_1 = "sbs1 example"
    hw2.sbs.sbs_source_1 = "SBS1 Src"
    hw2.sbs.sbs_sutta_1 = "SBS1 Sut"
    hw2.sbs.sbs_example_2 = ""
    hw2.sbs.dhp_example = ""
    hw2.sbs.pat_example = ""
    hw2.sbs.vib_example = ""
    hw2.sbs.discourses_example = ""
    hw2.source_1 = None
    hw2.sutta_1 = None
    hw2.example_1 = None
    _check("sbs1_example", hw2.sbs, hw2)

    hw3 = MagicMock()
    hw3.sbs = MagicMock()
    hw3.sbs.class_example = ""
    hw3.sbs.class_source = ""
    hw3.sbs.class_sutta = ""
    hw3.sbs.sbs_example_1 = ""
    hw3.sbs.sbs_example_2 = ""
    hw3.sbs.dhp_example = ""
    hw3.sbs.pat_example = ""
    hw3.sbs.vib_example = ""
    hw3.sbs.discourses_example = ""
    hw3.source_1 = "Src1"
    hw3.sutta_1 = "Sutta1"
    hw3.example_1 = "Ex1"
    _check("fallback_source_1", hw3.sbs, hw3)

    hw4 = MagicMock()
    hw4.sbs = MagicMock()
    hw4.sbs.class_example = ""
    hw4.sbs.class_source = ""
    hw4.sbs.class_sutta = ""
    hw4.sbs.sbs_example_1 = ""
    hw4.sbs.sbs_example_2 = ""
    hw4.sbs.dhp_example = ""
    hw4.sbs.pat_example = ""
    hw4.sbs.vib_example = ""
    hw4.sbs.discourses_example = ""
    hw4.source_1 = None
    hw4.sutta_1 = None
    hw4.example_1 = None
    hw4.source_2 = "Src2"
    hw4.sutta_2 = "Sutta2"
    hw4.example_2 = "Ex2"
    _check("fallback_source_2", hw4.sbs, hw4)

    hw5 = MagicMock()
    hw5.sbs = MagicMock()
    hw5.sbs.class_example = ""
    hw5.sbs.class_source = ""
    hw5.sbs.class_sutta = ""
    hw5.sbs.sbs_example_1 = ""
    hw5.sbs.sbs_example_2 = ""
    hw5.sbs.dhp_example = ""
    hw5.sbs.pat_example = ""
    hw5.sbs.vib_example = ""
    hw5.sbs.discourses_example = ""
    hw5.source_1 = None
    hw5.sutta_1 = None
    hw5.example_1 = None
    hw5.source_2 = None
    hw5.sutta_2 = None
    hw5.example_2 = None
    _check("no_fallback", hw5.sbs, hw5)

    hw6 = MagicMock()
    hw6.sbs = MagicMock()
    hw6.sbs.class_example = ""
    hw6.sbs.class_source = ""
    hw6.sbs.class_sutta = ""
    hw6.sbs.sbs_example_1 = ""
    hw6.sbs.sbs_example_2 = ""
    hw6.sbs.dhp_example = ""
    hw6.sbs.pat_example = ""
    hw6.sbs.vib_example = ""
    hw6.sbs.discourses_example = ""
    hw6.source_1 = None
    hw6.sutta_1 = None
    hw6.example_1 = None
    hw6.source_2 = None
    hw6.sutta_2 = None
    hw6.example_2 = None
    _check("sbs_is_none", hw6.sbs, hw6)


def test_get_unique_example_2() -> None:
    cases = FIXTURES["get_unique_example_2"]

    sbs = MagicMock()
    sbs.class_example = "Unique class example sentence."
    sbs.sbs_example_1 = "A very different sentence about something else."
    sbs.sbs_source_1 = "AN 2"
    sbs.sbs_sutta_1 = "AN 2.1"
    sbs.sbs_example_2 = ""
    sbs.dhp_example = ""
    sbs.pat_example = ""
    sbs.vib_example = ""
    sbs.discourses_example = ""

    def _check(key, sbs):
        result = anki_csv.get_unique_example_2(sbs)
        assert list(result) == cases[key], f"get_unique_example_2 failed for {key}"

    _check("unique_found", sbs)

    sbs2 = MagicMock()
    sbs2.class_example = "The first sentence example."
    sbs2.sbs_example_1 = "The first sentence example."
    sbs2.sbs_source_1 = "AN 3"
    sbs2.sbs_sutta_1 = "AN 3.1"
    sbs2.sbs_example_2 = ""
    sbs2.dhp_example = ""
    sbs2.pat_example = ""
    sbs2.vib_example = ""
    sbs2.discourses_example = ""
    _check("similar_skipped", sbs2)

    sbs3 = MagicMock()
    sbs3.class_example = ""
    sbs3.sbs_example_1 = ""
    sbs3.sbs_example_2 = ""
    sbs3.dhp_example = ""
    sbs3.pat_example = ""
    sbs3.vib_example = ""
    sbs3.discourses_example = ""
    _check("all_empty", sbs3)

    assert list(anki_csv.get_unique_example_2(None)) == cases["sbs_is_none"]


def _dhp_headword_mock(dhp_source: str) -> MagicMock:
    hw = MagicMock()
    hw.id = 1
    hw.lemma_1 = "kamma"
    hw.grammar = "nt"
    hw.neg = ""
    hw.verb = ""
    hw.trans = ""
    hw.plus_case = ""
    hw.meaning_1 = "action"
    hw.meaning_2 = ""
    hw.meaning_lit = ""
    hw.sanskrit = "karma"
    hw.rt = None
    hw.root_sign = ""
    hw.root_base = ""
    hw.construction = ""
    hw.derivative = ""
    hw.suffix = ""
    hw.phonetic = ""
    hw.compound_type = ""
    hw.compound_construction = ""
    hw.sbs = MagicMock()
    hw.sbs.dhp_source = dhp_source
    hw.sbs.dhp_sutta = "Yamakavaggo"
    hw.sbs.dhp_example = "manopubbaṅgamā dhammā"
    hw.link = ""
    hw.lemma_clean = "kamma"
    return hw


def test_dhp_writes_translation_column(tmp_path: Path) -> None:
    dpspth = DPSPaths(base_dir=tmp_path)
    dpd_db = [_dhp_headword_mock("DHP1"), _dhp_headword_mock("DHP2")]

    with patch(
        "scripts.export.anki_csv.SBS_table_tools.get_dhp_translation",
        return_value="Literal: x<br>Figurative: y",
    ):
        anki_csv.dhp(dpspth, dpd_db)

    output_path = dpspth.anki_csvs_dir / "anki_dhp.csv"
    with open(output_path, encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t"))

    assert len(rows) == 2
    translation_column_index = 29
    for row in rows:
        assert row[translation_column_index] == "Literal: x<br>Figurative: y"
