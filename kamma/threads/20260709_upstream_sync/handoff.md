# Handoff: Upstream Sync 2026-07-09

## Status

**Stage 3 (FAST execution) — Batches A–F DONE ✓. Batch G verification battery RUN: all sync-related
checks pass; 2 PRE-EXISTING broken tests block the "all sync tests pass" criterion. AT COMMIT 2 GATE,
awaiting user decision on the pre-existing tests + commit approval. No Commit 2 yet.**

Commit 1 landed (`699c10cd1`) in a prior session; the automated pull is done. Batches A, B,
B-completion, C, D, E, F are DONE + verified from files.

### Batch G battery results (all run this session)
- `test_shadow_cleanup` ✓ · `test_template_syntax` ✓ (178) · `check_shadow_modifications` ✓ (S9
  titlepage no-op re-keyed to sync_commit `699c10cd1…` in `reviewed_shadow_noops.json`) ·
  `smoke_test_sync` ✓ (25) · `validate_registry` ✓ · ruff/format/pyright on all 22 hand-edited files
  ✓ 0 errors (formatted `export_variant_spelling_ru.py`) · `test_ai_manager` ✓ (20) · import smoke ✓.
- **BLOCKER (pre-existing, NOT this sync):** `test_shadow_parity` (collection error) +
  `test_namespace_isolation` (30 fail). Both helpers (`get_python_pairs`/`get_test_cases`) iterate
  `registry[cat].items()` treating the value as an upstream-path string, but the schema is
  `{shadow: {upstream: str, …}}` since `bdddb9e3c`. Fails at HEAD too, on shadows this sync never
  touched. Fix = 1 line in each helper (`upstream` → `upstream["upstream"]`). Out of sync-port scope —
  needs user approval to touch test files (or spin a separate thread).
- **NOTICED — NOT TOUCHING:** `registry.json` ~line 375 has a stale `(help_ru)` parenthetical (should
  be `reference_ru` post-D7); outside §7 scope.

### Commit 2 staging state (flattened from Batch D stash/pop)
7 files staged / 56 unstaged (non-`resources/`); D7 rename split into ` D shared_data/help_ru/*`
(unstaged) + `A  shared_data/reference_ru/*` (staged). Restage the full non-`resources/` changeset so
git re-detects the rename by content. `resources/*` submodules dirty — EXCLUDE from commit.
Prepared message: `#sync: manual merge resolutions 2026-07-09`.

## Batch ledger (Stage 3) — unchanged from prior session, kept for continuity

- **Batch A — DONE ✓** Registry-flagged manual merges (D1–D6, D8, D13). Report:
  `stage3_batchA_report.md`.
- **Batch B — DONE ✓** Simple ports + rename + removals (S1–S3, S9–S13, D7, D11, D12). Report:
  `stage3_batchB_report.md`.
- **Batch B-completion — DONE ✓** `tools/cst_source/__init__.py` materialized (gitignored-package
  gap), `docs/pics/kindle/*.png` `git rm`'d, `docs_setup_guide.md` untracked to `temp/`.
- **Batch C — DONE ✓** Header-once / no-ORM-mutation shadow ports (S4–S8). Report:
  `stage3_batchC_report.md`.
- **Batch D — DONE ✓ (open item RESOLVED)** I3–I8 (except I1/I2), I11, I14; I9/I10/I13 confirmed
  no-op. `main_sbs.py` pre-existing pyright `RenderedSizes` mismatch fixed via `cast` at the 2
  append sites (ADVANCED decision, documented). Report: `stage3_batchD_report.md`.
