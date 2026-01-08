#!/usr/bin/env python3

"""
Processes additions from additions_added.json and updates TSV files by replacing id_add with id values.
Filters out already processed IDs to avoid duplicates and tracks processed additions.
"""

import json
from pathlib import Path
from typing import Dict, Set
from gui2.paths import Gui2Paths
from tools.paths_dps import DPSPaths


def load_additions_data(json_path: Path) -> Dict[str, int]:
    """
    Load additions data from JSON file and create id_add -> id mapping.

    Args:
        json_path: Path to the additions_added.json file

    Returns:
        Dictionary mapping id_add (string) to id (integer)
    """
    with open(json_path, "r", encoding="utf-8") as f:
        additions_data = json.load(f)

    # Create mapping from id_add to id
    id_mapping = {}
    for entry in additions_data:
        id_add = str(entry["id_add"])
        id_val = entry["id"]
        id_mapping[id_add] = id_val

    return id_mapping


def load_processed_ids(processed_path: Path) -> Set[str]:
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
        with open(processed_path, "r", encoding="utf-8") as f:
            processed_data = json.load(f)
        return set(processed_data)
    except (json.JSONDecodeError, FileNotFoundError):
        return set()


def save_processed_ids(processed_path: Path, processed_ids: Set[str]) -> None:
    """
    Save processed id_add values to the processed file.

    Args:
        processed_path: Path to the addition_replaced.json file
        processed_ids: Set of processed id_add values to save
    """
    # Load existing processed IDs
    existing_ids = load_processed_ids(processed_path)

    # Merge with new processed IDs
    all_processed_ids = existing_ids.union(processed_ids)

    # Save back to file
    with open(processed_path, "w", encoding="utf-8") as f:
        json.dump(list(all_processed_ids), f, indent=2)


def replace_ids_in_tsv(tsv_path: Path, id_mapping: Dict[str, int]) -> int:
    """
    Replace id_add with id in a TSV file.

    Args:
        tsv_path: Path to the TSV file to update
        id_mapping: Dictionary mapping id_add (string) to id (integer)

    Returns:
        Number of replacements made
    """
    if not tsv_path.exists():
        print(f"Warning: TSV file {tsv_path} does not exist")
        return 0

    replacements = 0

    # Read the TSV file
    with open(tsv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Process each line
    updated_lines = []
    for line_num, line in enumerate(lines, 1):
        updated_line = line
        for id_add, id_val in id_mapping.items():
            # Replace id_add with id in the line
            if id_add in line:
                updated_line = updated_line.replace(id_add, str(id_val))
                if updated_line != line:
                    replacements += 1
                    print(
                        f"Replaced '{id_add}' with '{id_val}' in {tsv_path.name} line {line_num}"
                    )

        updated_lines.append(updated_line)

    # Write the updated content back to the file
    with open(tsv_path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    return replacements


def process_additions() -> None:
    """
    Main function to process additions and update TSV files.
    """
    # Initialize path objects
    pthgui = Gui2Paths()
    pthdps = DPSPaths()

    # Load additions data
    print("Loading additions data...")
    id_mapping = load_additions_data(pthgui.additions_added_path)
    print(f"Found {len(id_mapping)} additions to process")

    # Load already processed IDs
    print("Loading already processed IDs...")
    processed_ids = load_processed_ids(pthdps.addition_replaced_json_path)
    print(f"Already processed {len(processed_ids)} additions")

    # Filter out already processed IDs
    new_id_mapping = {
        id_add: id_val
        for id_add, id_val in id_mapping.items()
        if id_add not in processed_ids
    }

    if not new_id_mapping:
        print("No new additions to process")
        return

    print(f"Processing {len(new_id_mapping)} new additions")

    # Replace IDs in TSV files
    print(f"Updating SBS TSV file: {pthdps.sbs_path}")
    sbs_replacements = replace_ids_in_tsv(pthdps.sbs_path, new_id_mapping)

    print(f"Updating Russian TSV file: {pthdps.russian_path}")
    russian_replacements = replace_ids_in_tsv(pthdps.russian_path, new_id_mapping)

    # Update processed IDs file
    print("Updating processed IDs file...")
    save_processed_ids(pthdps.addition_replaced_json_path, set(new_id_mapping.keys()))

    print("Processing complete!")
    print(f"- SBS replacements: {sbs_replacements}")
    print(f"- Russian replacements: {russian_replacements}")
    print(f"- Total new additions processed: {len(new_id_mapping)}")


if __name__ == "__main__":
    process_additions()
