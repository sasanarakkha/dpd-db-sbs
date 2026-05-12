"""Tests for SuttaCentralExporterRu.

The class initialises a DB session at class-definition time (class-level
attributes), which succeeds because the real dpd.db exists in the project
root.  Individual method tests bypass __init__ via object.__new__ and set
instance attributes manually, keeping tests independent of the DB.
"""

import json
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from db.models import DpdHeadword, Lookup
from exporter.sutta_central.sutta_central_exporter_ru import SuttaCentralExporterRu


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bare(with_ai: bool = False, with_eng_fallback: bool = False) -> SuttaCentralExporterRu:
    """Return a SuttaCentralExporterRu instance without running __init__."""
    inst = object.__new__(SuttaCentralExporterRu)
    inst.with_ai = with_ai
    inst.with_eng_fallback = with_eng_fallback
    inst.pth = MagicMock()
    inst.db_session = MagicMock()
    inst.sc_word_set = set()
    inst.lookup_dict = {}
    inst.headword_dict = {}
    inst.sc_dict = {}
    inst.sc_dict_compiled = []
    inst.no_entries_list = []
    return inst


def _ru(ru_meaning="", ru_meaning_raw="", ru_meaning_lit=""):
    """Create a mock Russian translation object."""
    ru = MagicMock()
    ru.ru_meaning = ru_meaning
    ru.ru_meaning_raw = ru_meaning_raw
    ru.ru_meaning_lit = ru_meaning_lit
    return ru


def _hw(lemma_1="dhamma", pos="masc", ru=None, construction_summary=""):
    """Create a mock DpdHeadword."""
    hw = MagicMock()
    hw.lemma_1 = lemma_1
    hw.pos = pos
    hw.ru = ru
    hw.construction_summary = construction_summary
    return hw


def _lookup(headword_ids=None, deconstructions=None):
    """Create a mock Lookup row."""
    lk = MagicMock()
    lk.headwords = json.dumps(headword_ids) if headword_ids else ""
    lk.headwords_unpack = headword_ids or []
    lk.deconstructor = json.dumps(deconstructions) if deconstructions else ""
    lk.deconstructor_unpack = deconstructions or []
    return lk


# ---------------------------------------------------------------------------
# flip()
# ---------------------------------------------------------------------------

class TestFlip:
    def setup_method(self):
        self.inst = _bare()

    def test_replaces_niggahita(self):
        assert self.inst.flip("dhammaṃ") == "dhammaṁ"

    def test_no_niggahita_unchanged(self):
        assert self.inst.flip("dhamma") == "dhamma"

    def test_replaces_all_occurrences(self):
        assert self.inst.flip("saṃsāraṃ") == "saṁsāraṁ"

    def test_empty_string(self):
        assert self.inst.flip("") == ""

    def test_only_niggahita_character(self):
        assert self.inst.flip("ṃ") == "ṁ"

    def test_cyrillic_text_unchanged(self):
        text = "учение закон принцип"
        assert self.inst.flip(text) == text

    def test_mixed_pali_and_cyrillic(self):
        text = "dhammaṃ учение"
        assert self.inst.flip(text) == "dhammaṁ учение"


# ---------------------------------------------------------------------------
# make_sc_headword_entry()
# ---------------------------------------------------------------------------

MODULE = "exporter.sutta_central.sutta_central_exporter_ru"


