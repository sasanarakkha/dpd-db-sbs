#!/usr/bin/env python3

"""Rebuild the database from scratch from files in backup_tsv folder."""

import csv
import sys
from tools.duplicates import has_duplicate_values_in_column

from rich import print

from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.db_helpers import create_db_if_not_exists
from db.models import DpdHeadword, DpdRoot, Russian, SBS
from tools.printer import printer as pr
from tools.paths import ProjectPaths
from tools.configger import config_update, config_test


def main():
    pr.tic()
    pr.title("rebuilding db from tsvs")

    if config_test("regenerate", "db_rebuild", "no"):
        config_update("regenerate", "db_rebuild", "yes")

    pth = ProjectPaths()

    if pth.dpd_db_path.exists():
        print("[red]this will destroy your current database!")
        # response = input("are you sure you would like to rebuild the db? [y/n] ")
        # if response != "y":
        #     return
        # else:
        pth.dpd_db_path.unlink()

    create_db_if_not_exists(pth.dpd_db_path)

    # Define TSV files and their ID columns to check for duplicates
    tsvs_to_check = [
        {"path": pth.pali_word_path, "id_col": "id"},
        {"path": pth.pali_root_path, "id_col": "root"}, 
        {"path": pth.russian_path, "id_col": "id"},
        {"path": pth.sbs_path, "id_col": "id"},
        {"path": pth.ru_root_path, "id_col": "root"}
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

    make_pali_word_table_data(pth, db_session)
    make_pali_root_table_data(pth, db_session)
    make_russian_table_data(pth, db_session)
    make_sbs_table_data(pth, db_session)
    make_ru_root_table_data(pth, db_session)

    pr.green("committing to db")
    db_session.commit()
    db_session.close()
    pr.yes("ok")
    pr.green_title("database restored successfully")
    pr.toc()


def make_pali_word_table_data(pth: ProjectPaths, db_session: Session):
    """Read TSV and return DpdHeadword table data."""

    pr.green("creating DpdHeadword table data")
    counter = 0
    with open(pth.pali_word_path, "r", newline="") as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in ("user_id", "created_at", "updated_at"):
                    data[col_name] = value
            db_session.add(DpdHeadword(**data))
            counter += 1
    pr.yes(counter)


def make_pali_root_table_data(pth: ProjectPaths, db_session: Session):
    """Read TSV and return DpdRoot table data."""
    pr.green("creating DpdRoot table data")
    counter = 0
    with open(pth.pali_root_path, "r", newline="") as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in (
                    "created_at",
                    "updated_at",
                    "root_info",
                    "root_matrix",
                    "root_ru_meaning",
                    "sanskrit_root_ru_meaning",
                ):
                    data[col_name] = value
            db_session.add(DpdRoot(**data))
            counter += 1
    pr.yes(counter)


def make_russian_table_data(pth: ProjectPaths, db_session: Session):
    """Read TSV and return Russian table data."""
    pr.green("creating Russian table data")
    counter = 0
    with open(pth.russian_path, "r", newline="") as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            db_session.add(Russian(**data))
            counter += 1
    pr.yes(counter)


def make_sbs_table_data(pth: ProjectPaths, db_session: Session):
    """Read TSV and return SBS table data."""
    pr.green("creating SBS table data")
    counter = 0
    with open(pth.sbs_path, "r", newline="") as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            db_session.add(SBS(**data))
            counter += 1
    pr.yes(counter)


def make_ru_root_table_data(pth: ProjectPaths, db_session: Session):
    """Read TSV and return ru columns from DpdRoot."""
    pr.green("filling ru in DpdRoot table")
    counter = 0
    with open(pth.ru_root_path, "r", newline="") as tsvfile:
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
