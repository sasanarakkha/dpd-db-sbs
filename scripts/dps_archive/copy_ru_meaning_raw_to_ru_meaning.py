#!/usr/bin/env python3

"""
Copies ru_meaning_raw to ru_meaning for words from an ID list
if ru_meaning_raw is not empty and differs from ru_meaning.
"""

import csv
from pathlib import Path

from sqlalchemy.orm import Session, joinedload

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr

_LITERAL_SEP = "; досл."
_CHUNK_SIZE = 500


def read_ids_from_tsv(file_path: Path) -> list[int]:
    with open(file_path, mode="r", encoding="utf-8-sig") as tsv_file:
        tsv_reader = csv.reader(tsv_file, delimiter="\t")
        next(tsv_reader)  # Skip header row
        return [int(row[0]) for row in tsv_reader]


def copy_raw_to_meaning(db_session: Session, unique_ids: list[int]) -> int:
    updated_count = 0
    total_ids = len(unique_ids)

    pr.green(f"Processing {total_ids} unique IDs...")

    for i in range(0, total_ids, _CHUNK_SIZE):
        chunk = unique_ids[i : i + _CHUNK_SIZE]
        words = (
            db_session.query(DpdHeadword)
            .options(joinedload(DpdHeadword.ru))
            .filter(DpdHeadword.id.in_(chunk))
            .all()
        )

        for word in words:
            if not (word.ru and word.ru.ru_meaning_raw):
                continue
            raw = word.ru.ru_meaning_raw
            if (
                not word.ru.ru_meaning
                and not word.ru.ru_meaning_lit
                and _LITERAL_SEP in raw
            ):
                parts = raw.split(_LITERAL_SEP, 1)
                word.ru.ru_meaning = parts[0].strip()
                word.ru.ru_meaning_lit = parts[1].strip()
                pr.white(
                    f"Splitting ID {word.id}: main='{parts[0].strip()}'"
                    f" | lit='{parts[1].strip()}'"
                )
                updated_count += 1
            elif not word.ru.ru_meaning:
                pr.green(f"Updating ID {word.id} (raw copy): '{raw}'")
                word.ru.ru_meaning = raw
                updated_count += 1

        pr.green(f"{min(i + _CHUNK_SIZE, total_ids)}/{total_ids} processed...")

    if updated_count > 0:
        pr.amber(f"Found {updated_count} potential changes.")
        confirm = input(
            "Proceed with committing these changes to the database? (yes/no): "
        )
        if confirm.lower() == "yes":
            try:
                pr.green(f"Committing {updated_count} changes...")
                db_session.commit()
                pr.green("Changes committed successfully.")
            except Exception as e:
                pr.red(f"Error during commit: {e}")
                db_session.rollback()
                pr.red("Changes rolled back.")
        else:
            pr.red("Commit cancelled by user.")
            db_session.rollback()
            pr.red("Changes rolled back.")
    else:
        pr.green("No changes needed.")

    pr.green(f"Processed {total_ids} IDs. Updated {updated_count} ru_meaning fields.")
    return updated_count


def main() -> None:
    pr.tic()
    pr.green("Copying ru_meaning_raw to ru_meaning for words from ID list")

    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)

    try:
        id_file_path = dpspth.id_to_add_path
        pr.green(f"Reading IDs from: {id_file_path}")
        ordered_ids = read_ids_from_tsv(id_file_path)
        unique_ids = list(dict.fromkeys(ordered_ids))
        pr.green(f"Found {len(unique_ids)} unique IDs to process.")

        if unique_ids:
            copy_raw_to_meaning(db_session, unique_ids)
        else:
            pr.green("No unique IDs found in the file.")

    except FileNotFoundError:
        pr.red(f"Error: ID file not found at {dpspth.id_to_add_path}")
    except Exception as e:
        pr.red(f"An unexpected error occurred: {e}")
        db_session.rollback()
    finally:
        db_session.close()
        pr.green("Database session closed.")

    pr.toc()


if __name__ == "__main__":
    main()
