#!/usr/bin/env python3

"""Compile data for Tamil to Pāḷi dictionary and add to the Lookup table."""

from dataclasses import dataclass, field

from sqlalchemy.orm import Session, joinedload

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.configger import config_read
from tools.lookup_sync import sync_lookup_column
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr

POS_EXCLUDE = frozenset({"abbrev", "cs", "letter", "root", "suffix", "ve"})


@dataclass
class GlobalVars:
    db_session: Session
    dpd_db: list[DpdHeadword]
    tpd_data_dict: dict[str, list[tuple[str, str, str]]] = field(default_factory=dict)


def compile_headwords_data(g: GlobalVars) -> None:
    """Compile Tamil meanings in DpdHeadword."""
    pr.green_title("compiling headwords data")

    for counter, i in enumerate(g.dpd_db):
        if i.ta and i.ta.ta_meaning and i.pos not in POS_EXCLUDE:
            ta_meanings_clean = i.ta.ta_meaning.casefold()
            meanings_list = [m.strip() for m in ta_meanings_clean.split(";")]
            tpd_data = (i.lemma_clean, i.pos, i.ta.ta_meaning)
            for meaning in meanings_list:
                if meaning:
                    g.tpd_data_dict.setdefault(meaning, []).append(tpd_data)

        if counter % 10000 == 0:
            pr.counter(counter, len(g.dpd_db), i.lemma_1)


def add_to_lookup_table(g: GlobalVars) -> None:
    """Add TPD data to lookup table."""

    pr.green_title("saving to Lookup table")
    pr.white_tmr("syncing tpd column")
    result = sync_lookup_column(g.db_session, "tpd", g.tpd_data_dict)
    pr.yes(result.updated + result.inserted)


def main() -> None:
    pr.tic()
    pr.green_title("generating tpd data for lookup table")

    if config_read("generate", "tpd", "yes") == "no":
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pr.green_tmr("making global data")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = sorted(
        db_session.query(DpdHeadword).options(joinedload(DpdHeadword.ta)).all(),
        key=lambda x: pali_sort_key(x.lemma_1),
    )
    g = GlobalVars(db_session=db_session, dpd_db=dpd_db)
    pr.yes("")

    compile_headwords_data(g)
    add_to_lookup_table(g)
    pr.toc()


if __name__ == "__main__":
    main()
