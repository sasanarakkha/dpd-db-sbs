# scripts/work_with_csv/

## Purpose & Rationale
`scripts/work_with_csv/` provides utilities for processing CSV/TSV data — handling imports, conversions, and transformations needed to move data between spreadsheets and the database.

## Architectural Logic
"CSV Pipeline" pattern:
1. **Parse:** Reads CSV/TSV files with appropriate encoding and delimiter handling.
2. **Transform:** Applies data cleaning, mapping, and restructuring.
3. **Serialize:** Outputs to the target format (updated CSV, DB records, Anki files).

## Relationships & Data Flow
- **Input:** Raw CSV/TSV files from `shared_data/`, collaborators, or external tools.
- **Output:** Processed files for ingestion by `scripts/add/` or `scripts/change_in_db/`.
- **Format bridge:** Converts between XLSX ↔ CSV, and CSV ↔ DB records.

## Interface
- `uv run python scripts/work_with_csv/additions_processor.py`
- `uv run python scripts/work_with_csv/anki_class_grammar.py`
- `uv run python scripts/work_with_csv/pat_for_anki.py`
- `uv run python scripts/work_with_csv/xlsx2csv.py`
