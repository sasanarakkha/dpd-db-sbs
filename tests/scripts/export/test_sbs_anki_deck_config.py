"""Golden-master tests for sbs_anki_deck_config helper functions."""

import json
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from scripts.export.sbs_anki_deck_config import (
    get_construction,
    get_example_for_class,
    get_paritta_source,
    get_phonetic,
    get_root_key,
)
from tools.paths import ProjectPaths

FIXTURE_PATH = Path(__file__).parent / "test_sbs_anki_deck_config_fixtures.json"
FIXTURES: dict = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

pth = ProjectPaths()


@pytest.fixture(scope="module")
def db_session() -> Session:  # type: ignore[return]
    session = get_db_session(pth.dpd_db_path)
    yield session
    session.close()


def get_word(session: Session, word_id: int) -> DpdHeadword:
    word = session.get(DpdHeadword, word_id)
    assert word is not None
    return word


# ── get_root_key ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("word_id,case", FIXTURES["get_root_key"].items())
def test_get_root_key(db_session: Session, word_id: str, case: dict) -> None:
    word = get_word(db_session, int(word_id))
    assert get_root_key(word) == case["output"]


# ── get_construction ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("word_id,case", FIXTURES["get_construction"].items())
def test_get_construction(db_session: Session, word_id: str, case: dict) -> None:
    word = get_word(db_session, int(word_id))
    assert get_construction(word) == case["output"]


def test_get_construction_no_raw_newlines(db_session: Session) -> None:
    for word_id, case in FIXTURES["get_construction"].items():
        if case["input"]:
            word = get_word(db_session, int(word_id))
            assert "\n" not in get_construction(word)


# ── get_phonetic ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("word_id,case", FIXTURES["get_phonetic"].items())
def test_get_phonetic(db_session: Session, word_id: str, case: dict) -> None:
    word = get_word(db_session, int(word_id))
    assert get_phonetic(word) == case["output"]


def test_get_phonetic_no_raw_newlines(db_session: Session) -> None:
    for word_id, case in FIXTURES["get_phonetic"].items():
        if case["input"]:
            word = get_word(db_session, int(word_id))
            assert "\n" not in get_phonetic(word)


# ── get_paritta_source ────────────────────────────────────────────────────────


@pytest.mark.parametrize("word_id,case", FIXTURES["get_paritta_source"].items())
def test_get_paritta_source(db_session: Session, word_id: str, case: dict) -> None:
    word = get_word(db_session, int(word_id))
    result = get_paritta_source(word)
    assert list(result) == case["output"]


def test_get_paritta_source_no_sbs_returns_empty(db_session: Session) -> None:
    for word_id, case in FIXTURES["get_paritta_source"].items():
        if not case["has_sbs"]:
            word = get_word(db_session, int(word_id))
            assert get_paritta_source(word) == ("", "", "")


# ── get_example_for_class ─────────────────────────────────────────────────────


@pytest.mark.parametrize("word_id,case", FIXTURES["get_example_for_class"].items())
def test_get_example_for_class(db_session: Session, word_id: str, case: dict) -> None:
    word = get_word(db_session, int(word_id))
    result = get_example_for_class(word)
    assert list(result) == case["output"]


def test_get_example_for_class_no_sbs_returns_empty(db_session: Session) -> None:
    for word_id, case in FIXTURES["get_example_for_class"].items():
        if not case["has_sbs"]:
            word = get_word(db_session, int(word_id))
            assert get_example_for_class(word) == ("", "", "")


def test_get_example_for_class_returns_three_tuple(db_session: Session) -> None:
    for word_id in FIXTURES["get_example_for_class"]:
        word = get_word(db_session, int(word_id))
        result = get_example_for_class(word)
        assert len(result) == 3
        assert all(isinstance(v, str) for v in result)
