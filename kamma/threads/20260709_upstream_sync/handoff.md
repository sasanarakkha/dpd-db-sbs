# Handoff: Upstream Sync 2026-07-09

## Status

**Stage 3 (FAST execution) — Batches A–G DONE ✓. COMMIT 2 LANDED: `426aa64fc` (60 files),
pre-commit hook fully green. Next boundary: Stage 4 (ADVANCED acceptance + retrospective).**

Commit 2 resolution notes:
- 2 pre-existing broken test helpers (rich-object registry schema) fixed in `test_shadow_parity.py`
  + `test_namespace_isolation.py`; 3 intentional divergences whitelisted. User authorized.
- Pre-commit **pyrefly** (not pyright — pyright excludes gui2, pyrefly has no config so it checks
  every staged file) blocked on 18 pre-existing errors in `gui2/dps_example_field.py`. User chose to
  fix (rejected the config-exclusion option). Fixed with `cast()` accessors (`_stash`/`_view`/
  `_active_page`) for the intentional incompatible base-attribute overrides, `cast(ft.ControlEvent,
  None)` for the base handler that ignores `e`, and renamed `get_fields`→`get_fields_dps` (all base
  callers child-overridden; no external caller — behavior preserved). 0 pyrefly diagnostics, import OK.
- Excluded from commit (intentional): kindle build artifacts (`titlepage.xhtml`, `content.opf`,
  `shared_data/changed_templates`) and all `resources/*` submodule pointers — still dirty in tree.

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

## Stage 4 verification findings (2026-07-10, live build run)

User ran `scripts/cl/dpd-build-db` (→ `scripts/bash/initial_build_db.py`). Two issues surfaced:

1. **D7 rename regression — FIXED.** `main_sbs.py` → `export_help_sbs.py` → `add_abbrev_html` crashed
   `FileNotFoundError: shared_data/help_ru/abbreviations.tsv`. Root cause: D7 renamed
   `shared_data/help_ru/` → `shared_data/reference_ru/` and updated `tools/paths_ru.py` (RuPaths) but
   **missed the sibling `tools/paths_dps.py` (DPSPaths)** — Atomic Rename Protocol miss. Fixed
   `paths_dps.py` lines 99–108: all 5 TSV paths + comment `help_ru` → `reference_ru`, mirroring the
   already-correct `paths_ru.py`. Verified: ruff/format/pyright clean; `DPSPaths()` all 5 TSV paths now
   resolve to existing files under `shared_data/reference_ru/`. **Retrospective "landed" item.** Grep
   confirmed no other stale `help_ru` *path* references in code (remaining hits are identifiers:
   `add_help_ru`, `help_ru_pack`, `export_help_ru.py`, `help_help_ru.jinja`).
2. **Soft error, NOT sync-related.** `audio/db_release_download.py` "no archive found" — file untouched
   in the sync range; the external `dpd-audio` latest GitHub release currently has no `.tar.gz` asset.
   Graceful (build continued). No sync action.

3. **`scripts/build/tarball_db.py` — NOT a bug, no change.** SBS build OK; the RU build
   (`make_ru_dpd.sh`) crashed at `tar -I "xz -9e -T0"` on macOS bsdtar (GNU-tar-only syntax). But this
   file is **upstream-only and runs on Linux CI** (`ru_release.yml`, `ru_release_test.yml`,
   `draft_release.yml` each call it directly at ~line 294/277) — where GNU tar works. It only failed
   because the user ran the full `dpd-makedict` locally. Investigated a pipe-based local patch, then
   **reverted to pristine upstream** (would be a needless permanent divergence). **User themselves
   commented out the local `tarball_db.py` call in `make_ru_dpd.sh`** — resolved on the user side. No
   sync action, no registry entry.
4. **`scripts/cl_dps/*` CWD hardening — DONE (separate concern, user-requested, NOT sync).** 5 wrappers
   (`decks`, `dpd-anki`, `dpd-makedict`, `dpd-push`, `dpd-review-comments`) called `uv run tools/ask.py`
   (relative path) before cd'ing to the repo root → failed when run from PATH outside the root. Added a
   `cd` to repo root at top of each; verified (`bash -n` + live `/tmp` run). Commit separately from the
   sync, e.g. `fix(cl_dps): cd to repo root so wrappers run from any cwd`.

