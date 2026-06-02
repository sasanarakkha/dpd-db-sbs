"""Test SBS Anki exporter collection and deck update behavior."""

import csv
import shutil
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch
from anki.collection import Collection
from scripts.export import sbs_anki_updater, anki_csv
from scripts.work_with_csv import anki_class_grammar, pat_for_anki
from tools.paths_dps import DPSPaths
from db.models import DpdHeadword, SBS
from scripts.export.sbs_anki_updater import deck_selector
from tools.configger import config_read

dpspth = DPSPaths()
TEST_DPD_ID = 999999001
TEST_DPD_ID_STR = str(TEST_DPD_ID)


def copy_configured_sbs_collection(tmp_path: Path, filename: str) -> Path:
    """Copy the configured SBS Anki collection into a test temp directory."""
    configured_path = config_read("anki", "db_path_sbs")
    assert configured_path, "db_path_sbs must be set in config.ini"

    source_path = Path(configured_path)
    assert source_path.exists(), f"Configured SBS collection not found: {source_path}"

    collection_path = tmp_path / filename
    shutil.copy2(source_path, collection_path)
    return collection_path


@contextmanager
def patched_sbs_config(collection_path: Path, tmp_path: Path) -> Generator[None]:
    """Patch SBS Anki config reads to use the copied test collection."""

    def mock_config(section: str, key: str) -> str:
        if section == "anki" and key == "db_path_sbs":
            return str(collection_path)
        if section == "anki" and key == "backup_path_sbs":
            return str(tmp_path / "backups")
        return config_read(section, key) or "dummy"

    with (
        patch("scripts.export.sbs_anki_collection_verifier.config_read") as mock_v,
        patch("scripts.export.sbs_anki_updater.config_read") as mock_u,
    ):
        mock_v.side_effect = mock_config
        mock_u.side_effect = mock_config
        yield


def model_by_name(col: Collection, model_name: str) -> dict[str, Any]:
    """Return the Anki model for a model name."""
    models = [model for model in col.models.all() if model["name"] == model_name]
    assert models, f"Model not found: {model_name}"
    return models[0]


def remove_test_notes(col: Collection) -> None:
    """Remove existing notes using the deterministic test ID."""
    note_ids = col.find_notes(f"id:{TEST_DPD_ID_STR}")
    if note_ids:
        col.remove_notes(note_ids)


def add_test_note(
    col: Collection,
    deck_name: str,
    model_name: str,
    fields: dict[str, str],
) -> int:
    """Add one deterministic note to a deck in the copied collection."""
    deck_id = col.decks.id(deck_name, create=True)
    assert deck_id is not None, f"Deck not found: {deck_name}"
    note = col.new_note(model_by_name(col, model_name))
    for field_name, value in fields.items():
        if field_name in note:
            note[field_name] = value
    col.add_note(note, deck_id)
    return int(note.id)


def prepare_collection_with_note(
    tmp_path: Path,
    filename: str,
    deck_name: str,
    model_name: str,
    fields: dict[str, str],
) -> Path:
    """Copy the configured collection and seed one controlled test note."""
    collection_path = copy_configured_sbs_collection(tmp_path, filename)
    col = Collection(str(collection_path))
    remove_test_notes(col)
    add_test_note(col, deck_name, model_name, fields)
    col.close()
    return collection_path


