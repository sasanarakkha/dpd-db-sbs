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
    checker.checked_ids = set()
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons)[:5] == FIXTURES["meaning"]


def test_get_words_for_comparison_meaning_raw_mode_matches_fixture():
    checker = RussianMeaningChecker(mode="meaning_raw")
    checker.checked_ids = set()
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons)[:5] == FIXTURES["meaning_raw"]


def test_get_words_for_comparison_russian_grammar_meaning_raw_mode_matches_fixture():
    checker = RussianMeaningChecker(mode="russian_grammar_meaning_raw")
    checker.checked_ids = set()
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert (
        _comparisons_to_dicts(comparisons)[:5]
        == FIXTURES["russian_grammar_meaning_raw"]
    )


def test_get_words_for_comparison_meaning_lit_mode_matches_fixture():
    checker = RussianMeaningChecker(mode="meaning_lit")
    checker.checked_ids = set()
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons)[:5] == FIXTURES["meaning_lit"]


def test_get_words_for_comparison_notes_mode_matches_fixture():
    checker = RussianMeaningChecker(mode="notes")
    checker.checked_ids = set()
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons)[:5] == FIXTURES["notes"]


def test_get_words_for_comparison_notes_raw_mode_matches_fixture():
    checker = RussianMeaningChecker(mode="notes_raw")
    checker.checked_ids = set()
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons)[:5] == FIXTURES["notes_raw"]


def test_get_words_for_comparison_meaning_lit_list_mode_matches_fixture(tmp_path):
    ids = [row["headword_id"] for row in FIXTURES["meaning_lit_list"]]
    list_file = tmp_path / "list_ids.json"
    list_file.write_text(json.dumps(ids), encoding="utf-8")

    checker = RussianMeaningChecker(mode="meaning_lit_list")
    checker.checked_ids = set()
    checker.list_ids_file = list_file
    comparisons = checker.get_words_for_comparison_with_session(db_session)
    assert _comparisons_to_dicts(comparisons) == FIXTURES["meaning_lit_list"]


def test_get_words_for_comparison_meaning_raw_list_mode_matches_fixture(tmp_path):
    ids = [row["headword_id"] for row in FIXTURES["meaning_raw_list"]]
    list_file = tmp_path / "list_ids.json"
    list_file.write_text(json.dumps(ids), encoding="utf-8")

    checker = RussianMeaningChecker(mode="meaning_raw_list")
    checker.checked_ids = set()
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


def _strict_flag_for(mode: str, monkeypatch) -> bool:
    from kamma.translate.scripts import ai_meaning_checker

    seen: dict[str, bool] = {}

    class _Recorder:
        def __init__(self, provider=None, model=None, strict_parse=False):
            seen["strict_parse"] = strict_parse

    monkeypatch.setattr(ai_meaning_checker, "BatchProcessor", _Recorder)
    RussianMeaningChecker(mode=mode).batch_processor  # noqa: B018 - property builds it
    return seen["strict_parse"]


def test_clearing_modes_use_strict_parse(monkeypatch):
    for mode in ("meaning_raw", "meaning_raw_list", "notes_raw"):
        assert _strict_flag_for(mode, monkeypatch) is True, mode


def test_non_clearing_modes_keep_lenient_parse(monkeypatch):
    for mode in (
        "meaning",
        "meaning_lit",
        "meaning_lit_list",
        "notes",
        "russian_grammar_meaning_raw",
    ):
        assert _strict_flag_for(mode, monkeypatch) is False, mode


# --- 3.4: clear on MISMATCH only, one clearing call per mode ---


def _result(hid: int, status: str):
    from tools.ai_batch_processor import ComparisonResult

    return ComparisonResult(
        headword_id=hid,
        lemma_1=f"w{hid}",
        match_status=status,
        confidence=0.9,
        reasoning="because",
        suggested_fix=None,
    )


def _memory_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from db.models import Base, Russian

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    for hid in (1, 2, 3):
        session.add(Russian(id=hid, ru_meaning_raw="x"))
    session.commit()
    return session


