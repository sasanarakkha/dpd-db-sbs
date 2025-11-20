#!/usr/bin/env python3

"""Distribute sbs examples according to Anki deck"""
from rich import print
import re

from db.db_helpers import get_db_session
from db.models import DpdHeadword, SBS, Russian
from tools.paths import ProjectPaths

from sqlalchemy.orm import joinedload

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)
db = db_session.query(DpdHeadword) \
    .options(joinedload(DpdHeadword.sbs), joinedload(DpdHeadword.ru)) \
    .outerjoin(Russian, DpdHeadword.id == Russian.id) \
    .outerjoin(SBS, DpdHeadword.id == SBS.id) \
        .all()


def dhp():
    # Sanity check: Ensure DpdHeadword IDs are unique in the fetched list
    # This is a safeguard in case the initial query somehow returns duplicates,
    # which should not happen for primary keys but can be a symptom of deeper issues.
    unique_db_list = []
    seen_ids_for_dedup = set()
    for item in db:
        if item.id not in seen_ids_for_dedup:
            seen_ids_for_dedup.add(item.id)
            unique_db_list.append(item)
    
    # Use the de-duplicated list for processing
    processed_db_items = unique_db_list
    
    count = 0
    count_sbs = 0
    added_ids = set()
    with db_session.no_autoflush:
        for i in processed_db_items:
            if i.sbs and not i.sbs.dhp_example:
                for idx in range(1, 3):
                    source_value = getattr(i, f"source_{idx}")
                    if source_value and re.search(r"DHP\d", source_value) and not re.search("DHPa", source_value) and i.meaning_1:
                        setattr(i.sbs, "dhp_source", getattr(i, f"source_{idx}"))
                        setattr(i.sbs, "dhp_sutta", getattr(i, f"sutta_{idx}"))
                        setattr(i.sbs, "dhp_example", getattr(i, f"example_{idx}"))
                        count_sbs += 1 # Increment once per record
                        break

            if not i.sbs:
                # Prevent adding duplicate SBS objects for the same id in this session
                if i.id in added_ids:
                    continue
                existing_sbs = db_session.query(SBS).filter_by(id=i.id).first()
                if existing_sbs:
                    continue
                for idx in range(1, 3):
                    source_value = getattr(i, f"source_{idx}")
                    if source_value and re.search(r"DHP\d", source_value) and not re.search("DHPa", source_value) and i.meaning_1:
                        new_sbs = SBS(id=i.id)
                        i.sbs = new_sbs
                        db_session.add(new_sbs)
                        added_ids.add(i.id)
                        setattr(i.sbs, "dhp_source", getattr(i, f"source_{idx}"))
                        setattr(i.sbs, "dhp_sutta", getattr(i, f"sutta_{idx}"))
                        setattr(i.sbs, "dhp_example", getattr(i, f"example_{idx}"))
                        count += 1 # Increment once per record
                        break

    # db_session.commit()
    db_session.close()
    print(f"dhp examples has been added to {count} records.")
    print(f"dhp examples has been added to existing {count_sbs} records.")


def extra_example_rearrangement():
    # Sanity check: Ensure DpdHeadword IDs are unique in the fetched list
    # This is a safeguard in case the initial query somehow returns duplicates,
    # which should not happen for primary keys but can be a symptom of deeper issues.
    unique_db_list = []
    seen_ids_for_dedup = set()
    for item in db:
        if item.id not in seen_ids_for_dedup:
            seen_ids_for_dedup.add(item.id)
            unique_db_list.append(item)

    # Use the de-duplicated list for processing
    processed_db_items = unique_db_list

    count_copy = 0
    count_clear = 0
    with db_session.no_autoflush:
        for i in processed_db_items:
            if i.sbs and i.sbs.sbs_example_2:
                # Copy from sbs_example_2 to extra_example if extra_example is empty
                if not i.sbs.extra_example and not i.sbs.sbs_chapter_2:
                    i.sbs.extra_source = getattr(i.sbs, 'sbs_source_2', '')
                    i.sbs.extra_sutta = getattr(i.sbs, 'sbs_sutta_2', '')
                    i.sbs.extra_example = getattr(i.sbs, 'sbs_example_2', '')
                    count_copy += 1

                # Clear sbs_example_2 fields if sbs_chapter_2 is empty
                if not i.sbs.sbs_chapter_2:
                    setattr(i.sbs, 'sbs_source_2', '')
                    setattr(i.sbs, 'sbs_sutta_2', '')
                    setattr(i.sbs, 'sbs_example_2', '')
                    count_clear += 1

    # db_session.commit()
    db_session.close()
    print(f"extra_example has been copied from sbs_example_2 in {count_copy} records.")
    print(f"sbs_example_2 has been cleared in {count_clear} records.")


def moving_sutta_names():
    """Move sutta names from meaning_2 to ru.meaning_ru for records where
    meaning_2 is not empty and family_set starts with 'suttas of'"""
    # Sanity check: Ensure DpdHeadword IDs are unique in the fetched list
    unique_db_list = []
    seen_ids_for_dedup = set()
    for item in db:
        if item.id not in seen_ids_for_dedup:
            seen_ids_for_dedup.add(item.id)
            unique_db_list.append(item)
    
    # Use the de-duplicated list for processing
    processed_db_items = unique_db_list
    
    count = 0
    with db_session.no_autoflush:
        for i in processed_db_items:
            # Filter: meaning_2 is not empty AND family_set starts with "suttas of"
            if i.meaning_2 and i.family_set.startswith("suttas of"):
                # Ensure Russian record exists
                if not i.ru:
                    new_russian = Russian(id=i.id)
                    i.ru = new_russian
                    db_session.add(new_russian)
                
                # Copy meaning_2 to ru.meaning_ru
                i.ru.ru_meaning = i.meaning_2
                count += 1

    # db_session.commit()
    db_session.close()
    print(f"Copied meaning_2 to ru.meaning_ru for {count} records.")


if __name__ == "__main__":
    print("sbs_example_rearrangement")
    # dhp()
    # extra_example_rearrangement()
    # moving_sutta_names()