class TestMakeScHeadwordEntry:
    """Tests for the core translation-selection logic."""

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="сущ")
    def test_ru_meaning_basic(self, _abbr):
        inst = _bare()
        result = inst.make_sc_headword_entry(_hw(ru=_ru(ru_meaning="учение")))
        assert result == "сущ. <b>учение</b>"

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="гл")
    def test_ru_meaning_with_literal(self, _abbr):
        inst = _bare()
        result = inst.make_sc_headword_entry(
            _hw(pos="verb", ru=_ru(ru_meaning="знать", ru_meaning_lit="держать в уме"))
        )
        assert result == "гл. <b>знать</b>; досл. держать в уме"

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="сущ")
    def test_ru_meaning_with_construction(self, _abbr):
        inst = _bare()
        result = inst.make_sc_headword_entry(
            _hw(ru=_ru(ru_meaning="учение"), construction_summary="dhā + ma")
        )
        assert result == "сущ. <b>учение</b> [dhā + ma]"

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="прил")
    def test_ru_meaning_with_literal_and_construction(self, _abbr):
        inst = _bare()
        result = inst.make_sc_headword_entry(
            _hw(
                pos="adj",
                ru=_ru(ru_meaning="добрый", ru_meaning_lit="хорошо сделанный"),
                construction_summary="su + kata",
            )
        )
        assert result == "прил. <b>добрый</b>; досл. хорошо сделанный [su + kata]"

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="сущ")
    def test_empty_ru_meaning_lit_excluded(self, _abbr):
        """Empty ru_meaning_lit (falsy) must not add '; досл.' clause."""
        inst = _bare()
        result = inst.make_sc_headword_entry(_hw(ru=_ru(ru_meaning="учение", ru_meaning_lit="")))
        assert "досл." not in result
        assert result == "сущ. <b>учение</b>"

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="гл")
    def test_ai_entry_when_ai_enabled(self, _abbr):
        inst = _bare(with_ai=True)
        result = inst.make_sc_headword_entry(_hw(pos="verb", ru=_ru(ru_meaning_raw="понимать")))
        assert result == "гл. <i>[пер. ИИ]</i> понимать"

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="гл")
    def test_ai_entry_returns_none_when_ai_disabled(self, _abbr):
        inst = _bare(with_ai=False)
        result = inst.make_sc_headword_entry(_hw(pos="verb", ru=_ru(ru_meaning_raw="понимать")))
        assert result is None

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="гл")
    def test_ai_entry_includes_construction(self, _abbr):
        inst = _bare(with_ai=True)
        result = inst.make_sc_headword_entry(
            _hw(pos="verb", ru=_ru(ru_meaning_raw="понимать"), construction_summary="pa + jānā")
        )
        assert "[pa + jānā]" in result

    @patch(f"{MODULE}.make_meaning_combo", return_value="teaching; law")
    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="сущ")
    def test_eng_fallback_when_no_ru_and_fallback_enabled(self, _abbr, mock_combo):
        inst = _bare(with_eng_fallback=True)
        hw = _hw(ru=None)
        result = inst.make_sc_headword_entry(hw)
        assert result == "сущ. teaching; law"
        mock_combo.assert_called_once_with(hw)

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="сущ")
    def test_eng_fallback_returns_none_when_disabled(self, _abbr):
        inst = _bare(with_eng_fallback=False)
        result = inst.make_sc_headword_entry(_hw(ru=None))
        assert result is None

    @patch(f"{MODULE}.make_meaning_combo", return_value="teaching")
    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="сущ")
    def test_eng_fallback_includes_construction(self, _abbr, _combo):
        inst = _bare(with_eng_fallback=True)
        result = inst.make_sc_headword_entry(_hw(ru=None, construction_summary="dhā + ma"))
        assert "[dhā + ma]" in result

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="сущ")
    def test_all_empty_ru_fields_returns_none(self, _abbr):
        """ru object with all empty meaning fields → None."""
        inst = _bare()
        result = inst.make_sc_headword_entry(_hw(ru=_ru(ru_meaning="", ru_meaning_raw="")))
        assert result is None

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="сущ")
    def test_ru_meaning_preferred_over_raw(self, _abbr):
        """When both fields are set, ru_meaning wins over ru_meaning_raw."""
        inst = _bare(with_ai=True)
        result = inst.make_sc_headword_entry(
            _hw(ru=_ru(ru_meaning="учение", ru_meaning_raw="ИИ перевод"))
        )
        assert "<b>учение</b>" in result
        assert "[пер. ИИ]" not in result

    @patch(f"{MODULE}.ru_replace_abbreviations")
    def test_pos_abbreviation_always_called(self, mock_abbr):
        """ru_replace_abbreviations is called with (pos, 'gram') for every hit."""
        mock_abbr.return_value = "гл"
        inst = _bare()
        inst.make_sc_headword_entry(_hw(pos="verb", ru=_ru(ru_meaning="знать")))
        mock_abbr.assert_called_once_with("verb", "gram")


# ---------------------------------------------------------------------------
# make_sc_dict()
# ---------------------------------------------------------------------------

