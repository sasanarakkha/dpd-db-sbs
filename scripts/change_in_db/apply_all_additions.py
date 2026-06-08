#!/usr/bin/env python3

"""Add all additions from gui2/data/additions.json to the database with new IDs."""

import json
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.configger import config_read
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.paths_dps import DPSPaths
from gui2.database_manager import DatabaseManager
from gui2.paths import Gui2Paths


app_pth = ProjectPaths()
db_session = get_db_session(app_pth.dpd_db_path)
dpspth = DPSPaths()


def replace_old_ids_in_tsv_files(id_map: dict[str, int]) -> None:
    """
    Replaces old IDs with new IDs in specified TSV files.
    id_map: A dictionary mapping old_id_str to new_id (int).
    """
    pr.green_title("Replacing old IDs in TSV files (russian.tsv, sbs.tsv)...")

    if not id_map:
        pr.red("ID map is empty. No TSV files to update.")
        return

    def process_file(file_path: Path, current_id_map: dict[str, int]) -> None:
        try:
            with open(file_path, "r", newline="", encoding="utf-8") as file:
                lines = file.readlines()
        except FileNotFoundError:
            pr.red(f"File not found: {file_path}")
            return

        replacements_done = 0
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            for line_number, line in enumerate(lines):
                columns = line.strip().split("\t")
                if columns:
                    # Clean the first column ID for matching (remove existing quotes)
                    id_to_check = columns[0].strip().strip('"')
                    if id_to_check in current_id_map:
                        new_id = current_id_map[id_to_check]
                        columns[0] = f'"{new_id}"'  # Add quotes to the new ID
                        replacements_done += 1
                file.write("\t".join(columns) + "\n")
        pr.green(
            f"Finished processing {file_path}. Replacements made: {replacements_done}"
        )
        pr.yes("ok")

    process_file(dpspth.russian_path, id_map)
    process_file(dpspth.sbs_path, id_map)
    pr.yes("ok")


def add_all_additions_with_new_ids() -> None:
    """
    Processes all additions from additions.json, assigns new IDs,
    and adds them to the database.
    Does not modify any JSON files.
    """
    pr.green_title(
        "Starting batch addition of 'additions.json' entries to DB with new IDs..."
    )

    username = config_read("gui2", "username") or "1"
    additions_json_path = Gui2Paths.for_user(username).additions_path

    try:
        with open(additions_json_path) as f:
            all_additions_to_process = json.load(f)
    except FileNotFoundError:
        pr.red(f"File not found: {additions_json_path}")
        return
    except json.JSONDecodeError:
        pr.red(f"Error decoding JSON from {additions_json_path}")
        return

    db_manager = DatabaseManager()
    db_manager.db_session = db_session

    if not all_additions_to_process:
        pr.red("No additions found in additions.json.")
        return

    pr.green(f"Found {len(all_additions_to_process)} additions to process.")
    pr.yes("ok")

    processed_count = 0
    failed_count = 0
    successful_id_map: dict[str, int] = {}

    for old_id_str, addition_data in all_additions_to_process.items():
        lemma_1_to_check = addition_data.get("lemma_1")
        if lemma_1_to_check:
            existing_headword = (
                db_session.query(DpdHeadword)
                .filter(DpdHeadword.lemma_1 == lemma_1_to_check)
                .first()
            )
            if existing_headword:
                pr.red(
                    f"  Error: Lemma '{lemma_1_to_check}' (from old ID {old_id_str}) already exists in DB with ID {existing_headword.id}. Skipping this addition."
                )
                failed_count += 1
                continue
        else:
            pr.red(
                f"  Error: 'lemma_1' not found in addition data for old ID {old_id_str}. Skipping."
            )
            failed_count += 1
            continue

        new_id = db_manager.get_next_id()
        new_headword = DpdHeadword()
        setattr(new_headword, "id", new_id)

        for field_name, value in addition_data.items():
            if field_name in ("id", "comment"):
                continue
            if hasattr(new_headword, field_name):
                try:
                    if (
                        field_name == "ebt_count"
                        and isinstance(value, str)
                        and value.isdigit()
                    ):
                        value = int(value)
                    setattr(new_headword, field_name, value)
                except Exception as e:
                    pr.red(f"  Could not set field '{field_name}' to '{value}': {e}")
            else:
                pr.red(
                    f"  Field '{field_name}' (value: '{value}') from addition data does not exist in DpdHeadword model. Skipping this field."
                )

        try:
            db_session.add(new_headword)
            db_session.commit()
            processed_count += 1
            successful_id_map[old_id_str] = new_id
        except Exception as e:
            db_session.rollback()
            pr.red(
                f"  Database commit failed for '{new_headword.lemma_1}' (Old ID: {old_id_str}, New ID: {new_id}): {e}"
            )
            failed_count += 1
            continue

    pr.yes("done")

    if successful_id_map:
        replace_old_ids_in_tsv_files(successful_id_map)
    elif failed_count == len(all_additions_to_process):
        pr.red(
            "No words were successfully added to the database. TSV files not updated."
        )
    else:
        pr.green("No new words were committed to the database. TSV files not updated.")
    pr.yes("ok")

    pr.green_title("Batch Addition Summary")
    pr.green(f"Total additions attempted: {len(all_additions_to_process)}")
    pr.green(f"Successfully prepared and (attempted) to add to DB: {processed_count}")
    pr.green(f"Failed during preparation or DB commit: {failed_count}")
    pr.green("Batch script finished. additions.json was NOT modified.")
    pr.yes("ok")


def main() -> None:
    pr.tic()
    add_all_additions_with_new_ids()
    pr.toc()


if __name__ == "__main__":
    main()
