#!/usr/bin/env python3

"""
    Save list of words from text.txt which are not in sbs db
"""

import csv

from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from db.db_helpers import get_db_session

from tools.cst_sc_text_sets import make_cst_text_list_from_file

from db.models import SBS, DpdHeadword
from sqlalchemy import or_


pth: ProjectPaths = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)

field_to_check = ["vib_example", "pat_example"]


def dps_make_no_field_inflections_set(db_session, fields):
    """
    Generate a set of all inflections in the DPD database where the specified SBS field is not empty.
    """
    
    if isinstance(fields, str):
        fields = [fields]

    conditions = [
        or_(getattr(SBS, field) != "", getattr(SBS, field).isnot(None))
        for field in fields
    ]

    inflections_db = db_session.query(DpdHeadword).join(SBS, DpdHeadword.id == SBS.id).filter(
        or_(*conditions)
    ).all()

    dps_filtered_inflections_set = set()
    for i in inflections_db:
        dps_filtered_inflections_set.update(i.inflections_list)

    print(f"dps_filtered_inflections_set: {len(dps_filtered_inflections_set)}")

    return dps_filtered_inflections_set


def make_sp_mistakes_list(pth):

    with open(pth.spelling_mistakes_path) as f:
        reader = csv.reader(f, delimiter="\t")
        sp_mistakes_list = [row[0] for row in reader]

    print(f"sp_mistakes_list: {len(sp_mistakes_list)}")
    return sp_mistakes_list


def make_variant_list(pth):
    with open(pth.variant_readings_path) as f:
        reader = csv.reader(f, delimiter="\t")
        variant_list = [row[0] for row in reader]

    print(f"variant_list: {len(variant_list)}")
    return variant_list


def make_sandhi_ok_list(pth):
    with open(pth.decon_checked) as f:
        reader = csv.reader(f, delimiter="\t")
        sandhi_ok_list = [row[0] for row in reader]

    print(f"sandhi_ok_list: {len(sandhi_ok_list)}")
    return sandhi_ok_list


def dps_make_words_to_add_list_from_text_no_field(
        pth,
        dpspth,
        db_session,
        fields,
    ) -> list:
    """
    Generalized function to create words to add lists with various configurations.

    Parameters:
    - db_session: The database session for retrieving inflections.
    - pth: Path for resources.
    - make_cst_func: Function to create the CST text list.
    - make_sc_func: Optional function to create the SC text list.
    - inflection_func: Function to generate the inflection set.
    - book: The book name (optional).
    - sutta_name: The sutta name (optional).
    - dpspth: Path for DPS files.
    - source: Source identifier (optional).
    - field: Field name for inflections (optional).
    - output_filename_template: Template for the output file name.

    Returns:
    - A sorted list of words to add.
    """
    # Generate CST and SC text lists
    cst_text_list = make_cst_text_list_from_file(dpspth)

    sc_text_list = []
    original_text_list = list(cst_text_list) + list(sc_text_list)

    # Generate additional lists
    sp_mistakes_list = make_sp_mistakes_list(pth)
    variant_list = make_variant_list(pth)
    sandhi_ok_list = make_sandhi_ok_list(pth)

    all_inflections_set = dps_make_no_field_inflections_set(db_session, fields)

    # Filter the text set
    text_set = set(cst_text_list) | set(sc_text_list)
    text_set -= set(sandhi_ok_list)
    text_set -= set(sp_mistakes_list)
    text_set -= set(variant_list)
    text_set -= all_inflections_set

    # Sort based on original order
    text_list = sorted(text_set, key=lambda x: original_text_list.index(x))

    print(f"words_to_add: {len(text_list)}")

    # Determine filename
    if isinstance(fields, list):
        output_filename=f"temp/text_{'_'.join(fields)}.tsv"
    else:
        output_filename=f"temp/text_{fields}.tsv"

    # Save to a file
    with open(output_filename, "w") as f:
        for word in text_list:
            f.write(f"{word}\n")

    print(f"Saved to {output_filename}")

    return text_list


words_to_add_list = dps_make_words_to_add_list_from_text_no_field(
    pth,
    dpspth,
    db_session,
    field_to_check
)