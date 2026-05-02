#!/usr/bin/env python3

"""Verify SBS Anki collection structure against expected snapshot."""

import os
from typing import Any
from anki.collection import Collection
from anki.errors import DBError
from rich import print

from tools.configger import config_read
from tools.printer import printer as pr
from scripts.export.sbs_anki_deck_config import EXPECTED_COLLECTION


class CollectionChangedError(Exception):
    """Raised when the Anki collection structure differs from the expected snapshot."""

    pass


def verify_sbs_collection(col: Collection) -> bool:
    """
    Verify the live SBS collection against the snapshot in deck_config.
    Returns True if matches, otherwise raises CollectionChangedError or generates a report.
    """
    pr.green("verifying anki collection structure")

    live_structure: dict[str, dict[str, Any]] = {}

    # Get all decks
    all_decks = col.decks.all_names_and_ids()
    deck_ids = {d.name: d.id for d in all_decks}

    # For each deck, find its notes and their models
    for deck_name, deck_id in deck_ids.items():
        # Get one note from this deck to find the model
        note_ids = col.find_notes(f'deck:"{deck_name}"')
        if not note_ids:
            # Empty deck, might still have a default model but harder to find
            # For now, just note it as empty
            live_structure[deck_name] = {
                "model_name": "Unknown (Empty Deck)",
                "fields": [],
                "count": 0,
            }
            continue

        note = col.get_note(note_ids[0])
        model = note.note_type()
        if model is None:
            live_structure[deck_name] = {
                "model_name": "Unknown (Missing Model)",
                "fields": [],
                "count": len(note_ids),
            }
            continue

        model_name = model["name"]
        fields = [f["name"] for f in model["flds"]]

        live_structure[deck_name] = {
            "model_name": model_name,
            "fields": fields,
            "count": len(note_ids),
        }

    if not EXPECTED_COLLECTION:
        generate_report(live_structure)
        pr.amber(
            "Collection snapshot not set — review report and populate EXPECTED_COLLECTION in deck_config"
        )
        return False

    # Comparison logic
    mismatches = []
    for deck_name, expected in EXPECTED_COLLECTION.items():
        if deck_name not in live_structure:
            mismatches.append(f"Missing deck: {deck_name}")
            continue

        live = live_structure[deck_name]
        if live["model_name"] != expected["model_name"]:
            mismatches.append(
                f"Deck '{deck_name}' model mismatch: expected '{expected['model_name']}', found '{live['model_name']}'"
            )

        if live["fields"] != expected["fields"]:
            # Check for missing or extra fields
            expected_fields = set(expected["fields"])
            live_fields = set(live["fields"])
            missing = expected_fields - live_fields
            extra = live_fields - expected_fields
            if missing:
                mismatches.append(f"Deck '{deck_name}' missing fields: {missing}")
            if extra:
                mismatches.append(f"Deck '{deck_name}' extra fields: {extra}")

    if mismatches:
        for m in mismatches:
            pr.red(m)
        generate_report(live_structure)
        raise CollectionChangedError(
            "Collection structure changed — update EXPECTED_COLLECTION in sbs_anki_deck_config.py and re-run"
        )

    pr.yes("Collection structure verified")
    return True


def generate_report(live_structure: dict[str, dict[str, Any]]) -> None:
    """Generate a markdown report of the live collection structure."""
    report_path = "temp/sbs_collection_report.md"
    os.makedirs("temp", exist_ok=True)

    with open(report_path, "w") as f:
        f.write("# SBS Anki Collection Report\n\n")
        f.write("## Live Structure\n\n")
        f.write("| Deck Name | Model Name | Note Count | Fields |\n")
        f.write("|---|---|---|---|\n")

        for deck_name, info in sorted(live_structure.items()):
            fields_str = ", ".join(info["fields"])
            f.write(
                f"| {deck_name} | {info['model_name']} | {info['count']} | {fields_str} |\n"
            )

        f.write("\n## Suggested EXPECTED_COLLECTION Entry\n\n")
        f.write("```python\nEXPECTED_COLLECTION = {\n")
        for deck_name, info in sorted(live_structure.items()):
            if info["model_name"] != "Unknown (Empty Deck)":
                f.write(f'    "{deck_name}": {{\n')
                f.write(f'        "model_name": "{info["model_name"]}",\n')
                f.write(f'        "fields": {info["fields"]}\n')
                f.write("    },\n")
        f.write("}\n```\n\n")

        f.write("## Name Mapping Table (Draft)\n\n")
        f.write("| Collection deck name | CSV source file | .apkg slug | Notes |\n")
        f.write("|---|---|---|---|\n")
        for deck_name in sorted(live_structure.keys()):
            f.write(f"| {deck_name} | | | |\n")

    print(f"[green]Report generated at {report_path}")


def main() -> None:
    anki_db_path = config_read("anki", "db_path_sbs")
    if not anki_db_path:
        pr.red("db_path_sbs not found in config.ini")
        return

    try:
        col = Collection(anki_db_path)
        verify_sbs_collection(col)
        col.close()
    except DBError as e:
        pr.red(f"Anki DBError: {e}")
        pr.red("Anki is currently open, close it and try again.")
    except Exception as e:
        pr.red(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
