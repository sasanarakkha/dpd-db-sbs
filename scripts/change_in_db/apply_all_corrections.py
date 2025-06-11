#!/usr/bin/env python3

"""Apply all corrections from gui2/data/corrections.json to the database."""
import typing

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from gui2.toolkit import ToolKit # Import ToolKit for casting
from tools.printer import printer as pr

from gui2.corrections_manager import CorrectionsManager
from gui2.paths import Gui2Paths


class MockToolKit:
    """A minimal toolkit mock to satisfy CorrectionsManager's dependency."""
    def __init__(self):
        self.paths = Gui2Paths()


app_pth = ProjectPaths() # pth is a common abbreviation for paths, app_pth for application specific
db_session = get_db_session(app_pth.dpd_db_path)


def apply_all_corrections_from_json():
    """
    Processes all corrections from corrections.json and applies them to the database.
    """
    pr.title("Starting batch application of corrections from JSON...")

    mock_toolkit = MockToolKit()
    # Use typing.cast to inform the type checker that mock_toolkit is sufficient
    # for CorrectionsManager's needs in this context.
    corrections_manager = CorrectionsManager(toolkit=typing.cast(ToolKit, mock_toolkit))

    # Create a copy to iterate over, as we'll modify the original dict.
    all_corrections_to_process = dict(corrections_manager.corrections_dict)

    if not all_corrections_to_process:
        pr.red("No corrections found in corrections.json.")
        return

    pr.green(f"Found {len(all_corrections_to_process)} corrections to process.")
    pr.yes("ok")


    processed_count = 0
    failed_count = 0
    # successfully_processed_ids = [] # Not needed if not modifying corrections.json

    for word_id_str, correction_data in all_corrections_to_process.items():
        # pr.green(f"Processing correction for ID: {word_id_str}")
        # pr.yes("ok")
        try:
            word_id = int(word_id_str)
        except ValueError:
            pr.red(f"  Invalid ID format '{word_id_str}' for correction entry. Skipping.")
            failed_count += 1
            continue

        db_entry = db_session.query(DpdHeadword).filter(DpdHeadword.id == word_id).first()

        if not db_entry:
            pr.red(f"  Headword with ID {word_id} not found in the database. Skipping.")
            failed_count += 1
            continue

        fields_updated_log = []
        for field_name, new_value in correction_data.items():
            if field_name == "comment":  # Skip 'comment' for direct attribute setting
                continue
            if hasattr(db_entry, field_name):
                current_value = getattr(db_entry, field_name)
                if current_value != new_value:
                    setattr(db_entry, field_name, new_value)
                    fields_updated_log.append(f"'{field_name}': '{current_value}' -> '{new_value}'")
            else:
                pr.red(f"  Field '{field_name}' (value: '{new_value}') from correction data does not exist in DpdHeadword model. Skipping this field.")

        if fields_updated_log:
            try:
                db_session.commit()
                # pr.green(f"  Successfully updated headword ID {word_id} ({db_entry.lemma_1}) in the database.")
                # pr.green(f"  Fields updated: {'; '.join(fields_updated_log)}")
                # corrections_manager.save_processed_correction(correction_data) # Removed for simplicity
                # pr.green(f"  Entry for ID {word_id} would be saved to corrections_added.json.") # Log instead
                # successfully_processed_ids.append(word_id_str) # Not needed
                processed_count += 1
            except Exception as e:
                db_session.rollback()
                pr.red(f"  Failed to commit changes for headword ID {word_id}: {e}")
                failed_count += 1
        else:
            pr.red(f"  No actual field changes for headword ID {word_id} ({db_entry.lemma_1}).")
            # corrections_manager.save_processed_correction(correction_data) # Removed for simplicity
            # successfully_processed_ids.append(word_id_str) # Not needed
            # processed_count += 1 # Optionally count this as processed

    # Removed the block for modifying corrections.json for simplicity
    # if successfully_processed_ids:
    #     pr.green(f"\nRemoving {len(successfully_processed_ids)} processed items from corrections.json.")
    #     for sid in successfully_processed_ids:
    #         if sid in corrections_manager.corrections_dict:
    #             del corrections_manager.corrections_dict[sid]
    #     corrections_manager.save_corrections()
    #     pr.green("corrections.json has been updated.")

    pr.yes("ok")
    pr.title("Batch Correction Summary")
    print(f"Total corrections attempted: {len(all_corrections_to_process)}")
    print(f"Successfully processed and updated in DB: {processed_count}")
    print(f"Failed or skipped: {failed_count}")
    print("Batch script finished.")
    pr.yes("ok")

# Ensure main function calls the correct processing function
def main():
    pr.tic()
    apply_all_corrections_from_json()
    pr.toc()


if __name__ == "__main__":
    main()