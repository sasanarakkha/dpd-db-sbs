#!/usr/bin/env python3

"""
Add all additions from gui2/data/additions.json to the database with new IDs.
And replace old id with new id in the backup tsvs
"""
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
dpspth = DPSPaths() # Initialize DPSPaths


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
        pr.green(f"Processing TSV file: {file_path}")
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
    
    words_to_add_to_db = []
    successful_id_map: dict[str, int] = {} # To store old_id_str: new_id

    for old_id_str, addition_data in all_additions_to_process.items():
        # pr.green(f"Processing addition for old ID: {old_id_str}")

        new_id = db_manager.get_next_id()
        # pr.info(f"  Old ID: {old_id_str}, New ID: {new_id}")

        new_headword = DpdHeadword()
        
        # Set the new ID
        setattr(new_headword, "id", new_id)
        
        fields_set_log = [f"'id': '{old_id_str}' (original) -> '{new_id}' (assigned)"]

        for field_name, value in addition_data.items():
            if field_name == "id":  # Skip the old 'id' field from the JSON data
                continue
            # if field_name == "comment": # 'comment' is for the addition entry, not DpdHeadword
            #     pr.info(f"  Comment for old ID {old_id_str}: {value}")
            #     continue

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
        
        words_to_add_to_db.append(new_headword)
        processed_count +=1
        successful_id_map[old_id_str] = new_id # Tentatively add to map
        # pr.green(f"  Prepared '{new_headword.lemma_1}' for addition with new ID {new_id}.")
        # pr.info(f"  Fields set: {'; '.join(fields_set_log)}")
    pr.yes("ok")


    if words_to_add_to_db:
        pr.title(f"\nAttempting to add {len(words_to_add_to_db)} new words to the database...")
        try:
            db_session.add_all(words_to_add_to_db)
            db_session.commit()
            pr.green(f"Successfully added {len(words_to_add_to_db)} words to the database.")
            # Now that DB commit is successful, process TSV files
            replace_old_ids_in_tsv_files(successful_id_map)
        except Exception as e:
            db_session.rollback()
            pr.red(f"  Database commit failed: {e}")
            failed_count = len(words_to_add_to_db) # All failed if commit fails
            successful_id_map.clear() # Clear map as DB commit failed
            processed_count = 0 # Or adjust based on how you want to count this
    else:
        pr.red("No words were prepared for addition.")
    pr.yes("ok")


    pr.title("Batch Addition Summary")
    print(f"Total additions attempted: {len(all_additions_to_process)}")
    print(f"Successfully prepared and (attempted) to add to DB: {processed_count}")
    print(f"Failed during preparation or DB commit: {failed_count}")
    print("Batch script finished. additions.json was NOT modified.")
    pr.yes("ok")


def main():
    pr.tic()
    add_all_additions_with_new_ids()
    pr.toc()


if __name__ == "__main__":
    main()
