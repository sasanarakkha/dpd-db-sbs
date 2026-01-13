# Session Context: Advanced Pāḷi Analysis Tool

## Current Status
- **Phase:** 1 (Robust Python Analyzer)
- **Progress:** Core analyzer logic refined, deduplication implemented, and tests passing.

## Key Implementation Details (Session Jan 9, 2026)
1. **Schema Change**: The `pali` field in the analysis JSON now always equals the input `token` (inflected form) for both top-level words and components.
2. **Grammar Formatting**: Inflection details are formatted as `"{grammar} of {lemma}"` (e.g., `"masc nom sg of buddha"`).
3. **Strict Filtering**:
   - **Gender matching**: Nouns now strictly match their headword gender (masc/fem/nt) against the lookup grammar string.
   - **Grammatical filtering**: Non-grammatical POS (`abbrev`, `root`, `suffix`, etc.) and headwords with `(gram)` in `meaning_1` are excluded by default (`grammatical=True`).
   - **Stem filtering**: Headwords with `!` or `-` in `stem` are filtered globally. (Note: `ind` words with `-` stem were initially excluded but then allowed to make tokens like `na` work).
4. **Compound Logic**:
   - Parts of compounds have `grammar=""` and are not duplicated by inflectional options.
   - Recursive breakdown of compounds correctly propagates the `is_compound_part` flag.
5. **Deduplication**: `analyze_sentence` now prevents duplicate sandhi options by checking if a deconstructor construction already exists as a headword.
6. **New Fields**: `compound_construction` has been added to the output.

## Outstanding Items & Decisions
- **GUI UX (Stage 3)**: Words like `antā` can have 51+ possibilities. 
  - **Decision**: Keep analyzer output flat for AI accuracy. 
  - **Plan**: Implement grouping by **Meaning/Headword** at the GUI layer to manage user scrolling.

## Files Modified
- `exporter/mcp/analyzer.py`
- `tests/test_analyze_sentence.py`
- `tests/generate_debug_dump.py` (debug utility)
