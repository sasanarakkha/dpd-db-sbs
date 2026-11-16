"""Checker reject memory: clearing ru_meaning_raw counts a reject; the report shows English + rejected text."""

from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword, Russian
from kamma.translate.scripts import ai_meaning_checker
from kamma.translate.scripts.ai_meaning_checker import RussianMeaningChecker
from kamma.translate.scripts.rejects import load_rejects, parked_ids
from tools.ai_batch_processor import ComparisonResult


@pytest.fixture
def session(monkeypatch: pytest.MonkeyPatch) -> Generator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    db = factory()
    for i in (1, 2):
        db.add(DpdHeadword(id=i, lemma_1=f"w{i}", meaning_1="state", grammar="n."))
        db.add(Russian(id=i, ru_meaning="", ru_meaning_raw=f"черновик{i}"))
    db.commit()
    monkeypatch.setattr(ai_meaning_checker, "get_db_session", lambda _path: factory())
    yield db
    db.close()


def _mismatch(headword_id: int, reasoning: str = "wrong sense") -> ComparisonResult:
    return ComparisonResult(
        headword_id=headword_id,
        lemma_1=f"w{headword_id}",
        match_status="MISMATCH",
        confidence=0.9,
        reasoning=reasoning,
    )


def _checker(tmp_path: Path, mode: str = "meaning_raw") -> RussianMeaningChecker:
    checker = RussianMeaningChecker(mode=mode)
    checker.rejects_path = tmp_path / "rejects.json"
    checker.output_txt_folder = tmp_path / "reports"
    checker.checked_ids_file = tmp_path / "checked.json"
    return checker


def test_clear_counts_one_reject_with_reason(session: Session, tmp_path: Path):
    checker = _checker(tmp_path)
    checker._clear_for_mode([_mismatch(1, "means 'dog'")])
    session.expire_all()
    russian = session.get(Russian, 1)
    assert russian is not None and russian.ru_meaning_raw == ""
    entry = load_rejects(checker.rejects_path)["1"]
    assert entry["count"] == 1 and entry["reason"] == "means 'dog'"


def test_second_clear_parks_the_id(session: Session, tmp_path: Path):
    checker = _checker(tmp_path)
    checker._clear_for_mode([_mismatch(1, "first")])
    checker._clear_for_mode([_mismatch(1, "second")])
    assert load_rejects(checker.rejects_path)["1"]["count"] == 2
    assert parked_ids(checker.rejects_path) == [1]


def test_partial_match_is_not_counted(session: Session, tmp_path: Path):
    checker = _checker(tmp_path)
    partial = ComparisonResult(1, "w1", "PARTIAL_MATCH", 0.5, "close")
    checker._clear_for_mode([partial])
    assert load_rejects(checker.rejects_path) == {}


def test_non_raw_modes_do_not_record_rejects(session: Session, tmp_path: Path):
    checker = _checker(tmp_path, mode="notes_raw")
    checker._clear_for_mode([_mismatch(1)])
    assert load_rejects(checker.rejects_path) == {}


def test_report_contains_english_and_rejected_russian(session: Session, tmp_path: Path):
    checker = _checker(tmp_path)
    checker.english_by_id = {1: "state of being"}
    checker.russian_by_id = {1: "состояние собаки"}
    checker.generate_report([_mismatch(1)])
    report = next((tmp_path / "reports").glob("*_mismatches.txt")).read_text(
        encoding="utf-8"
    )
    assert "English: state of being" in report
    assert "Rejected Russian: состояние собаки" in report
