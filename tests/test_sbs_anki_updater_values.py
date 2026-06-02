"""Tests for SBS Anki updater field value normalization."""

from pathlib import Path
from typing import Any, cast

from scripts.export.sbs_anki_deck_config import DeckSpec
from scripts.export.sbs_anki_updater import (
    UpdateStats,
    delete_stale_csv_notes,
    update_from_csv,
    update_note_values,
    update_note_values_csv,
)


class FakeNote:
    """Minimal note object for updater field assignment tests."""

    def __init__(
        self,
        field_names: list[str] | None = None,
        fields: list[Any] | None = None,
    ) -> None:
        self.field_names = field_names or ["field"]
        self.fields: list[Any] = fields or ["" for _ in self.field_names]
        self.id = 1

    def __contains__(self, field_name: str) -> bool:
        return field_name in self.field_names

    def __setitem__(self, field_name: str, value: Any) -> None:
        self.fields[self.field_names.index(field_name)] = value


class FakeCollection:
    """Minimal collection object for CSV updater behavior tests."""

    def __init__(self) -> None:
        self.updated_notes: list[FakeNote] = []
        self.added_notes: list[FakeNote] = []
        self.removed_note_ids: list[int] = []

    def update_note(self, note: FakeNote) -> None:
        self.updated_notes.append(note)

    def new_note(self, _model_id: int) -> FakeNote:
        return FakeNote(["pali", "meaning"], ["", ""])

    def add_note(self, note: FakeNote, _deck_id: int) -> None:
        self.added_notes.append(note)

    def remove_notes(self, note_ids: list[int]) -> None:
        self.removed_note_ids.extend(note_ids)


class FakeHeadword:
    """Minimal headword object for updater error messages."""

    lemma_1 = "test"


def test_update_note_values_coerces_db_values_to_strings() -> None:
    """DB field producers may return non-string values, but Anki fields require strings."""
    note = FakeNote()
    deck_config = DeckSpec(
        deck_name="Test",
        model_name="Test",
        csv_path_attr="",
        slug="test",
        source="db",
        field_map={"field": lambda _: cast(str, 42)},
    )

    changed = update_note_values(note, FakeHeadword(), deck_config)

    assert changed is True
    assert note.fields == ["42"]


def test_update_note_values_csv_coerces_csv_values_to_strings() -> None:
    """CSV field producers may pass through non-string values, but Anki fields require strings."""
    note = FakeNote()
    deck_config = DeckSpec(
        deck_name="Test",
        model_name="Test",
        csv_path_attr="",
        slug="test",
        source="csv",
        field_map={"field": lambda row: cast(str, row["value"])},
    )

    changed = update_note_values_csv(cast(Any, note), {"value": 42}, deck_config)

    assert changed is True
    assert note.fields == ["42"]


def test_csv_keys_are_normalized_before_matching_and_deleting(tmp_path: Path) -> None:
    """Visibly identical Pali keys must not churn when Unicode forms differ."""
    deck_name = "Pali Patimokkha Word By Word"
    existing_note = FakeNote(["pali", "meaning"], ["niṭṭhitā", "Old"])
    all_data = [{"deck": deck_name, "note": existing_note}]
    csv_path = tmp_path / "anki_patimokkha.csv"
    csv_path.write_text(
        "pali\tmeaning\nniṭṭhita\u0304\tUpdated\n",
        encoding="utf-8",
    )
    deck_config = DeckSpec(
        deck_name=deck_name,
        model_name="Pātimokkha word by word",
        csv_path_attr="anki_patimokkha.csv",
        slug="pali_patimokkha_word_by_word",
        source="csv",
        field_map={
            "pali": lambda row: row["pali"],
            "meaning": lambda row: row["meaning"],
        },
    )
    collection = FakeCollection()
    stats = UpdateStats()

    csv_keys = update_from_csv(
        cast(Any, collection),
        deck_name,
        str(csv_path),
        deck_config,
        all_data,
        {deck_name: 1},
        {"Pātimokkha word by word": 1},
        stats,
    )
    delete_stale_csv_notes(cast(Any, collection), all_data, deck_name, csv_keys, stats)

    assert collection.added_notes == []
    assert collection.removed_note_ids == []
    assert collection.updated_notes == [existing_note]
    assert existing_note.fields == ["niṭṭhitā", "Updated"]
    assert csv_keys == {"niṭṭhitā"}
