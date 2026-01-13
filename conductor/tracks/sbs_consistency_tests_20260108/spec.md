# Specification: SBS Example Consistency Tests

**Overview**
Implement a suite of data integrity tests to ensure consistency across the SBS (Sasanarakkha Buddhist Sanctuary) table and its relationships with the `dpd_headwords` table. These tests will validate example-source mappings, chanting details, and class information.

**Functional Requirements**

1.  **`pat` (Patimokkha) Consistency**
    *   If `SBS.pat_example` is present, `SBS.pat_source` must contain "VIN PAT".
    *   If `SBS.pat_source` contains "VIN PAT", `SBS.pat_example` must not be empty.
    *   If any of `pat_example`, `pat_source`, or `pat_sutta` is present, all three must be present.

2.  **`dhp` (Dhammapada) Consistency**
    *   If `DpdHeadword.source_1` or `DpdHeadword.source_2` contains a pattern matching `DHP\d+` (DHP followed by digits), then `SBS.dhp_source` must not be empty.
    *   If any of `dhp_example`, `dhp_source`, or `dhp_sutta` is present, all three must be present.

3.  **General Source-Example Triplets**
    *   For the following pairs: `vib` (Vibhanga), `class`, and `discourses`:
        *   If the `_example` field is present, the corresponding `_source` and `_sutta` fields must also be present.

4.  **`class` (SBS Class) Specific Logic**
    *   There must be a 1:1 relationship between `SBS.class_example` and `SBS.class_anki`.
    *   If `SBS.class_anki` is not "1" (or 1), then `SBS.class_example` AND `SBS.class_example_translation` must have values.

5.  **`discourses_source` Validation**
    *   The prefix of `SBS.discourses_source` (the part before the first `.`, e.g., "SN12" in "SN12.2") must exist in the `sbs_category_list` defined in `tools/sbs_table_functions.py` (case-insensitive check).

6.  **`sbs_example_1/2` (Chanting) Consistency**
    *   Each set of 6 related fields (`sbs_source_1/2`, `sbs_sutta_1/2`, `sbs_example_1/2`, `sbs_chant_pali_1/2`, `sbs_chant_eng_1/2`, `sbs_chapter_1/2`) must be fully populated if any one of them has a value.
    *   **Exception**: If `sbs_source_1/2` is one of `["Trad", "Sri Lanka", "Thai", "MJG"]`, then `sbs_sutta_1/2` is allowed to be empty (optional).

7.  **Chanting/Chapter Mapping Validation**
    *   For `sbs_example_1` and `sbs_example_2`, the combination of `sbs_chant_pali`, `sbs_chant_eng`, and `sbs_chapter` must match a valid row in `shared_data/sbs_csvs/sbs_index.csv`.

8.  **Bold Tag Verification in Examples**
    *   All SBS-related example fields must contain both start `<b>` and end `</b>` tags if the field is not empty.
    *   **Fields to check**:
        *   `sbs_example_1`
        *   `sbs_example_2`
        *   `dhp_example`
        *   `pat_example`
        *   `vib_example`
        *   `class_example`
        *   `discourses_example`
    *   **Reporting**: The output must be categorized by the specific example field (e.g., "Missing bold tags in dhp_example") to clearly identify the source of the error.

9.  **Class Example Translation Uniqueness**
    *   Each unique `class_example_translation` should ideally correspond to only one `class_source`.
    *   **Normalization**: Both `class_example_translation` and `class_source` must be stripped of leading/trailing whitespace before comparison to avoid false positives.
    *   **Reporting**: If the same translation is used across different sources, it must be flagged. The output must group problematic sources by their shared translation for easier investigation.

**Acceptance Criteria**
*   A new test module `db_tests/sbs_consistency_tests.py` is created.
*   The script `db_tests/sbs_consistency_tests.py` is made executable (`chmod +x`).
*   The test script identifies and reports all records violating the above rules.
*   Tests are integrated into the project's testing workflow.
*   No regressions in existing database tests.
