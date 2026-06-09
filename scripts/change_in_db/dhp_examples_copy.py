#!/usr/bin/env python3

"""Copy DHP examples from DPD to SBS"""

import re

from sqlalchemy.orm import joinedload

from db.db_helpers import get_db_session
from db.models import SBS, DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr

_RE_DHP = re.compile(r"DHP\d")


def _find_dhp_source_idx(word: DpdHeadword) -> int | None:
    """Return the first source index (1 or 2) matching DHP\\d but not DHPa, else None."""
    for idx in range(1, 3):
        source_value: str = getattr(word, f"source_{idx}") or ""
        if _RE_DHP.search(source_value) and "DHPa" not in source_value:
            return idx
    return None


def dhp() -> None:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.sbs))
        .filter(DpdHeadword.meaning_1 != "")
        .all()
    )

    count_new = 0
    count_existing = 0

    with db_session.no_autoflush:
        for word in db:
            if word.sbs and word.sbs.dhp_example:
                continue
            idx = _find_dhp_source_idx(word)
            if idx is None:
                continue
            if not word.sbs:
                new_sbs = SBS(id=word.id)
                word.sbs = new_sbs
                db_session.add(new_sbs)
                count_new += 1
            else:
                count_existing += 1
            word.sbs.dhp_source = getattr(word, f"source_{idx}")
            word.sbs.dhp_sutta = getattr(word, f"sutta_{idx}")
            word.sbs.dhp_example = getattr(word, f"example_{idx}")
            pr.green(str(word.id))

    db_session.commit()
    db_session.close()
    pr.green(f"dhp examples added to {count_new} new records.")
    pr.green(f"dhp examples added to {count_existing} existing records.")


if __name__ == "__main__":
    pr.white("dhp examples copy from dpd")
    dhp()
