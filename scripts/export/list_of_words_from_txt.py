#!/usr/bin/env python3

"""
Save list of words from text.txt which are not in sbs db
"""

from typing import Any

from sqlalchemy import and_, func, or_

from db.db_helpers import get_db_session
from db.models import SBS, DpdHeadword, Lookup
from tools.cst_sc_text_sets import make_cst_text_list_from_file
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr


def make_field_conditions(fields: str | list[str]) -> list[Any]:
    if isinstance(fields, str):
        fields = [fields]

    conditions = []
    for field in fields:
        column = getattr(SBS, field)
        conditions.append(and_(column.isnot(None), func.trim(column) != ""))
    return conditions


def make_decon_word_list(deconstruction: list[str]) -> list[str]:
    """Mirror gui2 deconstructor word splitting for lookup fallback."""

    word_list: list[str] = []
    for deconstruction_item in deconstruction:
        for word in deconstruction_item.split(" + "):
            word = word.strip()
            if word not in word_list:
                word_list.append(word)
    return word_list


def get_headwords_ids(db_session, word_in_text: str) -> list[int]:
    """Mirror gui2 DatabaseManager.get_headwords; returns ids only.

    Direct headwords have priority: if headwords_unpack exists, return it without
    fallback to deconstructor. This matches gui2/database_manager.py:307-335.
    """
    lookup_item = (
        db_session.query(Lookup).filter(Lookup.lookup_key == word_in_text).first()
    )
    if not lookup_item:
        return []

    ids = lookup_item.headwords_unpack
    if ids:
        return list(ids)

    return get_headwords_from_deconstructor_ids(db_session, lookup_item)


def get_headwords_from_deconstructor_ids(db_session, lookup_item: Lookup) -> list[int]:
    """Mirror gui2 DatabaseManager.get_headwords_from_deconstructor.

    Recursively resolve deconstructor parts via gui2 priority (direct first).
    Matches gui2/database_manager.py:337-351.
    """
    headwords_list: list[int] = []
    deconstruction = lookup_item.deconstructor_unpack

    if deconstruction:
        for word in make_decon_word_list(deconstruction):
            headwords_list.extend(get_headwords_ids(db_session, word))

    return headwords_list


def make_words_with_matching_fields_set(
    db_session, words: list[str], fields: str | list[str]
) -> set[str]:
    """Return text words whose resolved headwords already have the target fields.

    Matches gui2's bulk-filter architecture: precompute covered ids once, then
    resolve each text word in memory via lookup dict (no per-word DB calls).
    """
    conditions = make_field_conditions(fields)
    unique_words = list(set(words))

    # Bulk fetch 1: all Lookup rows for text words
    lookup_dict: dict[str, Lookup] = {
        r.lookup_key: r
        for r in db_session.query(Lookup)
        .filter(Lookup.lookup_key.in_(unique_words))
        .all()
    }

    # Bulk fetch 2: any decon parts not yet loaded
    extra_keys: set[str] = set()
    for r in lookup_dict.values():
        if not r.headwords_unpack and r.deconstructor_unpack:
            for part in make_decon_word_list(r.deconstructor_unpack):
                if part not in lookup_dict:
                    extra_keys.add(part)
    if extra_keys:
        for r in (
            db_session.query(Lookup).filter(Lookup.lookup_key.in_(extra_keys)).all()
        ):
            lookup_dict[r.lookup_key] = r

    # Bulk fetch 3: covered headword ids (one query)
    covered_ids: set[int] = {
        row[0]
        for row in db_session.query(DpdHeadword.id)
        .join(SBS, DpdHeadword.id == SBS.id)
        .filter(or_(*conditions))
        .all()
    }

    # In-memory resolve + intersect (no DB)
    def resolve(word: str) -> list[int]:
        item = lookup_dict.get(word)
        if not item:
            return []
        if item.headwords_unpack:
            return list(item.headwords_unpack)
        if not item.deconstructor_unpack:
            return []
        ids: list[int] = []
        for part in make_decon_word_list(item.deconstructor_unpack):
            ids.extend(resolve(part))
        return ids

    covered_words: set[str] = set()
    for word in unique_words:
        if any(i in covered_ids for i in resolve(word)):
            covered_words.add(word)

    pr.green_tmr("covered_text_words")
    pr.yes(len(covered_words))
    return covered_words


def dps_make_words_to_add_list_from_text_no_field(
    pth,
    dpspth,
    db_session,
    fields,
) -> list[str]:
    """
    Read words from text.txt, exclude those already covered by SBS fields,
    and write the remainder to temp/text_{fields}.tsv.

    Parameters:
    - pth: ProjectPaths instance.
    - dpspth: DPSPaths instance (provides text_to_add_path).
    - db_session: SQLAlchemy database session.
    - fields: SBS field(s) to check for existing coverage.

    Returns:
    - Sorted list of words to add.
    """
    # Generate CST and SC text lists
    cst_text_list = make_cst_text_list_from_file(dpspth)

    sc_text_list = []
    original_text_list = list(cst_text_list) + list(sc_text_list)

    covered_words_set = make_words_with_matching_fields_set(
        db_session, original_text_list, fields
    )

    # Filter the text set
    text_set = set(cst_text_list) | set(sc_text_list)
    text_set -= covered_words_set

    # Sort based on original order
    text_list = sorted(text_set, key=lambda x: original_text_list.index(x))

    pr.green_tmr("words_to_add")
    pr.yes(len(text_list))

    # Determine filename
    if isinstance(fields, list):
        output_filename = f"temp/text_{'_'.join(fields)}.tsv"
    else:
        output_filename = f"temp/text_{fields}.tsv"

    # Save to a file
    with open(output_filename, "w", encoding="utf-8") as f:
        f.writelines(f"{word}\n" for word in text_list)

    pr.green(f"Saved to {output_filename}")
    for word in text_list:
        pr.amber(word)

    return text_list


if __name__ == "__main__":
    pth: ProjectPaths = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)

    field_to_check = ["vib_source", "pat_source"]

    dps_make_words_to_add_list_from_text_no_field(
        pth, dpspth, db_session, field_to_check
    )
