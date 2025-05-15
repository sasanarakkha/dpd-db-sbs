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
    counter = 0
    with open(dpspth.ru_root_path, "r", newline="") as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                # Include 'root' in the data dictionary
                data[col_name] = value
            existing_record = (
                db_session.query(DpdRoot).filter_by(root=data["root"]).first()
            )
            if existing_record:
                for key, value in data.items():
                    setattr(existing_record, key, value)
            else:
                db_session.add(DpdRoot(**data))
            counter += 1
    pr.yes(counter)


if __name__ == "__main__":
    main()
