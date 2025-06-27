#!/usr/bin/env python3

"""
Cleans sbs.class_source and finds the corresponding sutta from the main entry.
"""
from rich import print
import re

from db.db_helpers import get_db_session
from db.models import DpdHeadword, SBS
from tools.paths import ProjectPaths

from sqlalchemy.orm import joinedload

def main():
    """
    1. Builds a global map of {source: sutta} from all headword and SBS sources.
       - DpdHeadword: `source_1`/`sutta_1`, `source_2`/`sutta_2`
       - SBS: `sbs_source_1/2`, `vib_source`, `pat_source` and their suttas.
    2. Iterates through all entries, cleaning `sbs.class_source` by removing bracketed text.
    3. Uses the cleaned source to look up the corresponding sutta in the global map.
    4. Updates `sbs.class_sutta` with the found sutta, only if `class_sutta` is currently empty.
    """

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    
    # Eagerly load sbs relationship to avoid N+1 queries
    db = db_session.query(DpdHeadword) \
        .options(joinedload(DpdHeadword.sbs)) \
        .outerjoin(SBS, DpdHeadword.id == SBS.id) \
        .all()
    
    # --- Phase 1: Build a global source-to-sutta dictionary ---
    print("Building source-sutta map from all headwords...")
    source_sutta_map = {}
    for i in db:
        for idx in range(1, 3):  # Check source_1, source_2
            source = getattr(i, f"source_{idx}", None)
            sutta = getattr(i, f"sutta_{idx}", None)
            if source and sutta:
                # Clean the source to use as a key, e.g., "SN12.11 (aṭṭha)" -> "SN12.11"
                cleaned_source_key = re.sub(r'\s*\(.+?\)\s*', '', source).strip()
                if cleaned_source_key and cleaned_source_key not in source_sutta_map:
                    source_sutta_map[cleaned_source_key] = sutta

    # Part B: From SBS sources
    print("Augmenting map with SBS-specific sources...")
    sbs_sources_to_check = [
        ('sbs_source_1', 'sbs_sutta_1'),
        ('sbs_source_2', 'sbs_sutta_2'),
        ('vib_source', 'vib_sutta'),
        ('pat_source', 'pat_sutta'),
        ('discourses_source', 'discourses_sutta')
    ]
    for i in db:
        if i.sbs:
            for source_field, sutta_field in sbs_sources_to_check:
                source = getattr(i.sbs, source_field, None)
                sutta = getattr(i.sbs, sutta_field, None)
                if source and sutta:
                    cleaned_source_key = re.sub(r'\s*\(.+?\)\s*', '', source).strip()
                    if cleaned_source_key and cleaned_source_key not in source_sutta_map:
                        source_sutta_map[cleaned_source_key] = sutta
    
    print(f"Map built with {len(source_sutta_map)} unique source-sutta pairs.")

    # --- Phase 2: Use the dictionary to update sbs.class_sutta ---
    print("\nUpdating sbs.class_sutta based on the map...")
    updated_count = 0
    cleaned_source_count = 0

    with db_session.no_autoflush:
        for i in db:
            if i.sbs and i.sbs.class_source:
                original_source = i.sbs.class_source
                # Clean the class_source, e.g., "SN12.11 (simpl)" -> "SN12.11"
                cleaned_source = re.sub(r'\s*\(.+?\)\s*', '', original_source).strip()

                # cleaned_source_count
                if cleaned_source != original_source:
                    # print(f"ID {i.id}: Cleaning class_source '{original_source}' to '{cleaned_source}'")
                    cleaned_source_count += 1

                # Find sutta in the map and update if class_sutta is empty
                if cleaned_source in source_sutta_map:
                    sutta_value = source_sutta_map[cleaned_source]
                    if not i.sbs.class_sutta:
                        print(f"ID {i.id}: Found sutta for '{cleaned_source}'. Setting class_sutta to '{sutta_value}'")
                        i.sbs.class_sutta = sutta_value
                        updated_count += 1

    print("\nScript finished.")
    print(f"Cleaned {cleaned_source_count} class_source fields.")
    print(f"Updated {updated_count} class_sutta fields.")
    
    db_session.commit()
    print("Changes are ready to be committed. Uncomment `db_session.commit()` to save.")
    db_session.close()

if __name__ == "__main__":
    main()