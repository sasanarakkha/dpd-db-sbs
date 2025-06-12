#!/usr/bin/env python3

"""
Add all additions from gui2/data/additions.json to the database with new IDs.
And replace old id with new id in the backup tsvs
"""
import json
import typing

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.paths_dps import DPSPaths # For TSV paths

from gui2.additions_manager import AdditionsManager
from gui2.database_manager import DatabaseManager # For get_next_id and add_word_to_db
from gui2.paths import Gui2Paths
from gui2.toolkit import ToolKit # For type casting


class MockToolKit:
    """A minimal toolkit mock to satisfy manager dependencies."""
    def __init__(self):
        self.paths = Gui2Paths()
        # AdditionsManager and DatabaseManager might need more from toolkit,
        # but for this script, paths and db_session (handled separately) are key.
        # If DatabaseManager is used more extensively, it might need more mock attributes.


app_pth = ProjectPaths()
db_session = get_db_session(app_pth.dpd_db_path)
dpspth = DPSPaths()


def load_id_map_from_additions_added(gui_paths: Gui2Paths) -> dict[str, int]:
    """
    Loads an ID map from the additions_added.json file.
    The map is from old_id (id_add) to new_id (id).
    """
    pr.title(f"Loading ID map from {gui_paths.additions_added_path}")
    id_map: dict[str, int] = {}
    try:
        with open(gui_paths.additions_added_path, 'r', encoding='utf-8') as f:
            additions_data = json.load(f)
            if not isinstance(additions_data, list):
                pr.red(f"Error: {gui_paths.additions_added_path} is not a JSON list.")
                return {}
            
            for item in additions_data:
                if isinstance(item, dict) and "id_add" in item and "id" in item:
                    old_id = str(item["id_add"]) # Ensure old_id is string
                    new_id = int(item["id"])     # Ensure new_id is int
                    id_map[old_id] = new_id
                else:
                    pr.red(f"Skipping invalid item in additions_added.json: {item}")
            pr.green(f"Successfully loaded {len(id_map)} ID mappings.")
            pr.yes("ok")
    except FileNotFoundError:
        pr.red(f"File not found: {gui_paths.additions_added_path}")
    except json.JSONDecodeError:
        pr.red(f"Error decoding JSON from {gui_paths.additions_added_path}")
    return id_map


def replace_old_ids_in_tsv_files(id_map: dict[str, int]):
    """
    Replaces old IDs with new IDs in specified TSV files.
    id_map: A dictionary mapping old_id_str to new_id (int).
    """
    pr.title("Replacing old IDs in TSV files (russian.tsv, sbs.tsv)...")

    if not id_map:
        pr.red("ID map is empty. No TSV files to update.")
        return

    def process_file(file_path: str, current_id_map: dict[str, int]):
        # pr.green(f"Processing TSV file: {file_path}")
        pr.yes("ok")

        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as file:
                lines = file.readlines()
        except FileNotFoundError:
            pr.red(f"File not found: {file_path}")
            return

        replacements_done = 0
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            for line_number, line in enumerate(lines):
                columns = line.strip().split('\t')
                if columns:
                    # Clean the first column ID for matching (remove existing quotes)
                    id_to_check = columns[0].strip().strip('"')
                    if id_to_check in current_id_map:
                        new_id = current_id_map[id_to_check]
                        columns[0] = f'"{new_id}"' # Add quotes to the new ID
                        replacements_done +=1
                file.write('\t'.join(columns) + '\n')
        pr.green(f"Finished processing {file_path}. Replacements made: {replacements_done}")
        pr.yes("ok")

    process_file(str(dpspth.russian_path), id_map)
    process_file(str(dpspth.sbs_path), id_map)
    pr.yes("ok")
    

