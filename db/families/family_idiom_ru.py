#!/usr/bin/env python3

"""Compile idioms and save to database (ru)."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyIdiom
from tools.configger import config_test
from tools.degree_of_completion_ru import degree_of_completion_ru
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
    pr.yellow_title("idioms generator (ru)")

    if not (
        config_test("exporter", "make_dpd", "yes")
        or config_test("regenerate", "db_rebuild", "yes")
    ):
        pr.green_tmr("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    dpd_db = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.ru))
        .filter(DpdHeadword.family_idioms != "")
        .all()
    )
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    idioms_dict = create_idioms_dict(dpd_db)
    idioms_dict = compile_idioms_html_ru(dpd_db, idioms_dict)
    add_idioms_to_db(db_session, idioms_dict)

    pr.toc()


def create_idioms_dict(dpd_db):
    pr.green_tmr("extracting idioms and headwords")

    idioms_dict: dict = {}
    for i in dpd_db:
        for word in i.family_idioms_list:
            if i.meaning_1:
                if word in idioms_dict:
                    idioms_dict[word]["headwords"].append(i.lemma_1)
                else:
                    idioms_dict[word] = {
                        "headwords": [i.lemma_1],
                        "html_ru": "",
                        "data_ru": [],
                    }

    pr.yes(len(idioms_dict))
    return idioms_dict


def compile_idioms_html_ru(dpd_db: list[DpdHeadword], idioms_dict):
    pr.green_tmr("compiling html ru")

    for i in dpd_db:
        if i.pos in ["idiom", "sandhi"]:
            for word in i.family_idioms_list:
                if (
                    i.meaning_1
                    and word in idioms_dict
                    and i.lemma_1 in idioms_dict[word]["headwords"]
                ):
                    # rus
                    if not idioms_dict[word]["html_ru"]:
                        ru_html_string = "<table class='family'>"
                    else:
                        ru_html_string = idioms_dict[word]["html_ru"]

                    ru_meaning = make_short_ru_meaning(i, i.ru)
                    pos = ru_replace_abbreviations(i.pos)
                    ru_html_string += "<tr>"
                    ru_html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                    ru_html_string += f"<td><b>{pos}</b></td>"
                    ru_html_string += f"<td>{ru_meaning}</td>"
                    ru_html_string += f"<td>{degree_of_completion_ru(i)}</td>"
                    ru_html_string += "</tr>"

                    idioms_dict[word]["html_ru"] = ru_html_string

                    # rus data
                    idioms_dict[word]["data_ru"].append(
                        (
                            i.lemma_1,
                            pos,
                            ru_meaning,
                            degree_of_completion_ru(i, html=False),
                        )
                    )

    for i in idioms_dict:
        idioms_dict[i]["html_ru"] += "</table>"
    pr.yes(len(idioms_dict))
    return idioms_dict


def add_idioms_to_db(db_session, idioms_dict):
    pr.green_tmr("adding to db")

    for idiom in idioms_dict:
        # find in db
        idiom_data = db_session.query(FamilyIdiom).filter_by(idiom=idiom).first()
        if idiom_data:
            idiom_data.html_ru = idioms_dict[idiom]["html_ru"]
            idiom_data.data_ru_pack(idioms_dict[idiom]["data_ru"])
            db_session.add(idiom_data)

    db_session.commit()
    pr.yes("ok")


if __name__ == "__main__":
    main()