class TestMakeScDict:
    def test_word_not_in_lookup_dict_skipped(self):
        inst = _bare()
        inst.sc_word_set = {"dhamma"}
        inst.make_sc_dict()
        assert "dhamma" not in inst.sc_dict

    def test_word_matched_but_no_headwords_no_deconstructor(self):
        inst = _bare()
        inst.sc_word_set = {"dhamma"}
        inst.lookup_dict = {"dhamma": _lookup()}
        inst.make_sc_dict()
        assert "dhamma" in inst.sc_dict
        assert inst.sc_dict["dhamma"] == []

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="сущ")
    def test_word_with_valid_headword_entry(self, _abbr):
        inst = _bare()
        hw = _hw(lemma_1="dhamma", pos="masc", ru=_ru(ru_meaning="учение"))
        inst.sc_word_set = {"dhamma"}
        inst.lookup_dict = {"dhamma": _lookup(headword_ids=[1])}
        inst.headword_dict = {1: hw}
        inst.make_sc_dict()
        assert len(inst.sc_dict["dhamma"]) == 1
        lemma, entry = inst.sc_dict["dhamma"][0]
        assert lemma == "dhamma"
        assert "<b>учение</b>" in entry

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="сущ")
    def test_headword_entry_returning_none_not_appended(self, _abbr):
        """Headword with no eligible translation produces no entry tuple."""
        inst = _bare(with_ai=False, with_eng_fallback=False)
        hw = _hw(lemma_1="dhamma", pos="masc", ru=None)
        inst.sc_word_set = {"dhamma"}
        inst.lookup_dict = {"dhamma": _lookup(headword_ids=[1])}
        inst.headword_dict = {1: hw}
        inst.make_sc_dict()
        assert inst.sc_dict["dhamma"] == []

    def test_deconstructor_only(self):
        inst = _bare()
        inst.sc_word_set = {"dhammaṃ"}
        inst.lookup_dict = {"dhammaṃ": _lookup(deconstructions=["dhamma + ṃ"])}
        inst.make_sc_dict()
        assert len(inst.sc_dict["dhammaṃ"]) == 1
        assert inst.sc_dict["dhammaṃ"][0] == ("", "dhamma + ṃ")

    def test_only_first_deconstruction_is_taken(self):
        inst = _bare()
        inst.sc_word_set = {"ab"}
        inst.lookup_dict = {"ab": _lookup(deconstructions=["a + b", "c + d"])}
        inst.make_sc_dict()
        assert len(inst.sc_dict["ab"]) == 1
        assert inst.sc_dict["ab"][0] == ("", "a + b")

    def test_unknown_headword_id_silently_skipped(self):
        inst = _bare()
        inst.sc_word_set = {"dhamma"}
        inst.lookup_dict = {"dhamma": _lookup(headword_ids=[999])}
        inst.headword_dict = {}
        inst.make_sc_dict()
        assert inst.sc_dict["dhamma"] == []

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="сущ")
    def test_headwords_and_deconstructor_both_added(self, _abbr):
        hw = _hw(lemma_1="dhamma", pos="masc", ru=_ru(ru_meaning="учение"))
        inst = _bare()
        inst.sc_word_set = {"dhamma"}
        inst.lookup_dict = {"dhamma": _lookup(headword_ids=[1], deconstructions=["x + y"])}
        inst.headword_dict = {1: hw}
        inst.make_sc_dict()
        assert len(inst.sc_dict["dhamma"]) == 2

    @patch(f"{MODULE}.ru_replace_abbreviations", return_value="сущ")
    def test_multiple_headword_ids_all_processed(self, _abbr):
        hw1 = _hw(lemma_1="dhamma 1", pos="masc", ru=_ru(ru_meaning="учение"))
        hw2 = _hw(lemma_1="dhamma 2", pos="masc", ru=_ru(ru_meaning="закон"))
        inst = _bare()
        inst.sc_word_set = {"dhamma"}
        inst.lookup_dict = {"dhamma": _lookup(headword_ids=[1, 2])}
        inst.headword_dict = {1: hw1, 2: hw2}
        inst.make_sc_dict()
        assert len(inst.sc_dict["dhamma"]) == 2

    def test_multiple_words_each_processed_independently(self):
        inst = _bare()
        inst.sc_word_set = {"dhamma", "sangha"}
        inst.lookup_dict = {
            "dhamma": _lookup(),
            "sangha": _lookup(),
        }
        inst.make_sc_dict()
        assert "dhamma" in inst.sc_dict
        assert "sangha" in inst.sc_dict


