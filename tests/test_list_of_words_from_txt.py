"""Regression tests for extracting missing words from a text file."""

from scripts.export.list_of_words_from_txt import dps_make_no_field_inflections_set


class _FakeQuery:
    def __init__(self) -> None:
        self.filter_expression = None

    def join(self, *_args, **_kwargs):
        return self

    def filter(self, expression):
        self.filter_expression = expression
        return self

    def all(self):
        return []


class _FakeSession:
    def __init__(self) -> None:
        self.query_obj = _FakeQuery()

    def query(self, *_args, **_kwargs):
        return self.query_obj


def test_no_field_query_requires_non_empty_and_non_null_values():
    """Each field condition must exclude NULL, empty, and whitespace-only values."""
    session = _FakeSession()

    dps_make_no_field_inflections_set(session, ["vib_example", "pat_example"])

    compiled = str(
        session.query_obj.filter_expression.compile(
            compile_kwargs={"literal_binds": True}
        )
    )

    assert "sbs.vib_example IS NOT NULL AND trim(sbs.vib_example) != ''" in compiled
    assert "sbs.pat_example IS NOT NULL AND trim(sbs.pat_example) != ''" in compiled
