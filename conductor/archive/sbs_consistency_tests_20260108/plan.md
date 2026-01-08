# Implementation Plan: SBS Example Consistency Tests

**Phase 1: Research & Setup**
- [x] Task: Research: Review existing data integrity tests in `db_tests/` to ensure consistent reporting format.
- [x] Task: Create the test script skeleton `db_tests/sbs_consistency_tests.py` and make it executable.
- [x] Task: Conductor - User Manual Verification 'Research & Setup' (Protocol in workflow.md)

**Phase 2: Core Logic & Initial Tests (TDD)**
- [x] Task: Write failing unit tests in `tests/test_sbs_consistency.py` that mock database records for `pat` and `dhp` violations.
- [x] Task: Implement `pat` and `dhp` consistency checks in `db_tests/sbs_consistency_tests.py` to pass the tests.
- [x] Task: Write failing unit tests for `vib`, `class`, and `discourses` triplets.
- [x] Task: Implement `vib`, `class`, and `discourses` triplet checks.
- [x] Task: Refactor DHP consistency check into two separate rules for better clarity.
- [x] Task: Implement exception for `check_class_consistency` (class_anki == 2 and specific words).
- [x] Task: Conductor - User Manual Verification 'Core Logic & Initial Tests' (Protocol in workflow.md)

**Phase 3: Advanced Logic (TDD)**
- [x] Task: Write failing unit tests for `class_anki` logic (including `class_example_translation`).
- [x] Task: Implement `class_anki` and `class_example` relationship checks.
- [x] Task: Write failing unit tests for `discourses_source` prefix validation against `sbs_category_list`.
- [x] Task: Implement `discourses_source` prefix validation.
- [x] Task: Conductor - User Manual Verification 'Advanced Logic' (Protocol in workflow.md)

**Phase 4: Chanting & Mapping (TDD)**
- [x] Task: Write failing unit tests for `sbs_example_1/2` mandatory field logic and traditional source exception.
- [x] Task: Implement `sbs_example_1/2` field population checks.
- [x] Task: Write failing unit tests for `sbs_index.csv` mapping validation.
- [x] Task: Implement `shared_data/sbs_csvs/sbs_index.csv` lookup and validation logic.
- [x] Task: Conductor - User Manual Verification 'Chanting & Mapping' (Protocol in workflow.md)

**Phase 5: Integration & Finalization**
- [x] Task: Run the `sbs_consistency_tests.py` against the actual database and document all discovered errors.
- [x] Task: Verify that all tests in `tests/test_sbs_consistency.py` pass with the final implementation.
- [x] Task: Update `db_tests/README.md` to include information about the new SBS consistency tests.
- [x] Task: Conductor - User Manual Verification 'Integration & Finalization' (Protocol in workflow.md)