#!/usr/bin/env python3

"""Update SBS Anki collection from DB and CSV sources."""

import copy
import os
import re
import shutil
import csv
from typing import Any, cast

from anki.collection import Collection
from anki.notes import Note
from anki.cards import Card
from anki.errors import DBError
from sqlalchemy.orm import joinedload

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr
from tools.configger import config_read
from tools.sbs_table_functions import recalculate_all_sbs_indices

from scripts.export.sbs_anki_deck_config import (
    DECKS,
    EXPECTED_COLLECTION,
    DeckSpec,
    SUTTAS_PREFIX_MAP,
    VOCAB_CLASS_RANGE,
)
from scripts.export.sbs_anki_collection_verifier import verify_sbs_collection


class UpdateStats:
    def __init__(self):
        self.added = 0
        self.updated = 0
        self.moved = 0
        self.deleted = 0
        self.deck_stats = {
            d.deck_name: {"added": 0, "updated": 0, "moved": 0, "deleted": 0}
            for d in DECKS
        }

    def pr_summary(self):
        pr.summary("added", self.added)
        pr.summary("updated", self.updated)
        pr.summary("moved", self.moved)
        pr.summary("deleted", self.deleted)
        for deck_name, stats in self.deck_stats.items():
            if (
                stats["added"] > 0
                or stats["updated"] > 0
                or stats["moved"] > 0
                or stats["deleted"] > 0
            ):
                pr.summary(
                    f"{deck_name}",
                    f"added: {stats['added']}, updated: {stats['updated']}, moved: {stats['moved']}, deleted: {stats['deleted']}",
                )


def backup_anki_db():
    """Backup Anki collection to backup_path_sbs."""
    pr.green("backup anki db")
    anki_db_path = config_read("anki", "db_path_sbs")
    backup_dir = config_read("anki", "backup_path_sbs")

    if not anki_db_path or not backup_dir:
        pr.red("Paths not found in config.ini")
        return

    os.makedirs(backup_dir, exist_ok=True)
    import datetime

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = os.path.join(backup_dir, f"collection_{timestamp}.anki2")

    try:
        shutil.copy2(anki_db_path, backup_path)
        pr.yes(f"backed up to {backup_path}")
    except Exception as e:
        pr.no("error")
        pr.red(f"Backup failed: {e}")


def setup_anki_updater(
    decks: list[str],
) -> tuple[
    Collection | None,
    dict | None,
    list | None,
    dict | None,
    dict | None,
]:
    """Setup Anki collection and return all required dicts."""
    col = get_anki_collection()
    if not col:
        return None, None, None, None, None

    try:
        verify_sbs_collection(col)

        notes = get_notes(col, decks)
        cards = get_cards(col, decks)
        deck_dict = get_decks(col)
        model_dict = get_models(col)
        data_dict, all_data = make_data_dict(notes, cards, deck_dict)

        return col, data_dict, all_data, deck_dict, model_dict
    except Exception as e:
        pr.red(f"Setup failed: {e}")
        if col:
            col.close()
        return None, None, None, None, None


def get_anki_collection() -> Collection | None:
    """Get Anki collection from config path."""
    pr.green("get anki collection")
    anki_db_path = config_read("anki", "db_path_sbs")
    if not anki_db_path:
        pr.red("db_path_sbs not found in config.ini")
        return None
    try:
        col = Collection(anki_db_path)
        pr.yes("ok")
        return col
    except DBError as e:
        pr.no("error")
        pr.red(f"Anki DBError: {e}")
        return None


def get_notes(col: Collection, decks: list[str]) -> list[Note]:
    """Get all notes for a list of decks."""
    pr.green("get notes")
    search_query = " or ".join(f'deck:"{deck}"' for deck in decks)
    note_ids = col.find_notes(search_query)
    notes = [col.get_note(note_id) for note_id in note_ids]
    pr.yes(len(notes))
    return notes