# ---------------------------------------------------------------------------
# compile_sc_dict()
# ---------------------------------------------------------------------------

class TestCompileScDict:
    def test_empty_word_set(self):
        inst = _bare()
        inst.compile_sc_dict()
        assert inst.sc_dict_compiled == []
        assert inst.no_entries_list == []

    def test_word_absent_from_sc_dict_goes_to_no_entries(self):
        inst = _bare()
        inst.sc_word_set = {"dhamma"}
        inst.compile_sc_dict()
        assert "dhamma" in inst.no_entries_list
        assert inst.sc_dict_compiled == []

    def test_word_with_empty_entries_list_goes_to_no_entries(self):
        inst = _bare()
        inst.sc_word_set = {"dhamma"}
        inst.sc_dict = {"dhamma": []}
        inst.compile_sc_dict()
        assert "dhamma" in inst.no_entries_list
        assert inst.sc_dict_compiled == []

    def test_word_with_headword_entry_compiled_correctly(self):
        inst = _bare()
        inst.sc_word_set = {"dhamma"}
        inst.sc_dict = {"dhamma": [("dhamma", "сущ. <b>учение</b>")]}
        inst.compile_sc_dict()
        assert len(inst.sc_dict_compiled) == 1
        entry = inst.sc_dict_compiled[0]
        assert entry["entry"] == "dhamma"
        assert entry["definition"] == ["dhamma: сущ. <b>учение</b>"]

    def test_niggahita_flipped_in_word_entry(self):
        inst = _bare()
        inst.sc_word_set = {"dhammaṃ"}
        inst.sc_dict = {"dhammaṃ": [("dhammaṃ", "сущ. <b>учение</b>")]}
        inst.compile_sc_dict()
        assert inst.sc_dict_compiled[0]["entry"] == "dhammaṁ"

    def test_niggahita_flipped_in_definition(self):
        inst = _bare()
        inst.sc_word_set = {"dhammaṃ"}
        inst.sc_dict = {"dhammaṃ": [("dhammaṃ", "сущ. <b>учение</b>")]}
        inst.compile_sc_dict()
        assert "dhammaṁ: сущ. <b>учение</b>" in inst.sc_dict_compiled[0]["definition"]

    def test_deconstructor_entry_has_no_headword_prefix(self):
        """Empty headword string → definition added without '<headword>:' prefix."""
        inst = _bare()
        inst.sc_word_set = {"dhammaṃ"}
        inst.sc_dict = {"dhammaṃ": [("", "dhamma + ṃ")]}
        inst.compile_sc_dict()
        defn = inst.sc_dict_compiled[0]["definition"][0]
        assert defn == "dhamma + ṁ"
        assert ":" not in defn

    def test_multiple_entries_all_included(self):
        inst = _bare()
        inst.sc_word_set = {"dhamma"}
        inst.sc_dict = {
            "dhamma": [
                ("dhamma 1", "сущ. <b>учение</b>"),
                ("dhamma 2", "сущ. <b>закон</b>"),
            ]
        }
        inst.compile_sc_dict()
        assert len(inst.sc_dict_compiled[0]["definition"]) == 2

    def test_words_iterated_in_sorted_order(self):
        """compile_sc_dict sorts sc_word_set before iterating."""
        inst = _bare()
        inst.sc_word_set = {"zzz", "aaa"}
        inst.sc_dict = {
            "zzz": [("zzz", "последний")],
            "aaa": [("aaa", "первый")],
        }
        inst.compile_sc_dict()
        assert inst.sc_dict_compiled[0]["entry"] == "aaa"
        assert inst.sc_dict_compiled[1]["entry"] == "zzz"

    def test_both_no_entries_and_compiled_entries(self):
        inst = _bare()
        inst.sc_word_set = {"dhamma", "unknown"}
        inst.sc_dict = {"dhamma": [("dhamma", "учение")]}
        inst.compile_sc_dict()
        assert len(inst.sc_dict_compiled) == 1
        assert inst.sc_dict_compiled[0]["entry"] == "dhamma"
        assert "unknown" in inst.no_entries_list

    def test_compiled_entry_has_definition_key(self):
        inst = _bare()
        inst.sc_word_set = {"dhamma"}
        inst.sc_dict = {"dhamma": [("dhamma", "учение")]}
        inst.compile_sc_dict()
        entry = inst.sc_dict_compiled[0]
        assert "entry" in entry
        assert "definition" in entry
        assert isinstance(entry["definition"], list)


