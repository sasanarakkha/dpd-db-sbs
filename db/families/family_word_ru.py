#!/usr/bin/env python3

"""Create an html table of all words belonging to the same family (ru)."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyWord
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.superscripter import superscripter_uni
from tools.degree_of_completion_ru import rus_degree_of_completion
from tools.tools_for_ru_exporter import (
    make_short_ru_meaning,
    ru_replace_abbreviations,
)

from sqlalchemy.orm import joinedload


def main():
    pr.tic()
    pr.title("word families generator (ru)")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    wf_db = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.ru))
        .filter(DpdHeadword.family_word != "")
        .all()
    )

    wf_db: list[DpdHeadword] = sorted(wf_db, key=lambda x: pali_sort_key(x.lemma_1))

    wf_dict = make_word_fam_dict(wf_db)
    wf_dict = compile_wf_html_ru(wf_db, wf_dict)
    update_db(db_session, wf_dict)

    pr.toc()


def make_word_fam_dict(wf_db: list[DpdHeadword]):
    pr.green("extracting word families")

    # create a dict of all word families
    # word: {headwords: [], html: "", }

    wf_dict: dict = {}

    for __counter__, i in enumerate(wf_db):
        wf = i.family_word

        if wf in wf_dict:
            wf_dict[wf]["headwords"] += [i.lemma_1]
        else:
            wf_dict[wf] = {
                "headwords": [i.lemma_1],
                "html_ru": "",
                "data_ru": [],
            }

    pr.yes(len(wf_dict))
    return wf_dict


def compile_wf_html_ru(wf_db: list[DpdHeadword], wf_dict):
    pr.green("compiling html ru")

    for __counter__, i in enumerate(wf_db):
        wf = i.family_word
        if i.lemma_1 in wf_dict[wf]["headwords"]:
            # rus
            if not wf_dict[wf]["html_ru"]:
                ru_html_string = "<table class='family'>"
            else:
                ru_html_string = wf_dict[wf]["html_ru"]

            ru_meaning = make_short_ru_meaning(i, i.ru)
            pos = ru_replace_abbreviations(i.pos)
            ru_html_string += "<tr>"
            ru_html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
            ru_html_string += f"<td><b>{pos}</b></td>"
            ru_html_string += f"<td>{ru_meaning}</td>"
            ru_html_string += f"<td>{rus_degree_of_completion(i)}</td>"
            ru_html_string += "</tr>"

            wf_dict[wf]["html_ru"] = ru_html_string

            # rus data
            wf_dict[wf]["data_ru"].append(
                (i.lemma_1, pos, ru_meaning, rus_degree_of_completion(i, html=False))
            )

    for i in wf_dict:
        wf_dict[i]["html_ru"] += "</table>"

    pr.yes(len(wf_dict))
    return wf_dict


def update_db(db_session, wf_dict):
    pr.green("updating db")

    for wf in wf_dict:
        # find in db
        wf_data = db_session.query(FamilyWord).filter_by(word_family=wf).first()

        if wf_data:
            wf_data.html_ru = wf_dict[wf]["html_ru"]
            wf_data.data_ru_pack(wf_dict[wf]["data_ru"])
            db_session.add(wf_data)
        else:
            pr.red(f"{wf} not found in db")

    db_session.commit()
    db_session.close()
    pr.yes("ok")


if __name__ == "__main__":
    main()
