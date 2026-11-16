"""Op 5 (RU remove_irrelevant): a Russian row is deleted only when every RU column is empty."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword, Russian
from kamma.translate.scripts import ai_generate_translation as gen

# id -> Russian column values (unset columns stay "")
ROWS: dict[int, dict[str, str]] = {
    1: {},
    2: {"ru_notes": "only notes"},
    3: {"ru_meaning_lit": "only lit"},
    4: {"ru_cognate": "only cognate"},
    5: {"ru_meaning": "full"},
    6: {"ru_meaning_raw": "only raw"},
}


@pytest.fixture
def session(monkeypatch: pytest.MonkeyPatch) -> Generator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    for i, columns in ROWS.items():
        db.add(DpdHeadword(id=i, lemma_1=f"w{i}", meaning_1="state"))
        db.add(Russian(id=i, **columns))
    db.commit()
    monkeypatch.setattr(gen, "db_session", db)
    yield db
    db.close()


def _remaining_ids(session: Session) -> set[int]:
    return {row_id for (row_id,) in session.query(Russian.id).all()}


def test_only_fully_empty_row_is_deleted(session: Session):
    gen.remove_irrelevant(None, lang="ru")
    assert _remaining_ids(session) == {2, 3, 4, 5, 6}


def test_dry_run_deletes_nothing(session: Session):
    gen.remove_irrelevant(None, lang="ru", dry_run=True)
    assert _remaining_ids(session) == set(ROWS)