def get_cards(col: Collection, decks: list[str]) -> list[Card]:
    """Get all cards for a list of decks."""
    pr.green("get cards")
    search_query = " or ".join(f'deck:"{deck}"' for deck in decks)
    card_ids = col.find_cards(search_query)
    cards = [col.get_card(card_id) for card_id in card_ids]
    pr.yes(len(cards))
    return cards


def get_decks(col: Collection) -> dict:
    """Get all decks and their IDs."""
    pr.green("get decks")
    decks = col.decks.all()
    deck_dict = {deck["name"]: deck["id"] for deck in decks}
    deck_dict_rev = {v: k for k, v in deck_dict.items()}
    deck_dict.update(deck_dict_rev)
    pr.yes(len(deck_dict))
    return deck_dict


def get_models(col: Collection) -> dict:
    """Get all models and their IDs."""
    pr.green("get models")
    models = col.models.all()
    model_dict = {model["name"]: model["id"] for model in models}
    pr.yes(len(model_dict))
    return model_dict


def make_data_dict(
    notes: list[Note], cards: list[Card], deck_dict: dict
) -> tuple[dict, list]:
    """Make data dict keyed by headword ID and a flat list of all note data."""
    pr.green("make data dict")

    temp_dict = {}
    for note in notes:
        temp_dict[note.id] = {
            "nid": note.id,
            "mid": note.mid,
            "note": note,
            "cards": [],
            "deck": "",
        }

    for card in cards:
        if card.nid in temp_dict:
            temp_dict[card.nid]["cards"].append(card)
            if not temp_dict[card.nid]["deck"]:
                temp_dict[card.nid]["deck"] = deck_dict.get(card.did, "")

    all_data = list(temp_dict.values())
    data_dict = {}
    for data in all_data:
        note = data["note"]
        model = note.note_type()
        fields = [f["name"] for f in model["flds"]]
        if "id" in fields:
            idx = fields.index("id")
            dpd_id = note.fields[idx]
            if dpd_id:
                if dpd_id not in data_dict:
                    data_dict[dpd_id] = []
                data_dict[dpd_id].append(data)

    pr.yes(len(data_dict))
    return data_dict, all_data


def deck_selector(i: DpdHeadword) -> list[str]:
    """Return a list of target deck names for this headword."""
    target_decks = []

    if not i.sbs:
        return []

    if i.sbs.sbs_index:
        target_decks.append("SBS Pali-English Vocab")
    if i.sbs.dhp_source:
        target_decks.append("Pali DHP vocab")
    chant_names = ["Karaṇīya-metta-sutta", "Ratana-sutta", "Maṅgala-sutta"]
    sources = [i.sbs.sbs_chant_pali_1 or "", i.sbs.sbs_chant_pali_2 or ""]
    if any(chant_name in source for source in sources for chant_name in chant_names):
        target_decks.append("Pali Parittas")
    if i.sbs.vib_source:
        target_decks.append("Pali Bhikkhu Vibhanga")
    if i.sbs.class_anki:
        class_num = i.sbs.class_anki
        if 1 <= class_num <= 29:
            target_decks.append(f"Vocab Pali Class::{str(class_num).zfill(2)}.Class")
        else:
            target_decks.append("Vocab Pali Class")
    if i.sbs.class_anki and i.rt:
        target_decks.append("Roots Pali Class")
    if i.sbs.class_anki and i.phonetic:
        target_decks.append("Phonetic Changes Pali Class")
    if i.sbs.discourses_example:
        matched_subdeck = None
        if i.sbs.discourses_source:
            for line in i.sbs.discourses_source.split("<br>"):
                for prefix, subdeck in SUTTAS_PREFIX_MAP.items():
                    if line.startswith(prefix):
                        matched_subdeck = subdeck
                        break
                if matched_subdeck:
                    break
        target_decks.append(matched_subdeck or "Suttas Advanced Pali Class")
    if (
        i.sbs.class_anki
        or i.sbs.discourses_example
        or i.sbs.vib_example
        or i.sbs.pat_example
        or i.sbs.dhp_example
        or i.sbs.sbs_index
    ):
        target_decks.append("Пали Словарь")

    seen = set()
    result = []
    for d in target_decks:
        if d not in seen:
            seen.add(d)
            result.append(d)
    return result