- **Batch E — DONE ✓** I1 `export_dpd_ru.py` + I2 `export_dpd_sbs.py` both ported from
  `multiprocessing.Process` → `ProcessPoolExecutor`/`_worker_init`/`_render_batch` (upstream
  `export_dpd.py` skeleton), re-layering RU (I1: `.ru` joinedload, `Russian.id.isnot(None)`, `rupth`,
  `ru_components/templates`, `dpd_headword_ru.jinja`, RU synonyms) and SBS (I2: `dpspth`,
  `.ru/.ta/.sbs` joinedloads, 4 locale flags threaded through worker render data, `sbs_templates`,
  `dpd_headword_sbs.jinja`; NO Russian filter — SBS exports every headword, matches pre-sync). Both
  dropped the pre-sync `joinedload(DpdHeadword.rt)` per the new upstream pattern (perf-only —
  extraction runs in the main process where lazy load still works — NOT a correctness change;
  **Stage-4 runtime watch item**). The `{**TypedDict,...}` pyrefly limitation resolved on BOTH via
  localized `cast(DpdHeadwordRenderData, {...})` (ADVANCED decision, Batch D `cast` precedent —
  runtime no-op). All 5 gates green on both files (import, ruff, format, pyright 0/0/0, pyrefly 0);
  combined import smoke OK. Verified from files.

**⚠️ INDEX STAGING STILL FLATTENED from Batch D's stash/pop** (see prior handoff for detail) —
redo staging cleanly at the Batch G commit gate; content is intact, only staging state is cosmetic.

## This dispatch — Batch E, item I1 (`export_dpd_ru.py`)

**Scope:** port `exporter/goldendict/export_dpd_ru.py` from the old `multiprocessing.Process`
architecture to the new upstream `ProcessPoolExecutor`/`_worker_init`/`_render_batch` architecture
(template: `git show be49bffe2c2c:exporter/goldendict/export_dpd.py`), re-layering every RU
specialization the old local file had over OLD upstream (`518672a65fa3:exporter/goldendict/export_dpd.py`).
Touched ONLY `exporter/goldendict/export_dpd_ru.py`.

**Architecture now in place (confirmed, no more `multiprocessing.Process`):**
- `ProcessPoolExecutor` + module-level `_WORKER_RENDER_DATA` + `_worker_init` + `_render_batch`
  (replaces `Manager`/`Process`/`_parse_batch_top_level`/`ListProxy`).
- Preloaded `fc_map`/`fi_map`/`fs_map` family maps built once in `generate_dpd_html`, looked up via
  new `_lookup_family_compounds`/`_lookup_family_idioms`/`_lookup_family_set` + `_dedupe_keys`
  (replaces the old per-headword `get_family_compounds`/`get_family_idioms`/`get_family_set` calls
  and their import from `tools.exporter_functions`, which is now unused/removed from imports).
- `_base_dpd_query` + `_iter_dpd_row_pages` keyset low-mem paging (single page ordered by
  `lemma_1` in default/high-mem mode; keyset pages ordered by `id` in low-mem mode).
- Streaming progress via `as_completed` + `report_every = 5000` counter (replaces the old
  per-offset `pr.counter` call gated on `offset % limit == 0`).
- Single-pass synonyms contraction (list comprehension instead of the old mutate-while-iterating
  loop) — upstream's exact fix, applied verbatim.

**RU specializations re-layered on top (all preserved from the old local file):**
- `DpdHeadwordDbRowItems` / `DpdHeadwordDbParts` carry a 4th element / `ru: Russian` key (upstream's
  is 3-tuple / no `ru` key).
- `DpdHeadwordRenderData.pth: RuPaths` (not `ProjectPaths`).
- `_base_dpd_query` adds `.outerjoin(Russian, DpdHeadword.id == Russian.id)`,
  `.options(joinedload(DpdHeadword.ru))`, `.filter(Russian.id.isnot(None))` — upstream's bare
  version has none of this (3-way join only, no joinedload at all). Per the dispatch recipe, the RU
  file previously ALSO had `joinedload(DpdHeadword.rt)`; that one was DROPPED to match the new
  upstream pattern (which does not eager-load `.rt` anywhere — `pw.rt` is accessed lazily in
  `_add_parts`, same for RU now). Only `joinedload(DpdHeadword.ru)` was kept, per the explicit
  recipe instruction ("keep `joinedload(DpdHeadword.ru)`" — no mention of `.rt`).
