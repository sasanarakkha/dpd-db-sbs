#!/usr/bin/env python3

import csv
import sys
import termios
import tty

from sqlalchemy.orm import joinedload

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr
from tools.tsv_read_write import dotdict


def get_char() -> str:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def _has_meaning_diff(csv_row: dotdict, current_meaning: str) -> bool:
    return bool(
        csv_row.corrections_ru_meaning
        and csv_row.corrections_ru_meaning.strip() != current_meaning
    )


def _has_lit_diff(csv_row: dotdict, current_meaning_lit: str) -> bool:
    return bool(
        csv_row.corrections_ru_meaning_lit
        and csv_row.corrections_ru_meaning_lit.strip() != current_meaning_lit
    )


def _auto_update_meaning(csv_row: dotdict, current_meaning: str) -> tuple[str, bool]:
    if (not current_meaning or not current_meaning.strip()) and (
        csv_row.corrections_ru_meaning and csv_row.corrections_ru_meaning.strip()
    ):
        return csv_row.corrections_ru_meaning.strip(), True
    return current_meaning, False


def main() -> None:
    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)
    csv_path = dpspth.ru_apply_path

    pr.amber(f"Updating db from {csv_path}")

    with open(csv_path, "r", encoding="utf-8") as f:
        sample = f.read(2048)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = "\t"

    csv_data: list[dotdict] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            csv_data.append(dotdict(row))

    pr.cyan(f"Delimiter detected: {delimiter!r}")
    if csv_data:
        pr.cyan(f"First entry after headings in the csv: {csv_data[0]}")
    pr.cyan(f"Total number of rows in the file: {len(csv_data)}")
    input("Press enter to continue: ")

    pending_items: list[tuple[dotdict, DpdHeadword]] = []
    count_auto_updated: int = 0

    for csv_row in csv_data:
        if csv_row.get("processed") == "ok":
            continue

        db_entry = (
            db_session.query(DpdHeadword)
            .options(joinedload(DpdHeadword.ru))
            .filter(DpdHeadword.id == csv_row.id)
            .first()
        )
        if db_entry and db_entry.ru:
            new_meaning, auto_updated = _auto_update_meaning(
                csv_row, db_entry.ru.ru_meaning
            )
            if auto_updated:
                db_entry.ru.ru_meaning = new_meaning
                count_auto_updated += 1

            has_diff_m = _has_meaning_diff(csv_row, db_entry.ru.ru_meaning)
            has_diff_l = _has_lit_diff(csv_row, db_entry.ru.ru_meaning_lit)

            if auto_updated and not has_diff_m and not has_diff_l:
                csv_row.processed = "ok"
                continue

            if has_diff_m or has_diff_l:
                pending_items.append((csv_row, db_entry))

    pending_items.sort(key=lambda x: x[1].pos)

    pr.cyan(f"Total unique suggestions to review: {len(pending_items)}")
    pr.cyan(f"Total automatically updated: {count_auto_updated}")

    count_meanings: int = 0
    count_lit: int = 0

    for idx, (csv_row, db_entry) in enumerate(pending_items):
        pr.white("-" * 20)
        pr.cyan(f"Suggestions left: {len(pending_items) - idx}")
        pr.amber(
            f"ID: {csv_row.id} | Pali: {db_entry.lemma_1} |  "
            f"POS: {db_entry.pos} | Meaning_1: {db_entry.meaning_1}"
        )
        pr.cyan(f"  Current RU Meaning: {db_entry.ru.ru_meaning}")
        if csv_row.corrections_ru_meaning != db_entry.ru.ru_meaning:
            pr.green(f"Suggested RU Meaning: {csv_row.corrections_ru_meaning}")
        else:
            pr.green("Suggested RU Meaning:")
        pr.cyan(f"  Current RU Meaning Lit: {db_entry.ru.ru_meaning_lit}")
        if csv_row.corrections_ru_meaning_lit != db_entry.ru.ru_meaning_lit:
            pr.green(f"Suggested RU Meaning Lit: {csv_row.corrections_ru_meaning_lit}")
        else:
            pr.green("Suggested RU Meaning Lit:")
        if csv_row.get("notes"):
            pr.green(f"Suggested Notes: {csv_row.notes}")

        pr.white(
            "Enter (both), 1 (skip), 2 (meaning), 3 (lit), "
            "4 (man meaning), 5 (man lit), q (quit): "
        )
        response = get_char()
        pr.white(response)

        if response in ("\r", "\n"):
            response = ""
        elif response == "q":
            pr.amber("Quitting loop...")
            break

        csv_row.processed = "ok"

        if response == "1":
            pr.amber("Skipping...")
            continue
        elif response == "2":
            if (
                csv_row.corrections_ru_meaning
                and csv_row.corrections_ru_meaning.strip()
            ):
                db_entry.ru.ru_meaning = csv_row.corrections_ru_meaning.strip()
                count_meanings += 1
                pr.green("Updated ru_meaning from suggestion")

                man_lit = input("input manual ru_meaning_lit (enter to skip) ")
                if man_lit:
                    db_entry.ru.ru_meaning_lit = man_lit.strip()
                    count_lit += 1
                    pr.green("Updated ru_meaning_lit manually")
            else:
                pr.red("Suggested ru_meaning is empty, not updating.")
        elif response == "3":
            if (
                csv_row.corrections_ru_meaning_lit
                and csv_row.corrections_ru_meaning_lit.strip()
            ):
                db_entry.ru.ru_meaning_lit = csv_row.corrections_ru_meaning_lit.strip()
                count_lit += 1
                pr.green("Updated ru_meaning_lit from suggestion")

                user_m = input("input manual ru_meaning (enter to skip) ")
                if user_m:
                    db_entry.ru.ru_meaning = user_m.strip()
                    count_meanings += 1
                    pr.green("Updated ru_meaning manually")
            else:
                pr.red("Suggested ru_meaning_lit is empty, not updating.")
        elif response == "4":
            user_m = input("user ru_meaning: ").strip()
            if user_m:
                db_entry.ru.ru_meaning = user_m
                count_meanings += 1
                pr.green("Updated ru_meaning manually")
        elif response == "5":
            user_lit = input("user ru_meaning_lit: ").strip()
            if user_lit:
                db_entry.ru.ru_meaning_lit = user_lit
                count_lit += 1
                pr.green("Updated ru_meaning_lit manually")
        elif response == "":
            updated = False
            if (
                csv_row.corrections_ru_meaning
                and csv_row.corrections_ru_meaning.strip()
            ):
                db_entry.ru.ru_meaning = csv_row.corrections_ru_meaning.strip()
                count_meanings += 1
                updated = True
            if (
                csv_row.corrections_ru_meaning_lit
                and csv_row.corrections_ru_meaning_lit.strip()
            ):
                db_entry.ru.ru_meaning_lit = csv_row.corrections_ru_meaning_lit.strip()
                count_lit += 1
                updated = True

            if updated:
                pr.green("Updated (where suggested)")
            else:
                pr.amber("Nothing to update (suggestions were empty)")
        else:
            pr.red("Invalid input, skipping...")

    db_session.commit()

    if csv_data:
        fieldnames = list(csv_data[0].keys())
        if "processed" not in fieldnames:
            fieldnames.append("processed")

        for csv_row in csv_data:
            if "processed" not in csv_row:
                csv_row.processed = ""

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(csv_data)

    db_session.close()

    pr.green("Database update process completed.")
    pr.green(f"Number of updated ru_meanings: {count_meanings}")
    pr.green(f"Number of updated ru_meaning_lit: {count_lit}")


if __name__ == "__main__":
    main()
