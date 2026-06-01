#!/usr/bin/env python3

"""Compile data for Russian to Pāḷi dictionary and add to the Lookup table."""

import re
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, Lookup
from tools.configger import config_read
from tools.lookup_is_another_value import is_another_value
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.update_test_add import update_test_add

from tools.tools_for_ru_exporter import (
    ru_replace_abbreviations,
)

if config_read("generate", "rpd", "yes") == "no":
    pr.tic()
    pr.green_title("generating rpd data for lookup table")
    pr.green_title("disabled in config.ini")
    pr.toc()
    raise SystemExit(0)


class GlobalVars:
    pr.tic()
    pr.green_title("generating rpd data for lookup table")
    pr.green("making global data")
    pth: ProjectPaths = ProjectPaths()
    db_session: Session = get_db_session(pth.dpd_db_path)

    dpd_db: list[DpdHeadword] = (
        db_session.query(DpdHeadword).options(joinedload(DpdHeadword.ru)).all()
    )
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))
    dpd_db_length = len(dpd_db)

    roots_db: list = db_session.query(DpdRoot).all()
    roots_db_length = len(roots_db)

    pos_exclude_list = ["abbrev", "cs", "letter", "root", "suffix", "ve"]
    rpd_data_dict: dict[str, list[tuple[str, str, str]]] = {}

    pr.yes("")


def compile_headwords_data(g: GlobalVars):
    """Compile meanings and sutta names in DpdHeadword."""
    pr.green_title("compiling headwords data")

    for counter, i in enumerate(g.dpd_db):
        if i.ru and i.ru.ru_meaning and i.pos not in g.pos_exclude_list:
            meanings_list = make_clean_meaning_list(i)
            for meaning in meanings_list:
                meaning_plus_case = make_meaning_plus_case(i)
                ru_pos = ru_replace_abbreviations(i.pos, "gram")
                rpd_data = (i.lemma_clean, ru_pos, meaning_plus_case)

                if meaning and meaning in g.rpd_data_dict.keys():
                    g.rpd_data_dict[meaning].append(rpd_data)
                else:
                    g.rpd_data_dict[meaning] = [rpd_data]

        if counter % 10000 == 0:
            pr.counter(counter, g.dpd_db_length, i.lemma_1)


def compile_roots_data(g: GlobalVars):
    """Compile root meanings in DpdRoot."""
    pr.green("compiling roots data")

    counter = 0
    for i in g.roots_db:
        root_meanings_list: list = i.root_ru_meaning.split(", ")

        for root_meaning in root_meanings_list:
            rpd_data = (i.root, "корень", i.root_ru_meaning)
            if root_meaning in g.rpd_data_dict.keys():
                g.rpd_data_dict[root_meaning].append(rpd_data)
            else:
                g.rpd_data_dict[root_meaning] = [rpd_data]
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
    # remove ?
    ru_meanings_clean = re.sub(r"\\?", "", ru_meanings_clean)
    # make lowercase
    ru_meanings_clean = ru_meanings_clean.casefold()

    return ru_meanings_clean.split(";")


def make_meaning_plus_case(i: DpdHeadword):
    """Return meaning and optionally (plus_case)"""

    if i.plus_case:
        ru_plus_case = ru_replace_abbreviations(i.plus_case, "gram")
        return f"{i.ru.ru_meaning} ({ru_plus_case})"
    else:
        return i.ru.ru_meaning


def add_to_lookup_table(g: GlobalVars):
    """Add EPD data to lookup table."""

    pr.green_title("saving to Lookup table")

    pr.white("update test or add")
    lookup_table = g.db_session.query(Lookup).all()
    results = update_test_add(lookup_table, g.rpd_data_dict)
    update_set, test_set, add_set = results
    pr.yes("")

    pr.white("updating and deleting")
    # update test add
    for i in lookup_table:
        if i.lookup_key in update_set:
            i.rpd_pack(g.rpd_data_dict[i.lookup_key])
        elif i.lookup_key in test_set:
            if is_another_value(i, "rpd"):
                i.rpd = ""
            else:
                g.db_session.delete(i)
    pr.yes(len(update_set))

    pr.white("adding")
    # add
    add_to_db = []
    for key, data in g.rpd_data_dict.items():
        if key in add_set:
            add_me = Lookup()
            add_me.lookup_key = key
            add_me.rpd_pack(data)
            add_to_db.append(add_me)
    pr.yes(len(add_set))

    pr.white("committing")
    g.db_session.add_all(add_to_db)
    g.db_session.commit()
    pr.yes("ok")


def main():
    g = GlobalVars()
    compile_headwords_data(g)
    compile_roots_data(g)
    add_to_lookup_table(g)
    pr.toc()


if __name__ == "__main__":
    main()