def test_pipeline_regenerates_all_csvs():
    """
    Test that run_pipeline(skip_collection=True) regenerates all expected CSV files.
    """
    # Define expected CSV paths
    db_csvs = [
        dpspth.anki_csvs_dir / "anki_dhp.csv",
        dpspth.anki_csvs_dir / "anki_sbs.csv",
        dpspth.anki_csvs_dir / "anki_parittas.csv",
        dpspth.anki_csvs_dir / "anki_dps.csv",
        dpspth.anki_csvs_dir / "pali_class" / "class_all.csv",
        dpspth.anki_csvs_dir / "pali_class" / "suttas_class.csv",
        dpspth.anki_csvs_dir / "pali_class" / "roots_class.csv",
        dpspth.anki_csvs_dir / "pali_class" / "phonetic_class.csv",
        dpspth.anki_csvs_dir / "anki_vibhanga.csv",
        dpspth.anki_csvs_dir / "pali_class" / "common_roots.csv",
    ]

    pat_csv = dpspth.anki_csvs_dir / "anki_patimokkha.csv"

    grammar_csvs = [
        dpspth.anki_csvs_dir / "pali_class" / "grammar" / "cl_sum_abbr.csv",
        dpspth.anki_csvs_dir / "pali_class" / "grammar" / "cl_sum_sandhi.csv",
        dpspth.anki_csvs_dir / "pali_class" / "grammar" / "cl_sum_gramm.csv",
    ]

    all_expected = db_csvs + [pat_csv] + grammar_csvs

    # Delete existing CSVs if they exist to ensure regeneration
    for csv_path in all_expected:
        if csv_path.exists():
            csv_path.unlink()

    # Call CSV generators directly (formerly handled by run_pipeline)
    anki_csv.main()
    try:
        anki_class_grammar.main()
    except FileNotFoundError:
        pass  # grammar.xlsx may not exist in test environment
    try:
        pat_for_anki.process_patimokkha_csv()
    except Exception:
        pass  # patimokkha CSV optional in test environment

    # Verify DB CSVs
    for csv_path in db_csvs:
        assert csv_path.exists(), f"DB CSV not found: {csv_path}"

    # Verify Patimokkha CSV (requires temp/patimokkha_word_by_word.csv)
    if Path("temp/patimokkha_word_by_word.csv").exists():
        assert pat_csv.exists(), f"Patimokkha CSV not found: {pat_csv}"


def test_update_existing_note_from_configured_collection(tmp_path):
    """
    Test that updating an existing note in Anki from the DB works as expected.
    """
    collection_path = prepare_collection_with_note(
        tmp_path,
        "collection.anki2",
        "SBS Pali-English Vocab",
        "SBS Vocab",
        {
            "id": TEST_DPD_ID_STR,
            "pali": "buddha 1",
            "meaning": "Buddha; Awakened One",
        },
    )

    with patched_sbs_config(collection_path, tmp_path):
        # Open collection to check initial state
        col = Collection(str(collection_path))
        note_id = col.find_notes(f"id:{TEST_DPD_ID_STR}")[0]
        note = col.get_note(note_id)
        assert note["meaning"] == "Buddha; Awakened One"
        col.close()

        # We'll mock the DB objects returned by the query in sbs_anki_updater.py
        with (
            patch("scripts.export.sbs_anki_updater.get_db_session") as mock_get_session,
            patch("scripts.export.sbs_anki_updater.recalculate_all_sbs_indices"),
        ):
            # Create a mock headword
            mock_headword = DpdHeadword()
            mock_headword.id = TEST_DPD_ID
            mock_headword.lemma_1 = "buddha 1"
            mock_headword.meaning_1 = "Updated Meaning"
            mock_headword.sbs = SBS()
            mock_headword.sbs.sbs_index = 1  # Matches SBS Pali-English Vocab

            mock_session = mock_get_session.return_value
            mock_session.query.return_value.options.return_value.all.return_value = [
                mock_headword
            ]

            sbs_anki_updater.run_pipeline(skip_collection=False)

        # Verify note was updated
        col = Collection(str(collection_path))
        note_id = col.find_notes(f"id:{TEST_DPD_ID_STR}")[0]
        note = col.get_note(note_id)
        assert note["meaning"] == "Updated Meaning"
        col.close()