def add_all_additions_with_new_ids():
    """
    Processes all additions from additions.json, assigns new IDs,
    and adds them to the database.
    """

    pr.title("Starting batch addition of 'additions.json' entries to DB with new IDs...")

    mock_toolkit = MockToolKit()
    
    # Initialize DatabaseManager to get next ID and add words
    # Note: DatabaseManager usually initializes its own db_session.
    # For this script, we're using the global db_session.
    # If DatabaseManager methods strictly rely on its internal session,
    # this might need adjustment or DatabaseManager might need a way to accept an external session.
    # For get_next_id and add_word_to_db, it should be fine as they use self.db_session.
    db_manager = DatabaseManager()
    db_manager.db_session = db_session # Ensure it uses our script's session

    additions_manager = AdditionsManager(toolkit=typing.cast(ToolKit, mock_toolkit))

    all_additions_to_process = dict(additions_manager.additions_dict)

    if not all_additions_to_process:
        pr.red("No additions found in additions.json.")
        return

    pr.green(f"Found {len(all_additions_to_process)} additions to process.")
    pr.yes("ok")

    processed_count = 0
    failed_count = 0
    
    successful_id_map: dict[str, int] = {} # To store old_id_str: new_id

    for old_id_str, addition_data in all_additions_to_process.items():
        # pr.green(f"Processing addition for old ID: {old_id_str}")

        # Check if lemma_1 from addition_data already exists in the database
        lemma_1_to_check = addition_data.get("lemma_1")
        if lemma_1_to_check:
            existing_headword = db_session.query(DpdHeadword).filter(DpdHeadword.lemma_1 == lemma_1_to_check).first()
            if existing_headword:
                pr.red(f"  Error: Lemma '{lemma_1_to_check}' (from old ID {old_id_str}) already exists in DB with ID {existing_headword.id}. Skipping this addition.")
                failed_count += 1
                continue
        else:
            pr.red(f"  Error: 'lemma_1' not found in addition data for old ID {old_id_str}. Skipping.")
            failed_count += 1
            continue

        new_id = db_manager.get_next_id()
        # pr.info(f"  Old ID: {old_id_str}, New ID: {new_id}")

        new_headword = DpdHeadword()
        
        # Set the new ID
        setattr(new_headword, "id", new_id)
        
        fields_set_log = [f"'id': '{old_id_str}' (original) -> '{new_id}' (assigned)"]

        for field_name, value in addition_data.items():
            if field_name == "id":  # Skip the old 'id' field from the JSON data
                continue
            if field_name == "comment": # 'comment' is for the addition entry, not DpdHeadword
                # pr.info(f"  Comment for old ID {old_id_str}: {value}") # Optional: log if needed
                continue

            if hasattr(new_headword, field_name):
                # Basic type coversion for common fields if they are strings in JSON
                # but numbers in the model. DpdHeadword model should ideally handle this.
                # For now, we assume direct assignment is okay or model handles it.
                try:
                    # If field is an integer type in model and value is string digit
                    if field_name in ["ebt_count"] and isinstance(value, str) and value.isdigit(): # Add other int fields if necessary
                        value = int(value)
                    
                    setattr(new_headword, field_name, value)
                    fields_set_log.append(f"'{field_name}': '{value}'")
                except Exception as e:
                    pr.red(f"  Could not set field '{field_name}' to '{value}': {e}")
            else:
                pr.red(f"  Field '{field_name}' (value: '{value}') from addition data does not exist in DpdHeadword model. Skipping this field.")
        
        try:
            db_session.add(new_headword)
            db_session.commit()
            # pr.green(f"  Successfully added '{new_headword.lemma_1}' (New ID: {new_id}) to DB.")
            # pr.info(f"  Fields set: {'; '.join(fields_set_log)}") # Uncomment for detailed log
            processed_count +=1
            successful_id_map[old_id_str] = new_id # Add to map for TSV update
        except Exception as e:
            db_session.rollback()
            pr.red(f"  Database commit failed for '{new_headword.lemma_1}' (Old ID: {old_id_str}, New ID: {new_id}): {e}")
            failed_count += 1
            continue # Skip to next item in all_additions_to_process

    pr.yes("done") # After loop

    # Update TSV files if any words were successfully added
    if successful_id_map:
        # pr.title(f"\nUpdating TSV files for {len(successful_id_map)} successfully added words...")
        replace_old_ids_in_tsv_files(successful_id_map)
    else:
        if not all_additions_to_process: # handles case where all_additions_to_process was empty
            pass # Message already printed if no additions found
        elif failed_count == len(all_additions_to_process): # All attempted additions failed
            pr.red("No words were successfully added to the database. TSV files not updated.")
        else: # Some other scenario, e.g. all were skipped due to existing lemma_1
            pr.info("No new words were committed to the database. TSV files not updated.")
    pr.yes("ok")


    pr.title("Batch Addition Summary")
    print(f"Total additions attempted: {len(all_additions_to_process)}")
    print(f"Successfully prepared and (attempted) to add to DB: {processed_count}")
    print(f"Failed during preparation or DB commit: {failed_count}")
    print("Batch script finished. additions.json was NOT modified.")
    pr.yes("ok")


def process_additions_added_and_update_tsvs():
    """
    Loads ID map from additions_added.json and updates TSV files.
    """
    pr.title("Processing additions_added.json and updating TSVs...")
    gui_paths = Gui2Paths()
    id_map = load_id_map_from_additions_added(gui_paths)

    if id_map:
        replace_old_ids_in_tsv_files(id_map)
    else:
        pr.warning("No ID map loaded or map is empty, TSV files will not be updated.")
    pr.yes("ok")
    pr.title("Finished processing additions_added.json.")


def main():
    pr.tic()
    add_all_additions_with_new_ids()
    process_additions_added_and_update_tsvs()
    pr.toc()


if __name__ == "__main__":
    main()