# ---------------------------------------------------------------------------
# make_lookup_dict()
# ---------------------------------------------------------------------------

class TestMakeLookupDict:
    def test_populates_lookup_dict_from_db(self):
        inst = _bare()
        lk_a, lk_b = MagicMock(), MagicMock()
        lk_a.lookup_key = "dhamma"
        lk_b.lookup_key = "sangha"
        inst.db_session.query.return_value.all.return_value = [lk_a, lk_b]

        inst.make_lookup_dict()

        assert inst.lookup_dict == {"dhamma": lk_a, "sangha": lk_b}

    def test_empty_db_gives_empty_dict(self):
        inst = _bare()
        inst.db_session.query.return_value.all.return_value = []
        inst.make_lookup_dict()
        assert inst.lookup_dict == {}

    def test_queries_lookup_model(self):
        inst = _bare()
        inst.db_session.query.return_value.all.return_value = []
        inst.make_lookup_dict()
        inst.db_session.query.assert_called_once_with(Lookup)

    def test_duplicate_keys_last_one_wins(self):
        """If two Lookup rows share a key, the last one stored wins (dict insert)."""
        inst = _bare()
        lk_first, lk_second = MagicMock(), MagicMock()
        lk_first.lookup_key = "dhamma"
        lk_second.lookup_key = "dhamma"
        inst.db_session.query.return_value.all.return_value = [lk_first, lk_second]
        inst.make_lookup_dict()
        assert inst.lookup_dict["dhamma"] is lk_second


# ---------------------------------------------------------------------------
# make_headwords_dict()
# ---------------------------------------------------------------------------

class TestMakeHeadwordsDict:
    def test_populates_headword_dict_by_id(self):
        inst = _bare()
        hw1, hw2 = MagicMock(), MagicMock()
        hw1.id = 1
        hw1.lemma_1 = "a_word"
        hw2.id = 2
        hw2.lemma_1 = "b_word"
        inst.db_session.query.return_value.all.return_value = [hw1, hw2]

        inst.make_headwords_dict()

        assert inst.headword_dict[1] is hw1
        assert inst.headword_dict[2] is hw2

    def test_empty_db_gives_empty_dict(self):
        inst = _bare()
        inst.db_session.query.return_value.all.return_value = []
        inst.make_headwords_dict()
        assert inst.headword_dict == {}

    def test_headword_db_sorted_by_lemma(self):
        """headword_db list is sorted with pali_sort_key(lemma_1)."""
        inst = _bare()
        hw_z, hw_a = MagicMock(), MagicMock()
        hw_z.id = 2
        hw_z.lemma_1 = "zzz"
        hw_a.id = 1
        hw_a.lemma_1 = "aaa"
        inst.db_session.query.return_value.all.return_value = [hw_z, hw_a]

        inst.make_headwords_dict()

        assert inst.headword_db[0].lemma_1 == "aaa"
        assert inst.headword_db[1].lemma_1 == "zzz"

    def test_queries_dpdheadword_model(self):
        inst = _bare()
        inst.db_session.query.return_value.all.return_value = []
        inst.make_headwords_dict()
        inst.db_session.query.assert_called_once_with(DpdHeadword)


# ---------------------------------------------------------------------------
# save_sc_dict()
# ---------------------------------------------------------------------------