def update_note_values(note, i, deck_config: DeckSpec) -> bool:
    """Update note fields using deck_config.field_map. Returns True if changed."""
    old_fields = copy.copy(note.fields)

    for field_name, producer in deck_config.field_map.items():
        if field_name in note:
            try:
                value = producer(i)
                note[field_name] = str(value) if value is not None else ""
            except Exception as e:
                pr.red(f"Error producing field '{field_name}' for {i.lemma_1}: {e}")

    if deck_config.updates_tags:
        if i.sbs:
            tags = []
            if i.sbs.sbs_chant_pali_1:
                tags.extend(i.sbs.sbs_chant_pali_1.split())
            if i.sbs.sbs_chant_pali_2:
                tags.extend(i.sbs.sbs_chant_pali_2.split())
            tags = list(set(filter(None, tags)))
            if set(note.tags) != set(tags):
                note.tags = tags

    return note.fields != old_fields


def update_note_values_csv(note: Note, row: dict, deck_config: DeckSpec) -> bool:
    """Update note fields from CSV row. Returns True if changed."""
    old_fields = copy.copy(note.fields)

    for field_name, producer in deck_config.field_map.items():
        if field_name in note:
            try:
                value = producer(row)
                note[field_name] = str(value) if value is not None else ""
            except Exception as e:
                pr.red(
                    f"Error producing field '{field_name}' for row {row.get('pali_1', row.get('id', 'unknown'))}: {e}"
                )

    return note.fields != old_fields


def update_deck(
    col: Collection,
    note: Note,
    i: DpdHeadword,
    target_deck_name: str,
    item_data: dict,
    deck_dict: dict,
    model_dict: dict,
) -> bool:
    """Move note to target deck if needed. Returns True if moved."""
    old_deck = item_data["deck"]

    if old_deck != target_deck_name:
        top_level = target_deck_name.split("::")[0]
        deck_specs = {d.deck_name: d for d in DECKS}
        if top_level not in deck_specs:
            return False

        model_name = deck_specs[top_level].model_name

        if model_name in model_dict:
            target_mid = model_dict[model_name]
            if note.mid != target_mid:
                target_model = col.models.get(target_mid)
                if target_model is None:
                    pr.amber(
                        f"Model id {target_mid} not found for deck '{target_deck_name}'"
                    )
                    return False
                target_field_count = len(target_model["flds"])
                if len(note.fields) < target_field_count:
                    note.fields.extend([""] * (target_field_count - len(note.fields)))
                elif len(note.fields) > target_field_count:
                    note.fields = note.fields[:target_field_count]

                note.mid = target_mid

            if "cards" in item_data:
                for card in item_data["cards"]:
                    card.did = deck_dict[target_deck_name]
                    card.queue = 0
                    card.lapse = 0
                    card.due = 0
                    col.update_card(card)

            item_data["deck"] = target_deck_name
            return True

    return False


def make_new_note(
    col: Collection,
    deck_name: str,
    model_dict: dict,
    deck_dict: dict,
    i: DpdHeadword,
    deck_config: DeckSpec,
) -> Note | None:
    """Create a new note in the specified deck."""
    pr.green(f"creating new note for {i.lemma_1} in {deck_name}")

    if deck_config.model_name in model_dict:
        model_id = model_dict[deck_config.model_name]
        deck_id = deck_dict[deck_name]
        note = col.new_note(model_id)
        update_note_values(note, i, deck_config)
        col.add_note(note, deck_id)
        return note
    else:
        pr.red(f"Model '{deck_config.model_name}' not found for {i.lemma_1}")
        return None