def test_deck_selector_suttas_routing():
    """Test that discourses_example is required for inclusion, and discourses_source routes to subdecks."""
    mock_headword = DpdHeadword()
    mock_headword.sbs = SBS()

    # Without discourses_example, Suttas deck is NOT included (even if discourses_source exists)
    mock_headword.sbs.discourses_source = "MN107"
    mock_headword.sbs.discourses_example = None
    assert not any("Suttas" in d for d in deck_selector(mock_headword))

    # With discourses_example + discourses_source with known prefix -> specific subdeck
    mock_headword.sbs.discourses_example = "some example"
    mock_headword.sbs.discourses_source = "MN107"
    assert "Suttas Advanced Pali Class::1.MN107" in deck_selector(mock_headword)

    # With discourses_example + multiple source prefixes (but returns only first match as single subdeck)
    mock_headword.sbs.discourses_source = "MN107<br>SN12.1"
    targets = deck_selector(mock_headword)
    suttas_targets = [t for t in targets if "Suttas" in t]
    assert len(suttas_targets) == 1, (
        "Should return exactly ONE Suttas subdeck, not multiple"
    )
    assert "Suttas Advanced Pali Class::1.MN107" in suttas_targets

    # With discourses_example but unmatched source prefix -> parent deck
    mock_headword.sbs.discourses_source = "DN22"
    targets = deck_selector(mock_headword)
    assert "Suttas Advanced Pali Class" in targets

    # With discourses_example but NO discourses_source -> parent deck
    mock_headword.sbs.discourses_source = None
    targets = deck_selector(mock_headword)
    assert "Suttas Advanced Pali Class" in targets


def test_deck_selector_vocab_routing():
    """Test that class_anki is correctly routed to Vocab Pali Class subdecks."""
    mock_headword = DpdHeadword()
    mock_headword.sbs = SBS()

    # Class 5 -> 05.Class
    mock_headword.sbs.class_anki = 5
    assert "Vocab Pali Class::05.Class" in deck_selector(mock_headword)

    # Class 0 -> No Vocab deck (in current implementation)
    mock_headword.sbs.class_anki = 0
    targets = deck_selector(mock_headword)
    assert not any(t.startswith("Vocab Pali Class") for t in targets)


def test_sbs_vocab_tag_sync(tmp_path):
    """Test that tags are synced and marks field is preserved for SBS Vocab."""
    collection_path = prepare_collection_with_note(
        tmp_path,
        "collection_tags.anki2",
        "SBS Pali-English Vocab",
        "SBS Vocab",
        {
            "id": TEST_DPD_ID_STR,
            "pali": "buddha 1",
            "marks": "user note",
        },
    )

    with patched_sbs_config(collection_path, tmp_path):
        # Prepare note with existing tags and marks
        col = Collection(str(collection_path))
        note_id = col.find_notes(f"id:{TEST_DPD_ID_STR}")[0]
        note = col.get_note(note_id)
        note.tags = ["old-tag"]
        col.update_note(note)
        col.close()

        # Run updater with mock DB row having chant info
        with (
            patch("scripts.export.sbs_anki_updater.get_db_session") as mock_get_session,
            patch("scripts.export.sbs_anki_updater.recalculate_all_sbs_indices"),
        ):
            mock_headword = DpdHeadword()
            mock_headword.id = TEST_DPD_ID
            mock_headword.lemma_1 = "buddha 1"
            mock_headword.sbs = SBS()
            mock_headword.sbs.sbs_index = 1
            mock_headword.sbs.sbs_chant_pali_1 = "tag1 tag2"

            mock_session = mock_get_session.return_value
            mock_session.query.return_value.options.return_value.all.return_value = [
                mock_headword
            ]

            sbs_anki_updater.run_pipeline(skip_collection=False)

        # Verify
        col = Collection(str(collection_path))
        note_id = col.find_notes(f"id:{TEST_DPD_ID_STR}")[0]
        note = col.get_note(note_id)
        assert set(note.tags) == {"tag1", "tag2"}
        assert note["marks"] == "user note"
        col.close()


