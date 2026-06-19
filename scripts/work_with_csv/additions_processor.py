#!/usr/bin/env python3

"""
Processes additions from additions_added.json and updates TSV files by replacing id_add with id values.
Filters out already processed IDs to avoid duplicates and tracks processed additions.
"""

import json
from pathlib import Path

from gui2.paths import Gui2Paths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr


def load_additions_data(json_path: Path) -> dict[str, int]:
    """
    Load additions data from JSON file and create id_add -> id mapping.

    Args:
        json_path: Path to the additions_added.json file

    Returns:
        Dictionary mapping id_add (string) to id (integer)
    """
    additions_data = json.loads(json_path.read_text(encoding="utf-8"))

    id_mapping = {}
    for entry in additions_data:
        id_add = str(entry["id_add"])
        id_val = entry["id"]
        id_mapping[id_add] = id_val

    return id_mapping


def load_processed_ids(processed_path: Path) -> set[str]:
    """
    Load already processed id_add values from the processed file.

    Args:
        processed_path: Path to the addition_replaced.json file

    Returns:
        Set of already processed id_add values
    """
    if not processed_path.exists():
        return set()

    try:
        processed_data = json.loads(processed_path.read_text(encoding="utf-8"))
        return set(processed_data)
    except (json.JSONDecodeError, FileNotFoundError):
        return set()


def save_processed_ids(processed_path: Path, processed_ids: set[str]) -> None:
    """
    Save processed id_add values to the processed file.

    Args:
        processed_path: Path to the addition_replaced.json file
        processed_ids: Set of processed id_add values to save
    """
    existing_ids = load_processed_ids(processed_path)
    all_processed_ids = existing_ids.union(processed_ids)
    processed_path.write_text(
        json.dumps(list(all_processed_ids), indent=2), encoding="utf-8"
    )


def replace_ids_in_tsv(tsv_path: Path, id_mapping: dict[str, int]) -> int:
    """
    Replace id_add with id in the first (id) column of a TSV file.

    Args:
        tsv_path: Path to the TSV file to update
        id_mapping: Dictionary mapping id_add (string) to id (integer)

    Returns:
        Number of replacements made
    """
    if not tsv_path.exists():
        pr.amber(f"Warning: TSV file {tsv_path} does not exist")
        return 0

    lines = tsv_path.read_text(encoding="utf-8").splitlines(keepends=True)

    replacements = 0
    updated_lines = []
    for line in lines:
        columns = line.split("\t", 1)
        current_id = columns[0].strip().strip('"')
        if current_id in id_mapping:
            new_id = id_mapping[current_id]
            columns[0] = f'"{new_id}"'
            line = "\t".join(columns)
            replacements += 1
            pr.cyan(f"Replaced '{current_id}' with '{new_id}' in {tsv_path.name}")
        updated_lines.append(line)

    tsv_path.write_text("".join(updated_lines), encoding="utf-8")

    return replacements


def process_additions() -> None:
    """
    Main function to process additions and update TSV files.
    """
    pthgui = Gui2Paths()
    pthdps = DPSPaths()

    pr.cyan("Loading additions data...")
    id_mapping = load_additions_data(pthgui.additions_added_path)
    pr.green(f"Found {len(id_mapping)} additions to process")

    pr.cyan("Loading already processed IDs...")
    processed_ids = load_processed_ids(pthdps.addition_replaced_json_path)
    pr.green(f"Already processed {len(processed_ids)} additions")

    new_id_mapping = {
        id_add: id_val
        for id_add, id_val in id_mapping.items()
        if id_add not in processed_ids
    }

    if not new_id_mapping:
        pr.green("No new additions to process")
        return

    pr.green(f"Processing {len(new_id_mapping)} new additions")

    pr.cyan(f"Updating SBS TSV file: {pthdps.sbs_path}")
    sbs_replacements = replace_ids_in_tsv(pthdps.sbs_path, new_id_mapping)

    pr.cyan(f"Updating Russian TSV file: {pthdps.russian_path}")
    russian_replacements = replace_ids_in_tsv(pthdps.russian_path, new_id_mapping)

    pr.cyan("Updating processed IDs file...")
    save_processed_ids(pthdps.addition_replaced_json_path, set(new_id_mapping))

    pr.green("Processing complete!")
    pr.green(f"- SBS replacements: {sbs_replacements}")
    pr.green(f"- Russian replacements: {russian_replacements}")
    pr.green(f"- Total new additions processed: {len(new_id_mapping)}")


if __name__ == "__main__":
    process_additions()
