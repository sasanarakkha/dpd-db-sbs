#!/usr/bin/env python3

"""
Script to automatically clean up extra spaces in SBS source fields.
Fixes issues like 'SN35.28 ' -> 'SN35.28' and 'VIN 1.4.1.2' -> 'VIN1.4.1.2'.
Exceptions: Fields containing 'PAT', 'Sri Lanka', '(modif)', or '(simpl)' are exempt
from internal space removal, but trailing/leading spaces will still be stripped.
"""

from db.db_helpers import get_db_session
from db.models import SBS
from tools.paths import ProjectPaths
from tools.printer import printer as pr

SOURCE_FIELDS: list[str] = [
    "sbs_source_1",
    "sbs_source_2",
    "dhp_source",
    "pat_source",
    "vib_source",
    "class_source",
    "discourses_source",
]

EXEMPTS: list[str] = ["PAT", "Sri Lanka", "(modif)", "(simpl)"]


def main() -> None:
    pr.tic()
    pr.yellow_title("running sbs source cleanup")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    changed_count = 0
    sbs_data = db_session.query(SBS).all()

    for sbs in sbs_data:
        row_changed = False
        for field in SOURCE_FIELDS:
            val = getattr(sbs, field)
            if not val:
                continue

            new_val = val.strip()
            # If the value does not contain any of the exempt substrings, remove all spaces
            if not any(exempt in new_val for exempt in EXEMPTS):
                new_val = new_val.replace(" ", "")

            if val != new_val:
                setattr(sbs, field, new_val)
                row_changed = True
                pr.green(f"row {sbs.id} {field}: '{val}' -> '{new_val}'")

        if row_changed:
            changed_count += 1

    if changed_count > 0:
        db_session.commit()
        pr.yes(f"cleaned up {changed_count} rows")
    else:
        pr.yes("no source cleanup needed")
    pr.toc()


if __name__ == "__main__":
    main()