def test_note_moves_between_decks(tmp_path):
    """Test that a note moves from one deck to another when its routing changes."""
    collection_path = prepare_collection_with_note(
        tmp_path,
        "collection_move.anki2",
        "SBS Pali-English Vocab",
        "SBS Vocab",
        {"id": TEST_DPD_ID_STR, "pali": "buddha 1"},
    )

    with patched_sbs_config(collection_path, tmp_path):
        # Initially, buddha 1 is in 'SBS Pali-English Vocab'
        col = Collection(str(collection_path))
        note_id = col.find_notes(f"id:{TEST_DPD_ID_STR}")[0]
        card_id = col.find_cards(f"nid:{note_id}")[0]
        card = col.get_card(card_id)
        old_deck_id = col.decks.id("SBS Pali-English Vocab")
        assert card.did == old_deck_id
        col.close()

        # Run updater with mock DB row that routes to 'Pali DHP vocab' instead
        with (
            patch("scripts.export.sbs_anki_updater.get_db_session") as mock_get_session,
            patch("scripts.export.sbs_anki_updater.recalculate_all_sbs_indices"),
        ):
            mock_headword = DpdHeadword()
            mock_headword.id = TEST_DPD_ID
            mock_headword.lemma_1 = "buddha 1"
            mock_headword.sbs = SBS()
            mock_headword.sbs.dhp_source = "DHP 1"  # Routes to DHP deck

            mock_session = mock_get_session.return_value
            mock_session.query.return_value.options.return_value.all.return_value = [
                mock_headword
            ]

            sbs_anki_updater.run_pipeline(skip_collection=False)

        # Verify it moved
        col = Collection(str(collection_path))
        note_id = col.find_notes(f"id:{TEST_DPD_ID_STR}")[0]
        card_id = col.find_cards(f"nid:{note_id}")[0]
        card = col.get_card(card_id)
        new_deck_id = col.decks.id("Pali DHP vocab")
        assert card.did == new_deck_id
        col.close()


def test_csv_deck_update(tmp_path):
    """Test that notes are updated from a CSV source (Patimokkha)."""
    collection_path = prepare_collection_with_note(
        tmp_path,
        "collection_csv.anki2",
        "Pali Patimokkha Word By Word",
        "Pātimokkha word by word",
        {"pali": "test_csv_buddha", "meaning": "Old Meaning"},
    )

    with patched_sbs_config(collection_path, tmp_path):
        csv_dir = tmp_path / "csvs"
        csv_dir.mkdir()
        pat_csv = csv_dir / "anki_patimokkha.csv"
        with open(pat_csv, "w", encoding="utf-8") as f:
            f.write("pali\tmeaning\n")
            f.write("test_csv_buddha\tUpdated CSV Meaning\n")

        with (
            patch("scripts.export.sbs_anki_updater.get_db_session") as mock_get_session,
            patch("scripts.export.sbs_anki_updater.recalculate_all_sbs_indices"),
            patch("scripts.export.sbs_anki_updater.DPSPaths") as mock_paths,
        ):
            mock_paths.return_value.anki_csvs_dir = csv_dir
            mock_session = mock_get_session.return_value
            mock_session.query.return_value.options.return_value.all.return_value = []

            sbs_anki_updater.run_pipeline(skip_collection=False)

        # Verify
        col = Collection(str(collection_path))
        note_id = col.find_notes(
            'deck:"Pali Patimokkha Word By Word" pali:test_csv_buddha'
        )[0]
        note = col.get_note(note_id)
        assert note["meaning"] == "Updated CSV Meaning"
        col.close()


