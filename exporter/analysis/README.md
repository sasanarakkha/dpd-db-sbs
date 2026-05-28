# Pali Passage Analysis

This folder contains the standalone DPD-backed Pali analysis pipeline.

## Runtime Folders

The first script run creates these folders automatically:

- `input/` - source text files and verse JSON extracted from CST.
- `reports/` - editable markdown study reports from Stage 1.
- `output/` - AI JSON, rendered markdown, and Stage 2 TSV/CSV exports.

Existing data from the old `exporter/mcp/` location has been moved here.

## Main Passage Workflow

1. Preview extraction without AI:

```bash
uv run python exporter/analysis/passage_extraction.py AN3.12
```

2. Run Stage 1 AI analysis:

```bash
uv run python exporter/analysis/study_passage.py
```

Enter a passage code such as `DHP1`, `SNP1`, `SN12.3`, or `AN3.12`. For multi-unit passages, select paragraphs or verses with inputs such as `1`, `1-3`, or `1-2 4`.

Stage 1 writes:

- `reports/<source>_study.md`
- `output/<source>_study.json`

3. Edit the markdown report:

- Delete rows you do not want in the final vocabulary export.
- Fix wrong DPD IDs in the first column.
- Keep component rows such as `- mano` under their parent compound when needed.

4. Run Stage 2 vocabulary export:

```bash
uv run python exporter/analysis/export_words_csv.py
```

Enter the same source used by the report, for example `SN12.3_p1`. Select `basic`, `advanced`, or `custom`.

Stage 2 writes:

- `output/<base-source>_words.csv`

For passage selections, Stage 2 keeps the selected report lookup (`SN12.3_p1`) but writes the canonical source (`SN12.3`) into the output filename and `source` column.

## Batch Verse Workflow

Extract CST verses into `input/`:

```bash
uv run python exporter/analysis/book_to_verses.py --book kn2
```

Analyze the extracted verses:

```bash
uv run python exporter/analysis/ai_batch_translate.py --book kn2
```

Use `--limit N` for a small batch and `--dry-run` to inspect work without AI calls.

Render one analyzed verse to markdown:

```bash
uv run python exporter/analysis/ai_pali_translate.py --book kn2 --verse DHP1
```

## Custom CSV Columns

Edit `column_options.py` and change `CUSTOM` to control the Stage 2 `custom` profile. Use keys from `REGISTRY`.
