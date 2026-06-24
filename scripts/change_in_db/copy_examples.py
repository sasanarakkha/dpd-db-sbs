#!/usr/bin/env python3

"""Copies source/sutta/example triplets from DPD or SBS source fields into a target SBS column prefix."""

import re

from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload

from db.db_helpers import get_db_session
from db.models import SBS, DpdHeadword
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
    words = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.sbs))
        .outerjoin(SBS)
        .filter(
            or_(
                SBS.vib_source == source_value,
                SBS.sbs_source_1 == source_value,
                SBS.sbs_source_2 == source_value,
                and_(
                    DpdHeadword.meaning_1 != "",
                    or_(
                        DpdHeadword.source_1 == source_value,
                        DpdHeadword.source_2 == source_value,
                    ),
                ),
            ),
        )
        .all()
    )

    stats = {"already": 0, "from_sbs": 0, "from_dpd": 0, "new_row": 0}
    prefix = modifier_column_to_copy

    for word in words:
        sbs = word.sbs

        if sbs and sbs.vib_source == source_value:
            stats["already"] += 1
            pr.amber(f"{word.id} {word.lemma_1}")
            continue

        if sbs:
            matched_sbs = False
            for idx in range(1, 3):
                sbs_source = getattr(sbs, f"sbs_source_{idx}")
                if sbs_source and re.search(source_value, sbs_source):
                    for field in _SOURCE_FIELDS:
                        setattr(
                            sbs, f"{prefix}_{field}", getattr(sbs, f"sbs_{field}_{idx}")
                        )
                    stats["from_sbs"] += 1
                    pr.cyan(f"Updated from sbs_source: {word.id} {word.lemma_1}")
                    matched_sbs = True
                    break
            if matched_sbs:
                continue

            if _copy_dpd_fields(word, sbs, source_value, prefix):
                stats["from_dpd"] += 1
                pr.cyan(f"Updated from dpd_source: {word.id} {word.lemma_1}")
        else:
            word.sbs = SBS(id=word.id)
            if _copy_dpd_fields(word, word.sbs, source_value, prefix):
                stats["new_row"] += 1
                pr.cyan(
                    f"Added new row & copied from dpd_source: {word.id} {word.lemma_1}"
                )

    pr.cyan("")
    pr.green("Total count:")
    pr.green(f"already have: {stats['already']}")
    pr.green(f"copied from dpd_source(s): {stats['from_dpd']}")
    pr.green(f"copied from sbs_source(s): {stats['from_sbs']}")
    pr.green(f"added new row(s): {stats['new_row']}")
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