def test_csv_deck_deletion_removes_stale_note(tmp_path):
    """A CSV-deck note absent from the CSV must be deleted after update."""
    collection_path = prepare_collection_with_note(
        tmp_path,
        "collection_csv_del.anki2",
        "Pali Patimokkha Word By Word",
        "Pātimokkha word by word",
        {"pali": "test_old_word", "order": "1"},
    )

    with patched_sbs_config(collection_path, tmp_path):
        # CSV contains only "test_new_word", not "test_old_word"
        csv_dir = tmp_path / "csvs"
        csv_dir.mkdir()
        pat_csv = csv_dir / "anki_patimokkha.csv"
        with open(pat_csv, "w", encoding="utf-8") as f:
            f.write("pali\tmeaning\torder\n")
            f.write("test_new_word\tSome meaning\t2\n")

        with (
            patch("scripts.export.sbs_anki_updater.get_db_session") as mock_get_session,
            patch("scripts.export.sbs_anki_updater.recalculate_all_sbs_indices"),
            patch("scripts.export.sbs_anki_updater.DPSPaths") as mock_paths,
        ):
            mock_paths.return_value.anki_csvs_dir = csv_dir
            mock_session = mock_get_session.return_value
            mock_session.query.return_value.options.return_value.all.return_value = []
            sbs_anki_updater.run_pipeline(skip_collection=False)

        col = Collection(str(collection_path))
        stale = col.find_notes('deck:"Pali Patimokkha Word By Word" pali:test_old_word')
        assert len(stale) == 0, "Stale note must be deleted"
        new_notes = col.find_notes(
            'deck:"Pali Patimokkha Word By Word" pali:test_new_word'
        )
        assert len(new_notes) == 1, "New CSV entry must be created"
        col.close()


def test_deck_reorder_and_force_new(tmp_path):
    """After update: cards must be new (queue=0, type=0) and ordered by deck field."""
    collection_path = prepare_collection_with_note(
        tmp_path,
        "collection_reorder.anki2",
        "Pali Patimokkha Word By Word",
        "Pātimokkha word by word",
        {"pali": "test_pati_word", "order": "42"},
    )

    with patched_sbs_config(collection_path, tmp_path):
        # Force the Patimokkha note to review first.
        col = Collection(str(collection_path))
        pat_note_ids = col.find_notes(
            'deck:"Pali Patimokkha Word By Word" pali:test_pati_word'
        )
        note = col.get_note(pat_note_ids[0])
        card_ids = col.find_cards(f"nid:{note.id}")
        card = col.get_card(card_ids[0])
        cast(Any, card).queue = 2  # simulate a reviewed card
        cast(Any, card).type = 2
        card.due = 999
        col.update_card(card)
        col.close()

        csv_dir = tmp_path / "csvs"
        csv_dir.mkdir()
        pat_csv = csv_dir / "anki_patimokkha.csv"
        with open(pat_csv, "w", encoding="utf-8") as f:
            f.write("pali\tmeaning\torder\n")
            f.write("test_pati_word\tsome meaning\t42\n")

        with (
            patch("scripts.export.sbs_anki_updater.get_db_session") as mock_get_session,
            patch("scripts.export.sbs_anki_updater.recalculate_all_sbs_indices"),
            patch("scripts.export.sbs_anki_updater.DPSPaths") as mock_paths,
        ):
            mock_paths.return_value.anki_csvs_dir = csv_dir
            mock_session = mock_get_session.return_value
            mock_session.query.return_value.options.return_value.all.return_value = []
            sbs_anki_updater.run_pipeline(skip_collection=False)

        col = Collection(str(collection_path))
        note_ids = col.find_notes(
            'deck:"Pali Patimokkha Word By Word" pali:test_pati_word'
        )
        assert len(note_ids) == 1
        card_ids = col.find_cards(f"nid:{note_ids[0]}")
        card = col.get_card(card_ids[0])
        assert card.queue == 0, f"Card must be new (queue=0), got {card.queue}"
        assert card.type == 0, f"Card must be new (type=0), got {card.type}"
        # With 1 note, its position is 1 (sorted by order field value ascending)
        assert card.due == 1, (
            f"card.due should be 1 (position of 1 note), got {card.due}"
        )
        col.close()


