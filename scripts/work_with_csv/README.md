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

## Grammar deck source (`anki_class_grammar.py`)
The "Grammar Pali Class" data is no longer downloaded from Google Sheets. The source is `shared_data/pali_class/grammar/*.tsv`, one TSV per former sheet, maintained by the agent. `sheet_order.txt` in the same folder lists the sheet names in order; row order in `cl_sum_gramm.csv` follows it. To add a sheet, create `<name>.tsv` and add `<name>` as a line in `sheet_order.txt` (the extractor warns about a TSV missing from the manifest, or a manifest entry without a file). The old downloader is archived at `scripts/dps_archive/download_grammar.sh`.

## Pātimokkha deck source (`pat_for_anki.py`)
The Pātimokkha word-by-word data is no longer downloaded from Google Sheets. The source is `../sasanarakkha/study-tools/data/patimokkha_word_by_word.tsv` (`dpspth.pat_source_path`), one row per word, bold kept as `<b>…</b>`; edit it in the study-tools repo (a pre-commit hook there regenerates the Markdown pages). `pat_for_anki.py` keeps, per word, the first row that has a `pos` (words compared without `<b>` tags and surrounding whitespace) and only if its `meaning` is non-empty. The old `#` column no longer exists. `xlsx2csv.py` and its test are archived in `scripts/dps_archive/`.
