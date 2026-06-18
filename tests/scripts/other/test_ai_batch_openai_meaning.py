from types import SimpleNamespace

from scripts.other.ai_batch_openai_meaning import serialize_request_counts


def test_serialize_request_counts_none() -> None:
    assert serialize_request_counts(None) == {}


def test_serialize_request_counts_full() -> None:
    counts = SimpleNamespace(total=10, completed=7, failed=1)
    assert serialize_request_counts(counts) == {
        "total": 10,
        "completed": 7,
        "failed": 1,
    }


def test_serialize_request_counts_missing_attrs_default_to_zero() -> None:
    counts = SimpleNamespace(total=5)
    assert serialize_request_counts(counts) == {
        "total": 5,
        "completed": 0,
        "failed": 0,
    }
