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

from rich.console import Console

console = Console()

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def update_column_for_some_criteria(source_value, column_to_update, value_to_update, modifier_column_to_copy):
    # Query the database to find the rows that match the conditions
    rows_to_update_sbs = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).outerjoin(SBS).filter(
            or_(
                SBS.sbs_source_1 == source_value,
                SBS.sbs_source_2 == source_value,
                SBS.sbs_source_3 == source_value,
                SBS.sbs_source_4 == source_value,
            ),
    ).all()

    # Get the IDs of rows_to_update_sbs
    ids_to_exclude = [row.id for row in rows_to_update_sbs]


    rows_to_update = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).outerjoin(SBS).filter(
            and_(
                not_(DpdHeadword.id.in_(ids_to_exclude)),
                or_(
                    DpdHeadword.source_1 == source_value,
                    DpdHeadword.source_2 == source_value,
                ),
            ),
    ).all()

    count_changed = 0
    count_changed_sbs = 0
    count_added = 0
    count_already_have = 0

    console.print(f"[bold bright_green]Total rows fit criteria sbs: {len(rows_to_update_sbs)} : ")

    for __word__ in rows_to_update_sbs:
        # old_value = __word__.sbs.sbs_patimokkha
        old_value = getattr(__word__.sbs, column_to_update)
        if not old_value:
            # __word__.sbs.sbs_patimokkha = "vib"
            setattr(__word__.sbs, column_to_update, value_to_update)

            console.print(f"[bold bright_yellow]{__word__.id} {__word__.lemma_1} {value_to_update}")

            # Check for source_value in sbs_source fields
            for idx in range(1, 5):  # Assuming there are 4 positions
                sbs_source_value = getattr(__word__.sbs, f"sbs_source_{idx}")
                if sbs_source_value and re.search(source_value, sbs_source_value):
                    # Copy values to pat fields
                    for field_prefix in ['source', 'sutta', 'example']:
                        sbs_value = getattr(__word__.sbs, f"sbs_{field_prefix}_{idx}")
                        setattr(__word__.sbs, f"{modifier_column_to_copy}_{field_prefix}", sbs_value)
                        print(f"{__word__.id} {sbs_value}")
                    break

            count_changed_sbs += 1
        else:
            console.print(f"[bright_yellow] already {old_value} for {__word__.id} {__word__.lemma_1} ")
            count_already_have += 1

    console.print(f"[bold bright_green]Total rows fit criteria dpd: {len(rows_to_update)} : ")

    for __word__ in rows_to_update:
        # value_with_dash = f"{value_to_update}_"
        if not __word__.sbs:
            # If SBS row does not exist, create a new one
            # __word__.sbs = SBS(id=__word__.id, sbs_patimokkha="vib_")
            __word__.sbs = SBS(id=__word__.id)
            setattr(__word__.sbs, column_to_update, value_to_update)
            console.print(f"[bold bright_yellow]Added {__word__.id} {__word__.lemma_1} {value_to_update}")
            count_added += 1
            # Check for source_value in source fields
            for idx in range(1, 3):  # Assuming there are 2 positions
                dpd_source_value = getattr(__word__, f"source_{idx}")
                if dpd_source_value and re.search(source_value, dpd_source_value):
                    # Copy values to pat fields
                    for field_prefix in ['source', 'sutta', 'example']:
                        dpd_value = getattr(__word__, f"{field_prefix}_{idx}")
                        setattr(__word__.sbs, f"{modifier_column_to_copy}_{field_prefix}", dpd_value)
                        print(f"{__word__.id} {dpd_value}")
                    break
        else:
            # old_value = __word__.sbs.sbs_patimokkha
            old_value = getattr(__word__.sbs, column_to_update)
            if not old_value:
                # __word__.sbs.sbs_patimokkha = "vib_"
                setattr(__word__.sbs, column_to_update, value_to_update)

                console.print(f"[bold bright_yellow]{__word__.id} {__word__.lemma_1} {value_to_update}")

                count_changed += 1
                # Check for source_value in source fields
                for idx in range(1, 3):  # Assuming there are 2 positions
                    dpd_source_value = getattr(__word__, f"source_{idx}")
                    if dpd_source_value and re.search(source_value, dpd_source_value):
                        # Copy values to pat fields
                        for field_prefix in ['source', 'sutta', 'example']:
                            dpd_value = getattr(__word__, f"{field_prefix}_{idx}")
                            setattr(__word__.sbs, f"{modifier_column_to_copy}_{field_prefix}", dpd_value)
                            print(f"{__word__.id} {dpd_value}")
                        break
            else:
                console.print(f"[bright_yellow]already {old_value} for {__word__.id} {__word__.lemma_1} ")
                count_already_have += 1


    console.print("")
    console.print(f"[bold bright_green]Total count of already has: {count_already_have}")
    console.print(f"[bold bright_green]Total count of changed: {count_changed}")
    console.print(f"[bold bright_green]Total count of changed sbs: {count_changed_sbs}")
    console.print(f"[bold bright_green]Total count of added: {count_added}")

    db_session.commit()


# !To use the functions:
source_value = "VIN1.4.3.6"
column_to_update = "sbs_patimokkha"
value_to_update = "vib"
modifier_column_to_copy = "vib"

update_column_for_some_criteria(source_value, column_to_update, value_to_update, modifier_column_to_copy)