def update_from_db(
    db: list[DpdHeadword],
    col: Collection,
    data_dict: dict,
    deck_dict: dict,
    model_dict: dict,
    stats: UpdateStats,
):
    """Update Anki notes from DB headwords."""
    pr.green("updating from db")

    deck_specs = {d.deck_name: d for d in DECKS if d.source == "db"}
    csv_deck_names = {d.deck_name for d in DECKS if d.source == "csv"}

    for counter, i in enumerate(db):
        targets = deck_selector(i)
        dpd_id_str = str(i.id)
        existing_items = data_dict.get(dpd_id_str, [])

        matched_item_ids = set()
        unmatched_targets = list(targets)

        for item in existing_items:
            item_top_level = item["deck"].split("::")[0]
            found_target = None
            for target in unmatched_targets:
                target_top_level = target.split("::")[0]
                if item_top_level == target_top_level:
                    found_target = target
                    break

            if found_target:
                matched_item_ids.add(id(item))
                unmatched_targets.remove(found_target)

                note = item["note"]
                top_level = found_target.split("::")[0]
                deck_config = deck_specs[top_level]

                if update_deck(col, note, i, found_target, item, deck_dict, model_dict):
                    stats.moved += 1
                    stats.deck_stats[top_level]["moved"] += 1

                if update_note_values(note, i, deck_config):
                    col.update_note(note)
                    stats.updated += 1
                    stats.deck_stats[top_level]["updated"] += 1

        for target in unmatched_targets:
            top_level = target.split("::")[0]
            if top_level in deck_specs:
                deck_config = deck_specs[top_level]
                if deck_config.creates_new_notes:
                    if make_new_note(
                        col, target, model_dict, deck_dict, i, deck_config
                    ):
                        stats.added += 1
                        stats.deck_stats[top_level]["added"] += 1

        for item in existing_items:
            if id(item) not in matched_item_ids:
                top_level = item["deck"].split("::")[0]
                if top_level in csv_deck_names:
                    continue
                col.remove_notes([item["note"].id])
                stats.deleted += 1
                if top_level in stats.deck_stats:
                    stats.deck_stats[top_level]["deleted"] += 1
                pr.amber(f"deleted {item['note'].fields[0]} from {item['deck']}")

        if counter % 5000 == 0:
            pr.counter(counter, len(db), i.lemma_1)


def update_from_csv(
    col: Collection,
    deck_name: str,
    csv_path: str,
    deck_config: DeckSpec,
    all_data: list,
    deck_dict: dict,
    model_dict: dict,
    stats: UpdateStats,
) -> set[str]:
    """Update Anki notes from a CSV source. Return set of CSV key values seen."""
    pr.green(f"updating {deck_name} from {csv_path}")

    if not os.path.exists(csv_path):
        pr.no("skipped (csv missing)")
        return set()

    top_level = deck_name.split("::")[0]

    notes_by_key = {}
    csv_keys: set[str] = set()
    for item in all_data:
        if item["deck"].startswith(top_level):
            key = item["note"].fields[0]
            notes_by_key[key] = item

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            headers = reader.fieldnames
            if not headers:
                continue
            key_header = headers[0]
            key_value = row[key_header]
            csv_keys.add(key_value)

            if key_value in notes_by_key:
                item = notes_by_key[key_value]
                note = item["note"]
                if update_note_values_csv(note, row, deck_config):
                    try:
                        col.update_note(note)
                        stats.updated += 1
                        stats.deck_stats[top_level]["updated"] += 1
                    except Exception as e:
                        pr.amber(f"Failed to update note id={note.id}: {e}")
            else:
                if deck_config.creates_new_notes:
                    pr.green(f"creating new note for {key_value}")
                    if deck_config.model_name in model_dict:
                        model_id = model_dict[deck_config.model_name]
                        deck_id = deck_dict[deck_name]
                        note = col.new_note(model_id)
                        update_note_values_csv(note, row, deck_config)
                        col.add_note(note, deck_id)
                        stats.added += 1
                        stats.deck_stats[top_level]["added"] += 1

    return csv_keys


