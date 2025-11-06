#!/usr/bin/env python3

"""Rebuild the database from scratch from files in backup_tsv folder."""

import csv
import sys
from typing import Iterator, List, Tuple
from tools.duplicates import has_duplicate_values_in_column
from db.models import DpdHeadword
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdRoot, Russian, SBS
from tools.printer import printer as pr
from tools.paths import ProjectPaths
from pathlib import Path
from tools.paths_dps import DPSPaths


def main():
    pr.tic()
    pr.title("populating ru sbs tables from tsvs")

    pth = ProjectPaths()
    dpspth = DPSPaths()

    # Define TSV files and their ID columns to check for duplicates
    tsvs_to_check = [
        {"path": dpspth.russian_path, "id_col": "id"},
        {"path": dpspth.sbs_path, "id_col": "id"},
        {"path": dpspth.ru_root_path, "id_col": "root"}
    ]

    # Check each TSV for duplicates before processing
    for tsv_info in tsvs_to_check:
        if not tsv_info["path"].exists():
            pr.red(f"TSV backup file does not exist: {tsv_info['path']}")
            sys.exit(1)
        
        has_dupes, dupes_list, dupes_lines = has_duplicate_values_in_column(
            tsv_path=tsv_info["path"],
            column_name=tsv_info["id_col"]
        )
        if has_dupes:
            pr.red(f"Duplicate values found in '{tsv_info['path']}' (column: '{tsv_info['id_col']}'):")
            for val in dupes_list:
                lines = ", ".join(map(str, dupes_lines[val]))
                pr.red(f"  - Value: '{val}' found on lines: {lines}")
            pr.red("Please fix the TSV file and try again.")
            sys.exit(1)
        else:
            pr.yes

    # Check that all IDs in russian_path and sbs_path exist in pali_word_path
    db_session = get_db_session(pth.dpd_db_path)
    pali_word_ids_query = db_session.query(DpdHeadword.id).all()
    pali_word_ids = {str(id_tuple[0]) for id_tuple in pali_word_ids_query}

    # --- SBS: print missing, ask, remove if yes ---
    sbs_missing_rows = []
    sbs_rows = []
    with open(dpspth.sbs_path, "r", newline="") as f:
        reader = csv.reader(f, delimiter="\t", quotechar='"')
        sbs_columns = next(reader)
        sbs_rows.append(sbs_columns)
        for row in reader:
            sbs_rows.append(row)
            tsv_id = row[0]
            if tsv_id not in pali_word_ids:
                sbs_missing_rows.append(row)

    if sbs_missing_rows:
        pr.red("IDs in SBS TSV not found in pali_word_path:")
        for row in sbs_missing_rows:
            pr.red("  - " + "\t".join(row))
        answer = input("Can we remove them? (y/n): ").strip().lower()
        if answer == "y":
            # Remove missing rows from SBS TSV
            new_sbs_rows = [row for row in sbs_rows[1:] if row[0] in pali_word_ids]
            with open(dpspth.sbs_path, "w", newline="") as f:
                csvwriter = csv.writer(
                    f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL
                )
                csvwriter.writerow(sbs_columns)
                for row in new_sbs_rows:
                    csvwriter.writerow(row)
            pr.green("Removed unused IDs from SBS TSV.")
        else:
            pr.red("Aborted by user.")
            sys.exit(1)

    # --- Russian: print missing, remove silently ---
    russian_missing_rows = []
    russian_rows = []
    with open(dpspth.russian_path, "r", newline="") as f:
        reader = csv.reader(f, delimiter="\t", quotechar='"')
        ru_columns = next(reader)
        russian_rows.append(ru_columns)
        for row in reader:
            if row[0] in pali_word_ids:
                russian_rows.append(row)
            else:
                russian_missing_rows.append(row)
    if russian_missing_rows:
        pr.red("IDs in Russian TSV not found in pali_word_path:")
        for row in russian_missing_rows:
            pr.red("  - " + "\t".join(row))
    with open(dpspth.russian_path, "w", newline="") as f:
        csvwriter = csv.writer(
            f, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL
        )
        csvwriter.writerows(russian_rows)

    # Re-read the cleaned data for processing
    db_session = get_db_session(pth.dpd_db_path)

    make_russian_table_data(dpspth, db_session)
    make_sbs_table_data(dpspth, db_session)
    make_ru_root_table_data(dpspth, db_session)

    pr.green("committing to db")
    db_session.commit()
    db_session.close()
    pr.yes("ok")
    pr.green_title("database restored successfully")
    pr.toc()


