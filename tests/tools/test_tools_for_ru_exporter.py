"""Characterization tests for tools/tools_for_ru_exporter.py.

Frozen current output — prove refactored code reproduces it.
"""

import json
from pathlib import Path
from unittest.mock import patch

from tools.tools_for_ru_exporter import (
    get_first_synonym,
    make_ru_meaning,
    make_ru_meaning_for_ebook,
    make_ru_meaning_html,
    make_ru_meaning_simpl,
    make_short_meaning,
    make_short_ru_meaning,
    populate_set_ru_and_check_errors,
    read_set_ru_from_tsv,
    ru_make_grammar_line,
    ru_replace_abbreviations,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parent / "test_tools_for_ru_exporter_fixtures.json"
)
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class FakeRussian:
    """Minimal stand-in for db.models.Russian — only exposes the attrs the code reads."""

    def __init__(self, ru_meaning="", ru_meaning_raw="", ru_meaning_lit=""):
        self.ru_meaning = ru_meaning
        self.ru_meaning_raw = ru_meaning_raw
        self.ru_meaning_lit = ru_meaning_lit


class FakeHeadword:
    """Minimal stand-in for db.models.DpdHeadword — only exposes the attrs the code reads."""

    def __init__(
        self,
        lemma_1="",
        meaning_1="",
        meaning_2="",
        meaning_lit="",
        ru=None,
        grammar="",
        neg="",
        verb="",
        trans="",
        plus_case="",
        pos="",
    ):
        self.lemma_1 = lemma_1
        self.meaning_1 = meaning_1
        self.meaning_2 = meaning_2
        self.meaning_lit = meaning_lit
        self.ru = ru
        self.grammar = grammar
        self.neg = neg
        self.verb = verb
        self.trans = trans
        self.plus_case = plus_case
        self.pos = pos

    @property
    def lemma_link(self):
        return self.lemma_1.replace(" ", "%20")


# ── Pure function tests ──


def test_get_first_synonym_single():
    assert get_first_synonym("слово") == FIXTURES["get_first_synonym_single"]


def test_get_first_synonym_multi():
    assert (
        get_first_synonym("слово; значение; перевод")
        == FIXTURES["get_first_synonym_multi"]
    )


def test_get_first_synonym_empty():
    assert get_first_synonym("") == FIXTURES["get_first_synonym_empty"]


def test_ru_replace_abbreviations_meaning():
    assert (
        ru_replace_abbreviations("root letter form", "meaning")
        == FIXTURES["ru_replace_abbreviations_meaning"]
    )


def test_ru_replace_abbreviations_inflect():
    assert (
        ru_replace_abbreviations("reflexive irregular conjugation", "inflect")
        == FIXTURES["ru_replace_abbreviations_inflect"]
    )


def test_ru_replace_abbreviations_root():
    assert (
        ru_replace_abbreviations("Pāḷi Root and Sanskrit Root", "root")
        == FIXTURES["ru_replace_abbreviations_root"]
    )


def test_ru_replace_abbreviations_gram():
    assert (
        ru_replace_abbreviations("indeclinable word", "gram")
        == FIXTURES["ru_replace_abbreviations_gram"]
    )


def test_ru_replace_abbreviations_base():
    assert (
        ru_replace_abbreviations("pass, caus irreg intens", "base")
        == FIXTURES["ru_replace_abbreviations_base"]
    )


def test_ru_replace_abbreviations_phonetic():
    assert (
        ru_replace_abbreviations("metathesis before a vowel", "phonetic")
        == FIXTURES["ru_replace_abbreviations_phonetic"]
    )


# ── make_ru_meaning family ──


def test_make_ru_meaning_with_meaning_and_lit():
    f = FIXTURES["hq_with_meaning_and_lit"]
    ru = FakeRussian(
        ru_meaning=f["ru_meaning"],
        ru_meaning_lit=f["ru_meaning_lit"],
        ru_meaning_raw=f["ru_meaning_raw"],
    )
    i = FakeHeadword(lemma_1=f["lemma_1"], meaning_1=f["meaning_1"], ru=ru)
    assert make_ru_meaning(i) == f["make_ru_meaning"]


