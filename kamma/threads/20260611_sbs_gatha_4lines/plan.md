# Plan: Rearrange all gāthā in SBS examples into verse-line format

**GitHub issue:** [sasanarakkha/dpd-db-sbs#9 — arrange all gāthā in 4 lines](https://github.com/sasanarakkha/dpd-db-sbs/issues/9)
**Spec:** `kamma/threads/20260611_sbs_gatha_4lines/spec.md`

## Architecture Decisions

- **Do NOT reuse `clean_gatha` from `tools/cst_source_sutta_example.py`.** It
  re-cleans raw CST text (lowercasing, `".."` → `"."`, abbreviation stripping)
  — destructive on already-clean DB text containing `<b>` markup. The migration
  reimplements only its line rule as a pure function
  `split_gatha_lines(text: str) -> str`: preserve every existing `\n`; inside
  each existing line, split at `", "` and internal `". "`. Existing lines are
  never joined. Runs of short comma phrases stay together rather than becoming
  short isolated lines.
- **Script placement:** one-shot migration in
  `scripts/change_in_db/rearrange_sbs_gatha_lines.py` (existing pattern for DB
  data fixes; root folder stays clean). Pure transform lives in the script, not
  `tools/` — single consumer, one-shot.
- **Verse detection:** (a) any of the 8 example fields containing `\n`;
  (b) flat fields whose paired source field starts with a verse-only prefix.
  Prefix list compiled at implementation time from
  `SELECT DISTINCT <source>` values (expected: DHP, SNP, THAG, THIG, VV, PV…)
  and hardcoded as a constant with a comment.
- **Field→source pairing:** `sbs_example_1↔sbs_source_1`,
  `sbs_example_2↔sbs_source_2`, `dhp↔dhp_source`, `pat↔pat_source`,
  `vib↔vib_source`, `class↔class_source`, `discourses↔discourses_source`,
  `extra↔extra_source`. `class_example_translation` is English — data
  migration never touches it (display fix only).
- **Apply + report:** transform applied unconditionally to detected verses;
  results with line counts ∉ {4, 6} written to
  `temp/sbs_gatha_review.tsv` (id, field, source, before, after).
  Narrow high-risk outputs are also written to
  `temp/sbs_gatha_concerns.tsv`: changed output with more than 4 lines that
  still contains a genuinely short phrase line. Long one-word pādas are not
  concerns.
- **DPD transfer generation before apply:** dry-run helper
  `scripts/change_in_db/sbs_dpd_example_transfers.py` finds SBS example fields
  that can be replaced by `DpdHeadword.example_1/2` when `id`, source, and
  punctuation-stripped text match. It writes
  `temp/sbs_dpd_example_transfers.tsv`; it does not write the DB.
- **Durability:** DB update → regenerate `db/backup_tsv/sbs.tsv` via existing
  `backup_sbs()` in `scripts/backup/backup_dps.py`. User commits. The
  embedded git-commit step in `backup_dps.py` (~line 177) must NOT run —
  call `backup_sbs()` selectively.
- **No new shadow/registry entries:** `data_classes.py` /
  `data_classes_dps.py` are already tracked; one-shot `scripts/change_in_db/`
  scripts follow the existing untracked pattern (verified in Phase 3 via
  registry/coverage checks).

## Phase 1: Transform logic + migration script (TDD)

- [x] **1.1 Pure transform + tests.** Create
  `tests/test_rearrange_sbs_gatha_lines.py` first (Red), then implement
  `split_gatha_lines()` and `is_verse_source()` in
  `scripts/change_in_db/rearrange_sbs_gatha_lines.py` (Green). Test cases:
  2-pādas-per-line → 4 lines; flat 4-pāda → 4 lines; already-correct 4-line
  idempotent; 6-pāda idempotent; `<b>` markup preserved byte-for-byte aside
  from added line breaks; existing period-separated lines remain unjoined;
  internal `. ` splits; short comma phrase runs stay together; trailing
  `.`/`,` untouched; empty string → empty.
  → verify: `uv run pytest tests/test_rearrange_sbs_gatha_lines.py -v`, all pass
- [x] **1.2 Migration script body.** Iterate `sbs` rows via SQLAlchemy
  (`db_session`, model `SBS` from `db/models.py`); select targets per detection
  rules; `--dry-run` flag (default) prints per-field change counts via `pr`
  (`tools/printer`, call `pr.bip()` before timed work) and writes
  `temp/sbs_gatha_review.tsv`; `--apply` commits. Compile the verse-prefix
  constant from distinct source values first.
  → verify: `uv run python scripts/change_in_db/rearrange_sbs_gatha_lines.py`
  (dry-run) — counts plausible (~888 newlined + flat verse-source entries),
  review TSV written, DB unchanged (re-query shows same data)
- [x] **1.3 Phase validation.** Run all 5 quality-gate commands on the new
  script and test file, one at a time.
  → verify: ruff check/format, pyright, pyrefly clean; targeted pytest passes
- [x] **1.4 DPD transfer generator helper.** Create a dry-run script that finds
  safe same-id/source/text SBS examples that can be copied from DPD
  `example_1/2`, using punctuation/tag/space-insensitive text matching. Write
  the candidates to `temp/sbs_dpd_example_transfers.tsv` with before and
  after text; do not write to the DB.
  → verify: targeted pytest passes; dry-run TSV generated; DB unchanged

## Phase 2: Run migration + backup

- [ ] **2.1 Apply migration.** Run with `--apply`. Then spot-check known cases:
  DHP86 (`sbs_example_1`, was 2-line), DHP191/DHP406/DHP88 (`dhp_example`,
  were flat), SNP13 (`sbs_example_1`, 6-line, must be unchanged).
  → verify: sqlite queries show DHP86 example = 4 lines, DHP191 = 4 lines,
  SNP13 byte-identical to before
- [ ] **2.2 Global integrity check.** No multi-pāda lines remain in verse
  entries; prose untouched.
  → verify: sqlite — count of entries containing `\n` where any line contains
  `", "` is 0 (excluding review-TSV ids); total row count unchanged; flat-prose
  count unchanged except detected flat verses; review TSV line count reported
  to user
- [ ] **2.3 Regenerate backup.** Read `scripts/backup/backup_dps.py`
  entrypoint first; state command plus side effects; run only the
  `backup_sbs()` path — the embedded git commit step must NOT run.
  → verify: `git diff db/backup_tsv/sbs.tsv` shows only line-break insertions
  in example columns; no id/column drift; nothing was committed

## Phase 3: Exporter display fixes

- [ ] **3.1 Webapp newline conversion.** In `exporter/webapp/data_classes.py`
  `convert_newlines`, add `dhp_example`, `pat_example`, `vib_example`,
  `class_example`, `class_example_translation`, `discourses_example`,
  `extra_example` to `string_columns`. Add unit tests (staticmethod + dummy
  object) to the thread test file.
  → verify: targeted pytest passes; webapp smoke test — run webapp, open a
  headword with `dhp_example` (e.g. the DHP191 entry), confirm `<br>`
  rendering in SBS tab HTML
- [ ] **3.2 GoldenDict newline conversion.** In
  `exporter/goldendict/data_classes_dps.py`: add `class_example_translation`
  to `_convert_newlines_sbs`; change `_convert_newlines_ru` to
  `ru_notes.replace("\n", "<br>")`. Unit tests for both staticmethods.
  → verify: targeted pytest passes — ru_notes test asserts plain `\n`
  converts (covers the 35 affected rows)
- [ ] **3.3 Final validation.** Quality gates on both exporter files; registry
  and shadow-doc gate; cleanup check.
  → verify: all 5 quality-gate commands clean on changed files;
  `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` and
  `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` pass;
  no artifacts in repo root (`temp/` only); draft commit message prepared
  for user
