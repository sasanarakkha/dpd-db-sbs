"""RussianMeaningChecker pool: `limit` stops early, skips checked ids, and pages by id (in-memory DB)."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword, Russian
from kamma.translate.scripts import ai_meaning_checker as checker_module
from kamma.translate.scripts.ai_meaning_checker import RussianMeaningChecker

N_ROWS = 25


@pytest.fixture
def session(monkeypatch: pytest.MonkeyPatch) -> Generator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    for i in range(1, N_ROWS + 1):
        db.add(DpdHeadword(id=i, lemma_1=f"w{i}", meaning_1="en", grammar="n."))
        db.add(Russian(id=i, ru_meaning="", ru_meaning_raw="ru"))
    db.commit()
    monkeypatch.setattr(checker_module, "POOL_PAGE_SIZE", 4)
    yield db
    db.close()


def _checker(checked: set[int]) -> RussianMeaningChecker:
    checker = RussianMeaningChecker(mode="meaning_raw")
    checker.checked_ids = checked
    return checker


def _ids(
    checker: RussianMeaningChecker, session: Session, limit: int | None
) -> list[int]:
    result = checker.get_words_for_comparison_with_session(session, limit=limit)
    return [c.headword_id for c in result]


def test_no_limit_returns_whole_pool_across_pages(session: Session):
    assert _ids(_checker(set()), session, None) == list(range(1, N_ROWS + 1))


def test_limit_returns_id_ordered_prefix_across_page_boundary(session: Session):
    assert _ids(_checker(set()), session, 6) == [1, 2, 3, 4, 5, 6]


def test_limit_counts_only_unchecked_rows(session: Session):
    checked = {1, 2, 3, 4, 5}
    assert _ids(_checker(checked), session, 3) == [6, 7, 8]


def test_limit_larger_than_pool_returns_pool(session: Session):
    assert _ids(_checker({1, 2}), session, 1000) == list(range(3, N_ROWS + 1))
