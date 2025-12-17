#!/usr/bin/env python3

"""Compile sets save to database (ru)."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilySet
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.superscripter import superscripter_uni
from tools.degree_of_completion_ru import rus_degree_of_completion
from tools.tools_for_ru_exporter import (
    make_short_ru_meaning,
    ru_replace_abbreviations,
    populate_set_ru_and_check_errors,
)

from sqlalchemy.orm import joinedload


def main():
    pr.tic()
    pr.title("sets generator (ru)")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    sets_db = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.ru))
        .filter(DpdHeadword.family_set != "")
        .all()
    )
    sets_db = sorted(sets_db, key=lambda x: pali_sort_key(x.lemma_1))

    sets_dict = make_sets_dict(sets_db)
    sets_dict = compile_sf_html_ru(sets_db, sets_dict)
    update_db(db_session, sets_dict)

    pr.toc()


def make_sets_dict(sets_db):
    pr.green("extracting set names")

    sets_dict: dict = {}

    for __counter__, i in enumerate(sets_db):
        for fs in i.family_set_list:
            if i.meaning_1:
                if fs in sets_dict:
                    sets_dict[fs]["headwords"] += [i.lemma_1]
                else:
                    sets_dict[fs] = {
                        "headwords": [i.lemma_1],
                        "html_ru": "",
                        "set_ru": "",
                        "data_ru": [],
                    }
    pr.yes(len(sets_dict))
    return sets_dict


def compile_sf_html_ru(sets_db: list[DpdHeadword], sets_dict):
    pr.green("compiling html ru")

    populate_set_ru_and_check_errors(sets_dict)

    for __counter__, i in enumerate(sets_db):
        for sf in i.family_set_list:
            if sf in sets_dict:
                if i.lemma_1 in sets_dict[sf]["headwords"]:
                    # rus
                    if not sets_dict[sf]["html_ru"]:
                        ru_html_string = "<table class='family'>"
                    else:
                        ru_html_string = sets_dict[sf]["html_ru"]

                    ru_meaning = make_short_ru_meaning(i, i.ru)
                    pos = ru_replace_abbreviations(i.pos)
                    ru_html_string += "<tr>"
                    ru_html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                    ru_html_string += f"<td><b>{pos}</b></td>"
                    ru_html_string += f"<td>{ru_meaning}</td>"
                    ru_html_string += f"<td>{rus_degree_of_completion(i)}</td>"
                    ru_html_string += "</tr>"

                    sets_dict[sf]["html_ru"] = ru_html_string

                    # rus data
                    sets_dict[sf]["data_ru"].append(
                        (
                            i.lemma_1,
                            pos,
                            ru_meaning,
                            rus_degree_of_completion(i, html=False),
                        )
                    )

    for i in sets_dict:
        sets_dict[i]["html_ru"] += "</table>"

    pr.yes(len(sets_dict))
    return sets_dict


def update_db(db_session, sets_dict):
    pr.green("updating db")

    for sf in sets_dict:
        # find in db
        sf_data = db_session.query(FamilySet).filter_by(set=sf).first()

        if sf_data:
            sf_data.html_ru = sets_dict[sf]["html_ru"]
            sf_data.set_ru = sets_dict[sf]["set_ru"]
            sf_data.data_ru_pack(sets_dict[sf]["data_ru"])
            db_session.add(sf_data)
        else:
            pr.red(f"{sf} not found in db")

    db_session.commit()
    db_session.close()
    pr.yes("ok")


if __name__ == "__main__":
    main()