def test_make_ru_meaning_simpl_with_meaning_and_lit():
    f = FIXTURES["hq_with_meaning_and_lit"]
    ru = FakeRussian(
        ru_meaning=f["ru_meaning"],
        ru_meaning_lit=f["ru_meaning_lit"],
        ru_meaning_raw=f["ru_meaning_raw"],
    )
    i = FakeHeadword(lemma_1=f["lemma_1"], meaning_1=f["meaning_1"], ru=ru)
    assert make_ru_meaning_simpl(i) == f["make_ru_meaning_simpl"]


def test_make_ru_meaning_only():
    f = FIXTURES["hq_with_meaning_only"]
    ru = FakeRussian(
        ru_meaning=f["ru_meaning"],
        ru_meaning_lit=f["ru_meaning_lit"],
        ru_meaning_raw=f["ru_meaning_raw"],
    )
    i = FakeHeadword(lemma_1=f["lemma_1"], ru=ru)
    assert make_ru_meaning(i) == f["make_ru_meaning"]


def test_make_ru_meaning_raw_only():
    f = FIXTURES["hq_with_raw_only"]
    ru = FakeRussian(
        ru_meaning=f["ru_meaning"],
        ru_meaning_lit=f["ru_meaning_lit"],
        ru_meaning_raw=f["ru_meaning_raw"],
    )
    i = FakeHeadword(lemma_1=f["lemma_1"], ru=ru)
    assert make_ru_meaning(i) == f["make_ru_meaning"]


def test_make_ru_meaning_simpl_raw_only():
    f = FIXTURES["hq_with_raw_only"]
    ru = FakeRussian(
        ru_meaning=f["ru_meaning"],
        ru_meaning_lit=f["ru_meaning_lit"],
        ru_meaning_raw=f["ru_meaning_raw"],
    )
    i = FakeHeadword(lemma_1=f["lemma_1"], ru=ru)
    assert make_ru_meaning_simpl(i) == f["make_ru_meaning_simpl"]


def test_make_ru_meaning_html_raw_only():
    f = FIXTURES["hq_with_raw_only"]
    ru = FakeRussian(
        ru_meaning=f["ru_meaning"],
        ru_meaning_lit=f["ru_meaning_lit"],
        ru_meaning_raw=f["ru_meaning_raw"],
    )
    i = FakeHeadword(lemma_1=f["lemma_1"], ru=ru)
    assert make_ru_meaning_html(i, ru) == f["make_ru_meaning_html"]


def test_make_ru_meaning_for_ebook_raw_only():
    f = FIXTURES["hq_with_raw_only"]
    ru = FakeRussian(
        ru_meaning=f["ru_meaning"],
        ru_meaning_lit=f["ru_meaning_lit"],
        ru_meaning_raw=f["ru_meaning_raw"],
    )
    i = FakeHeadword(lemma_1=f["lemma_1"], ru=ru)
    assert make_ru_meaning_for_ebook(i, ru) == f["make_ru_meaning_for_ebook"]


def test_make_ru_meaning_no_ru():
    f = FIXTURES["hq_no_ru"]
    i = FakeHeadword(
        lemma_1=f["lemma_1"],
        meaning_1=f["meaning_1"],
        meaning_2=f["meaning_2"],
        ru=None,
    )
    with patch(
        "tools.tools_for_ru_exporter.year_month_day_dash", return_value="2026-06-26"
    ):
        assert make_ru_meaning(i) == f["make_ru_meaning"]


def test_make_ru_meaning_simpl_no_ru():
    f = FIXTURES["hq_no_ru"]
    i = FakeHeadword(
        lemma_1=f["lemma_1"],
        meaning_1=f["meaning_1"],
        meaning_2=f["meaning_2"],
        ru=None,
    )
    assert make_ru_meaning_simpl(i) == f["make_ru_meaning_simpl"]


