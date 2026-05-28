"""Unit tests for SBS_table_tools chant-lookup methods and update_sbs_chants logic."""

import pytest
from io import StringIO
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, DpdHeadword, SBS
from tools.sbs_table_functions import SBS_table_tools

# ── CSV fixture ──────────────────────────────────────────────────────────────

CSV_CONTENT = (
    "index\tpali_chant\tenglish_chant\tchapter\tlink\n"
    "1\tMaṅgala-sutta\tThe Discourse on Blessings\tProtective Recitations\tlink1\n"
    "2\tMettā-sutta\tThe Discourse on Loving-Kindness\tProtective Recitations\tlink2\n"
)


def _make_open_mock(content: str):
    """Return a mock for builtins.open that yields content as a file-like."""

    def side_effect(*args, **kwargs):
        return StringIO(content)

    m = MagicMock()
    m.side_effect = side_effect
    m.__enter__ = lambda s: s
    m.__exit__ = MagicMock(return_value=False)
    return m


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def sbs_tools():
    return SBS_table_tools()


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ── fetch_sbs_index ───────────────────────────────────────────────────────────


def test_fetch_sbs_index_found(sbs_tools):
    with patch("builtins.open", side_effect=lambda *a, **k: StringIO(CSV_CONTENT)):
        result = sbs_tools.fetch_sbs_index("Maṅgala-sutta")
    assert result == ("The Discourse on Blessings", "Protective Recitations")


def test_fetch_sbs_index_not_found(sbs_tools):
    with patch("builtins.open", side_effect=lambda *a, **k: StringIO(CSV_CONTENT)):
        result = sbs_tools.fetch_sbs_index("Nonexistent")
    assert result is None


# ── find_closest_chant ────────────────────────────────────────────────────────


def test_find_closest_chant_above_threshold(sbs_tools):
    # "Maṅgala-suta" is one character off from "Maṅgala-sutta"
    with patch("builtins.open", side_effect=lambda *a, **k: StringIO(CSV_CONTENT)):
        result = sbs_tools.find_closest_chant("Maṅgala-suta", threshold=0.8)
    assert result is not None
    candidate, ratio = result
    assert candidate == "Maṅgala-sutta"
    assert ratio >= 0.8


def test_find_closest_chant_below_threshold(sbs_tools):
    with patch("builtins.open", side_effect=lambda *a, **k: StringIO(CSV_CONTENT)):
        result = sbs_tools.find_closest_chant("xyz completely wrong", threshold=0.8)
    assert result is None


# ── update_sbs_chants (integration) ──────────────────────────────────────────


def test_update_auto_fix(in_memory_db):
    """Row with valid pali chant but wrong eng/chapter → auto-corrected."""
    from scripts.change_in_db.update_sbs_chants_in_db import update_sbs_chants

    h1 = DpdHeadword(id=1, lemma_1="l1", meaning_1="m1")
    s1 = SBS(
        id=1,
        sbs_chant_pali_1="Maṅgala-sutta",
        sbs_chant_eng_1="WRONG_ENG",
        sbs_chapter_1="WRONG_CHAP",
    )
    in_memory_db.add_all([h1, s1])
    in_memory_db.commit()

    mock_tools = MagicMock(spec=SBS_table_tools)
    mock_tools.fetch_sbs_index.return_value = (
        "The Discourse on Blessings",
        "Protective Recitations",
    )
    mock_tools.find_closest_chant.return_value = None

    update_sbs_chants(in_memory_db, mock_tools)
    in_memory_db.refresh(s1)

    assert s1.sbs_chant_eng_1 == "The Discourse on Blessings"
    assert s1.sbs_chapter_1 == "Protective Recitations"


def test_update_fuzzy_fix_yes(in_memory_db):
    """Row with unrecognized pali chant + fuzzy match + user says y → all three fields updated."""
    from scripts.change_in_db.update_sbs_chants_in_db import update_sbs_chants

    h1 = DpdHeadword(id=1, lemma_1="l1", meaning_1="m1")
    s1 = SBS(
        id=1,
        sbs_chant_pali_1="Maṅgala-suta",
        sbs_chant_eng_1="",
        sbs_chapter_1="",
    )
    in_memory_db.add_all([h1, s1])
    in_memory_db.commit()

    mock_tools = MagicMock(spec=SBS_table_tools)
    mock_tools.fetch_sbs_index.side_effect = lambda chant: (
        None
        if chant == "Maṅgala-suta"
        else ("The Discourse on Blessings", "Protective Recitations")
    )
    mock_tools.find_closest_chant.return_value = ("Maṅgala-sutta", 0.96)

    with patch("builtins.input", return_value="y"):
        update_sbs_chants(in_memory_db, mock_tools)

    in_memory_db.refresh(s1)
    assert s1.sbs_chant_pali_1 == "Maṅgala-sutta"
    assert s1.sbs_chant_eng_1 == "The Discourse on Blessings"
    assert s1.sbs_chapter_1 == "Protective Recitations"


def test_update_unresolved(in_memory_db):
    """Row with invalid pali chant and no fuzzy match → not changed, listed as unresolved."""
    from scripts.change_in_db.update_sbs_chants_in_db import update_sbs_chants

    h1 = DpdHeadword(id=1, lemma_1="l1", meaning_1="m1")
    s1 = SBS(
        id=1,
        sbs_chant_pali_1="completelyWrong",
        sbs_chant_eng_1="",
        sbs_chapter_1="",
    )
    in_memory_db.add_all([h1, s1])
    in_memory_db.commit()

    mock_tools = MagicMock(spec=SBS_table_tools)
    mock_tools.fetch_sbs_index.return_value = None
    mock_tools.find_closest_chant.return_value = None

    update_sbs_chants(in_memory_db, mock_tools)
    in_memory_db.refresh(s1)

    assert s1.sbs_chant_eng_1 == ""
    assert s1.sbs_chapter_1 == ""