- `pali_words_count` query keeps the RU-specific `.join(Russian, ...).filter(Russian.id.isnot(None))`
  (upstream's is a bare count).
- `_worker_init` loads the jinja env from `"exporter/goldendict/ru_components/templates"` (RU's own
  template dir), not `"exporter/goldendict/templates"`.
- `render_pali_word_dpd_html` uses `HeadwordData` from `exporter.goldendict.data_classes_dps` (not
  `data_classes`), passes `ru=ru`, renders `dpd_headword_ru.jinja` (not `dpd_headword.jinja`), and
  measures `data.ru_meaning` for `size_dict["dpd_summary"]` (not `data.meaning_combo_html`).
- Synonyms: kept the RU-only `set_ru_dict = read_set_ru_from_tsv()` block appending translated set
  names, kept `if i.su and i.needs_sutta_info_button:` (note: OLD upstream already had this without
  the `i.su and` guard — the guard is an RU-specific defensive addition present in the old local
  file, preserved verbatim; not part of what upstream changed in this sync).
  Verified `HeadwordData.__init__` (`data_classes_dps.py`, untouched) accepts `ru: Russian | None`
  and only needs `ru=ru` — the newer `show_ru_data` flag on that class is for the SBS combined
  dict (`export_dpd_sbs.py`), not the pure-RU dict; the RU template only branches on `d.ru`
  truthiness, so no new flag was added to the `HeadwordData(...)` call (matches old file exactly).
- Param name `rupth: RuPaths` (not `pth: ProjectPaths`) kept on `generate_dpd_html`, threaded into
  `ProcessPoolExecutor(initargs=(render_data, rupth))`.
- No `_ru`-suffixed function names were introduced for the new helpers (`_base_dpd_query`,
  `_iter_dpd_row_pages`, `_lookup_family_*`, `_dedupe_keys`, `_worker_init`, `_render_batch`) —
  matches the old file's own convention, where none of its internal functions carried a `_ru`
  suffix (only types/vars like `Russian`, `RuPaths`, `rupth`, `set_ru_dict`, `ru_set_list`, and the
  `_ru` template filenames were locale-marked). The file itself already carries the `_ru` suffix.

## Verification results (run individually on the exact file)

1. `uv run python -c "import exporter.goldendict.export_dpd_ru"` → **PASS**, no output.
2. `uv run ruff check exporter/goldendict/export_dpd_ru.py` → **PASS**, "All checks passed!"
3. `uv run ruff format exporter/goldendict/export_dpd_ru.py` → **PASS**, "1 file left unchanged"
   (already correctly formatted).
4. `uv run pyright exporter/goldendict/export_dpd_ru.py` → **PASS**, "0 errors, 0 warnings, 0
   informations" (pyright version-update notice only, not an error).
5. `uv run --with pyrefly pyrefly check --min-severity warn exporter/goldendict/export_dpd_ru.py`
   → **FAIL** (1 error) — see flagged judgment call below.

## FLAGGED — judgment call for ADVANCED, not silently resolved

`pyrefly` reports:
```
ERROR `dict[str, Environment | RuPaths | object]` is not assignable to variable
`_WORKER_RENDER_DATA` with type `DpdHeadwordRenderData | None` [bad-assignment]
  --> exporter/goldendict/export_dpd_ru.py:177  (the `_WORKER_RENDER_DATA = {**render_data, "pth":
      path, "jinja_env": ...}` literal inside `_worker_init`)
```

I confirmed this is **not caused by the RU port** — the byte-for-byte identical construct in the
untouched upstream template file itself fails the same way:
```
uv run --with pyrefly pyrefly check --min-severity warn exporter/goldendict/export_dpd.py
→ ERROR `dict[str, Environment | ProjectPaths | object]` is not assignable to variable
  `_WORKER_RENDER_DATA` with type `DpdHeadwordRenderData | None` [bad-assignment]  (same line shape)
```
This is a pyrefly limitation with TypedDict-spread (`{**base_typed_dict, "extra_key": val}`)
literals, inherent to the new upstream architecture I was told to port verbatim (`export_dpd.py`
is out of scope — I must not touch it). Two conflicting rules apply:
- "TOUCH A FILE = OWN ITS LINT" / "pyrefly warnings count as failures" → I own this file now, must
  fix it.
- "Strict Parity: for shadow copies, maintain strict logic parity with upstream. DO NOT introduce
  new solutions. Emulate upstream implementation exactly." + the recipe's explicit instruction to
  treat `export_dpd.py`'s `_worker_init`/`_WORKER_RENDER_DATA` pattern as the structural skeleton →
  diverging the dict-construction shape here to satisfy pyrefly would no longer be an exact mirror
  of upstream's (accepted, currently-shipped) pattern.

There is a known precedent for ADVANCED resolving a similar pre-existing type-checker conflict
during this same sync: Batch D's `main_sbs.py` `RenderedSizes` TypedDict mismatch was fixed with a
localized `cast(RenderedSizes, sizes)` at the 2 append boundaries (see "Batch D — DONE" above and
`stage3_batchD_report.md` §I8). A structurally analogous fix here (e.g. `cast` the dict literal, or
build `_WORKER_RENDER_DATA` via an explicit typed constructor instead of `**`-spread) is plausible
and would be behavior-preserving (runtime no-op), but I have NOT applied it — per the sync-fast
contract, a plan item requiring judgment/new-implementation decisions must be flagged, not silently
improvised. I did not modify the file further after finding this.

**RESOLVED by ADVANCED (2026-07-10):** applied the same `cast`-style localized fix used for
`main_sbs.py` — `_WORKER_RENDER_DATA = cast(DpdHeadwordRenderData, {...})` + `cast` added to the
`typing` import + an explanatory comment. Runtime no-op; the spread literal genuinely has every
`DpdHeadwordRenderData` key. pyrefly now 0 diagnostics. Same fix pre-authorized for and applied to
I2. I1 is fully complete and verified. (This FLAGGED section retained as the historical record.)

## Files changed in Batch E (both verified from files, NOT staged, NOT committed)

- `exporter/goldendict/export_dpd_ru.py` — architecture port + RU re-layering + `cast` fix.
- `exporter/goldendict/export_dpd_sbs.py` — architecture port + SBS re-layering + `cast` fix.

## Next action — AT COMMIT 2 GATE (user decision required)

1. **User decides the 2 pre-existing broken tests** (`test_shadow_parity`, `test_namespace_isolation`):
   approve the trivial in-scope-adjacent fix (each helper `upstream` → `upstream["upstream"]`), or defer
   to a separate thread. These are NOT sync-port defects; do not fix without approval.
2. **User approves Commit 2.** Then restage the full non-`resources/` Stage-3 changeset (so the D7
   rename is detected) and commit `#sync: manual merge resolutions 2026-07-09`. No autonomous commit —
   AI prepares, user runs.
3. After Commit 2: **Stage 4** (ADVANCED acceptance — user manual GoldenDict/webapp check, then
   `retrospective.md`, promote items, `finalize_accepted_sync.py`) + the async **Docs Track**
   (`docs_translation_plan.md`, still pending — see plan.md). Stage-4 TODO: reset
   `accepted_sync.json.last_accepted_upstream_ref` back to `"upstream/main"` (see plan.md §1.5 PIN NOTE).
   **Stage-4 runtime watch item:** I1/I2 dropped `joinedload(DpdHeadword.rt)` — verify the RU/SBS
   GoldenDict builds render root data correctly under the new ProcessPoolExecutor paging.

Restart with `/kamma:2-do kamma/threads/20260709_upstream_sync` if handing off — a fresh ADVANCED
orchestrator reads this ledger and resumes at the Commit 2 gate.
