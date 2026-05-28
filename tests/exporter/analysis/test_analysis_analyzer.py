"""Verify basic tokenizer and analyzer behavior in the analysis package."""

from exporter.analysis.analyzer import (
    _normalize_kammadharaya_construction,
    tokenize_sentence,
)


def test_normalize_kammadharaya_construction() -> None:
    assert _normalize_kammadharaya_construction("paññā eva āvudha") == "paññā + āvudha"
    assert _normalize_kammadharaya_construction("īsā viya danta") == "īsā + danta"
    assert (
        _normalize_kammadharaya_construction("icchā nidānaṃ etassa")
        == "icchā + nidānaṃ"
    )
    assert _normalize_kammadharaya_construction("paññā + āvudha") == "paññā + āvudha"
    assert _normalize_kammadharaya_construction("paññā āvudha") == "paññā + āvudha"
    assert _normalize_kammadharaya_construction("paññā") == "paññā"


def test_tokenize_sentence_basic() -> None:
    sentence = "Evaṃ me sutaṃ."
    tokens = tokenize_sentence(sentence)
    assert tokens == ["evaṃ", "me", "sutaṃ"]


def test_tokenize_sentence_punctuation() -> None:
    sentence = "Namo tassa bhagavato, arahato, sammāsambuddhassa!"
    tokens = tokenize_sentence(sentence)
    assert tokens == ["namo", "tassa", "bhagavato", "arahato", "sammāsambuddhassa"]


def test_tokenize_sentence_empty() -> None:
    assert tokenize_sentence("") == []
    assert tokenize_sentence("   ") == []


def test_analyze_sentence() -> None:
    # This test requires a valid dpd.db to be present at the expected path.
    from exporter.analysis.analyzer import analyze_sentence
    from db.db_helpers import get_db_session
    from exporter.mcp.config import mcp_config

    db_session = get_db_session(mcp_config.db_path)

    sentence = "Evaṃ me sutaṃ."
    results = analyze_sentence(sentence, db_session)

    assert len(results) == 3
    # Check "evaṃ"
    assert results[0]["word"] == "evaṃ"
    assert "lemma" in results[0]["data"][0]

    # Check "me"
    assert results[1]["word"] == "me"

    # Check "sutaṃ"
    assert results[2]["word"] == "sutaṃ"


def test_analyze_sentence_not_found() -> None:
    from exporter.analysis.analyzer import analyze_sentence
    from db.db_helpers import get_db_session
    from exporter.mcp.config import mcp_config

    db_session = get_db_session(mcp_config.db_path)

    # Using a string that is Pāḷi-alphabet-only but unlikely to be in the dictionary
    sentence = "abbcccddd"
    results = analyze_sentence(sentence, db_session)

    assert len(results) == 1
    assert results[0]["word"] == "abbcccddd"
    assert results[0]["status"] == "not_found"