class TestSaveScDict:
    def _run_save(self, inst):
        """Run save_sc_dict, capture written bytes, return parsed JSON."""
        buf = StringIO()

        class _CM:
            def __enter__(self_):
                return buf

            def __exit__(self_, *a):
                pass

        with patch("builtins.open", return_value=_CM()):
            inst.save_sc_dict()

        return json.loads(buf.getvalue())

    def test_creates_parent_directory(self):
        inst = _bare()
        inst.sc_dict_compiled = []
        with patch("builtins.open", return_value=MagicMock(__enter__=lambda s: StringIO(), __exit__=lambda s, *a: None)):
            inst.save_sc_dict()
        inst.pth.sc_pli2ru_dpd_json.parent.mkdir.assert_called_once_with(
            parents=True, exist_ok=True
        )

    def test_writes_correct_data(self):
        inst = _bare()
        data = [{"entry": "dhammaṁ", "definition": ["сущ. <b>учение</b>"]}]
        inst.sc_dict_compiled = data
        parsed = self._run_save(inst)
        assert parsed == data

    def test_unicode_characters_not_escaped(self):
        inst = _bare()
        inst.sc_dict_compiled = [{"entry": "dhammaṁ", "definition": ["учение"]}]
        buf = StringIO()

        class _CM:
            def __enter__(self_):
                return buf

            def __exit__(self_, *a):
                pass

        with patch("builtins.open", return_value=_CM()):
            inst.save_sc_dict()

        raw = buf.getvalue()
        assert "учение" in raw
        assert "dhammaṁ" in raw
        assert "\\u" not in raw

    def test_empty_list_written_as_empty_json_array(self):
        inst = _bare()
        inst.sc_dict_compiled = []
        parsed = self._run_save(inst)
        assert parsed == []

    def test_opens_file_at_correct_path(self):
        inst = _bare()
        inst.sc_dict_compiled = []
        mock_path = MagicMock()
        inst.pth.sc_pli2ru_dpd_json = mock_path

        with patch("builtins.open", return_value=MagicMock(__enter__=lambda s: StringIO(), __exit__=lambda s, *a: None)) as m_open:
            inst.save_sc_dict()

        m_open.assert_called_once_with(mock_path, "w")


# ---------------------------------------------------------------------------
# __init__() integration
# ---------------------------------------------------------------------------

_PATCH_BASE = "exporter.sutta_central.sutta_central_exporter_ru.SuttaCentralExporterRu"


@pytest.fixture()
def patched_init():
    """Patch all pipeline steps called by __init__ and return the patches."""
    with (
        patch(f"{MODULE}.make_sc_text_set", return_value=set()) as p_text,
        patch(f"{_PATCH_BASE}.make_lookup_dict") as p_lookup,
        patch(f"{_PATCH_BASE}.make_headwords_dict") as p_hw,
        patch(f"{_PATCH_BASE}.make_sc_dict") as p_sc,
        patch(f"{_PATCH_BASE}.compile_sc_dict") as p_compile,
        patch(f"{_PATCH_BASE}.save_sc_dict") as p_save,
    ):
        yield {
            "text": p_text,
            "lookup": p_lookup,
            "headwords": p_hw,
            "sc_dict": p_sc,
            "compile": p_compile,
            "save": p_save,
        }


class TestInit:
    def test_all_pipeline_steps_called(self, patched_init):
        SuttaCentralExporterRu()
        for step in patched_init.values():
            step.assert_called_once()

    def test_with_ai_stored_on_instance(self, patched_init):
        inst = SuttaCentralExporterRu(with_ai=True)
        assert inst.with_ai is True

    def test_with_eng_fallback_stored_on_instance(self, patched_init):
        inst = SuttaCentralExporterRu(with_eng_fallback=True)
        assert inst.with_eng_fallback is True

    def test_defaults_are_false(self, patched_init):
        inst = SuttaCentralExporterRu()
        assert inst.with_ai is False
        assert inst.with_eng_fallback is False

    def test_empty_words_filtered_from_sc_word_set(self, patched_init):
        patched_init["text"].return_value = {"dhamma", "", "  ", "sangha"}
        inst = SuttaCentralExporterRu()
        assert "" not in inst.sc_word_set
        assert "  " not in inst.sc_word_set
        assert "dhamma" in inst.sc_word_set
        assert "sangha" in inst.sc_word_set

    def test_make_sc_text_set_called_with_correct_kwargs(self, patched_init):
        SuttaCentralExporterRu()
        _, kwargs = patched_init["text"].call_args
        assert kwargs.get("niggahita") == "ṃ"
        assert kwargs.get("add_hyphenated_parts") is True
