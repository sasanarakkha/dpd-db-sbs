#!/usr/bin/env python3

"""Compile data for Tamil to Pāḷi dictionary and add to the Lookup table."""

from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.configger import config_read
from tools.lookup_is_another_value import is_another_value
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.update_test_add import update_test_add

if config_read("generate", "tpd", "yes") == "no":
    pr.tic()
    pr.green_title("generating tpd data for lookup table")
    pr.green_title("disabled in config.ini")
    pr.toc()
    raise SystemExit(0)


class GlobalVars:
    pr.tic()
    pr.green_title("generating tpd data for lookup table")
    pr.green("making global data")
    pth: ProjectPaths = ProjectPaths()
    db_session: Session = get_db_session(pth.dpd_db_path)

    dpd_db: list[DpdHeadword] = (
        db_session.query(DpdHeadword).options(joinedload(DpdHeadword.ta)).all()
    )
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))
    dpd_db_length = len(dpd_db)

    pos_exclude_list = ["abbrev", "cs", "letter", "root", "suffix", "ve"]
    tpd_data_dict: dict[str, list[tuple[str, str, str]]] = {}

    pr.yes("")


def compile_headwords_data(g: GlobalVars):
    """Compile Tamil meanings in DpdHeadword."""
    pr.green_title("compiling headwords data")

    for counter, i in enumerate(g.dpd_db):
        if i.ta and i.ta.ta_meaning and i.pos not in g.pos_exclude_list:
            ta_meanings_clean = i.ta.ta_meaning.casefold()
            meanings_list = [m.strip() for m in ta_meanings_clean.split(";")]

            for meaning in meanings_list:
                tpd_data = (i.lemma_clean, i.pos, i.ta.ta_meaning)

                if meaning and meaning in g.tpd_data_dict.keys():
                    g.tpd_data_dict[meaning].append(tpd_data)
                else:
                    g.tpd_data_dict[meaning] = [tpd_data]

        if counter % 10000 == 0:
            pr.counter(counter, g.dpd_db_length, i.lemma_1)


def add_to_lookup_table(g: GlobalVars):
    """Add TPD data to lookup table."""

    pr.green_title("saving to Lookup table")

    pr.white("update test or add")
    lookup_table = g.db_session.query(Lookup).all()
    results = update_test_add(lookup_table, g.tpd_data_dict)
    update_set, test_set, add_set = results
    pr.yes("")

    pr.white("updating and deleting")
    # update test add
    for i in lookup_table:
        if i.lookup_key in update_set:
            i.tpd_pack(g.tpd_data_dict[i.lookup_key])
        elif i.lookup_key in test_set:
            if is_another_value(i, "tpd"):
                i.tpd = ""
            else:
                g.db_session.delete(i)
    pr.yes(len(update_set))

    pr.white("adding")
    # add
    add_to_db = []
    for key, data in g.tpd_data_dict.items():
        if key in add_set:
            add_me = Lookup()
            add_me.lookup_key = key
            add_me.tpd_pack(data)
            add_to_db.append(add_me)
    pr.yes(len(add_set))

    pr.white("committing")
    g.db_session.add_all(add_to_db)
    g.db_session.commit()
    pr.yes("ok")


def main():
    g = GlobalVars()
    compile_headwords_data(g)
    add_to_lookup_table(g)
    pr.toc()


if __name__ == "__main__":
    main()
