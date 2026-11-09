# Review of uncommitted work (2026-11-09)

Review only — no files were edited. Method: HEAD → working tree compared row-by-row with
pandas (quote-safe, so cells with embedded newlines are handled), plus the loader logic
re-run read-only and the two grammar test files executed.

## What's in the working tree

| Bucket | Files | Nature |
|---|---|---|
| Thread cycles 0001–0004 | 47 grammar TSVs (`shared_data/pali_class/grammar/`) | 443 changed cells |
| Pre-thread, orphan | `grammar/samasa.tsv` | 1 cell (`kitaka` example `ceta` → `cetas`) — handoff says it was dirty before the thread, no cycle record |
| Unrelated task | `docs/abbreviations.md`, `shared_data/reference/abbreviations.tsv`, `shared_data/reference_ru/abbreviations.tsv`, `tests/tools/test_docs_update_abbreviations_fixtures.json` | 1 row (`interr` explanation) |
| New, untracked | `kamma/threads/20261109_grammar_tsv_fixes/` | thread docs + 4 cycles (~200 KB incl. audit report/proposals) |

## Verified clean (grammar TSVs)

- **Structure intact for all 61 sheets:** row/column counts equal `baseline.md`, column names
  unchanged, id order unchanged, no duplicate ids, no TSVs missing from `sheet_order.txt`,
  no CRLF / trailing-newline / encoding problems, `git diff --check` clean.
- **Loader totals match baseline:** `cl_sum_abbr 286 / cl_sum_sandhi 712 / cl_sum_gramm 1321`
  (recomputed read-only); 12 empty `native` cells = `cond.tsv`, as documented.
- **Only** `native` (402), `eng` (33), `gramma` (5), `pali` (3), `example` (1) changed —
  `pali` changes are trailing-space trims only; no other columns touched.
- **Provenance:** every changed cell traces to a documented cycle — 269 full matches to
  `0002_proposals.json`, all 54 `0004_proposals.json` values present, cycle 0001's 8 cells,
  cycle 0003's 5 / 25 / 45 cell batches, the 0002 decision list, and the three mechanical
  rules. **Zero rogue edits.** (Records total 502 "cells" vs 443 unique because later cycles
  re-edit cells already fixed earlier — e.g. 7 cells are in both 0002 and 0004; the numbers
  do not sum by design.)
- **Rule claims hold:** 0 Latin `o` left in native, 0 `вы` in rows labelled 2nd sg,
  0 `из ` left in genitive parts, `fam` → `fem` typo fixed (mana_prp:3500/35035),
  `<pr>` → `<br>` fixed (go_masc:52052 — `<pr>` appears nowhere else),
  `amonst` → `amongst`, `ghree` → `ghee`, `Виктор` → `победитель`, `привет, ад` → `ад`,
  `творог` etc.
- `uv run pytest tests/test_anki_class_grammar.py tests/test_anki_class_grammar_feedback.py`
  → 4 passed.

## Residual defects found

Not introduced wrongly, but the cycles touched these cells and left them half-done.

`a_pp` — the "uninflected participle" bulk fix (cycle 0003 item 2) only dropped `из ` and
left the participle nominative:

1. `a_pp` 37337 (`uppannāya`, gen sg): `(чего-то) возник` → should be `возникшего`
2. `a_pp` 3728 (`uppannānaṃ`, gen pl): `(чего-либо) возникло` → `возникших`
3. `a_pp` 3730 (`uppannassa`, gen sg): `(чего-либо) возник` → `возникшего`
4. `a_pp` 3707 (`niṭṭhitāya`, gen sg): `завершенного (чем-то)` → placeholder must be
   `(чего-то)` (the same cell's other parts already use `(чего-то)`)

Untouched, same family: `a_pp` 3736 `среди (чего-либо) возникло` (loc pl → `возникших`),
`a_pp` 37037 `в (чем-либо) …` (`чём`).

Other:

5. `u_adj` 40240 (`dummaṅkuyaṃ`, **fem** loc sg, explicitly approved):
   `в упрямом (одном)` — masculine placeholder for a fem label → `в упрямой (одной)`.
6. `pers_pron` 995: `ваши` should be `ваш` (untouched by the thread).

Also noted, by design / debatable: `anta_prp` now mixes conventions —
`(те, кто) уходят / живут / обитают` (plural agreement, applied) while
`(тех, кто) не знает` etc. remain singular. The deck also mixes `е`/`ё` inside single
cells (`завершенным` vs `завершённого`).

## Abbreviations change — one real problem

- Content is consistent: TSV (source of truth) + `reference_ru` + `docs/abbreviations.md`
  all carry the new `interr` text, and `docs/abbreviations.md` is byte-identical to freshly
  generated output (verified).
- **`tests/tools/test_docs_update_abbreviations.py::test_make_abbreviations_md_golden_master`
  FAILS.** Cause is *pre-existing*, not this edit: the fixture still holds `a compoun` while
  the TSV (and docs) have `a compound` since commit `503b9783d` "fix: typo in 'in comps'
  abbreviation description", which never regenerated the golden fixture. The uncommitted
  fixture edit hand-patched only the `interr` row, so the typo drift is still there — the
  fixture needs one real regeneration (or the one word fixed) for the suite to go green.
- Note this change is outside the grammar-TSV thread's documented scope (no cycle record,
  no `kamma/threads` entry).

## What was deliberately not run

`scripts/work_with_csv/anki_class_grammar.py` — it writes `temp/anki_csvs/` **and** rewrites
field-list `.md` files in the external `../sasanarakkha/study-tools` repo. Given the
"do not edit anything" instruction, its counting logic was reproduced read-only instead
(totals match baseline). External repo status unchanged: only pre-existing `?? kamma/draft/`.

## Suggested commit split (nothing staged or committed)

1. Grammar TSVs for cycles 0001–0004 + `kamma/threads/20261109_grammar_tsv_fixes/`
   (per-cycle draft messages are at the end of each `cycles/000N_*.md`).
2. Abbreviations `interr` fix together with a regenerated
   `test_docs_update_abbreviations_fixtures.json`.

Keep `samasa.tsv` out unless its origin is known.
