"""batch_runner --status: all counts come from in-process queries, never from subprocesses."""

import json
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword, DpdRoot, Russian
from kamma.translate.scripts import ai_generate_translation as gen
from kamma.translate.scripts import batch_runner
from kamma.translate.scripts.rejects import record_reject

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add(DpdRoot(root="√kar", root_ru_meaning="делать"))
    # 1: pending generate (no Russian row); 2: empty Russian row (Op 5 + pending);
    # 3: verified rooted headword; 4: rooted draft on a verified root (Op 6);
    # 5: duplicated meanings (Op 4 flagged); 6: parked reject
    for i, root in [(1, ""), (2, ""), (3, "√kar"), (4, "√kar"), (5, ""), (6, "")]:
        db.add(
            DpdHeadword(
                id=i, lemma_1=f"w{i}", meaning_1="state", root_key=root, grammar="n."
            )
        )
    db.add(Russian(id=2))
    db.add(Russian(id=3, ru_meaning="сделанный"))
    db.add(Russian(id=4, ru_meaning_raw="сделанное"))
    db.add(Russian(id=5, ru_meaning="состояние; состояние"))
    db.commit()
    monkeypatch.setattr(gen, "db_session", db)
    rejects = tmp_path / "rejects.json"
    monkeypatch.setattr(batch_runner, "REJECTS_PATH", rejects)
    monkeypatch.setattr(gen, "REJECTS_PATH", rejects)
    record_reject(rejects, 6, "a", NOW)
    record_reject(rejects, 6, "b", NOW)
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "last_op": "generate",
                "totals": {"generated": 1, "checked": 2},
                "last_audit": {"field": "ru_meaning", "flagged": 1, "mode": "report"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(batch_runner, "STATE_PATH", state_path)
    yield db
    db.close()


def test_collect_status_counts_every_operation(session: Session):
    status = batch_runner.collect_status(session)
    # pool = headwords 1 and 2; 3-5 already have Russian text; 6 is parked
    assert status["generate"]["meaning/ru"] == 2
    assert status["op4"]["ru_meaning"] == 1
    assert status["op4"]["ru_meaning_raw"] == 0
    assert status["op5"] == 1
    assert status["op6"] == 1
    assert status["parked"] == 1
    assert status["last_audit"] == {
        "field": "ru_meaning",
        "flagged": 1,
        "mode": "report",
    }
    assert "meaning" in status["checker"]


def test_print_status_never_spawns_subprocesses(
    session: Session, monkeypatch: pytest.MonkeyPatch
):
    def _boom(*_a: object, **_k: object) -> None:
        raise AssertionError("--status must not spawn a subprocess")

    monkeypatch.setattr(batch_runner.subprocess, "run", _boom)
    monkeypatch.setattr(batch_runner.subprocess, "Popen", _boom)
    monkeypatch.setattr(batch_runner, "get_db_session", lambda _path: session)
    batch_runner.print_status()
