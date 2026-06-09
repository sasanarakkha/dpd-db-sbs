#!/usr/bin/env python3

"""Copies source/sutta/example triplets from DPD or SBS source fields into a target SBS column prefix."""

import re

from sqlalchemy import and_, not_, or_
from sqlalchemy.orm import joinedload

from db.db_helpers import get_db_session
from db.models import DpdHeadword, SBS
from tools.paths import ProjectPaths
from tools.printer import printer as pr

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)

_SOURCE_FIELDS = ("source", "sutta", "example")


def _copy_dpd_fields(
    word: DpdHeadword, sbs: SBS, source_value: str, target_prefix: str
) -> bool:
    """Copy source/sutta/example triplet from DpdHeadword to SBS. Returns True if a match was found."""
    for idx in range(1, 3):
        dpd_source = getattr(word, f"source_{idx}")
        if dpd_source and re.search(source_value, dpd_source):
            for field in _SOURCE_FIELDS:
                setattr(
                    sbs, f"{target_prefix}_{field}", getattr(word, f"{field}_{idx}")
                )
            return True
    return False


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
        .filter(SBS.vib_source == source_value)
        .all()
    )

    ids_already_have = [row.id for row in rows_already_have]

    rows_to_update_sbs_query = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.sbs))
        .outerjoin(SBS)
        .filter(
            or_(
                SBS.sbs_source_1 == source_value,
                SBS.sbs_source_2 == source_value,
            ),
        )
    )

    if ids_already_have:
        rows_to_update_sbs_query = rows_to_update_sbs_query.filter(
            not_(DpdHeadword.id.in_(ids_already_have))
        )

    rows_to_update_sbs = rows_to_update_sbs_query.all()

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
        for word in rows_already_have:
            pr.amber(f"{word.id} {word.lemma_1}")

    if rows_to_update_sbs:
        pr.green(f"Found in sbs_source(s): {len(rows_to_update_sbs)}")
        for word in rows_to_update_sbs:
            changed = False
            for idx in range(1, 3):
                sbs_source = getattr(word.sbs, f"sbs_source_{idx}")
                if sbs_source and re.search(source_value, sbs_source):
                    for field in _SOURCE_FIELDS:
                        setattr(
                            word.sbs,
                            f"{modifier_column_to_copy}_{field}",
                            getattr(word.sbs, f"sbs_{field}_{idx}"),
                        )
                    changed = True
                    break
            if changed:
                pr.cyan(f"Updated from sbs_source: {word.id} {word.lemma_1}")
                count_changed_sbs += 1

    if rows_to_update:
        pr.green(f"Found in dpd_source(s): {len(rows_to_update)}")
        for word in rows_to_update:
            if not word.sbs:
                word.sbs = SBS(id=word.id)
                if _copy_dpd_fields(
                    word, word.sbs, source_value, modifier_column_to_copy
                ):
                    pr.cyan(
                        f"Added new row & copied from dpd_source: {word.id} {word.lemma_1}"
                    )
                    count_added += 1
            else:
                if _copy_dpd_fields(
                    word, word.sbs, source_value, modifier_column_to_copy
                ):
                    pr.cyan(f"Updated from dpd_source: {word.id} {word.lemma_1}")
                    count_changed += 1

    pr.cyan("")
    pr.green("Total count:")
    if rows_already_have:
        pr.green(f"already have: {len(rows_already_have)}")
    if count_changed:
        pr.green(f"copied from dpd_source(s): {count_changed}")
    if count_changed_sbs:
        pr.green(f"copied from sbs_source(s): {count_changed_sbs}")
    if count_added:
        pr.green(f"added new row(s): {count_added}")
    pr.cyan("")
    pr.yes(f"finished for {source_value}")

    if not dry_run:
        db_session.commit()
    else:
        pr.amber("DRY RUN — no changes written to database")


if __name__ == "__main__":
    source_value = "VIN2.5.7.5"
    value_to_update = "vib"
    modifier_column_to_copy = "vib"

    update_column_for_some_criteria(
        source_value, value_to_update, modifier_column_to_copy
    )
