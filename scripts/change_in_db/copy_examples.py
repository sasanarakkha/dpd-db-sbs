#!/usr/bin/env python3

"""
Filter the database on a specified column by a given value, then update another specified column with a provided value.
"""

import re

from sqlalchemy import and_, or_, not_
from sqlalchemy.orm import joinedload

from db.models import DpdHeadword, SBS
from tools.paths import ProjectPaths
from db.db_helpers import get_db_session
from tools.printer import printer as pr

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def update_column_for_some_criteria(
    source_value: str,
    value_to_update: str,
    modifier_column_to_copy: str,
    dry_run: bool = False,
) -> None:
    rows_already_have = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.sbs))
        .outerjoin(SBS)
        .filter(
            or_(
                SBS.vib_source == source_value,
            ),
        )
        .all()
    )

    ids_already_have = [row.id for row in rows_already_have]

    # Query the database to find the rows that match the conditions
    rows_to_update_sbs_query = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.sbs))
        .outerjoin(SBS)
        .filter(
            or_(
                SBS.sbs_source_1 == source_value,
                SBS.sbs_source_2 == source_value,
                # SBS.sbs_source_3 == source_value,
                # SBS.sbs_source_4 == source_value,
            ),
        )
    )

    if ids_already_have:
        rows_to_update_sbs_query = rows_to_update_sbs_query.filter(
            not_(DpdHeadword.id.in_(ids_already_have))
        )

    rows_to_update_sbs = rows_to_update_sbs_query.all()

    # Get the IDs of rows_to_update_sbs
    ids_to_exclude = [row.id for row in rows_to_update_sbs] + ids_already_have

    rows_to_update_query = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.sbs))
        .outerjoin(SBS)
        .filter(
            and_(
                DpdHeadword.meaning_1 != "",
                or_(
                    DpdHeadword.source_1 == source_value,
                    DpdHeadword.source_2 == source_value,
                ),
            ),
        )
    )

    if ids_to_exclude:
        rows_to_update_query = rows_to_update_query.filter(
            not_(DpdHeadword.id.in_(ids_to_exclude))
        )

    rows_to_update = rows_to_update_query.all()

    count_changed = 0
    count_changed_sbs = 0
    count_added = 0

    if rows_already_have:
        pr.green(
            f"Total rows already have {value_to_update}_source: {len(rows_already_have)}:"
        )

        for __word__ in rows_already_have:
            pr.amber(f"{__word__.id} {__word__.lemma_1}")

    if rows_to_update_sbs:
        pr.green(f"Found in sbs_source(s): {len(rows_to_update_sbs)}")

        for __word__ in rows_to_update_sbs:
            changed = False
            # Check for source_value in sbs_source fields
            for idx in range(1, 3):  # Assuming there are 2 positions
                sbs_source_value = getattr(__word__.sbs, f"sbs_source_{idx}")
                if sbs_source_value and re.search(source_value, sbs_source_value):
                    # Copy values to pat fields
                    for field_prefix in ["source", "sutta", "example"]:
                        sbs_value = getattr(__word__.sbs, f"sbs_{field_prefix}_{idx}")
                        setattr(
                            __word__.sbs,
                            f"{modifier_column_to_copy}_{field_prefix}",
                            sbs_value,
                        )
                    changed = True
                    break
            
            if changed:
                pr.cyan(f"Updated from sbs_source: {__word__.id} {__word__.lemma_1}")
                count_changed_sbs += 1

    if rows_to_update:
        pr.green(f"Found in dpd_source(s): {len(rows_to_update)}")

        for __word__ in rows_to_update:
            if not __word__.sbs:
                # If SBS row does not exist, create a new one
                __word__.sbs = SBS(id=__word__.id)
                added = False
                # Check for source_value in source fields
                for idx in range(1, 3):  # Assuming there are 2 positions
                    dpd_source_value = getattr(__word__, f"source_{idx}")
                    if dpd_source_value and re.search(source_value, dpd_source_value):
                        # Copy values to pat fields
                        for field_prefix in ["source", "sutta", "example"]:
                            dpd_value = getattr(__word__, f"{field_prefix}_{idx}")
                            setattr(
                                __word__.sbs,
                                f"{modifier_column_to_copy}_{field_prefix}",
                                dpd_value,
                            )
                        added = True
                        break
                
                if added:
                    pr.cyan(f"Added new row & copied from dpd_source: {__word__.id} {__word__.lemma_1}")
                    count_added += 1
            else:
                changed = False
                # Check for source_value in source fields
                for idx in range(1, 3):  # Assuming there are 2 positions
                    dpd_source_value = getattr(__word__, f"source_{idx}")
                    if dpd_source_value and re.search(source_value, dpd_source_value):
                        # Copy values to pat fields
                        for field_prefix in ["source", "sutta", "example"]:
                            dpd_value = getattr(__word__, f"{field_prefix}_{idx}")
                            setattr(
                                __word__.sbs,
                                f"{modifier_column_to_copy}_{field_prefix}",
                                dpd_value,
                            )
                        changed = True
                        break
                
                if changed:
                    pr.cyan(f"Updated from dpd_source: {__word__.id} {__word__.lemma_1}")
                    count_changed += 1

    pr.cyan("")
    if rows_already_have:
        pr.green(f"Total already have: {len(rows_already_have)}")
    if count_changed:
        pr.green(f"Total copied from dpd_source(s): {count_changed}")
    if count_changed_sbs:
        pr.green(f"Total copied from sbs_source(s): {count_changed_sbs}")
    if count_added:
        pr.green(f"Total added new row(s): {count_added}")
    pr.cyan("")
    pr.yes(f"finished for {source_value}")

    if not dry_run:
        db_session.commit()
    else:
        pr.amber("DRY RUN — no changes written to database")


if __name__ == "__main__":
    # !To use the functions:
    source_value = "VIN2.5.7.5"

    value_to_update = "vib"
    modifier_column_to_copy = "vib"

    update_column_for_some_criteria(
        source_value, value_to_update, modifier_column_to_copy
    )
