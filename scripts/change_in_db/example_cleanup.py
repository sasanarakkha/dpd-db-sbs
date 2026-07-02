#!/usr/bin/env python3

"""Script to auto-fix 5 categories of errors in SBS example fields."""

import argparse
import re
from typing import Final

from db.db_helpers import get_db_session
from db.models import SBS
from tools.paths import ProjectPaths
from tools.printer import printer as pr

EXAMPLE_FIELDS: Final[tuple[str, ...]] = (
    "sbs_example_1",
    "sbs_example_2",
    "dhp_example",
    "pat_example",
    "vib_example",
    "class_example",
    "discourses_example",
)


def clean_example(text: str) -> str:
    """Clean up a single example text by stripping whitespace, removing double spaces,
    fixing punctuation spacing, and lowercasing English capital letters."""
    if not text:
        return ""
    new_val = text.strip()
    new_val = re.sub(r"  +", " ", new_val)
    new_val = re.sub(r" ,", ",", new_val)
    new_val = re.sub(r" \.", ".", new_val)
    new_val = re.sub(r"[A-Z]", lambda m: m.group().lower(), new_val)
    return new_val


def main(dry_run: bool = False) -> None:
    pr.tic()
    pr.yellow_title("running sbs example cleanup")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    changed_count: int = 0
    sbs_data: list[SBS] = db_session.query(SBS).all()

    for sbs in sbs_data:
        row_changed: bool = False
        for field in EXAMPLE_FIELDS:
            val: str | None = getattr(sbs, field)
            if not val:
                continue

            new_val = clean_example(val)

            if val != new_val:
                if not dry_run:
                    setattr(sbs, field, new_val)
                row_changed = True
                pr.green(f"row {sbs.id} {field}: '{val}' -> '{new_val}'")

        if row_changed:
            changed_count += 1

    if changed_count > 0:
        if not dry_run:
            db_session.commit()
        pr.yes(f"cleaned up {changed_count} rows")
    else:
        pr.yes("no example cleanup needed")
    db_session.close()
    pr.toc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up SBS example fields.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Log changes without committing"
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run)
