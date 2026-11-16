"""Op 1 and reject memory: parked ids leave the pool; the rejection reason enters the regeneration prompt."""

from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword
from kamma.translate.scripts import ai_generate_translation as gen
from kamma.translate.scripts.rejects import record_reject

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    for i in (1, 2, 3):
        db.add(
            DpdHeadword(
                id=i, lemma_1=f"w{i}", meaning_1="state", grammar="n.", pos="noun"
            )
        )
    db.commit()
    monkeypatch.setattr(gen, "db_session", db)
    monkeypatch.setattr(gen, "REJECTS_PATH", tmp_path / "rejects.json")
    yield db
    db.close()


def _word(session: Session, headword_id: int) -> DpdHeadword:
    word = session.get(DpdHeadword, headword_id)
    assert word is not None
    return word


def test_pool_includes_everything_when_nothing_parked(session: Session):
    ids = {w.id for w in gen.filter_words_for_translation("meaning", None, "ru")}
    assert ids == {1, 2, 3}


def test_pool_excludes_ids_rejected_twice_but_not_once(
    session: Session, tmp_path: Path
):
    path = tmp_path / "rejects.json"
    record_reject(path, 1, "a", NOW)
    record_reject(path, 1, "b", NOW)
    record_reject(path, 2, "only once", NOW)
    ids = {w.id for w in gen.filter_words_for_translation("meaning", None, "ru")}
    assert ids == {2, 3}


def test_prompt_includes_reason_only_when_present(session: Session, tmp_path: Path):
    path = tmp_path / "rejects.json"
    record_reject(path, 1, "translated the wrong sense", NOW)
    with_reason = gen.create_translation_prompt(_word(session, 1), "meaning", "ru")
    without = gen.create_translation_prompt(_word(session, 2), "meaning", "ru")
    user_with = with_reason["body"]["messages"][1]["content"]
    user_without = without["body"]["messages"][1]["content"]
    assert (
        "A previous draft was rejected because: translated the wrong sense" in user_with
    )
    assert "previous draft" not in user_without


def test_limit_caps_rows_but_reports_full_total(
    session: Session, capsys: pytest.CaptureFixture[str]
):
    rows = gen.filter_words_for_translation("meaning", 2, "ru")
    assert len(rows) == 2
    assert "Rows filtered for the process: 2 / 3" in capsys.readouterr().out