def test_make_ru_meaning_html_no_ru():
    f = FIXTURES["hq_no_ru"]
    i = FakeHeadword(lemma_1=f["lemma_1"], meaning_1=f["meaning_1"], ru=None)
    assert make_ru_meaning_html(i, None) == f["make_ru_meaning_html"]


def test_make_ru_meaning_for_ebook_no_ru():
    f = FIXTURES["hq_no_ru"]
    i = FakeHeadword(lemma_1=f["lemma_1"], meaning_1=f["meaning_1"], ru=None)
    assert make_ru_meaning_for_ebook(i, None) == f["make_ru_meaning_for_ebook"]


# ── make_short_ru_meaning ──


def test_make_short_ru_meaning_with_meaning_and_lit():
    f = FIXTURES["hq_with_meaning_and_lit"]
    ru = FakeRussian(
        ru_meaning=f["ru_meaning"],
        ru_meaning_lit=f["ru_meaning_lit"],
        ru_meaning_raw=f["ru_meaning_raw"],
    )
    i = FakeHeadword(lemma_1=f["lemma_1"], ru=ru)
    assert make_short_ru_meaning(i, ru) == f["make_short_ru_meaning"]


def test_make_short_ru_meaning_no_ru():
    f = FIXTURES["hq_no_ru"]
    i = FakeHeadword(lemma_1=f["lemma_1"], meaning_1=f["meaning_1"], ru=None)
    assert make_short_ru_meaning(i, None) == f["make_short_ru_meaning"]


# ── make_short_meaning ──


def test_make_short_meaning_from_meaning_1():
    f = FIXTURES["hq_no_ru"]
    i = FakeHeadword(meaning_1=f["meaning_1"], meaning_2=f["meaning_2"])
    assert make_short_meaning(i) == f["make_short_meaning"]


def test_make_short_meaning_from_meaning_2():
    f = FIXTURES["hq_with_meaning2_only"]
    i = FakeHeadword(meaning_1=f["meaning_1"], meaning_2=f["meaning_2"])
    assert make_short_meaning(i) == f["make_short_meaning"]


def test_make_short_meaning_empty():
    i = FakeHeadword(meaning_1="", meaning_2="")
    assert make_short_meaning(i) == ""


# ── ru_make_grammar_line ──


def test_ru_make_grammar_line_full():
    f = FIXTURES["hq_full_grammar"]
    i = FakeHeadword(
        grammar=f["grammar"],
        neg=f["neg"],
        verb=f["verb"],
        trans=f["trans"],
        plus_case=f["plus_case"],
    )
    assert ru_make_grammar_line(i) == f["ru_make_grammar_line"]


def test_ru_make_grammar_line_with_meaning_and_lit():
    f = FIXTURES["hq_with_meaning_and_lit"]
    i = FakeHeadword(
        grammar=f["grammar"],
        neg=f["neg"],
        verb=f["verb"],
        trans=f["trans"],
        plus_case=f["plus_case"],
    )
    assert ru_make_grammar_line(i) == f["ru_make_grammar_line"]


# ── read_set_ru_from_tsv ──


def test_read_set_ru_from_tsv():
    result = read_set_ru_from_tsv()
    f = FIXTURES["read_set_ru_from_tsv_sample"]
    for k, v in f.items():
        assert result[k] == v
    assert len(result) == FIXTURES["read_set_ru_from_tsv_count"]


# ── populate_set_ru_and_check_errors ──


def test_populate_set_ru_all_found():
    f = FIXTURES["populate_set_ru_all_found"]
    sample = FIXTURES["read_set_ru_from_tsv_sample"]
    test_dict = {k: {"set_ru": ""} for k in sample}
    result = populate_set_ru_and_check_errors(test_dict)
    assert result == f["errors"]
    for k in sample:
        assert test_dict[k]["set_ru"] == sample[k]


def test_populate_set_ru_with_missing():
    f = FIXTURES["populate_set_ru_with_missing"]
    test_dict = {"NONEXISTENT_SET_XYZ": {"set_ru": ""}}
    result = populate_set_ru_and_check_errors(test_dict)
    assert result == f["errors"]
