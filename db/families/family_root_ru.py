#!/usr/bin/env python3

"""Create an html list of all words belonging to the same root family
and add to db (ru)."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyRoot
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
    pr.title("root families (ru)")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    dpd_db = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.ru))
        .filter(DpdHeadword.family_root != "")
        .all()
    )

    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    rf_dict = make_roots_family_dict(dpd_db)
    rf_dict = compile_rf_html_ru(dpd_db, rf_dict)
    update_db(db_session, rf_dict)

    db_session.close()

    pr.toc()


def make_roots_family_dict(dpd_db):
    pr.green("extracting root families")
    rf_dict = {}

    for i in dpd_db:
        # compile root subfamilies
        family = i.root_family_key

        if family not in rf_dict:
            rf_dict[family] = {
                "root_key": i.root_key,
                "root_family": i.family_root,
                "root_ru_meaning": i.rt.root_ru_meaning,
                "headwords": [i.lemma_1],
                "html_ru": "",
                "count": 1,
                "meaning_ru": i.rt.root_ru_meaning,
                "data_ru": [],
            }
        else:
            rf_dict[family]["headwords"] += [i.lemma_1]
            rf_dict[family]["count"] += 1

    pr.yes(len(rf_dict))
    return rf_dict


def compile_rf_html_ru(dpd_db: list[DpdHeadword], rf_dict):
    pr.green("compiling html ru")

    for __counter__, i in enumerate(dpd_db):
        family = i.root_family_key

        if i.lemma_1 in rf_dict[family]["headwords"]:
            # rus
            if not rf_dict[family]["html_ru"]:
                ru_html_string = "<table class='family'>"
            else:
                ru_html_string = rf_dict[family]["html_ru"]

            ru_meaning = make_short_ru_meaning(i, i.ru)
            pos = ru_replace_abbreviations(i.pos)
            ru_html_string += "<tr>"
            ru_html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
            ru_html_string += f"<td><b>{pos}</b></td>"
            ru_html_string += f"<td>{ru_meaning}</td>"
            ru_html_string += f"<td>{rus_degree_of_completion(i)}</td>"
            ru_html_string += "</tr>"

            rf_dict[family]["html_ru"] = ru_html_string

            # rus data
            rf_dict[family]["data_ru"].append(
                (i.lemma_1, pos, ru_meaning, rus_degree_of_completion(i, html=False))
            )

    for rf in rf_dict:
        header_ru = make_root_header_ru(rf_dict, rf)
        rf_dict[rf]["html_ru"] = header_ru + rf_dict[rf]["html_ru"] + "</table>"

    pr.yes(len(rf_dict))

    return rf_dict


def make_root_header_ru(rf_dict, rf):
    header = "<p class='heading underlined'>"
    if rf_dict[rf]["count"] == 1:
        header += "<b>1</b> слово принадлежит к семье корня "
    else:
        header += f"<b>{rf_dict[rf]['count']}</b> слов(а) принадлежат к семье корня "
    header += f"<b>{rf_dict[rf]['root_family']}</b> ({rf_dict[rf]['meaning_ru']})</p>"
    return header


def update_db(db_session, rf_dict):
    pr.green("updating db")

    for rf in rf_dict:
        # find in db
        root_family = (
            db_session.query(FamilyRoot)
            .filter_by(root_family_key=rf, root_key=rf_dict[rf]["root_key"])
            .first()
        )

        if root_family:
            root_family.root_ru_meaning = rf_dict[rf]["root_ru_meaning"]
            root_family.html_ru = rf_dict[rf]["html_ru"]
            root_family.data_ru_pack(rf_dict[rf]["data_ru"])
            db_session.add(root_family)
        else:
            pr.red(f"{rf} not found in db")

    db_session.commit()
    pr.yes("ok")


if __name__ == "__main__":
    main()
