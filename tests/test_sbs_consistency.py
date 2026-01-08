"""
Unit tests for SBS consistency logic.
These tests verify the correctness of data integrity rules (regexes, triplets, exceptions) 
defined in db_tests/sbs_consistency_tests.py using an in-memory database and mock data.
"""

import pytest
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, DpdHeadword, SBS
from db_tests.sbs_consistency_tests import (
    check_pat_consistency, 
    check_dhp_source_consistency, 
    check_dhp_triplet_consistency
)

@pytest.fixture
def in_memory_db():
    """Sets up an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_pat_consistency_logic(in_memory_db):
    # Case 1: All correct
    sbs1 = SBS(id=1, pat_example="ex", pat_source="VIN PAT", pat_sutta="su")
    in_memory_db.add(sbs1)
    
    # Case 2: pat_example present but "VIN PAT" missing from source (Violation)
    sbs2 = SBS(id=2, pat_example="ex", pat_source="OTHER", pat_sutta="su")
    in_memory_db.add(sbs2)
    
    # Case 3: "VIN PAT" present but pat_example empty (Violation)
    sbs3 = SBS(id=3, pat_example="", pat_source="VIN PAT", pat_sutta="su")
    in_memory_db.add(sbs3)
    
    # Case 4: Missing one of the triplet (Violation)
    sbs4 = SBS(id=4, pat_example="ex", pat_source="VIN PAT", pat_sutta="")
    in_memory_db.add(sbs4)
    
    in_memory_db.commit()
    
    name, results, count, solution = check_pat_consistency(in_memory_db)
    assert count == 3
    assert re.search(r"2", results)
    assert re.search(r"3", results)
    assert re.search(r"4", results)

def test_dhp_source_consistency_logic(in_memory_db):
    from db_tests.sbs_consistency_tests import check_dhp_source_consistency
    # Case 1: Correct - DHP source in headword and SBS dhp_source
    h1 = DpdHeadword(id=1, lemma_1="l1", source_1="DHP100")
    s1 = SBS(id=1, dhp_source="DHP100")
    in_memory_db.add_all([h1, s1])
    
    # Case 2: DHP source in headword but SBS dhp_source empty (Violation)
    h2 = DpdHeadword(id=2, lemma_1="l2", source_1="DHP200")
    s2 = SBS(id=2, dhp_source="")
    in_memory_db.add_all([h2, s2])
    
    # Case 3: No SBS entry but headword has DHP source (Violation)
    h3 = DpdHeadword(id=3, lemma_1="l3", source_2="DHP400")
    in_memory_db.add(h3)
    
    in_memory_db.commit()
    
    name, results, count, solution = check_dhp_source_consistency(in_memory_db)
    assert count == 2
    assert re.search(r"2", results)
    assert re.search(r"3", results)

def test_dhp_triplet_consistency_logic(in_memory_db):
    from db_tests.sbs_consistency_tests import check_dhp_triplet_consistency
    # Case 1: Correct triplet
    s1 = SBS(id=1, dhp_example="ex", dhp_source="DHP100", dhp_sutta="su")
    # Case 2: Missing one of the triplet in SBS (Violation)
    s2 = SBS(id=2, dhp_example="ex", dhp_source="DHP300", dhp_sutta="")
    
    in_memory_db.add_all([s1, s2])
    in_memory_db.commit()
    
    name, results, count, solution = check_dhp_triplet_consistency(in_memory_db)
    assert count == 1
    assert re.search(r"2", results)

def test_triplet_consistency_logic(in_memory_db):
    from db_tests.sbs_consistency_tests import (
        check_vib_consistency, 
        check_class_consistency, 
        check_discourses_consistency
    )
    
    # vib triplet violation
    s1 = SBS(id=1, vib_example="ex", vib_source="so", vib_sutta="")
    # class triplet violation
    s2 = SBS(id=2, class_example="ex", class_source="", class_sutta="su")
    # discourses triplet violation
    s3 = SBS(id=3, discourses_example="", discourses_source="so", discourses_sutta="su")
    # correct ones
    s4 = SBS(id=4, vib_example="ex", vib_source="so", vib_sutta="su")
    s5 = SBS(id=5, class_example="ex", class_source="so", class_sutta="su")
    s6 = SBS(id=6, discourses_example="ex", discourses_source="so", discourses_sutta="su")
    # class triplet violation but with exception (class_anki=2 and "upāsak")
    s7 = SBS(id=7, class_example="upāsako", class_source="", class_sutta="", class_anki=2)
    
    in_memory_db.add_all([s1, s2, s3, s4, s5, s6, s7])
    in_memory_db.commit()
    
    name, results, count, solution = check_vib_consistency(in_memory_db)
    assert count == 1
    assert re.search(r"1", results)

    name, results, count, solution = check_class_consistency(in_memory_db)
    assert count == 1 # Only s2 should be flagged, s7 is excepted
    assert re.search(r"2", results)
    assert not re.search(r"7", results)

    name, results, count, solution = check_discourses_consistency(in_memory_db)
    assert count == 1
    assert re.search(r"3", results)

def test_class_anki_logic(in_memory_db):
    from db_tests.sbs_consistency_tests import check_class_anki_consistency
    
    # 1. Correct: both present
    s1 = SBS(id=1, class_example="ex", class_anki=2, class_example_translation="tr")
    # 2. Correct: anki is 1, no example needed
    s2 = SBS(id=2, class_example="", class_anki=1, class_example_translation="")
    # 3. Violation: class_example present but class_anki missing
    s3 = SBS(id=3, class_example="ex", class_anki=None, class_example_translation="tr")
    # 4. Violation: class_anki present but class_example missing
    s4 = SBS(id=4, class_example="", class_anki=2, class_example_translation="tr")
    # 5. Violation: class_anki is 2 but class_example_translation missing
    s5 = SBS(id=5, class_example="ex", class_anki=2, class_example_translation="")
    
    in_memory_db.add_all([s1, s2, s3, s4, s5])
    in_memory_db.commit()
    
    name, results, count, solution = check_class_anki_consistency(in_memory_db)
    assert count == 3
    assert re.search(r"3", results)
    assert re.search(r"4", results)
    assert re.search(r"5", results)

def test_discourses_source_prefix_logic(in_memory_db):
    from db_tests.sbs_consistency_tests import check_discourses_source_prefix
    
    # Correct: SN12 is in sbs_category_list (sn12)
    s1 = SBS(id=1, discourses_source="SN12.2")
    # Violation: UNK99 is not in list
    s2 = SBS(id=2, discourses_source="UNK99.1")
    # Correct: MN107 is in list (even without dot)
    s3 = SBS(id=3, discourses_source="MN107")
    # Correct: case insensitive
    s4 = SBS(id=4, discourses_source="mn107.1")
    
    in_memory_db.add_all([s1, s2, s3, s4])
    in_memory_db.commit()
    
    name, results, count, solution = check_discourses_source_prefix(in_memory_db)
    assert count == 1
    assert re.search(r"2", results)

def test_sbs_example_population_logic(in_memory_db):
    from db_tests.sbs_consistency_tests import check_sbs_example_consistency
    
    # 1. Correct: all 6 populated
    s1 = SBS(
        id=1, 
        sbs_source_1="so", sbs_sutta_1="su", sbs_example_1="ex", 
        sbs_chant_pali_1="pa", sbs_chant_eng_1="en", sbs_chapter_1="ch"
    )
    # 2. Violation: one missing (sbs_chapter_1)
    s2 = SBS(
        id=2, 
        sbs_source_1="so", sbs_sutta_1="su", sbs_example_1="ex", 
        sbs_chant_pali_1="pa", sbs_chant_eng_1="en", sbs_chapter_1=""
    )
    # 3. Correct (Exception): sbs_source is "Trad", sbs_sutta can be empty
    s3 = SBS(
        id=3, 
        sbs_source_1="Trad", sbs_sutta_1="", sbs_example_1="ex", 
        sbs_chant_pali_1="pa", sbs_chant_eng_1="en", sbs_chapter_1="ch"
    )
    # 4. Correct: all empty
    s4 = SBS(id=4, sbs_source_1="", sbs_sutta_1="")

    # 5. Check _2 fields: violation
    s5 = SBS(
        id=5, 
        sbs_source_2="so", sbs_sutta_2="su", sbs_example_2="ex", 
        sbs_chant_pali_2="", sbs_chant_eng_2="en", sbs_chapter_2="ch"
    )
    
    in_memory_db.add_all([s1, s2, s3, s4, s5])
    in_memory_db.commit()
    
    name, results, count, solution = check_sbs_example_consistency(in_memory_db)
    assert count == 2
    assert re.search(r"2", results)
    assert re.search(r"5", results)

def test_sbs_index_mapping_logic(in_memory_db):
    from unittest.mock import patch, mock_open
    from db_tests.sbs_consistency_tests import check_sbs_index_mapping
    
    # Mock CSV data
    csv_content = (
        "index\tpali_chant\tenglish_chant\tchapter\tlink\n"
        "1\tPali1\tEng1\tChap1\tlink1\n"
        "2\tPali2\tEng2\tChap2\tlink2\n"
    )
    
    # 1. Correct mapping
    s1 = SBS(id=1, sbs_chant_pali_1="Pali1", sbs_chant_eng_1="Eng1", sbs_chapter_1="Chap1")
    # 2. Violation: Incorrect Eng mapping
    s2 = SBS(id=2, sbs_chant_pali_1="Pali1", sbs_chant_eng_1="WRONG", sbs_chapter_1="Chap1")
    # 3. Violation: Incorrect Chapter mapping
    s3 = SBS(id=3, sbs_chant_pali_2="Pali2", sbs_chant_eng_2="Eng2", sbs_chapter_2="WRONG")
    # 4. Correct mapping for _2
    s4 = SBS(id=4, sbs_chant_pali_2="Pali2", sbs_chant_eng_2="Eng2", sbs_chapter_2="Chap2")
    
    in_memory_db.add_all([s1, s2, s3, s4])
    in_memory_db.commit()
    
    with patch("builtins.open", mock_open(read_data=csv_content)):
        name, results, count, solution = check_sbs_index_mapping(in_memory_db)
        assert count == 2
        assert re.search(r"2", results)
        assert re.search(r"3", results)