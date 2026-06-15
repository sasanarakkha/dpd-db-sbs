#!/usr/bin/env python3

"""Verify SBS Anki collection structure against expected snapshot."""

import json
import traceback
from pathlib import Path
from typing import Any

from anki.collection import Collection
from anki.errors import DBError

from tools.configger import config_read
from tools.printer import printer as pr

SNAPSHOT_PATH = Path(__file__).resolve().parent / "sbs_anki_schema_snapshot.json"


class CollectionChangedError(Exception):
    """Raised when the Anki collection structure differs from the expected snapshot."""


def _find_mismatches(
    live_structure: dict[str, dict[str, Any]],
    expected: dict[str, dict[str, Any]],
) -> list[str]:
    """Return structural differences between live collection and expected snapshot."""
    mismatches: list[str] = []
    for deck_name, exp in expected.items():
        if deck_name not in live_structure:
            mismatches.append(f"Missing deck: {deck_name}")
            continue

        live = live_structure[deck_name]
        if live["model_name"] != exp["model_name"]:
            mismatches.append(
                f"Deck '{deck_name}' model mismatch: expected '{exp['model_name']}', found '{live['model_name']}'"
            )

        if live["fields"] != exp["fields"]:
            expected_fields = set(exp["fields"])
            live_fields = set(live["fields"])
            missing = expected_fields - live_fields
            extra = live_fields - expected_fields
            if missing:
                mismatches.append(f"Deck '{deck_name}' missing fields: {missing}")
            if extra:
                mismatches.append(f"Deck '{deck_name}' extra fields: {extra}")
            if not missing and not extra:
                mismatches.append(
                    f"Deck '{deck_name}' field order changed: expected {exp['fields']}, found {live['fields']}"
                )

    return mismatches


def verify_sbs_collection(col: Collection) -> bool:
    """
    Verify the live SBS collection against the JSON snapshot.
    Returns True if matches, otherwise raises CollectionChangedError or generates a report.
    """
    pr.green("verifying anki collection structure")

    live_structure: dict[str, dict[str, Any]] = {}
    for d in col.decks.all_names_and_ids():
        deck_name = d.name
        note_ids = col.find_notes(f'deck:"{deck_name}"')
        if not note_ids:
            # empty deck — model is unavailable without a note
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

        live_structure[deck_name] = {
            "model_name": model["name"],
            "fields": [f["name"] for f in model["flds"]],
            "count": len(note_ids),
        }

    if not SNAPSHOT_PATH.exists():
        generate_report(live_structure)
        pr.amber(
            f"Schema snapshot not found — review temp/sbs_anki_schema_snapshot.json and copy to {SNAPSHOT_PATH}"
        )
        return False

    expected: dict[str, dict[str, Any]] = json.loads(
        SNAPSHOT_PATH.read_text(encoding="utf-8")
    )
    mismatches = _find_mismatches(live_structure, expected)

    if mismatches:
        for m in mismatches:
            pr.red(m)
        generate_report(live_structure)
        raise CollectionChangedError(
            f"Collection structure changed — update {SNAPSHOT_PATH.name} and re-run"
        )

    pr.yes("Collection structure verified")
    return True


def generate_report(live_structure: dict[str, dict[str, Any]]) -> None:
    """Generate a markdown report and JSON snapshot of the live collection structure."""
    report_dir = Path("temp")
    report_dir.mkdir(exist_ok=True)

    snapshot = {
        deck_name: {"model_name": info["model_name"], "fields": info["fields"]}
        for deck_name, info in sorted(live_structure.items())
        if info["model_name"] not in ("Unknown (Empty Deck)", "Unknown (Missing Model)")
    }
    snapshot_tmp = report_dir / "sbs_anki_schema_snapshot.json"
    snapshot_tmp.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    pr.green(f"Snapshot dumped to {snapshot_tmp} — copy to {SNAPSHOT_PATH} to update")

    report_path = report_dir / "sbs_collection_report.md"
    with report_path.open("w", encoding="utf-8") as f:
        f.write("# SBS Anki Collection Report\n\n")
        f.write("## Live Structure\n\n")
        f.write("| Deck Name | Model Name | Note Count | Fields |\n")
        f.write("|---|---|---|---|\n")
        for deck_name, info in sorted(live_structure.items()):
            fields_str = ", ".join(info["fields"])
            f.write(
                f"| {deck_name} | {info['model_name']} | {info['count']} | {fields_str} |\n"
            )
        f.write("\n## Name Mapping Table (Draft)\n\n")
        f.write("| Collection deck name | CSV source file | .apkg slug | Notes |\n")
        f.write("|---|---|---|---|\n")
        for deck_name in sorted(live_structure.keys()):
            f.write(f"| {deck_name} | | | |\n")
    pr.green(f"Report generated at {report_path}")


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
        traceback.print_exc()


if __name__ == "__main__":
    main()
