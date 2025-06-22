"""Update examples for class and discorses from csv"""

import os
from rich.console import Console

from db.db_helpers import get_db_session
from db.models import DpdHeadword, SBS
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.tsv_read_write import read_tsv_dot_dict
from sqlalchemy.orm import joinedload

console = Console()
pth = ProjectPaths()
dpspth = DPSPaths()


def update_sbs_from_tsv_with_filter(csv_path: str, sbs_anki_class_filter: int):
    """
    Updates SBS table from a CSV file based on sbs_anki_class_filter.

    Args:
        csv_path (str): Path to the CSV file.
        sbs_anki_class_filter (int): The value to filter sbs_anki_class by.
    """
    db_session = get_db_session(pth.dpd_db_path)
    console.print(f"[yellow]Updating SBS table from {csv_path} with sbs_anki_class_filter: {sbs_anki_class_filter}")

    try:
        # Read the CSV file
        tsv_data = read_tsv_dot_dict(csv_path)
        if not tsv_data:
            console.print(f"[red]CSV file is empty or could not be read: {csv_path}")
            return

        console.print(f"[blue]First data row from CSV: {tsv_data[0]} ")
        # console.print(f"[blue]Columns in CSV: {list(tsv_data[0].keys())}")

        tsv_ids = {int(row.id) for row in tsv_data}
        updated_count = 0
        filter_mismatch_ids_in_tsv = []

        # Iterate through the CSV data
        for row_idx, tsv_row in enumerate(tsv_data, start=1):
            try:
                word_id = int(tsv_row.id)
                db_entry = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).filter(
                    DpdHeadword.id == word_id).first()

                if db_entry:
                    if not db_entry.sbs:
                        # Create SBS record if it doesn't exist
                        db_entry.sbs = SBS(id=word_id)
                        # console.print(f"[cyan]Created SBS record for ID: {word_id}")

                    if db_entry.sbs.sbs_class_anki == sbs_anki_class_filter:
                        db_entry.sbs.class_source = tsv_row.class_source
                        db_entry.sbs.class_example = tsv_row.class_example
                        db_entry.sbs.class_example_translation = tsv_row.english_translation
                        db_entry.sbs.class_extra = tsv_row.extra
                        updated_count += 1
                        # console.print(f"[green]Updated ID: {word_id}")
                    else:
                        filter_mismatch_ids_in_tsv.append(word_id)
                # else:
                    # console.print(f"[red]ID {word_id} from CSV not found in database.")
            except ValueError:
                console.print(f"[red]Invalid ID format in CSV row {row_idx}: {tsv_row.id}")
            except Exception as e:
                console.print(f"[red]Error processing CSV row {row_idx} (ID: {tsv_row.id}): {e}")

        console.print(f"[green]{updated_count} records updated from CSV.")
        if filter_mismatch_ids_in_tsv:
            console.print(f"[yellow]IDs in CSV where sbs_class_anki did not match {sbs_anki_class_filter}: {filter_mismatch_ids_in_tsv}")

        # Check for IDs in DB with matching sbs_anki_class_filter but not in CSV
        db_entries_with_filter = db_session.query(DpdHeadword).join(SBS).filter(
            SBS.sbs_class_anki == sbs_anki_class_filter).all()

        missing_from_tsv = [entry.id for entry in db_entries_with_filter if entry.id not in tsv_ids]
        if missing_from_tsv:
            console.print(f"[yellow]IDs in DB with sbs_class_anki == {sbs_anki_class_filter} but NOT found in CSV: {missing_from_tsv}")

        # db_session.commit()
        # console.print("[bold green]Changes committed to the database.")

    except Exception as e:
        console.print(f"[bold red]An error occurred: {e}")
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == "__main__":
    # Example usage:
    class_number = 1
    base_path = dpspth.pali_class_output_dir
    csv_path = os.path.join(base_path, "done", f"class_{class_number}_output done.csv")

    if not csv_path:
        console.print("[bold red]Please update 'csv_path' in the script with the actual path to your CSV file.")
    else:
        update_sbs_from_tsv_with_filter(csv_path, class_number)
