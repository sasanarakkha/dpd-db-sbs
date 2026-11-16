"""Tests for kamma/translate/scripts/ai_translation_check.py (in-memory DB, no network)."""

import json
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword, Russian
from kamma.translate.scripts.ai_translation_check import (
    build_parser,
    check_translations,
)

HANGUL = "состояние 상태"
CLEAN = "состояние"


@pytest.fixture(autouse=True)
def isolate_last_translated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Never read the real temp/last_translated.json."""
    monkeypatch.setattr(
        "kamma.translate.scripts.ai_translation_check.LAST_TRANSLATED_PATH",
        tmp_path / "no_last_translated.json",
    )


@pytest.fixture
def session() -> Generator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    rows = {1: HANGUL, 2: HANGUL, 3: CLEAN}
    for i, raw in rows.items():
        db.add(DpdHeadword(id=i, lemma_1=f"w{i}", meaning_1="state", grammar="n."))
        db.add(Russian(id=i, ru_meaning="человек", ru_meaning_raw=raw))
    db.commit()
    yield db
    db.close()


def test_default_lang_is_ru():
    assert build_parser().parse_args([]).lang == "ru"


def test_hangul_in_ru_value_is_flagged(session: Session):
    flagged = check_translations("ru", db_session=session)
    assert sorted(flagged) == [1, 2]


def test_ids_file_restricts_scan_new_shape(session: Session, tmp_path: Path):
    ids_file = tmp_path / "ids.json"
    ids_file.write_text(json.dumps({"lang": "ru", "mode": "m", "ids": [2, 3]}))
    flagged = check_translations("ru", ids_file=ids_file, db_session=session)
    assert flagged == [2]


def test_ids_file_accepts_bare_list(session: Session, tmp_path: Path):
    ids_file = tmp_path / "ids.json"
    ids_file.write_text(json.dumps([1]))
    assert check_translations("ru", ids_file=ids_file, db_session=session) == [1]


def test_empty_ids_file_scans_nothing(session: Session, tmp_path: Path):
    ids_file = tmp_path / "ids.json"
    ids_file.write_text(json.dumps({"lang": "ru", "mode": "m", "ids": []}))
    assert check_translations("ru", ids_file=ids_file, db_session=session) == []


def test_delete_clears_flagged_columns_only(session: Session):
    check_translations("ru", auto_delete=True, db_session=session)
    rows = {r.id: r for r in session.query(Russian).all()}
    assert rows[1].ru_meaning_raw == "" and rows[2].ru_meaning_raw == ""
    assert rows[3].ru_meaning_raw == CLEAN
    assert all(r.ru_meaning == "человек" for r in rows.values())


def test_hangul_flagged_in_sutta_entry(session: Session):
    """The sutta exemption skips Latin/length checks, never the Hangul check."""
    hw = session.get(DpdHeadword, 3)
    assert hw is not None
    hw.family_set = "suttas of SN"
    ru = session.get(Russian, 3)
    assert ru is not None
    ru.ru_meaning_raw = HANGUL
    session.commit()
    assert check_translations("ru", specific_ids=[3], db_session=session) == [3]


def test_empty_ids_file_keeps_explicit_ids(session: Session, tmp_path: Path):
    ids_file = tmp_path / "ids.json"
    ids_file.write_text(json.dumps({"lang": "ru", "mode": "m", "ids": []}))
    flagged = check_translations(
        "ru", specific_ids=[1], ids_file=ids_file, db_session=session
    )
    assert flagged == [1]