def test_clean_clears_mismatch_only_not_partial_match(monkeypatch):
    from db.models import Russian
    from kamma.translate.scripts import ai_meaning_checker

    session = _memory_session()
    monkeypatch.setattr(ai_meaning_checker, "get_db_session", lambda _p: session)
    checker = RussianMeaningChecker(mode="meaning_raw")
    checker._clean_field_for_mismatches(
        [_result(1, "MISMATCH"), _result(2, "PARTIAL_MATCH"), _result(3, "MATCH")],
        "ru_meaning_raw",
    )
    session.expire_all()
    values: dict[int, str] = {}
    for hid in (1, 2, 3):
        record = session.get(Russian, hid)
        assert record is not None
        values[hid] = record.ru_meaning_raw
    assert values == {1: "", 2: "x", 3: "x"}


def test_clean_commits_once_per_call(monkeypatch):
    from kamma.translate.scripts import ai_meaning_checker

    session = _memory_session()
    commits: list[int] = []
    real_commit = session.commit
    monkeypatch.setattr(
        session, "commit", lambda: (commits.append(1), real_commit())[1]
    )
    monkeypatch.setattr(ai_meaning_checker, "get_db_session", lambda _p: session)
    checker = RussianMeaningChecker(mode="meaning_raw")
    checker._clean_field_for_mismatches(
        [_result(1, "MISMATCH"), _result(2, "MISMATCH")], "ru_meaning_raw"
    )
    assert len(commits) == 1


def _stub_checker(monkeypatch, tmp_path, mode, results):
    from tools.ai_batch_processor import WordComparison

    checker = RussianMeaningChecker(mode=mode)
    checker.output_txt_folder = tmp_path
    comps = [
        WordComparison(
            headword_id=r.headword_id,
            lemma_1=r.lemma_1,
            english_meaning="e",
            russian_meaning="r",
        )
        for r in results
    ]
    monkeypatch.setattr(
        checker, "get_words_for_comparison_with_session", lambda _s: comps
    )
    monkeypatch.setattr(checker, "compare_meanings_individual", lambda _c: results)
    monkeypatch.setattr(
        checker, "compare_meanings_batch", lambda _c, batch_size=50: results
    )
    monkeypatch.setattr(checker, "save_checked_ids", lambda: None)
    calls: list[str] = []
    monkeypatch.setattr(
        checker, "_clean_field_for_mismatches", lambda _r, field: calls.append(field)
    )
    return checker, calls


def test_individual_mode_clears_exactly_once(monkeypatch, tmp_path):
    results = [_result(1, "MISMATCH"), _result(2, "MATCH")]
    checker, calls = _stub_checker(monkeypatch, tmp_path, "meaning_raw", results)
    checker.run_analysis(db_session=None, use_batch=False, auto_invalidate=False)  # type: ignore[arg-type]
    assert calls == ["ru_meaning_raw"]


def test_batch_mode_clears_exactly_once(monkeypatch, tmp_path):
    results = [_result(1, "MISMATCH"), _result(2, "MATCH")]
    checker, calls = _stub_checker(monkeypatch, tmp_path, "meaning_raw", results)
    checker.run_analysis(db_session=None, use_batch=True, auto_invalidate=False)  # type: ignore[arg-type]
    assert calls == ["ru_meaning_raw"]


def test_report_has_separate_partial_match_section_and_never_clears(
    monkeypatch, tmp_path
):
    results = [_result(1, "MISMATCH"), _result(2, "PARTIAL_MATCH"), _result(3, "MATCH")]
    checker, calls = _stub_checker(monkeypatch, tmp_path, "meaning_raw", results)
    checker.generate_report(results)
    assert calls == []
    text = next(tmp_path.glob("*_mismatches.txt")).read_text(encoding="utf-8")
    assert "Complete mismatches: 1" in text
    assert "Partial matches (not cleared): 1" in text
    partial_part = text.split("PARTIAL MATCHES")[1]
    assert "ID: 2" in partial_part and "ID: 1" not in partial_part
