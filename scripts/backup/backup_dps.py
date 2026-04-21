#!/usr/bin/env python3

"""Save latest Russian, Tamil, SBS, and roots tables to backup_tsv folder."""

from git import Repo
import csv

from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import Russian, SBS, DpdRoot, Tamil
from tools.printer import printer as pr
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths


def backup_dps():
    pr.tic()
    pr.yellow_title("backing russian, sbs, and tamil tables to tsv")
    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)
    backup_ru(db_session, dpspth)
    backup_sbs(db_session, dpspth)
    backup_ta(db_session, dpspth)
    backup_roots_ru(db_session, dpspth)
    db_session.close()
    pr.toc()


def backup_ru(db_session: Session, dpspth: DPSPaths, custom_path: str = ""):
    """Backup Russian table to TSV."""
    pr.green_tmr("checking Russian table")

    # Query the Russian table
    db = db_session.query(Russian).all()

    # Check if the table is empty
    if not db:
        pr.red("Error: The Russian table is empty. Backup aborted.")
        return

    # Proceed with backup if the table is not empty
    pr.green_tmr("writing Russian table")

    # Use the custom path if provided, otherwise use the default path
    russian_path = custom_path if custom_path else dpspth.russian_path

    with open(russian_path, "w", newline="") as tsvfile:
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL
        )
        column_names = [column.name for column in Russian.__mapper__.columns]
        csvwriter.writerow(column_names)

        for i in db:
            row = [getattr(i, column.name) for column in Russian.__mapper__.columns]
            csvwriter.writerow(row)


def backup_sbs(db_session: Session, dpspth: DPSPaths, custom_path: str = ""):
    """Backup SBS tables to TSV."""
    pr.green_tmr("checking SBS table")

    # Query the SBS table
    db = db_session.query(SBS).all()

    # Check if the table is empty
    if not db:
        pr.red("Error: The SBS table is empty. Backup aborted.")
        return

    # Proceed with backup if the table is not empty
    pr.green_tmr("writing SBS table")

    # Use the custom path if provided, otherwise use the default path
    sbs_path = custom_path if custom_path else dpspth.sbs_path

    with open(sbs_path, "w", newline="") as tsvfile:
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL
        )
        column_names = [column.name for column in SBS.__mapper__.columns]
        csvwriter.writerow(column_names)

        for i in db:
            row = [getattr(i, column.name) for column in SBS.__mapper__.columns]
            csvwriter.writerow(row)


def backup_ta(db_session: Session, dpspth: DPSPaths, custom_path: str = ""):
    """Backup Tamil table to TSV."""
    pr.green_tmr("checking Tamil table")

    # Query the Tamil table
    db = db_session.query(Tamil).all()

    # Check if the table is empty
    if not db:
        pr.red("Error: The Tamil table is empty. Backup aborted.")
        return

    # Proceed with backup if the table is not empty
    pr.green_tmr("writing Tamil table")

    # Use the custom path if provided, otherwise use the default path
    tamil_path = custom_path if custom_path else dpspth.tamil_path

    with open(tamil_path, "w", newline="") as tsvfile:
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL
        )
        column_names = [column.name for column in Tamil.__mapper__.columns]
        csvwriter.writerow(column_names)

        for i in db:
            row = [getattr(i, column.name) for column in Tamil.__mapper__.columns]
            csvwriter.writerow(row)


def backup_roots_ru(db_session: Session, dpspth: DPSPaths, custom_path: str = ""):
    """Backup Ru columns from the DpdRoot to TSV."""
    pr.green_tmr("checking DpdRoot table")

    # Query DpdRoot table
    db = db_session.query(DpdRoot).all()

    # Check if the table is empty
    if not db:
        pr.red("Error: DpdRoot table is empty. Backup aborted.")
        return

    # Proceed with backup if the table is not empty
    pr.green_tmr("writing Ru columns from the DpdRoot table")

    # Check for rows where root.sanskrit_root is not "-" and root_sanskrit_root_ru_meaning is empty
    for record in db:
        if record.sanskrit_root != "-" and not record.sanskrit_root_ru_meaning:
            pr.red(f"No root_sanskrit_root_ru_meaning: {record}")
        if not record.root_ru_meaning:
            pr.red(f"No root_ru_meaning: {record}")

    # Use the custom path if provided, otherwise use the default path
    ru_root_path = custom_path if custom_path else dpspth.ru_root_path

    with open(ru_root_path, "w", newline="") as tsvfile:
        used_columns = ["root", "root_ru_meaning", "sanskrit_root_ru_meaning"]
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL
        )
        column_names = [
            column.name
            for column in DpdRoot.__mapper__.columns
            if column.name in used_columns
        ]
        csvwriter.writerow(column_names)

        for i in db:
            row = [
                getattr(i, column.name)
                for column in DpdRoot.__mapper__.columns
                if column.name in used_columns
            ]
            csvwriter.writerow(row)


def git_commit_dps():
    repo = Repo("./")
    index = repo.index
    index.add(
        [
            "db/backup_tsv/russian.tsv",
            "db/backup_tsv/sbs.tsv",
            "db/backup_tsv/ru_roots.tsv",
        ]
    )
    index.commit("backup russian & sbs")


if __name__ == "__main__":
    backup_dps()
