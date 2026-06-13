#!/usr/bin/env python3

"""Compile data for Russian to Pāḷi dictionary and add to the Lookup table."""

import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session, joinedload

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot
from tools.configger import config_read
from tools.lookup_sync import sync_lookup_column
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr

from tools.tools_for_ru_exporter import (
    ru_replace_abbreviations,
)

POS_EXCLUDE = frozenset({"abbrev", "cs", "letter", "root", "suffix", "ve"})


@dataclass
class GlobalVars:
    db_session: Session
    dpd_db: list[DpdHeadword]
    roots_db: list[DpdRoot]
    rpd_data_dict: dict[str, list[tuple[str, str, str]]] = field(default_factory=dict)


def compile_headwords_data(g: GlobalVars) -> None:
    """Compile meanings and sutta names in DpdHeadword."""
    pr.green_title("compiling headwords data")

    for counter, i in enumerate(g.dpd_db):
        if i.ru and i.ru.ru_meaning and i.pos not in POS_EXCLUDE:
            meaning_plus_case = make_meaning_plus_case(i)
            ru_pos = ru_replace_abbreviations(i.pos, "gram")
            rpd_data = (i.lemma_clean, ru_pos, meaning_plus_case)
            for meaning in make_clean_meaning_list(i):
                if meaning:
                    g.rpd_data_dict.setdefault(meaning, []).append(rpd_data)

        if counter % 10000 == 0:
            pr.counter(counter, len(g.dpd_db), i.lemma_1)


def compile_roots_data(g: GlobalVars) -> None:
    """Compile root meanings in DpdRoot."""
    pr.green("compiling roots data")

    counter = 0
    for i in g.roots_db:
        root_meanings_list: list[str] = i.root_ru_meaning.split(", ")
        rpd_data = (i.root, "корень", i.root_ru_meaning)
        for root_meaning in root_meanings_list:
            g.rpd_data_dict.setdefault(root_meaning, []).append(rpd_data)
            counter += 1

    pr.yes(counter)


def make_clean_meaning_list(i: DpdHeadword) -> list[str]:
    "Cleanup ru.ru_meaning"

    # remove double ??
    ru_meanings_clean = re.sub(r"\?\?", "", i.ru.ru_meaning)
    # remove all space brackets
    ru_meanings_clean = re.sub(r" \(.+?\)", "", ru_meanings_clean)
    # remove all brackets space
    ru_meanings_clean = re.sub(r"\(.+?\) ", "", ru_meanings_clean)
    # remove space at start and fin
    ru_meanings_clean = re.sub(r"(^ | $)", "", ru_meanings_clean)
    # remove double spaces
    ru_meanings_clean = re.sub(r"  ", " ", ru_meanings_clean)
    # remove space around ;
    ru_meanings_clean = re.sub(r" ;|; ", ";", ru_meanings_clean)
    # remove i.e.
    ru_meanings_clean = re.sub(r"т\.д\. ", "", ru_meanings_clean)
    # remove !
    ru_meanings_clean = re.sub(r"!", "", ru_meanings_clean)
    # make lowercase
    ru_meanings_clean = ru_meanings_clean.casefold()

    return ru_meanings_clean.split(";")


def make_meaning_plus_case(i: DpdHeadword) -> str:
    """Return meaning and optionally (plus_case)"""

    if i.plus_case:
        ru_plus_case = ru_replace_abbreviations(i.plus_case, "gram")
        return f"{i.ru.ru_meaning} ({ru_plus_case})"
    else:
        return i.ru.ru_meaning


def add_to_lookup_table(g: GlobalVars) -> None:
    """Add RPD data to lookup table."""

    pr.green_title("saving to Lookup table")
    pr.white_tmr("syncing rpd column")
    result = sync_lookup_column(g.db_session, "rpd", g.rpd_data_dict)
    pr.yes(result.updated + result.inserted)


def main() -> None:
    pr.tic()
    pr.green_title("generating rpd data for lookup table")

    if config_read("generate", "rpd", "yes") == "no":
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pr.green_tmr("making global data")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = sorted(
        db_session.query(DpdHeadword).options(joinedload(DpdHeadword.ru)).all(),
        key=lambda x: pali_sort_key(x.lemma_1),
    )
    roots_db = db_session.query(DpdRoot).all()
    g = GlobalVars(db_session=db_session, dpd_db=dpd_db, roots_db=roots_db)
    pr.yes("")

    compile_headwords_data(g)
    compile_roots_data(g)
    add_to_lookup_table(g)
    pr.toc()


if __name__ == "__main__":
    main()