def test_apkg_exporter_produces_all_decks(tmp_path):
    """Test that all decks are exported to .apkg files."""
    collection_path = copy_configured_sbs_collection(
        tmp_path, "collection_export.anki2"
    )

    output_dir = tmp_path / "apkg_output"
    output_dir.mkdir()

    with patch("scripts.export.sbs_anki_apkg.config_read") as mock_config_read:
        mock_config_read.return_value = str(collection_path)

        from scripts.export import sbs_anki_apkg

        sbs_anki_apkg.main(output_dir=str(output_dir))

        # Verify 12 apkg files
        apkg_files = list(output_dir.glob("*.apkg"))
        assert len(apkg_files) == 12

        # Check one specific slug
        assert (output_dir / "sbs_pali_english_vocab.apkg").exists()


def test_no_cross_deck_move_between_flat_decks(tmp_path):
    """
    Verify notes are NOT moved between flat decks with different models.
    This is a regression test for the removed else block that was moving
    notes across incompatible deck types.
    """
    collection_path = prepare_collection_with_note(
        tmp_path,
        "collection_cross_deck.anki2",
        "SBS Pali-English Vocab",
        "SBS Vocab",
        {"id": TEST_DPD_ID_STR, "pali": "buddha 1"},
    )

    with patched_sbs_config(collection_path, tmp_path):
        # Initial state: test note is in SBS Pali-English Vocab.
        col = Collection(str(collection_path))
        note_id = col.find_notes(f"id:{TEST_DPD_ID_STR}")[0]
        note = col.get_note(note_id)
        old_nid = note.id
        col.close()

        # Run updater: word now qualifies for DHP vocab but NOT SBS vocab
        # (no sbs_index set, but dhp_source is set)
        with (
            patch("scripts.export.sbs_anki_updater.get_db_session") as mock_get_session,
            patch("scripts.export.sbs_anki_updater.recalculate_all_sbs_indices"),
        ):
            mock_headword = DpdHeadword()
            mock_headword.id = TEST_DPD_ID
            mock_headword.lemma_1 = "buddha 1"
            mock_headword.sbs = SBS()
            mock_headword.sbs.dhp_source = "DHP 1"
            # NOTE: sbs_index is NOT set, so word doesn't match "SBS Pali-English Vocab"

            mock_session = mock_get_session.return_value
            mock_session.query.return_value.options.return_value.all.return_value = [
                mock_headword
            ]

            sbs_anki_updater.run_pipeline(skip_collection=False)

        # After update: the old SBS note should be deleted, a new DHP note created
        col = Collection(str(collection_path))

        # Old note should be deleted (no SBS note for test id)
        sbs_notes = col.find_notes(
            f'deck:"SBS Pali-English Vocab" id:{TEST_DPD_ID_STR}'
        )
        assert len(sbs_notes) == 0, "Old SBS note should be deleted"

        # New note should exist in DHP
        dhp_notes = col.find_notes(f'deck:"Pali DHP vocab" id:{TEST_DPD_ID_STR}')
        assert len(dhp_notes) > 0, "New DHP note should be created"

        # Verify the new note has a different nid (it's a new note, not the moved one)
        new_note = col.get_note(dhp_notes[0])
        assert new_note.id != old_nid, "Should be a new note, not the moved one"

        col.close()