def get_tsv_files(original_path: Path, base_filename: str) -> List[Path]:
    """Get list of TSV files to process, handling both split and single file formats."""

    backup_dir = original_path.parent

    # Check for split files (e.g., dpd_headwords_part_*.tsv)
    split_pattern = f"{base_filename}_part_*.tsv"
    split_files = sorted(backup_dir.glob(split_pattern))

    if split_files:
        pr.green(f"Found {len(split_files)} split {base_filename} files")
        return split_files

    # Fall back to single file format
    single_file = backup_dir / f"{base_filename}.tsv"
    if single_file.exists():
        pr.green(f"Found single {base_filename} file")
        return [single_file]

    return []


def read_tsv_files(file_paths: List[Path]) -> Iterator[Tuple[List[str], List[str]]]:
    """Read TSV files and yield (columns, row) tuples.

    Handles split files where only the first file has headers.
    """
    if not file_paths:
        return

    columns = None

    for file_idx, file_path in enumerate(file_paths):
        pr.green(f"Reading {file_path.name}")

        with open(file_path, "r", newline="") as tsv_file:
            csvreader = csv.reader(tsv_file, delimiter="\t", quotechar='"')

            # Read headers from first file only
            if file_idx == 0:
                columns = next(csvreader)
            else:
                # Skip headers for subsequent files
                next(csvreader)

            # Yield all data rows
            for row in csvreader:
                if columns:
                    yield columns, row


def make_russian_table_data(dpspth: DPSPaths, db_session: Session):
    """Read TSV and return Russian table data."""
    pr.green("creating Russian table data")
    counter = 0
    russian_files = get_tsv_files(dpspth.russian_path, "russian")
    for columns, row in read_tsv_files(russian_files):
        # Filter out empty keys that might come from empty column headers
        data = {k: v for k, v in zip(columns, row) if k}
        db_session.add(Russian(**data))
        counter += 1
    pr.yes(counter)


def make_sbs_table_data(dpspth: DPSPaths, db_session: Session):
    """Read TSV and return SBS table data."""
    pr.green("creating SBS table data")
    counter = 0
    sbs_files = get_tsv_files(dpspth.sbs_path, "sbs")
    for columns, row in read_tsv_files(sbs_files):
        # Filter out empty keys that might come from empty column headers
        data = {k: v for k, v in zip(columns, row) if k}
        db_session.add(SBS(**data))
        counter += 1
    pr.yes(counter)


def make_ru_root_table_data(dpspth: DPSPaths, db_session: Session):
    """Read TSV and return ru columns from DpdRoot."""
    pr.green("filling ru in DpdRoot table")
    updated_counter = 0
    not_found_in_db_counter = 0
    
    # Keep track of roots found in the TSV file
    roots_in_tsv = set()

    ru_root_files = get_tsv_files(dpspth.ru_root_path, "ru_roots")
    for columns, row in read_tsv_files(ru_root_files):
        data = dict(zip(columns, row))
        roots_in_tsv.add(data["root"])
        
        existing_record = db_session.query(DpdRoot).filter_by(root=data["root"]).first()
        if existing_record:
            for key, value in data.items():
                setattr(existing_record, key, value)
            updated_counter += 1
        else:
            pr.red(f"Root '{data['root']}' from TSV not found in DpdRoot table.")
            not_found_in_db_counter += 1

    # Check for roots in DB not present in TSV
    all_db_roots = db_session.query(DpdRoot.root).all()
    db_roots_set = {r[0] for r in all_db_roots}
    
    roots_in_db_not_in_tsv = db_roots_set - roots_in_tsv
    if roots_in_db_not_in_tsv:
        pr.green("Roots in DpdRoot table not found in TSV (no update performed for these):")
        for root_val in sorted(list(roots_in_db_not_in_tsv)): # Sort for consistent output
            pr.white(f"  - {root_val}")

    pr.yes(f"Updated: {updated_counter}")
    if not_found_in_db_counter > 0:
        pr.no(f"Not found in DB: {not_found_in_db_counter}")
    if roots_in_db_not_in_tsv:
        pr.cyan(f"In DB but not TSV: {len(roots_in_db_not_in_tsv)}")


if __name__ == "__main__":
    main()