**Confirmed working:** user re-ran and reported the **SBS exporter completed successfully** after the
`paths_dps.py` fix (2026-07-10).

**Still open (NOTICED — NOT TOUCHING):** `registry.json` line 388 prose has a stale `(help_ru)`
parenthetical describing the RU exporter paths (should read `reference_ru` post-D7). Doc-only; does not
affect `validate_registry.py` or runtime. Fix during finalize/cleanup if desired.

## Working-tree state at this handoff (2026-07-10)

**My sync fix (keep, commit with sync):** `tools/paths_dps.py` (D7 `help_ru`→`reference_ru`).
**My separate fix (commit separately):** `scripts/cl_dps/{decks,dpd-anki,dpd-makedict,dpd-push,dpd-review-comments}`.
**USER's own edits — DO NOT TOUCH:** `scripts/bash/make_ru_dpd.sh` (commented out local tarball call),
`scripts/bash/generate_components.sh` (toggled `db_release_download.py` + whitespace).
**Build side-effects / pre-existing (not sync, exclude):** `db/backup_tsv/{russian,sbs,sutta_info,tamil}.tsv`,
`gui2/data/addition_replaced.json`, `exporter/kindle/ru_components/epub/OEBPS/{titlepage.xhtml,content.opf}`,
`shared_data/changed_templates`, all `resources/*` submodules.

**Stage 4 still in progress:** user is running the local build (`dpd-makedict`) and surfacing issues one
by one. More issues to be reported in a fresh session. When the build completes cleanly + RU/SBS root
data renders correctly (the `joinedload(DpdHeadword.rt)` watch item), user says "all is good, proceed",
then ADVANCED writes `retrospective.md` (add the `paths_dps.py` D7-miss as a "landed" item) and runs
`finalize_accepted_sync.py`.

## Next action — STAGE 4 (ADVANCED acceptance) — user verification gate

Commit 2 is **LANDED** (`426aa64fc`). The 2 pre-existing broken tests were fixed inside Commit 2.
plan.md 3.1–3.4 all `[x]`. Remaining plan work: **Stage 4** + async **Docs Track**.

**Stage 4 gate (blocks on the USER — ADVANCED must not run builds/tests/pytest):**
1. **User manual verification** — build/spot-check RU + SBS GoldenDict and the webapp; confirm output
   correct. **Runtime watch item:** Batch E (I1/I2) dropped `joinedload(DpdHeadword.rt)` from
   `export_dpd_ru.py`/`export_dpd_sbs.py` under the new `ProcessPoolExecutor` paging — verify root data
   still renders (root, root family). `.rt` is now lazy-loaded in the main-process extraction step; this
   is perf-only by design, but is the one behavioral risk to eyeball. Do NOT proceed until the user
   says **"all is good, proceed."**
2. **Write `retrospective.md`** (copy `kamma/upstream_sync/templates/retrospective.md`) — landed /
   promote / drop buckets; promote items to `archive_improvements.md`. Hard-gate for finalize.
3. **Finalize** — after acceptance, ADVANCED may run `finalize_accepted_sync.py <thread_dir>` directly
   (pre-authorized scripted command). **Stage-4 TODO:** after finalize, reset
   `accepted_sync.json.last_accepted_upstream_ref` back to `"upstream/main"` (see plan.md §1.5 PIN NOTE:
   the +2 CI-only upstream commits `188600bbf`/`820113551` were deferred to the next sync).

**Docs Track (async, independent, non-blocking — its own session):** 5 queued items in
`kamma/upstream_sync/docs_translation_queue.md`. ADVANCED analysis needs FAST to first run
`check_docs_parity.py <thread_dir>` → `docs_parity_report.md`, then write `docs_translation_plan.md`.
Recommended to run AFTER the code sync is finalized, in a separate session.

Restart with `/kamma:2-do kamma/threads/20260709_upstream_sync` — a fresh ADVANCED orchestrator reads
this ledger and resumes at the Stage 4 user-verification gate.

## Addendum (2026-07-10, same-session Stage 4 continuation): Go deconstructor build findings

