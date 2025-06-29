#!/usr/bin/env python3

"""Rebuild the database from scratch from files in backup_tsv folder."""

import csv
import sys
from tools.duplicates import has_duplicate_values_in_column

from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdRoot, Russian, SBS
from tools.printer import printer as pr
from tools.paths import ProjectPaths
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
    pali_word_ids = set()
    with open(pth.pali_word_path, "r", newline="") as f:
        reader = csv.reader(f, delimiter="\t", quotechar='"')
        id_col_idx = 0  # assuming first column is id
        for row in reader:
            pali_word_ids.add(row[id_col_idx])

    for tsv_info in [
        {"path": dpspth.russian_path, "label": "Russian"},
        {"path": dpspth.sbs_path, "label": "SBS"}
    ]:
        missing_ids = []
        with open(tsv_info["path"], "r", newline="") as f:
            reader = csv.reader(f, delimiter="\t", quotechar='"')
            id_col_idx = 0  # assuming first column is id
            for row in reader:
                tsv_id = row[id_col_idx]
                if tsv_id not in pali_word_ids:
                    missing_ids.append(tsv_id)
        if missing_ids:
            pr.red(f"IDs in {tsv_info['label']} TSV not found in pali_word_path:")
            for mid in missing_ids:
                pr.red(f"  - {mid}")
            pr.red("Please fix the TSV file(s) and try again.")
            sys.exit(1)

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


def make_russian_table_data(dpspth: DPSPaths, db_session: Session):
    """Read TSV and return Russian table data."""
    pr.green("creating Russian table data")
    counter = 0
    with open(dpspth.russian_path, "r", newline="") as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            db_session.add(Russian(**data))
            counter += 1
    pr.yes(counter)


def make_sbs_table_data(dpspth: DPSPaths, db_session: Session):
    """Read TSV and return SBS table data."""
    pr.green("creating SBS table data")
    counter = 0
    with open(dpspth.sbs_path, "r", newline="") as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
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

    with open(dpspth.ru_root_path, "r", newline="") as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            
            roots_in_tsv.add(data["root"])
            
            existing_record = (
                db_session.query(DpdRoot).filter_by(root=data["root"]).first()
            )
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
