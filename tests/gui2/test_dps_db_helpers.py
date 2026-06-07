"""Tests for gui2/dps_db_helpers.py fetch helpers.

No JSON fixture: both functions are pure DB-query pass-throughs with no data
transformation logic. SQLAlchemy is trusted; these tests lock in the contract
(correct type returned, None on miss) using an in-memory SQLite session.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword, Russian, SBS
from gui2.dps_db_helpers import fetch_ru, fetch_sbs


@pytest.fixture
def db_session() -> Session:  # type: ignore[return]
    """In-memory SQLite session with headwords, russian, and sbs rows."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    hw1 = DpdHeadword(
        id=1, lemma_1="karoti 1", pos="v", grammar="pr. 3sg.", meaning_1="does"
    )
    hw2 = DpdHeadword(
        id=2, lemma_1="bhavati 1", pos="v", grammar="pr. 3sg.", meaning_1="is"
    )
    session.add_all([hw1, hw2])
    session.commit()

    ru = Russian(id=1, ru_meaning="делает")
    sbs = SBS(id=2, sbs_meaning="is")
    session.add_all([ru, sbs])
    session.commit()

    yield session  # type: ignore[misc]
    session.close()


def test_fetch_ru_returns_russian_for_existing_id(db_session: Session) -> None:
    result = fetch_ru(db_session, 1)
    assert isinstance(result, Russian)
    assert result.ru_meaning == "делает"


def test_fetch_ru_returns_none_for_missing_id(db_session: Session) -> None:
    result = fetch_ru(db_session, 999)
    assert result is None


def test_fetch_sbs_returns_sbs_for_existing_id(db_session: Session) -> None:
    result = fetch_sbs(db_session, 2)
    assert isinstance(result, SBS)
    assert result.sbs_meaning == "is"


def test_fetch_sbs_returns_none_for_missing_id(db_session: Session) -> None:
    result = fetch_sbs(db_session, 999)
    assert result is None
