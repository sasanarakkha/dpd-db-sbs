"""Regression tests for extracting missing words from a text file."""

from pathlib import Path

from scripts.export import list_of_words_from_txt as module
from scripts.export.list_of_words_from_txt import make_field_conditions


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


class _FakeLookupRow:
    def __init__(
        self,
        lookup_key: str,
        headwords_unpack: list[int],
        deconstructor_unpack: list[str],
    ) -> None:
        self.lookup_key = lookup_key
        self.headwords_unpack = headwords_unpack
        self.deconstructor_unpack = deconstructor_unpack


class _FakeLookupQuery:
    def __init__(self, rows: dict[str, _FakeLookupRow]) -> None:
        self.rows = rows
        self.lookup_key: str | None = None

    def filter(self, expression):
        right = getattr(expression, "right", None)
        self.lookup_key = getattr(right, "value", None)
        return self

    def first(self):
        if self.lookup_key is None:
            return None
        return self.rows.get(self.lookup_key)


class _FakeLookupSession:
    def __init__(self, rows: dict[str, _FakeLookupRow]) -> None:
        self.rows = rows

    def query(self, _model):
        return _FakeLookupQuery(self.rows)


class _FakePaths:
    def __init__(self, base_dir: Path) -> None:
        pass


def test_get_lookup_headword_ids_prefers_direct_headwords_over_deconstructor():
    """Mirror gui2: use direct headwords before any deconstructor fallback."""
    db_session = _FakeLookupSession(
        {
            "tathārūpappaccayā": _FakeLookupRow(
                "tathārūpappaccayā",
                [29712],
                ["tathā + rūpappaccayā"],
            ),
            "rūpappaccayā": _FakeLookupRow("rūpappaccayā", [99999], []),
        }
    )

    headword_ids = module.get_headwords_ids(db_session, "tathārūpappaccayā")

    assert headword_ids == [29712]


def test_no_field_query_requires_non_empty_and_non_null_values():
    """Each field condition must exclude NULL, empty, and whitespace-only values."""
    conditions = make_field_conditions(["vib_example", "pat_example"])

    # Verify that conditions include both NOT NULL and trim checks
    for condition in conditions:
        compiled = str(condition.compile(compile_kwargs={"literal_binds": True}))
        assert "IS NOT NULL" in compiled and "trim(" in compiled


class _FakeDpsPaths:
    def __init__(self, text_to_add_path: Path) -> None:
        self.text_to_add_path = text_to_add_path


def test_list_from_text_keeps_quote_ti_words_even_if_in_inflection_set(
    tmp_path, monkeypatch
):
    """Quote-attached `ti` forms stay intact and are filtered by lookup coverage."""
    text_path = tmp_path / "text.txt"
    text_path.write_text("sossāmī”ti karissāmī”ti parimocessāmī”ti", encoding="utf-8")
    pth = _FakePaths(tmp_path)
    dpspth = _FakeDpsPaths(text_path)
    (tmp_path / "temp").mkdir()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        module,
        "make_words_with_matching_fields_set",
        lambda _db_session, _words, _fields: {"sossāmīti", "karissāmīti"},
    )

    words = module.dps_make_words_to_add_list_from_text_no_field(
        pth,
        dpspth,
        db_session=None,
        fields=["vib_source", "pat_source"],
    )

    assert words == ["parimocessāmīti"]