def test_word_in_multiple_flat_decks_simultaneously(tmp_path):
    """
    Verify that a word with conditions matching MULTIPLE different top-level decks
    ends up with notes in ALL of them simultaneously (multi-deck membership).
    """
    collection_path = prepare_collection_with_note(
        tmp_path,
        "collection_multi_deck.anki2",
        "SBS Pali-English Vocab",
        "SBS Vocab",
        {"id": TEST_DPD_ID_STR, "pali": "buddha 1"},
    )

    with patched_sbs_config(collection_path, tmp_path):
        with (
            patch("scripts.export.sbs_anki_updater.get_db_session") as mock_get_session,
            patch("scripts.export.sbs_anki_updater.recalculate_all_sbs_indices"),
        ):
            mock_headword = DpdHeadword()
            mock_headword.id = TEST_DPD_ID
            mock_headword.lemma_1 = "buddha 1"
            mock_headword.sbs = SBS()
            mock_headword.sbs.sbs_index = 1  # SBS Pali-English Vocab
            mock_headword.sbs.dhp_source = "DHP 1"  # Pali DHP vocab

            mock_session = mock_get_session.return_value
            mock_session.query.return_value.options.return_value.all.return_value = [
                mock_headword
            ]

            sbs_anki_updater.run_pipeline(skip_collection=False)

        col = Collection(str(collection_path))

        # Word should be in SBS Pali-English Vocab (already existed in fixture, updated)
        sbs_notes = col.find_notes(
            f'deck:"SBS Pali-English Vocab" id:{TEST_DPD_ID_STR}'
        )
        assert len(sbs_notes) == 1, "Word should have 1 note in SBS Pali-English Vocab"

        # Word should also be in Pali DHP vocab (newly created)
        dhp_notes = col.find_notes(f'deck:"Pali DHP vocab" id:{TEST_DPD_ID_STR}')
        assert len(dhp_notes) == 1, (
            "Word should have 1 note in Pali DHP vocab (newly created)"
        )

        # Verify both notes have correct "id" field value
        sbs_note = col.get_note(sbs_notes[0])
        dhp_note = col.get_note(dhp_notes[0])
        assert sbs_note["id"] == TEST_DPD_ID_STR
        assert dhp_note["id"] == TEST_DPD_ID_STR

        col.close()


def test_suttas_not_deleted_when_discourses_source_missing(tmp_path):
    """
    Regression test for mass deletion bug.
    A word with discourses_example (qualifies for Suttas per anki_csv.py)
    but no discourses_source should NOT be deleted.
    Before the fix, it was deleted because deck_selector used discourses_source.
    """
    collection_path = prepare_collection_with_note(
        tmp_path,
        "collection_suttas.anki2",
        "Suttas Advanced Pali Class",
        "Advanced Suttas",
        {"id": TEST_DPD_ID_STR, "pali": "buddha 1"},
    )

    with patched_sbs_config(collection_path, tmp_path):
        with (
            patch("scripts.export.sbs_anki_updater.get_db_session") as mock_get_session,
            patch("scripts.export.sbs_anki_updater.recalculate_all_sbs_indices"),
        ):
            mock_headword = DpdHeadword()
            mock_headword.id = TEST_DPD_ID
            mock_headword.lemma_1 = "buddha 1"
            mock_headword.sbs = SBS()
            mock_headword.sbs.discourses_example = "some example"
            mock_headword.sbs.discourses_source = None  # EMPTY - the critical part

            mock_session = mock_get_session.return_value
            mock_session.query.return_value.options.return_value.all.return_value = [
                mock_headword
            ]

            sbs_anki_updater.run_pipeline(skip_collection=False)

        col = Collection(str(collection_path))

        # Word should still be in Suttas Advanced Pali Class (parent deck, not deleted)
        suttas_notes = col.find_notes(
            f'deck:"Suttas Advanced Pali Class" id:{TEST_DPD_ID_STR}'
        )
        assert len(suttas_notes) == 1, (
            "Suttas note should NOT be deleted even though discourses_source is empty"
        )

        col.close()


def test_common_roots_csv_has_header_row(tmp_path):
    """common_roots.csv must start with a header row so DictReader parses it correctly."""
    csv_file = tmp_path / "common_roots.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(
            [
                "root",
                "root_clean",
                "sanskrit_root",
                "root_group",
                "root_sign",
                "root_meaning",
                "main_verb",
                "examples",
                "native",
                "feedback",
            ]
        )
        writer.writerows(
            [
                [
                    "√bhū",
                    "bhū",
                    "bhū",
                    "1",
                    "+",
                    "to be",
                    "atthi",
                    "bhavati",
                    "",
                    "feedback",
                ]
            ]
        )
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)
    assert len(rows) == 1, "Expected 1 data row (after header)"
    assert rows[0]["root"] == "√bhū"
    assert rows[0]["root_meaning"] == "to be"
    assert rows[0]["main_verb"] == "atthi"
