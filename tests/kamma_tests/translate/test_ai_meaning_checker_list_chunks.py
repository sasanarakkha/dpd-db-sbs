"""List-mode id handling in RussianMeaningChecker: new ids-file shape and chunked IN clauses (in-memory DB)."""

import json
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword, Russian
from kamma.translate.scripts.ai_meaning_checker import (
    LIST_ID_CHUNK,
    RussianMeaningChecker,
)

N_IDS = 1200


@pytest.fixture
def engine_session() -> Generator[tuple[Engine, Session]]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    for i in range(1, N_IDS + 1):
        session.add(DpdHeadword(id=i, lemma_1=f"w{i}", meaning_1="en", grammar="n."))
        session.add(Russian(id=i, ru_meaning="", ru_meaning_raw="ru"))
    session.commit()
    yield engine, session
    session.close()


def _checker(tmp_path: Path, payload: object) -> RussianMeaningChecker:
    ids_path = tmp_path / "processed_ids.json"
    ids_path.write_text(json.dumps(payload), encoding="utf-8")
    checker = RussianMeaningChecker(mode="meaning_raw_list")
    checker.list_ids_file = ids_path
    checker.checked_ids = set()
    return checker


def _count_in_statements(engine: Engine, calls: list[str]) -> None:
    @event.listens_for(engine, "before_cursor_execute")
    def _capture(
        conn: object,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        if " IN (" in statement:
            calls.append(statement)


def test_chunk_size_is_500():
    assert LIST_ID_CHUNK == 500


def test_load_list_ids_reads_new_shape(tmp_path: Path):
    checker = _checker(tmp_path, {"lang": "ru", "mode": "meaning", "ids": [3, 1]})
    assert checker.load_list_ids() == {1, 3}


def test_load_list_ids_still_accepts_bare_list(tmp_path: Path):
    assert _checker(tmp_path, [4, 2]).load_list_ids() == {2, 4}


def test_get_words_with_1200_ids_uses_three_chunks(
    engine_session: tuple[Engine, Session], tmp_path: Path
):
    engine, session = engine_session
    checker = _checker(
        tmp_path, {"lang": "ru", "mode": "meaning", "ids": list(range(1, N_IDS + 1))}
    )
    calls: list[str] = []
    _count_in_statements(engine, calls)
    comparisons = checker.get_words_for_comparison_with_session(session)
    assert len(comparisons) == N_IDS
    assert len({c.headword_id for c in comparisons}) == N_IDS
    assert len(calls) == 3


def test_total_count_with_1200_ids_sums_chunks_and_excludes_checked(
    engine_session: tuple[Engine, Session], tmp_path: Path
):
    _, session = engine_session
    checker = _checker(
        tmp_path, {"lang": "ru", "mode": "meaning", "ids": list(range(1, N_IDS + 1))}
    )
    assert checker.get_total_count_with_session(session) == N_IDS
    checker.checked_ids = {1, 600, 1200}
    assert checker.get_total_count_with_session(session) == N_IDS - 3
