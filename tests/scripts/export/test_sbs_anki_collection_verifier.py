"""Tests for _find_mismatches() in sbs_anki_collection_verifier."""

from scripts.export.sbs_anki_collection_verifier import _find_mismatches

_LIVE: dict[str, dict] = {
    "SBS::Grammar": {
        "model_name": "SBS Grammar",
        "fields": ["Pali", "Meaning", "Grammar"],
        "count": 42,
    },
    "SBS::Vocab": {
        "model_name": "SBS Vocab",
        "fields": ["Word", "Definition"],
        "count": 100,
    },
}

_EXPECTED: dict[str, dict] = {
    "SBS::Grammar": {
        "model_name": "SBS Grammar",
        "fields": ["Pali", "Meaning", "Grammar"],
    },
    "SBS::Vocab": {
        "model_name": "SBS Vocab",
        "fields": ["Word", "Definition"],
    },
}


def test_no_mismatches() -> None:
    assert _find_mismatches(_LIVE, _EXPECTED) == []


def test_missing_deck() -> None:
    expected = {**_EXPECTED, "SBS::Missing": {"model_name": "X", "fields": []}}
    result = _find_mismatches(_LIVE, expected)
    assert result == ["Missing deck: SBS::Missing"]


def test_model_name_mismatch() -> None:
    expected = {
        "SBS::Grammar": {
            "model_name": "OLD Grammar",
            "fields": ["Pali", "Meaning", "Grammar"],
        },
        "SBS::Vocab": _EXPECTED["SBS::Vocab"],
    }
    result = _find_mismatches(_LIVE, expected)
    assert len(result) == 1
    assert "model mismatch" in result[0]
    assert "OLD Grammar" in result[0]
    assert "SBS Grammar" in result[0]


def test_missing_fields() -> None:
    expected = {
        "SBS::Grammar": {
            "model_name": "SBS Grammar",
            "fields": ["Pali", "Meaning", "Grammar", "ExtraField"],
        },
        "SBS::Vocab": _EXPECTED["SBS::Vocab"],
    }
    result = _find_mismatches(_LIVE, expected)
    assert len(result) == 1
    assert "missing fields" in result[0]
    assert "ExtraField" in result[0]


def test_extra_fields() -> None:
    live = {
        **_LIVE,
        "SBS::Grammar": {
            "model_name": "SBS Grammar",
            "fields": ["Pali", "Meaning", "Grammar", "Unexpected"],
            "count": 42,
        },
    }
    result = _find_mismatches(live, _EXPECTED)
    assert len(result) == 1
    assert "extra fields" in result[0]
    assert "Unexpected" in result[0]


def test_field_order_changed() -> None:
    live = {
        **_LIVE,
        "SBS::Grammar": {
            "model_name": "SBS Grammar",
            "fields": ["Grammar", "Pali", "Meaning"],
            "count": 42,
        },
    }
    result = _find_mismatches(live, _EXPECTED)
    assert len(result) == 1
    assert "field order changed" in result[0]


def test_multiple_mismatches() -> None:
    expected = {
        "SBS::Grammar": {"model_name": "OLD", "fields": ["Pali"]},
        "SBS::Nonexistent": {"model_name": "X", "fields": []},
    }
    result = _find_mismatches(_LIVE, expected)
    # model mismatch + extra fields (Meaning, Grammar) + missing deck
    assert len(result) == 3
    texts = " ".join(result)
    assert "model mismatch" in texts
    assert "extra fields" in texts
    assert "Missing deck" in texts
