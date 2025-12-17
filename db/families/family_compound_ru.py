#!/usr/bin/env python3

"""Compile compound families and save to database."""

import re

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyCompound
from tools.degree_of_completion_ru import rus_degree_of_completion
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.superscripter import superscripter_uni

from tools.tools_for_ru_exporter import (
    make_short_ru_meaning,
    ru_replace_abbreviations,
)

from sqlalchemy.orm import joinedload


def main():
    pr.tic()
    pr.title("compound families generator (ru)")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    dpd_db = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.ru))
        .filter(DpdHeadword.family_compound != "")
        .all()
    )

    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    cf_dict = create_comp_fam_dict(dpd_db)
    cf_dict = compile_cf_html_ru(dpd_db, cf_dict)
    update_db(db_session, cf_dict)

    pr.toc()


def create_comp_fam_dict(dpd_db: list[DpdHeadword]):
    pr.green("extracting compound families")

    cf_dict: dict = {}

    for __counter__, i in enumerate(dpd_db):
        for cf in i.family_compound_list:
            test1 = re.findall(r"\bcomp\b", i.grammar) != []
            test2 = len(i.lemma_clean) < 30
            test3 = i.meaning_1

            if test1 and test2 and test3:
                if cf in cf_dict:
                    cf_dict[cf]["headwords"] += [i.lemma_1]
                else:
                    cf_dict[cf] = {
                        "headwords": [i.lemma_1],
                        "html_ru": "",
                        "data_ru": [],
                    }

    pr.yes(len(cf_dict))
    return cf_dict


def compile_cf_html_ru(dpd_db: list[DpdHeadword], cf_dict):
    pr.green("compiling html ru")

    for __counter__, i in enumerate(dpd_db):
        for cf in i.family_compound_list:
            if cf in cf_dict:
                if i.lemma_1 in cf_dict[cf]["headwords"]:
                    # rus
                    if not cf_dict[cf]["html_ru"]:
                        ru_html_string = "<table class='family'>"
                    else:
                        ru_html_string = cf_dict[cf]["html_ru"]

                    ru_meaning = make_short_ru_meaning(i, i.ru)
                    pos = ru_replace_abbreviations(i.pos)
                    ru_html_string += "<tr>"
                    ru_html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                    ru_html_string += f"<td><b>{pos}</b></td>"
                    ru_html_string += f"<td>{ru_meaning}</td>"
                    ru_html_string += f"<td>{rus_degree_of_completion(i)}</td>"
                    ru_html_string += "</tr>"

                    cf_dict[cf]["html_ru"] = ru_html_string

                    # rus data
                    if i.meaning_1:
                        cf_dict[cf]["data_ru"].append(
                            (
                                i.lemma_1,
                                pos,
                                ru_meaning,
                                rus_degree_of_completion(i, html=False),
                            )
                        )

    for i in cf_dict:
        cf_dict[i]["html_ru"] += "</table>"
    pr.yes(len(cf_dict))
    return cf_dict


def update_db(db_session, cf_dict):
    pr.green("updating db")

    for __counter__, cf in enumerate(cf_dict):
        # find in db
        cf_data = db_session.query(FamilyCompound).filter_by(compound_family=cf).first()
        if cf_data:
            cf_data.html_ru = cf_dict[cf]["html_ru"]
            cf_data.data_ru_pack(cf_dict[cf]["data_ru"])
            db_session.add(cf_data)
        else:
            pr.red(f"{cf} not found in db")

    db_session.commit()
    db_session.close()
    pr.yes("ok")


if __name__ == "__main__":
    main()