During Stage 4 user manual verification (`dpd-build-db` full rebuild), the RU deconstructor
GoldenDict/MDict output came out near-empty (`wordcount=0`). Root-caused to the **Go** deconstructor
(`go run go_modules/deconstructor/main.go`), not the Python exporter. Three upstream-caused bugs found
and fixed locally (NOT registered in `registry.json` per user instruction — treated as plain upstream
bugs, to be reported and reconciled against upstream's eventual fix, not preserved as permanent fork
divergences):

1. **`go_modules/dpdDb/model.go`** — `Lookup` struct was missing `AbbrevOther` (upstream added
   `abbrev_other` to `db/models.py` in #77 but never mirrored it to the Go struct) and this fork's
   local-only `Tpd` (Tamil) column. The Go deconstructor's `SaveToDb()` does `DELETE FROM lookup` then
   re-inserts every row through this struct — a NOT-NULL column missing from the struct fails the
   whole re-insert. Fixed: added both fields. `Tpd` is genuinely fork-local (mirrors `tpd` in
   `db/models.py`); `AbbrevOther` is a plain upstream oversight.
2. **`go_modules/deconstructor/data/matchdata.go` `SaveToDb()`** — neither `CreateInBatches(...)` nor
   `Commit()` checked `.Error`, so the NOT NULL failure above exited 0 and the broken/emptied `lookup`
   table shipped silently (this is the "build didn't stop" structural bug the user flagged). Fixed:
   both now `tools.HardCheck`'d, with `Rollback()` on insert failure.
3. **Batch size vs. SQLite variable limit** — fixing bug 1 pushed `CreateInBatches(updatedResults,
   2000)` from `2000×16=32000` params/statement to `2000×18=36000`, over SQLite's `32766`
   (`SQLITE_MAX_VARIABLE_NUMBER`) ceiling → `panic: too many SQL variables`. Fixed: batch size lowered
   to 1500 (`1500×18=27000`, safe margin). This is latent upstream too — the 16-column struct is
   already at ~97% of the ceiling, so upstream adding `abbrev_other` alone would trip it.

All three verified with `go build ./go_modules/...` (exit 0) after each edit. **User-confirmed
(2026-07-10): a full end-to-end `go run go_modules/deconstructor/main.go` run with all three fixes
applied together completes successfully** — this issue is CLOSED.

Upstream issue write-up (self-contained, ready to file in a fresh session):
`kamma/threads/20260709_upstream_sync/upstream_issue_suggestion_go_lookup_struct.md` — covers all
three bugs with repro, root cause, and fix diffs. Says explicitly these are local-only stopgaps meant
to be dropped/reconciled once upstream lands its own fix.

**Separately (not sync-related, user-requested), local build/export config work also done this
session** — not part of the upstream sync diff, but touches files in this working tree:
- `scripts/rus_exporter/set_config.py` — added a `build_full` profile (asserts every `generate.*`
  population toggle on; deliberately does not touch any exporter-output toggle). User later edited
  this profile's `make_variants` back to `"no"` themselves — respected as-is, not reverted.
- `scripts/bash/rebuild_db.sh` — applies `--profile build_full` at the top of the "Rebuild db from
  db/backup_tsv?" block, before population steps run.
- `config.ini` (gitignored, no commit impact) — briefly hand-edited then reverted back to `no` per
  user correction; the `set_config.py` profile is the intended mechanism, not a hand-edit.
- Confirmed (read-only, no changes) that `.github/workflows/ru_release.yml` is unaffected by any of
  this: CI uses the Python deconstructor path (`scripts/build/deconstructor_output_add_to_db.py`, a
  safe upsert-only sync) rather than the Go full-table-rewrite path, and already sets
  `make_variants=yes` via its own `release_full_ru` profile — so none of the Go bugs or the
  `build_full` profile apply to CI.

**Next action for this thread:** Go deconstructor db-population issue is CLOSED (confirmed working).
Resume at the Stage 4 gate exactly as described above (user says "all is good, proceed" →
`retrospective.md` → `finalize_accepted_sync.py`). Filing the upstream issue (from the linked
suggestion doc) is independent of this thread and can be done in any fresh session — it does not
block Stage 4 completion.

## Addendum (2026-07-10): Kindle mobi "256 KB" investigation — CLOSED, not a sync/CI issue

User's local `dpd-makedict` produced `ru-dpd-kindle.mobi` at ~256 KB (from a valid 19 MB epub).
Root-caused empirically (isolated byte-for-byte): the entries are wrapped in Amazon Kindle dictionary
markup (`<mbp:frameset>`/`<idx:entry>`/`<idx:orth>`/`<idx:infl>`). Calibre `ebook-convert` is not a
dictionary compiler — it silently strips content inside those tags (test: same entry with idx markup →
9 bytes / dropped; flattened to plain HTML → survives). `make_mobi()` uses Calibre only on `Darwin`;
the bundled `exporter/kindle/kindlegen` is a Linux 32-bit ELF (`exec format error` on macOS), so the
Mac path has never produced a valid dictionary mobi. **Pre-existing, NOT sync-caused** (upstream
`dpd-kindle.mobi` is equally broken; sync left the kindlegen invocation byte-identical).

**CI is fine:** `ru_release.yml` runs on `ubuntu-latest` → `make_mobi` `else` branch → kindlegen (which
understands idx:entry). Latest GitHub release (2026-06-02) `ru-dpd-kindle.mobi` = **73,555,698 bytes**
(healthy). `kindlegen_path.exists()` True. No fix needed for the release pipeline.

**Change made (user-requested, local-dev-only):** `exporter/kindle/kindle_exporter_ru.py` `make_mobi`
Darwin branch — replaced the misleading `pr.yes("Converted with Calibre")` with a `pr.amber(...)`
warning that the local .mobi is a broken stub and the valid one is built by CI. No logic change, no CI
impact, no registry change (edit to an existing shadow, not a rename/move/create). All 4 gates green
(ruff/format/pyright 0/0/0/pyrefly 0). Commit with the sync's separate local-fix batch, or standalone.

## STAGE 4 — FINALIZED (2026-07-10)

User gave acceptance ("all is good, proceed", incl. the `.rt` root-render watch item + mobi
investigation). Completed:
- `retrospective.md` written (Landed / Promote / Drop).
- Promoted §21 (Atomic Rename must sweep all `tools/paths_*.py`), §22 (Go struct ↔ `db/models.py`
  column parity), §23 (macOS local kindle builds are non-authoritative) into `archive_improvements.md`.
- `finalize_accepted_sync.py kamma/threads/20260709_upstream_sync` ran, exit 0. `verify_manifest`
  passed (8 acknowledged blockers warned-not-blocked; 0 discuss). `accepted_sync.json` advanced to
  `last_accepted_upstream_sha = be49bffe`.
- **PIN reset applied** (plan §1.5 TODO): `accepted_sync.json.last_accepted_upstream_ref` →
  `"upstream/main"`; SHA stays `be49bffe`. The +2 CI-only commits `188600bbf`/`820113551`
  (`.github/workflows/deconstructor_ci_test.yml`) are deferred to the next sync.
- `plan.md` Stage 4 boxes ticked.

**REMAINING (user's call — not auto-committed):**
1. Commit the working-tree fixes. Suggested split:
   - **Sync-related** (fold into the sync or a follow-up `#sync` commit): `tools/paths_dps.py` (D7
     miss), `exporter/kindle/kindle_exporter_ru.py` (mobi warning), `kamma/**` thread docs +
     `accepted_sync.json` + `archive_improvements.md` + `retrospective.md` +
     `upstream_issue_suggestion_go_lookup_struct.md`.
   - **Go stopgaps** (separate commit, local-only, to reconcile w/ upstream): `go_modules/dpdDb/model.go`,
     `go_modules/deconstructor/data/matchdata.go`.
   - **EXCLUDE**: all `resources/*` submodule pointers; build side-effects (`db/backup_tsv/*.tsv`,
     `gui2/data/*.json`, `exporter/kindle/ru_components/epub/OEBPS/{titlepage.xhtml,content.opf}`,
     `shared_data/changed_templates`); **USER's own edits** (`scripts/bash/make_ru_dpd.sh`,
     `scripts/bash/generate_components.sh`, `scripts/bash/rebuild_db.sh`, `scripts/rus_exporter/set_config.py`
     — confirm before touching).
2. **Docs Track** — still open (plan lines 99–115), independent async session. Run
   `check_docs_parity.py <thread_dir>` → write `docs_translation_plan.md` → translate. Non-blocking.
3. File the upstream Go issue from `upstream_issue_suggestion_go_lookup_struct.md` (any session).

Code sync is ACCEPTED and finalized. Only committing + the async Docs Track remain.
