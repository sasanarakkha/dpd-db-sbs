"""Golden-master tests for kamma/translate/scripts/ai_meaning_checker.py against real dpd.db data."""

import json
from pathlib import Path

from db.db_helpers import get_db_session
from kamma.translate.scripts.ai_meaning_checker import RussianMeaningChecker
from tools.paths import ProjectPaths

FIXTURE_PATH = Path(__file__).parent / "test_ai_meaning_checker_fixtures.json"
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def _comparisons_to_dicts(comparisons) -> list[dict]:
    return [
        {
            "headword_id": c.headword_id,
            "lemma_1": c.lemma_1,
            "english_meaning": c.english_meaning,
            "russian_meaning": c.russian_meaning,
            "russian_meaning_alt": c.russian_meaning_alt,
            "grammar": c.grammar,
        }
        for c in comparisons
    ]


def test_get_words_for_comparison_meaning_mode_matches_fixture():
    checker = RussianMeaningChecker(mode="meaning")
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons)[:5] == FIXTURES["meaning"]


def test_get_words_for_comparison_meaning_raw_mode_matches_fixture():
    checker = RussianMeaningChecker(mode="meaning_raw")
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons)[:5] == FIXTURES["meaning_raw"]


def test_get_words_for_comparison_meaning_ru_raw_mode_matches_fixture():
    checker = RussianMeaningChecker(mode="meaning_ru_raw")
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons)[:5] == FIXTURES["meaning_ru_raw"]


def test_get_words_for_comparison_meaning_lit_mode_matches_fixture():
    checker = RussianMeaningChecker(mode="meaning_lit")
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons)[:5] == FIXTURES["meaning_lit"]


def test_get_words_for_comparison_notes_mode_matches_fixture():
    checker = RussianMeaningChecker(mode="notes")
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons)[:5] == FIXTURES["notes"]


def test_get_words_for_comparison_notes_raw_mode_matches_fixture():
    checker = RussianMeaningChecker(mode="notes_raw")
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons)[:5] == FIXTURES["notes_raw"]


def test_get_words_for_comparison_meaning_lit_list_mode_matches_fixture(tmp_path):
    ids = [row["headword_id"] for row in FIXTURES["meaning_lit_list"]]
    list_file = tmp_path / "list_ids.json"
    list_file.write_text(json.dumps(ids), encoding="utf-8")

    checker = RussianMeaningChecker(mode="meaning_lit_list")
    checker.list_ids_file = list_file
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons) == FIXTURES["meaning_lit_list"]


def test_get_words_for_comparison_meaning_raw_list_mode_matches_fixture(tmp_path):
    ids = [row["headword_id"] for row in FIXTURES["meaning_raw_list"]]
    list_file = tmp_path / "list_ids.json"
    list_file.write_text(json.dumps(ids), encoding="utf-8")

    checker = RussianMeaningChecker(mode="meaning_raw_list")
    checker.list_ids_file = list_file
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons) == FIXTURES["meaning_raw_list"]


def test_load_list_ids_returns_empty_set_when_no_list_file():
    checker = RussianMeaningChecker(mode="meaning")
    assert checker.load_list_ids() == set(FIXTURES["load_list_ids_none"])


def test_load_list_ids_reads_ids_from_file(tmp_path):
    ids = FIXTURES["load_list_ids_with_file"]
    list_file = tmp_path / "list_ids.json"
    list_file.write_text(json.dumps(ids), encoding="utf-8")

    checker = RussianMeaningChecker(mode="meaning_lit_list")
    checker.list_ids_file = list_file
    assert checker.load_list_ids() == set(ids)


def test_get_words_for_comparison_unknown_mode_raises_value_error():
    checker = RussianMeaningChecker(mode="bogus_mode")
    try:
        checker.get_words_for_comparison_with_session(db_session)
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "bogus_mode" in str(e)
