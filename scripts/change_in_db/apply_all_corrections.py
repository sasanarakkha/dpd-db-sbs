#!/usr/bin/env python3

"""Apply all corrections from gui2/data/corrections_{username}.json to the database."""

import json

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from gui2.paths import Gui2Paths
from tools.configger import config_read
from tools.paths import ProjectPaths
from tools.printer import printer as pr

app_pth = ProjectPaths()
db_session = get_db_session(app_pth.dpd_db_path)


def apply_all_corrections_from_json() -> None:
    """
    Processes all corrections from corrections.json and applies them to the database.
    Does not modify any JSON files.
    """
    pr.green_title("Starting batch application of corrections from JSON...")

    username = config_read("gui2", "username") or "1"
    corrections_json_path = Gui2Paths.for_user(username).corrections_path

    try:
        with open(corrections_json_path, encoding="utf-8") as f:
            all_corrections_to_process = json.load(f)
    except FileNotFoundError:
        pr.red(f"File not found: {corrections_json_path}")
        return
    except json.JSONDecodeError:
        pr.red(f"Error decoding JSON from {corrections_json_path}")
        return

    if not all_corrections_to_process:
        pr.red("No corrections found in corrections.json.")
        return

    pr.green(f"Found {len(all_corrections_to_process)} corrections to process.")
    pr.yes("ok")

    processed_count = 0
    failed_count = 0

    for word_id_str, correction_data in all_corrections_to_process.items():
        try:
            word_id = int(word_id_str)
        except ValueError:
            pr.red(
                f"  Invalid ID format '{word_id_str}' for correction entry. Skipping."
            )
            failed_count += 1
            continue

        db_entry = (
            db_session.query(DpdHeadword).filter(DpdHeadword.id == word_id).first()
        )

        if not db_entry:
            pr.red(f"  Headword with ID {word_id} not found in the database. Skipping.")
            failed_count += 1
            continue

        any_changed: bool = False
        for field_name, new_value in correction_data.items():
            if field_name == "comment":
                continue
            if hasattr(db_entry, field_name):
                current_value = getattr(db_entry, field_name)
                if current_value != new_value:
                    setattr(db_entry, field_name, new_value)
                    any_changed = True
            else:
                pr.red(
                    f"  Field '{field_name}' (value: '{new_value}') from correction data does not exist in DpdHeadword model. Skipping this field."
                )

        if any_changed:
            try:
                db_session.commit()
                processed_count += 1
            except Exception as e:  # noqa: BLE001
                db_session.rollback()
                pr.red(f"  Failed to commit changes for headword ID {word_id}: {e}")
                failed_count += 1
        else:
            pr.red(
                f"  No actual field changes for headword ID {word_id} ({db_entry.lemma_1})."
            )

    pr.green_title("Batch Correction Summary")
    pr.green(f"Total corrections attempted: {len(all_corrections_to_process)}")
    pr.green(f"Successfully processed and updated in DB: {processed_count}")
    pr.green(f"Failed or skipped: {failed_count}")
    pr.yes("ok")


def main() -> None:
    pr.tic()
    apply_all_corrections_from_json()
    pr.toc()


if __name__ == "__main__":
    main()
