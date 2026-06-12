# Spec: Rearrange all gāthā in SBS examples into verse-line format

**GitHub issue:** [sasanarakkha/dpd-db-sbs#9 — arrange all gāthā in 4 lines](https://github.com/sasanarakkha/dpd-db-sbs/issues/9)
(moved from digitalpalidictionary/dpd-db#96)

## Overview

Verse examples (gāthā) in the `sbs` table are stored inconsistently: some have one
pāda per line (correct), some have two pādas per line, some are completely flat.
This thread normalizes all gāthā in all 8 SBS example fields to verse-line format
— one pāda per line — and fixes the exporters so the line breaks actually render
as `<br>` everywhere.

"4-line format" means one pāda per line: a standard 4-pāda gāthā becomes 4 lines;
legitimate 6-pāda verses (e.g. Ratana Sutta) become/stay 6 lines.

## Current behavior

- Line breaks are stored as `\n` in the DB (no `<br>` in stored data).
- Distribution across the 8 example fields (`sbs_example_1`, `sbs_example_2`,
  `dhp_example`, `pat_example`, `vib_example`, `class_example`,
  `discourses_example`, `extra_example`):
  - 4,025 entries already correct (4 lines), 561 six-line (mostly legit 6-pāda),
  - ~888 entries with 2/3/5 lines holding multiple pādas per line (wrong),
  - 20,560 flat entries — mostly prose, but some flat gāthās among them
    (confirmed at least 3 in `dhp_example`: DHP191, DHP406, DHP88).
- The line-splitting rule already exists: `clean_gatha` in
  `tools/cst_source_sutta_example.py:456` splits at `", "` → `",\n"`. New
  extractions via that tool already produce the correct format.
- Display gaps:
  - **Webapp** (`exporter/webapp/data_classes.py` `convert_newlines`): converts
    `\n`→`<br>` only for `sbs_example_1/2`; the other 6 example fields and
    `class_example_translation` (13 rows contain `\n`) render raw newlines
    (invisible in HTML).
  - **GoldenDict** (`exporter/goldendict/data_classes_dps.py`): covers all 8
    example fields but not `class_example_translation`; `_convert_newlines_ru`
    replaces only `"\n, "` instead of `"\n"` in `ru_notes` (35 rows contain `\n`).

## What it should do

1. **One-time data migration script** (local text transform, no LLM/CST
   re-extraction):
   - Before relying on heuristic punctuation splitting, generate a dry-run TSV
     of SBS example fields that can be copied from the matching
     `DpdHeadword.example_1/2`: same `id`, same source, and same text after
     stripping tags, punctuation, spaces, and case. This writes a TSV only; it
     does not write the DB.
   - Target rows:
     a. any of the 8 example fields already containing `\n` (known verse), and
     b. flat entries whose corresponding source field references a verse-only
        text (DHP, SNP, THAG, THIG, and similar verse-only source prefixes —
        exact prefix list compiled during implementation from distinct source
        values in the table).
   - Transform: normalize to one pāda per line inside each existing line:
     split at `", "` and at internal `". "`, while preserving existing `\n`
     exactly; never collapse or join existing lines. Do not split runs of
     short comma phrases (e.g. `asambādhaṃ, averaṃ, asapattaṃ.` or
     `kayirā ce, kayirāth'enaṃ,`)
     into separate lines. Flat entries become multiple lines by the same rules.
     Already-correct entries must be byte-for-byte idempotent.
   - Apply the transform even when the resulting line count is unusual
     (not 4 or 6), but write every unusual result to a review TSV
     (entry id, field, source, before, after) for manual checking.
   - Write a separate concern TSV for narrow high-risk results: changed output
     with more than 4 lines that still contains a genuinely short phrase line
     after the short-phrase merge. Long one-word pādas are valid and are not
     concern rows.
   - Bold markup (`<b>…</b>`) inside examples must be preserved untouched.
2. **Backup sync:** after the DB update, regenerate `db/backup_tsv/sbs.tsv` via
   `scripts/backup/backup_dps.py` logic so the change is durable across rebuilds.
3. **Exporter display fixes** (from issue comment; approved in plan review):
   - Webapp `convert_newlines`: add `dhp_example`, `pat_example`, `vib_example`,
     `class_example`, `class_example_translation`, `discourses_example`,
     `extra_example`.
   - GoldenDict `_convert_newlines_sbs`: add `class_example_translation`.
   - GoldenDict `_convert_newlines_ru`: replace `"\n"` → `"<br>"` in `ru_notes`
     (matching webapp behavior) instead of the current `"\n, "` quirk.

## Assumptions & uncertainties

- "4-line format" = one pāda per line (comma rule), not literally forcing 4
  lines; 6-pāda verses keep 6 lines. (Inferred from data + `clean_gatha`.)
- Existing DB line breaks are meaningful formatting and must not be converted
  to spaces. The migration only adds new line breaks where a single existing
  line contains multiple comma-separated pādas.
- The verse-source prefix list for flat-entry detection is a heuristic; entries
  it selects are verses by definition of the source text. Mixed prose/verse
  sources (e.g. AN, MN suttas) are NOT auto-detected when flat — out of scope.
- Pādas with genuine internal `", "` can over-split; the migration avoids the
  most obvious short comma-phrase runs, and remaining unusual results are
  caught via the review TSV.
- `ru_notes` newlines (35 rows) are intentional formatting that should render
  as line breaks, as webapp already does.

## Constraints

- Economy rule: pure local text manipulation; no batch LLM, no CST re-extraction.
- Migration script is one-shot; place under `scripts/change_in_db/` (not root).
- Shadow/registry rules: webapp `data_classes.py` and goldendict
  `data_classes_dps.py` are already-tracked local files; no new shadow files
  expected. One-shot `scripts/change_in_db/` scripts need no registry entry
  (matching existing pattern — verify during final validation).
- No autonomous git commits: `backup_dps.py` contains an embedded git commit
  step which must NOT run; call `backup_sbs()` selectively.
- Standard validation gate: ruff check/format, pyright, pyrefly, targeted pytest.

## How we'll know it's done

- DB query shows no remaining multi-pāda lines in verse entries (no line
  containing `", "` in any entry that has `\n`), excluding review-TSV cases.
- The flat verse-source entries (DHP191, DHP406, DHP88 in `dhp_example`) are
  split into one pāda per line.
- Review TSV exists listing all unusual line counts.
- DPD→SBS transfer TSV exists listing same-id/source/text candidates
  that can reduce heuristic migration risk.
- `db/backup_tsv/sbs.tsv` regenerated and diff reflects only the line-break
  changes.
- Webapp + GoldenDict render `<br>` for all 8 example fields,
  `class_example_translation`, and `ru_notes` (verified on a sample headword).
- All validation commands pass.

## What's not included

- Re-extracting examples from CST XML source.
- Detecting flat gāthās in mixed prose/verse sources (AN/MN/SN prose suttas).
- Changes to `tools/cst_source_sutta_example.py` (already produces correct format).
- Russian table example content changes (Russian table has no example fields;
  only the `ru_notes` rendering fix).
- Editing `class_example_translation` content (display fix only — English text).
- Tamil/Sinhala tables.
