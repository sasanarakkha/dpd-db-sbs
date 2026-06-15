"""Test Common Roots Anki CSV export behavior."""

import csv
from types import SimpleNamespace
from unittest.mock import patch

from scripts.export import anki_csv
from scripts.export.sbs_anki_deck_config import DECKS


class FakeColumn:
    def label(self, _name):
        return self

    def desc(self):
        return self

    def contains(self, _value):
        return self

    def in_(self, _value):
        return self

    def __ge__(self, _value):
        return self

    def __eq__(self, _value):
        return self

    def __ne__(self, _value):
        return self

    def __invert__(self):
        return self


class FakeRootCounts:
    c = SimpleNamespace(root=FakeColumn(), root_count=FakeColumn())


class FakeQuery:
    def __init__(self, result=None, first_result=None):
        self.result = result or []
        self.first_result = first_result

    def group_by(self, *_args):
        return self

    def subquery(self):
        return FakeRootCounts()

    def join(self, *_args):
        return self

    def filter(self, *_args):
        return self

    def order_by(self, *_args):
        return self

    def limit(self, *_args):
        return self

    def all(self):
        return self.result

    def first(self):
        return self.first_result


class FakeSession:
    def __init__(self, roots):
        self.roots = roots
        self.query_count = 0

    def query(self, *_args):
        self.query_count += 1
        if self.query_count == 1:
            return FakeQuery()
        if self.query_count == 2:
            return FakeQuery(result=self.roots)
        if self.query_count == 3:
            return FakeQuery(first_result=SimpleNamespace(lemma_clean="karoti"))
        return FakeQuery()


def test_common_roots_csv_uses_root_key_and_keeps_duplicate_clean_roots(tmp_path):
    """Common Roots CSV must preserve distinct root_key rows and expose root_clean."""
    roots = [
        (
            SimpleNamespace(
                root="√kar 1",
                root_clean="√kar",
                sanskrit_root="kṛ",
                root_group=1,
                root_sign="o",
                root_meaning="to do",
                root_example="karoti, kata, kāra",
                root_ru_meaning="делать",
            ),
            30,
        ),
        (
            SimpleNamespace(
                root="√kar 2",
                root_clean="√kar",
                sanskrit_root="kṛ",
                root_group=8,
                root_sign="a",
                root_meaning="to scatter",
                root_example="kāreti, kiraṇa",
                root_ru_meaning="рассыпать",
            ),
            25,
        ),
    ]
    output_dir = tmp_path / "pali_class"
    output_dir.mkdir()
    dpspth = SimpleNamespace(anki_csvs_dir=tmp_path, sbs_anki_style_dir=tmp_path)

    with (
        patch.object(anki_csv.DpdHeadword, "root_key", FakeColumn()),
        patch.object(anki_csv.DpdHeadword, "id", FakeColumn()),
        patch.object(anki_csv.DpdHeadword, "stem", FakeColumn()),
        patch.object(anki_csv.DpdHeadword, "pos", FakeColumn()),
        patch.object(anki_csv.DpdHeadword, "grammar", FakeColumn()),
        patch.object(anki_csv.DpdHeadword, "family_root", FakeColumn()),
        patch.object(anki_csv.DpdHeadword, "ebt_count", FakeColumn()),
        patch.object(anki_csv.DpdHeadword, "example_2", FakeColumn()),
        patch.object(anki_csv.DpdRoot, "root", FakeColumn()),
    ):
        anki_csv.common_roots(FakeSession(roots), dpspth)

    with open(output_dir / "common_roots.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    assert [row["root"] for row in rows] == ["√kar 1", "√kar 2"]
    assert [row["root_clean"] for row in rows] == ["√kar", "√kar"]
    assert [row["root_meaning"] for row in rows] == ["to do", "to scatter"]
    assert [row["examples"] for row in rows] == ["kata, kāra", "kāreti, kiraṇa"]


def test_common_roots_deck_config_includes_root_clean():
    """Common Roots note type and field map must include root_clean."""
    common_roots_deck = next(deck for deck in DECKS if deck.deck_name == "Common Roots")
    common_roots_fields = list(common_roots_deck.field_map.keys())
    root_index = common_roots_fields.index("root")

    assert common_roots_fields[root_index + 1] == "root_clean"
    assert common_roots_deck.field_map["root_clean"]({"root_clean": "√kar"}) == "√kar"
