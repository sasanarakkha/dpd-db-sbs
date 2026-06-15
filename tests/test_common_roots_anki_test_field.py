"""Verify the Common Roots Anki export and updater test-date field."""

import csv
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from db.models import DpdHeadword, DpdRoot
from scripts.export import anki_csv
from scripts.export.sbs_anki_deck_config import DECKS
from scripts.export.sbs_anki_updater import update_note_values_csv


class FakeSubqueryColumns:
    """Provide the minimal SQLAlchemy-style columns used by common_roots."""

    root = "root"

    class RootCount:
        """Provide the desc method used for ordering."""

        def desc(self) -> str:
            return "root_count_desc"

    root_count = RootCount()


class FakeSubquery:
    """Provide the minimal subquery shape used by common_roots."""

    c = FakeSubqueryColumns()


class FakeQuery:
    """Provide a chainable fake query for common_roots."""

    def __init__(self, result: Any = None, first_result: Any = None) -> None:
        self._result = result
        self._first_result = first_result

    def group_by(self, *_args: Any) -> "FakeQuery":
        return self

    def subquery(self) -> FakeSubquery:
        return FakeSubquery()

    def join(self, *_args: Any) -> "FakeQuery":
        return self

    def filter(self, *_args: Any) -> "FakeQuery":
        return self

    def order_by(self, *_args: Any) -> "FakeQuery":
        return self

    def all(self) -> Any:
        return self._result

    def first(self) -> Any:
        return self._first_result


class FakeSession:
    """Provide the specific queries made by common_roots."""

    def __init__(self) -> None:
        root = SimpleNamespace(
            root="bhav 1",
            root_clean="bhav",
            sanskrit_root="bhu",
            root_group="1",
            root_sign="+",
            root_meaning="be",
            root_example="bhavati, hoti",
            root_ru_meaning="",
        )
        self._roots = [(root, 2)]
        self._main_verb = SimpleNamespace(lemma_clean="bhavati")

    def query(self, *args: Any) -> FakeQuery:
        if args and args[0] is DpdRoot:
            return FakeQuery(result=self._roots)
        if args and args[0] is DpdHeadword:
            return FakeQuery(first_result=self._main_verb)
        return FakeQuery()


class FakePaths:
    """Provide the export directories used by common_roots."""

    def __init__(self, tmp_path: Path) -> None:
        self.anki_csvs_dir = tmp_path / "csvs"
        self.sbs_anki_style_dir = tmp_path / "style"
        (self.anki_csvs_dir / "pali_class").mkdir(parents=True)
        self.sbs_anki_style_dir.mkdir()


class FakeNote:
    """Provide a mutable note with Common Roots fields."""

    def __init__(self) -> None:
        self.fields: dict[str, str] = {"test": ""}

    def __contains__(self, field_name: str) -> bool:
        return field_name in self.fields

    def __setitem__(self, field_name: str, value: str) -> None:
        self.fields[field_name] = value


def test_common_roots_csv_exports_test_date_between_native_and_feedback(
    tmp_path: Path,
) -> None:
    """Common Roots CSV and field list must place test before feedback."""
    paths = FakePaths(tmp_path)

    anki_csv.common_roots(FakeSession(), paths)

    csv_path = paths.anki_csvs_dir / "pali_class" / "common_roots.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t"))

    assert rows[0] == [
        "root",
        "root_clean",
        "sanskrit_root",
        "root_group",
        "root_sign",
        "root_meaning",
        "main_verb",
        "examples",
        "native",
        "test",
        "feedback",
    ]
    assert rows[1][rows[0].index("test")] == anki_csv.current_date

    field_list = (paths.sbs_anki_style_dir / "field-list-common-roots.md").read_text(
        encoding="utf-8"
    )
    assert "native\ntest\nfeedback\nmarks" in field_list


def test_common_roots_updater_maps_test_date_from_csv() -> None:
    """The Common Roots updater mapping must populate the Anki test field."""
    common_roots_deck = next(deck for deck in DECKS if deck.deck_name == "Common Roots")
    note = FakeNote()

    changed = update_note_values_csv(
        cast(Any, note),
        {"test": "02-02"},
        common_roots_deck,
    )

    assert changed is True
    assert note.fields["test"] == "02-02"
    assert list(common_roots_deck.field_map.keys()) == [
        "root",
        "root_clean",
        "sanskrit_root",
        "root_group",
        "root_sign",
        "root_meaning",
        "main_verb",
        "examples",
        "native",
        "test",
        "feedback",
    ]