def delete_stale_csv_notes(
    col: Collection,
    all_data: list,
    top_level: str,
    csv_keys: set[str],
    stats: UpdateStats,
) -> None:
    """Delete notes in top_level deck whose key (fields[0]) is absent from csv_keys."""
    notes_by_key: dict[str, dict] = {}
    for item in all_data:
        if item["deck"].startswith(top_level):
            key = item["note"].fields[0]
            notes_by_key[key] = item

    for key, item in notes_by_key.items():
        if key not in csv_keys:
            col.remove_notes([item["note"].id])
            stats.deleted += 1
            if top_level in stats.deck_stats:
                stats.deck_stats[top_level]["deleted"] += 1
            pr.amber(f"deleted '{key}' from {top_level}")


def _natural_sort_key(s: str) -> list[int | str]:
    """Natural sort key: 'DHP2' < 'DHP10'."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", s or "")]


def _get_note_field(note: Note, field_name: str) -> str:
    """Return value of a named field from a note, or '' if absent."""
    model = note.note_type()
    if model is None:
        return ""
    names = [f["name"] for f in model["flds"]]
    if field_name not in names:
        return ""
    return note.fields[names.index(field_name)]


def _reset_card_to_new(card: Card) -> None:
    """Reset a card to new without changing runtime behavior."""
    cast(Any, card).queue = 0
    cast(Any, card).type = 0


def reorder_all_decks(col: Collection) -> None:
    """Force all cards to new (queue=0, type=0) and reorder by deck-specific criteria."""
    pr.green("reordering all decks")

    # Build a local deck_id lookup so we can sort EXACTLY one deck (not its subdecks).
    # In Anki, deck:"Foo" matches Foo AND all subdecks; filtering by card.did == deck_id
    # ensures we only reorder notes that literally live in that exact deck.
    local_deck_dict: dict[str, int] = {d["name"]: d["id"] for d in col.decks.all()}

    def _apply_order(deck_name: str, key_fn) -> None:
        """Sort notes in EXACTLY deck_name (not subdecks) by key_fn; force all new."""
        deck_id = local_deck_dict.get(deck_name)
        if deck_id is None:
            return
        # find_cards includes subdecks; filter to exact deck by card.did
        seen_nids: set[int] = set()
        nids_in_deck: list[int] = []
        for cid in col.find_cards(f'deck:"{deck_name}"'):
            card = col.get_card(cid)
            if card.did == deck_id and card.nid not in seen_nids:
                seen_nids.add(card.nid)
                nids_in_deck.append(card.nid)
        if not nids_in_deck:
            return
        pairs = [(col.get_note(cast(Any, nid)), nid) for nid in nids_in_deck]
        pairs.sort(key=lambda x: key_fn(x[0]))
        for pos, (note, _) in enumerate(pairs, start=1):
            for cid in col.find_cards(f"nid:{note.id}"):
                card = col.get_card(cid)
                if card.queue != 0 or card.type != 0:
                    _reset_card_to_new(card)
                card.due = pos
                col.update_card(card)

    def _force_new_only(deck_name: str) -> None:
        for cid in col.find_cards(f'deck:"{deck_name}"'):
            card = col.get_card(cid)
            if card.queue != 0 or card.type != 0:
                _reset_card_to_new(card)
                col.update_card(card)

    # SBS Pali-English Vocab — sbs_index (int)
    _apply_order(
        "SBS Pali-English Vocab",
        lambda n: int(_get_note_field(n, "sbs_index") or "0"),
    )

    # Pali DHP vocab — source (natural str: DHP1, DHP2 … DHP10)
    _apply_order(
        "Pali DHP vocab",
        lambda n: _natural_sort_key(_get_note_field(n, "source")),
    )

    # Pali Parittas — source (natural str)
    _apply_order(
        "Pali Parittas",
        lambda n: _natural_sort_key(_get_note_field(n, "source")),
    )

    # Pali Bhikkhu Vibhanga — source (natural str)
    _apply_order(
        "Pali Bhikkhu Vibhanga",
        lambda n: _natural_sort_key(_get_note_field(n, "source")),
    )

    # Vocab Pali Class — parent deck + each numbered subdeck
    # Within each deck: extra empty first (0), then non-empty (1)
    vocab_decks = ["Vocab Pali Class"] + [
        f"Vocab Pali Class::{str(n).zfill(2)}.Class" for n in VOCAB_CLASS_RANGE
    ]
    for deck_name in vocab_decks:
        _apply_order(
            deck_name,
            lambda n: (0 if not _get_note_field(n, "extra") else 1,),
        )

    # Roots Pali Class — sbs_class_anki (int)
    _apply_order(
        "Roots Pali Class",
        lambda n: int(_get_note_field(n, "sbs_class_anki") or "0"),
    )

    # Phonetic Changes Pali Class — sbs_class_anki (int)
    _apply_order(
        "Phonetic Changes Pali Class",
        lambda n: int(_get_note_field(n, "sbs_class_anki") or "0"),
    )

    # Suttas Advanced Pali Class — parent deck + each known subdeck, sorted by source
    suttas_decks = ["Suttas Advanced Pali Class"] + list(SUTTAS_PREFIX_MAP.values())
    for deck_name in suttas_decks:
        _apply_order(
            deck_name,
            lambda n: _natural_sort_key(_get_note_field(n, "source")),
        )

    # Пали Словарь — pali (alphabetical)
    _apply_order(
        "Пали Словарь",
        lambda n: _get_note_field(n, "pali").lower(),
    )

    # Pali Patimokkha Word By Word — order field (int)
    _apply_order(
        "Pali Patimokkha Word By Word",
        lambda n: int(_get_note_field(n, "order") or "0"),
    )

    # Common Roots + Grammar — force new only, preserve existing due order
    _force_new_only("Common Roots")
    _force_new_only("Grammar Pali Class")

    pr.yes("reorder done")


def run_pipeline(skip_collection: bool = False):
    """Regenerate all CSVs and optionally update Anki collection."""

    pr.green("setup db")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.sbs), joinedload(DpdHeadword.ru))
        .all()
    )
    pr.yes(len(db))

    recalculate_all_sbs_indices(db_session, db)

    if skip_collection:
        pr.yes("pipeline complete (skipped collection)")
        return

    backup_anki_db()

    deck_names = list(EXPECTED_COLLECTION.keys())
    col, data_dict, all_data, deck_dict, model_dict = setup_anki_updater(deck_names)
    if (
        not col
        or data_dict is None
        or all_data is None
        or deck_dict is None
        or model_dict is None
    ):
        return

    stats = UpdateStats()
    try:
        update_from_db(db, col, data_dict, deck_dict, model_dict, stats)

        deck_specs = {d.deck_name: d for d in DECKS if d.source == "csv"}
        paths = DPSPaths()

        for deck_name, deck_config in deck_specs.items():
            if deck_name == "Grammar Pali Class":
                grammar_dir = paths.anki_csvs_dir / "pali_class" / "grammar"
                if grammar_dir.exists():
                    grammar_csv_keys: set[str] = set()
                    # for files starting only with "cl_"
                    for csv_file in os.listdir(grammar_dir):
                        if csv_file.endswith(".csv") and csv_file.startswith("cl_"):
                            seen = update_from_csv(
                                col,
                                deck_name,
                                str(grammar_dir / csv_file),
                                deck_config,
                                all_data,
                                deck_dict,
                                model_dict,
                                stats,
                            )
                            grammar_csv_keys |= seen
                    delete_stale_csv_notes(
                        col, all_data, deck_name, grammar_csv_keys, stats
                    )
            else:
                csv_path = paths.anki_csvs_dir / deck_config.csv_path_attr
                seen = update_from_csv(
                    col,
                    deck_name,
                    str(csv_path),
                    deck_config,
                    all_data,
                    deck_dict,
                    model_dict,
                    stats,
                )
                delete_stale_csv_notes(col, all_data, deck_name, seen, stats)

        reorder_all_decks(col)

        stats.pr_summary()

    finally:
        col.close()


def main():
    pr.tic()
    run_pipeline()
    pr.toc()


if __name__ == "__main__":
    main()
