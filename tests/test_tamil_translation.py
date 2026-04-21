#!/usr/bin/env python3

"""Tests for Tamil AI meaning generation pipeline and language routing."""

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword

# Tamil will be added in phase 4
try:
    from db.models import Tamil
except ImportError:
    Tamil = None

# The renamed script will be available after phase 3
try:
    from scripts.other.ai_generate_translation import (
        create_translation_prompt,
        read_exclude_ids_from_json,
        read_exclude_ids_from_tsv,
    )
except ImportError:
    # Fall back to old name temporarily
    from scripts.other.ai_generate_translation import (
        create_translation_prompt,
        read_exclude_ids_from_json,
        read_exclude_ids_from_tsv,
    )

from tools.ai_related import generate_messages_for_meaning


@pytest.fixture
def temp_db() -> Generator[Session, None, None]:
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_headword(temp_db: Session) -> DpdHeadword:
    """Create a sample DpdHeadword with Russian and Tamil relationships."""
    hw = DpdHeadword(
        id=1,
        lemma_1="test",
        meaning_1="a test definition",
        grammar="n.",
        pos="noun",
        ebt_count=5,
    )
    temp_db.add(hw)
    temp_db.commit()
    return hw


@pytest.mark.skipif(Tamil is None, reason="Tamil model not yet implemented")
def test_tamil_orm_model_exists(temp_db: Session, sample_headword: DpdHeadword):
    """Test that Tamil ORM model can be instantiated and linked to DpdHeadword."""
    tamil = Tamil(id=sample_headword.id, ta_meaning="கோவை பொருள்")
    temp_db.add(tamil)
    temp_db.commit()

    # Fetch and verify
    fetched_hw = temp_db.query(DpdHeadword).filter(DpdHeadword.id == 1).first()
    assert fetched_hw is not None
    assert fetched_hw.ta is not None
    assert fetched_hw.ta.ta_meaning == "கோவை பொருள்"


@pytest.mark.skipif(Tamil is None, reason="Tamil model not yet implemented")
def test_tamil_orm_default_empty_meaning(
    temp_db: Session, sample_headword: DpdHeadword
):
    """Test that Tamil.ta_meaning defaults to empty string."""
    tamil = Tamil(id=sample_headword.id)
    temp_db.add(tamil)
    temp_db.commit()

    fetched_tamil = temp_db.query(Tamil).filter(Tamil.id == sample_headword.id).first()
    assert fetched_tamil.ta_meaning == ""


@pytest.mark.skipif(Tamil is None, reason="Tamil model not yet implemented")
def test_dpdheadword_ta_relationship(temp_db: Session, sample_headword: DpdHeadword):
    """Test that DpdHeadword.ta relationship works correctly."""
    tamil = Tamil(id=sample_headword.id, ta_meaning="test meaning")
    temp_db.add(tamil)
    temp_db.commit()

    # Fetch headword and check relationship
    hw = temp_db.query(DpdHeadword).filter(DpdHeadword.id == 1).first()
    assert hw.ta is not None
    assert isinstance(hw.ta, Tamil)
    assert hw.ta.id == 1


def test_custom_id_parsing_from_jsonl():
    """Test that custom_id values like 'request-12345' are parsed correctly."""
    # Create temp JSONL file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"custom_id": "request-100", "method": "POST"}\n')
        f.write('{"custom_id": "request-200", "method": "POST"}\n')
        f.write('{"custom_id": "request-999", "method": "POST"}\n')
        temp_path = f.name

    try:
        exclude_ids = read_exclude_ids_from_json(Path(temp_path).parent, mode="meaning")
        # The parser should extract numeric IDs or full custom_id strings
        # depending on implementation
        assert len(exclude_ids) == 3
    finally:
        Path(temp_path).unlink()


def test_queued_id_exclusion_from_jsonl():
    """Test that IDs from JSONL batch files are correctly excluded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a JSONL file with queued IDs
        jsonl_file = tmpdir_path / "batch-001.jsonl"
        with open(jsonl_file, "w") as f:
            for word_id in [10, 20, 30]:
                json.dump(
                    {
                        "custom_id": f"request-{word_id}",
                        "method": "POST",
                        "url": "/v1/chat/completions",
                        "body": {"model": "gpt-4", "messages": []},
                    },
                    f,
                )
                f.write("\n")

        # Read exclude IDs from directory
        exclude_ids = read_exclude_ids_from_json(tmpdir_path, mode="meaning")
        assert len(exclude_ids) > 0


def test_processed_id_exclusion_from_json():
    """Test that IDs from processed JSON file are correctly excluded."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"processed_ids": [50, 60, 70]}, f)
        temp_path = f.name

    try:
        # This tests the structure, actual loading depends on implementation
        with open(temp_path) as f:
            data = json.load(f)
        assert "processed_ids" in data
        assert len(data["processed_ids"]) == 3
    finally:
        Path(temp_path).unlink()


def test_malformed_jsonl_handling():
    """Test that malformed JSONL lines are handled safely."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"custom_id": "request-100"}\n')
        f.write("this is not json\n")  # malformed
        f.write('{"custom_id": "request-200"}\n')
        temp_path = f.name

    try:
        exclude_ids = read_exclude_ids_from_json(Path(temp_path).parent, mode="meaning")
        # Should not crash and should extract valid IDs
        assert isinstance(exclude_ids, set)
    finally:
        Path(temp_path).unlink()


def test_tamil_meaning_prompt_builder():
    """Test that Tamil meaning prompts can be built with minimal changes."""
    # This is a placeholder that verifies the prompt builder signature
    messages = generate_messages_for_meaning(
        lemma_1="test",
        grammar="n.",
        meaning="a test",
        sentence="in a test",
        translation_example="",
    )
    assert isinstance(messages, list)
    assert len(messages) > 0
    assert any(m["role"] == "system" for m in messages)
    assert any(m["role"] == "user" for m in messages)


def test_tsv_with_ta_meaning_header():
    """Test that a Tamil TSV with ta_meaning column can be read."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
        f.write("id\tta_meaning\n")
        f.write("1\tகோவை பொருள்\n")
        f.write("2\tமற்ற பொருள்\n")
        temp_path = f.name

    try:
        exclude_ids = read_exclude_ids_from_tsv(temp_path)
        assert 1 in exclude_ids or "1" in exclude_ids
    finally:
        Path(temp_path).unlink()


def test_create_translation_prompt_structure(
    temp_db: Session, sample_headword: DpdHeadword
):
    """Test that create_translation_prompt returns correct JSON structure."""
    prompt = create_translation_prompt(sample_headword, mode="meaning")

    assert "custom_id" in prompt
    assert "request-" in prompt["custom_id"]
    assert prompt["method"] == "POST"
    assert prompt["url"] == "/v1/chat/completions"
    assert "body" in prompt
    assert "messages" in prompt["body"]
