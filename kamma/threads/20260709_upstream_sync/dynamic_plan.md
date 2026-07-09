# Dynamic Plan: Upstream Sync 2026-07-09

- **Range**: `518672a65fa3` → `be49bffe2c2c` (`upstream/main`, 120 commits)
- **Upstream themes**: #157 makedict performance (raw-SQL lookup sync, exporter pool rewrite,
  header-once rendering, `shared_data/help/`→`shared_data/reference/` rename, `tools/paths.py`
  reorganisation + dead-attr pruning, bz2→xz db artifact, deconstructor/frequency Go rewrites);
  #162 gui2 workflow features (pass2x in-commentary tab, commentary stash, spelling dedupe);
  #197 AI analysis (`exporter/analysis/` refactors, antigravity CLI, deepseek truncation fix);
  `tools/cst_source_sutta_example.py` → `tools/cst_source/` package split.
- **Sub-stage status**: 2a classification COMPLETE · 2b discuss COMPLETE (all D1-D13 resolved) · 2c literal edits COMPLETE (§9 authored; §5/§6/§7 reconciled) · 2d approval PENDING
- **2b scope correction (user directive)**: only registry-listed local specials get 3-way merge;
  every other path is pulled/overwritten verbatim with zero divergence. This reclassified D9
  (`exporter/analysis/`) and D10 (`tools/ai_antigravity_cli.py`) from discuss → plain mirror, and
  reduced D11 to "docs/, audio/, scripts/ folders mirror upstream; only docs_rus/ is maintained".
  2c MUST reconcile §5/§6/§7 accordingly (drop the analysis re-apply + antigravity PRESERVE items;
  remove the unregistered docs/scripts entries). See `skill_scope_improvement.md` for the guide fix.

---

## 0. Execution mechanics (facts verified from scripts)

1. `execute_sync.py` runs `git restore --source as_upstream --worktree -- .` (worktree-only;
   index untouched, changes stay unstaged for review), then **restores** every path in
   `registry.json.modified_upstream_files` + `no_sync_files` (`get_permanent_exclusions`,
   execute_sync.py:174-179) plus `run_exclusions.txt`. `skip_sync_patterns` only suppresses
   analysis — it does NOT restore. `unique_paths` is analysis-only classification: it is NOT
   in the restore set, so a unique_paths entry that exists in the upstream tree WOULD be
   overwritten by the pull.
2. The 6 registry discuss paths are all in `modified_upstream_files` → auto-restored after
   checkout; their upstream changes are merged **manually** in Stage 3.
3. Discuss gate: `verify_manifest(allow_discuss=False)` fails while `prep_manifest.json.discuss_paths`
   is non-empty. There is no acknowledge flag — after 2b resolves all items, **manually edit
   `prep_manifest.json` `discuss_paths` to `[]`** (same procedure as 2026-06 sync).
   **ORDERING**: the D8 registry edit + `prep_analyzer.py` rerun REGENERATE the manifest and
   repopulate `discuss_paths` (the 6 DISCUSS entries). Sequence strictly: (1) D8 registry edit →
   (2) rerun `prep_analyzer.py` → (3) clear `discuss_paths` to `[]` → (4) `execute_sync.py`.
   Clearing before the rerun gets silently undone.
4. Blocker gate: write `<thread_dir>/run_acknowledged_blockers.txt` with all 8 blocker paths
   (7 `shared_data/help/*` deletions + `exporter/analysis/ui_utils.py` collision). The ui_utils
   collision is safe: local file is **byte-identical** to upstream target (verified).
5. `uv.lock` is pulled from upstream, then regenerated after the manual `pyproject.toml` merge
   (`uv lock` + `uv sync --all-groups`) in Stage 3.
6. P0 deletion pass diffs `last_accepted_sha..target` with `--no-renames --diff-filter=D` and
   unlinks every unprotected candidate that exists locally — **~108 files, not just the 9
   `deleted_upstream_paths`**: the whole upstream-deleted `scripts/archive/` tree (~90 files),
   `tests/exporter/kindle/*`, `tests/exporter/tbw/*`,
   `tests/db/lookup/test_help_abbrev_add_to_lookup_fixtures.json`, `db_tests/single/*`,
   `exporter/pdf/pdf_exporter_test.py`, plus the 9. This is correct delete-to-match (verified:
   upstream's rewritten fixture-free `test_help_abbrev_add_to_lookup.py` and the new kindle
   `test_data_classes.py` arrive via the pull) — do NOT mistake the large deletion diff for a fault.
   **LIMIT**: P0 does NOT remove files upstream deleted BEFORE `last_accepted_sha` — the
   `audio/bhashini/*` orphans (D12, deleted upstream in `b692d2ccb`, an ancestor of `518672a`)
   survive P0 and need explicit `git rm` in Stage 3.

---

## 1. DISCUSS items — registry-flagged (resolve in 2b, one at a time)

### D1. `.gitignore` — merge, preserve DPS block
Upstream edits (5): `dpd.db.tar.bz2`→`dpd.db.tar.xz`; + `exporter/pdf/typst_chunk_*`;
+ `gui2/data/commentary_stash.json`; + `gui2/pass2x/data/` (with comment); + `/scripts/fix/pass2exceptions.json`.
**Proposed**: apply all 5 edits into local file; DPS/SBS/RU block untouched.
RESOLUTION: APPROVED as proposed — merge (registered: local DPS/SBS/RU block). Apply all 5 upstream edits, leave local block untouched.

### D2. `.pre-commit-config.yaml` — merge, preserve pyrefly hook
Upstream edit (1): top `exclude:` becomes `^(archive|scripts/archive|scripts/bash|tools/writemdict)/`.
**Proposed**: apply the exclude line; keep local pyrefly hook after pyright.
RESOLUTION: APPROVED as proposed — merge (registered: local pyrefly hook). Apply upstream `exclude:` line, keep local pyrefly hook after pyright.

### D3. `AGENTS.md` — merge new sections, preserve Localized Rules
Upstream adds: Data Verification (query live db, not TSVs); Go build rule (`go build ./go_modules/...`);
Codebase sweep rules (`rg --hidden`, grep by literal); optional/transitive dep policy;
slow-test marker workflow; pre-commit "touch a file = own its lint" (2 bullets);
other-dictionaries submodule single-dict recompress rule; Performance Work section
(re-derive numbers, `_raw_sql_sync` pattern, never `INSERT OR REPLACE` on lookup).
Removes: "Update Gemini CLI" section.
**Proposed**: merge all new sections verbatim into the upstream part of local AGENTS.md; drop the
gemini section; keep all fork-local sections; add a concise summary of genuinely new rules to
CLAUDE.md "Project Rules (from original upstream)".
RESOLUTION: MERGE, SCOPE-FILTERED (user directive). Merge ONLY the upstream AGENTS.md rule
additions that apply to files/areas WE actually maintain — i.e. registered local specials
(`modified_upstream_files`, `unique_paths`, `inspired_by_upstream`, `russian_copies`, `sbs_copies`,
`dps_copies`) or our own sync process. Do NOT adopt upstream-only workflow rules for work we do
not do (e.g. Go build, Performance Work number re-derivation, other-dictionaries submodule
recompress, codebase-sweep conventions) UNLESS they govern a maintained file. Drop the removed
Gemini section. Keep all fork-local sections verbatim. Only reflect in CLAUDE.md the in-scope new
rules. Rationale: our job is sync + maintaining shadows/translations, not mirroring upstream's full
workflow (see kamma/project.md). 2c authors the exact kept/dropped section list.

2c AUTHORED kept/dropped list (from `git diff <OLD> <NEW> -- AGENTS.md`):
KEEP — merge verbatim into the upstream part of local AGENTS.md; reflect a concise line in CLAUDE.md
"Project Rules (from original upstream)" only where noted:
- **Data Verification** (query live `dpd.db`, not stale TSVs) — governs our maintained db/exporter/
  translation work. KEEP + one CLAUDE.md line.
- **Optional/transitive deps belong to their parent** (openpyxl/httpx2 ownership comments) — governs
  `pyproject.toml`, a registered `modified_upstream_files` special (D6). KEEP + CLAUDE.md line.
- **Slow tests** (`@pytest.mark.slow`, run with `-m slow`) — governs `pyproject.toml` addopts (D6,
  registered) and our own test runs. KEEP + CLAUDE.md line.
- **Pre-commit "TOUCH A FILE = OWN ITS LINT"** — governs our sync/pre-commit process directly. KEEP.
- **Pre-commit hook-coverage note** (`gui2/` excluded from pyright but NOT ruff; narrow-except /
  direct-bool-return / `next(iter(d))` patterns) — governs `gui2/` where we maintain the `dps_*.py`
  shadows. KEEP.
- **(narrow) "never `INSERT OR REPLACE` on lookup; use the `_raw_sql_sync` pattern"** — one-line
  correctness rule governing lookup-writing shadows S1/S2 (`rpd/tpd_to_lookup*` now pass
  `use_raw_sql=True`). KEEP only this one sentence; drop the surrounding benchmarking prose (below).

DROP — upstream-only workflow for work we do not do (user-named or analogous):
- **Go build rule** (`go build ./go_modules/...`, binary-litter warning) — `go_modules/**` is mirrored
  verbatim; we don't build it. DROP (user-named).
- **Codebase Sweeps / Audits conventions** (`rg --hidden`, literal-grep discipline) — DROP (user-named).
- **other-dictionaries submodule single-dict recompress rule** — DROP (user-named; submodule work
  excluded from our scope).
- **Performance Work section bulk** (re-derive numbers from profiling log, bench on scratch db copy) —
  DROP (user-named); we do not do perf benchmarking. (Keep ONLY the narrow lookup-write sentence above.)
- **REMOVED upstream: "Update Gemini CLI"** — DROP to match upstream removal (we don't use Gemini CLI).

### D4. `db/models.py` — apply 3 upstream hunks manually
(1) `import inspect`; (2) module-level `transliterate.getmembers = lru_cache(maxsize=None)(inspect.getmembers)`
with its comment block (before `class DpdHeadword`); (3) `@lru_cache _lemma_ipa_transliterate()` helper +
`lemma_ipa` property now returns `_lemma_ipa_transliterate(self.lemma_clean)`.
**Proposed**: apply all 3, preserving SBS/Russian/Tamil/Sinhala tables, relationships, and the
`paragraphs_are_similar` import. No schema change → no rebuild required.
RESOLUTION: APPROVED as proposed — merge (registered: local RU/SBS/Tamil/Sinhala tables). Apply the
3 upstream hunks; preserve local tables/relationships/imports; no rebuild.

### D5. `gui2/main.py` — apply upstream hunks manually, preserve DPS tab + font scaler
Upstream edits: `import re`; import + instantiate `Pass2xInCommentaryView`; new "Pass2x" tab
between Pass2Pre and Pass2Auto; `_get_current_lemma` returns `lemma_clean` (regex strip) and its
tab map changed `6:`→`7:` for pass2_add (upstream inserted one tab before it); removed
`print(f"snakeviz ...")`.
**Proposed**: apply all; **recompute the tab-index map against the LOCAL tab order** (local has an
extra DpsView tab — 2c must count actual local tabs, not copy upstream's `3`/`7`). Font-scaler
patch and `fast_api_utils_dps` import untouched. New Pass2x view gets font-scaled automatically
by the global patch — acceptable.
RESOLUTION: APPROVED as proposed — merge (registered: local DpsView tab + font scaler). Apply
upstream hunks; recompute the tab-index map against the LOCAL tab order (2c counts actual local
tabs); font-scaler + `fast_api_utils_dps` untouched.
2c COUNTED (gui2/main.py at HEAD): LOCAL current order is Global0 Transl1 Pass1Auto2 Pass1Add3
Pass2Pre4 Pass2Auto5 Pass2Add6 DPS7 '8 Sandhi9 DB10 Tests11 BoldSearch12 √13 CT14; LOCAL
`tab_to_view = {3: self.pass1_add_view, 6: self.pass2_add_view}` (lines ~224-227). After inserting
the new **Pass2x** tab (`Pass2xInCommentaryView`) between Pass2Pre(4) and Pass2Auto, LOCAL order
shifts to ...Pass2Pre4 Pass2x5 Pass2Auto6 Pass2Add7 DPS8...; DpsView sits AFTER pass2_add so it does
NOT affect indices 3/7. → LOCAL literal edit: `tab_to_view = {3: self.pass1_add_view, 7:
self.pass2_add_view}` — identical to upstream's new `{3, 7}`. Also: `_get_current_lemma` returns
`lemma_clean` via regex strip (adopt upstream); `import re`; instantiate `Pass2xInCommentaryView`;
remove the `print(f"snakeviz ...")` line. Verify: `uv run python -c "import gui2.main"` +
`uv run ruff check gui2/main.py`.

### D6. `pyproject.toml` — 3-way merge, then `uv lock` + `uv sync --all-groups`
Upstream: prunes ~17 unused deps (black, flake8, bandit, pylint, pip, timeout-decorator, psutil*,
flask, flask-sqlalchemy, tomlkit, pandoc, dbf, typst, marimo, snakeviz, natsort,
indic-transliteration, modelcontextprotocol, elevenlabs, gtts); pins `flet[all]==0.28.3` (local
already pins this); adds `prompt-toolkit`, ownership comments on `httpx2`/`openpyxl`/`anki`;
`[tool.ruff.lint] select = ["E4","E7","E9","F"]`; pytest `-m 'not slow'` addopts + `slow` marker;
pyright/ruff excludes swap `tools/cst_source_sutta_example.py`→`tools/cst_source` and add `archive`.
**Proposed**: take upstream wholesale, then re-append local-only deps (`num2words>=0.5.14`,
`pyrefly>=1.1.1`). 2c must verify no OTHER local-only dep/setting exists (3-way diff local vs
upstream-old vs upstream-new). *psutil: verify it lives in `[project].dependencies` (export_dpd
imports it) before accepting the prune.
RESOLUTION: APPROVED as proposed — merge (registered: local-only deps). Take upstream wholesale,
re-append `num2words>=0.5.14` + `pyrefly>=1.1.1`; 2c 3-way diff for any other local-only setting;
verify `psutil` stays in `[project].dependencies` before accepting its prune; then `uv lock` +
`uv sync --all-groups`.
2c VERIFIED (3-way facts):
- `psutil>=7.0.0` is in upstream-NEW `[project].dependencies` (line 18) — upstream pruned only the
  duplicate in `[dependency-groups].tools`. Accepting the prune is SAFE; `export_dpd.py` import holds.
- `natsort>=8.4.0` stays in `[project].dependencies` in upstream-NEW (line 19) — NOT pruned there
  (only its `[dependency-groups]` duplicate went). Local `db/families/family_set.py` imports it.
  → no action; taking upstream wholesale already keeps it. (Earlier "natsort local-only" read was wrong.)
- Genuine local-only deps to re-append after taking upstream `[project].dependencies` wholesale:
  ONLY `num2words>=0.5.14` and `pyrefly>=1.1.1`. Local already pins `flet[all]==0.28.3` (matches upstream).
- FAST literal steps: (1) replace `pyproject.toml` `[project].dependencies` + `[dependency-groups]` +
  `[tool.ruff]`/`[tool.pyright]`/pytest sections with upstream-NEW verbatim; (2) re-add `num2words>=0.5.14`
  and `pyrefly>=1.1.1` into `[project].dependencies`; (3) keep the local pyrefly pre-commit hook (D2);
  (4) `uv lock` then `uv sync --all-groups`. Verify: `uv run python -c "import psutil, natsort, num2words"`.

---

## 2. NEW discuss items surfaced by 2a (resolve in 2b)

### D7. `shared_data/help/` → `shared_data/reference/` rename vs local `shared_data/help_ru/`
Upstream moved the dir and dropped the `abbrev_other` ALTER hack. Local shadow `shared_data/help_ru/`
(registry `russian_copies`) now points at a deleted upstream dir.
**Options**: (a) **mirror the rename** → `git mv shared_data/help_ru shared_data/reference_ru`,
update `RuPaths` attrs, `help_abbrev_add_to_lookup_ru.py`, registry entry (recommended: keeps
parity and future syncs clean); (b) keep `help_ru/`, only update the registry `upstream` pointer
to `shared_data/reference/`. Either way: acknowledge the 7 deletion blockers; 2c greps for any
other local reader of `shared_data/help/` paths.
RESOLUTION: OPTION (a) — MIRROR THE RENAME (user directive). `git mv shared_data/help_ru
shared_data/reference_ru`; update `RuPaths` attrs, `help_abbrev_add_to_lookup_ru.py`, and the
`russian_copies` registry entry (new upstream pointer `shared_data/reference/`); acknowledge the 7
`shared_data/help/*` deletion blockers; 2c greps for other local readers of `shared_data/help/`.

### D8. `tools/ai_models.json` — PRESERVE local (active translate-pipeline config)
Local grounded_models use `antigravity_cli`/`deepseek` (live quota config for kamma/translate);
upstream's list diverges (openrouter/gemini models). Overwrite would break the translate pipeline.
**Proposed**: add `tools/ai_models.json` to registry `modified_upstream_files` (sync_rule
PRESERVE-merge, discuss true) **before** `execute_sync.py` so the restore set protects it;
review upstream's model-list changes manually each sync. NOTE: registry change → rerun
`prep_analyzer.py` (manifest regenerates; path moves from unmapped to tracked-modified).
RESOLUTION (UPDATED, user directive 2026-07-09): PRESERVE PERMANENTLY — the file ALWAYS stays
local. Register in `modified_upstream_files` with `sync_rule: PRESERVE`, `discuss: false` (no
per-sync merge review, never gates a sync) BEFORE `execute_sync.py`, then rerun `prep_analyzer.py`.
NOT `unique_paths`: the file exists in the upstream tree, so the restore pass would overwrite a
unique_paths entry (unique_paths is analysis-only, not in the restore set — see §0.1), and that
category is reserved for files with no upstream counterpart. Compatibility verified: upstream's
rewritten `ai_manager.py` reads the same path via `ProjectPaths().ai_models_json_path` →
`tools/ai_models.json`, and local + upstream JSON share identical top-level keys
(`antigravity_cli_work_models`, `default_models`, `grounded_models`) — preserving local is safe.

### D9. `exporter/analysis/` local divergences (6 files)
Upstream is ahead (cst_source package imports, `ProjectPaths` routing in `paths.py`, aligned CLI
help). Local is ahead on one real fix upstream lacks:
`example_bolding.py: best_comp = max(comp_list, key=lambda x: int(x.get("ai_score") or 0))`
(crash fix, local commit be90fcb82; upstream has plain `x.get("ai_score", 0)`).
**Proposed**: take upstream for all 6 files (via normal pull), then re-apply the one-line
example_bolding fix in Stage 3; flag it for an upstream PR. Drop the other two local deltas
(ai_batch_translate help-text/lambda style, ai_response docstring) — cosmetic.
RESOLUTION: CORRECTED — PULL/OVERWRITE VERBATIM (user directive). `exporter/analysis/` is NOT
registered → it is a plain upstream area with ZERO permitted local divergence. Overwrite all files
from upstream, including dropping the local `example_bolding.py` crash-fix delta. My 2a preserve
flag was wrong (unregistered = overwrite, not preserve). If the crash fix is still valid, raise it
upstream as a PR separate from this sync — do NOT carry it as a local delta. Reclassify discuss →
plain mirror; remove from §5/§7 special-handling in 2c.

### D10. `tools/ai_antigravity_cli.py` — 1-line delta
Local has active `pr.green(f"  -> antigravity-cli {model} (timeout={timeout}s)...")`; upstream
commented it out ("fix antigravity terminal printout"). **Proposed**: take upstream (quieter);
if translate-batch visibility is wanted, keep local line instead (then register as PRESERVE like D8).
RESOLUTION: CORRECTED — PULL/OVERWRITE VERBATIM (user directive). `tools/ai_antigravity_cli.py` is
NOT registered → take upstream's version exactly (the commented-out print line). No local
divergence, no registration. Reclassify discuss → plain mirror.

### D11. Unregistered local files needing a user call (subset of §7)
- `docs/pics/kindle/*.png` (5): local images inside upstream-only `docs/` (Docs Sanctity).
  Origin unclear — register, move, or delete?
  RESOLUTION: DO NOT REGISTER — `docs/` is upstream-only, mirrored exactly (user directive). Our
  only maintained docs surface is `docs_rus/`. 2c verifies whether any local file references these
  PNGs: if unreferenced, remove them so `docs/` matches upstream; if referenced by `docs_rus/`,
  surface to the user before removing. No `unique_paths` entry.
- `docs_setup_guide.md` (repo root): register in `unique_paths` or relocate?
  RESOLUTION: MOVE TO `temp/` (user directive). Relocate out of the tracked tree into `temp/`; do
  not register.
- `scripts/extractor/README.md`, `scripts/patch/README.md`, `scripts/project_management/README.md`,
  `scripts/server/README.md`: local-only READMEs in upstream dirs — register as `unique_paths` or
  delete?
  RESOLUTION: REMOVE all 4 (user directive). Those `scripts/*` folders are plain upstream sync
  targets; delete the local-only READMEs. No `unique_paths` entries.

### D12. Upstream-deleted orphans `audio/bhashini/bhashini_generate_dpd.py`, `bhashini_generate_single.py`
Deleted upstream (before/at this range); still present locally, unregistered.
**Proposed**: delete locally to match upstream (audio TTS generation is upstream's domain).
RESOLUTION: APPROVED — DELETE-TO-MATCH (user directive: `audio/` is always synced with upstream).
**CORRECTION (verified)**: the P0 pass will NOT remove them — upstream deleted them in
`b692d2ccb`, an ancestor of last-accepted `518672a`, so they are outside the P0 diff range
(that is exactly why prep listed them under `upstream_deleted_orphans`, not
`deleted_upstream_paths`; their renamed successors `generate_dpd.py`/`generate_single.py`
already exist locally). Delete explicitly in Stage 3:
`git rm audio/bhashini/bhashini_generate_dpd.py audio/bhashini/bhashini_generate_single.py`.
No registration.

### D13. `.github/workflows/pdf_test.yml` (new upstream workflow)
Workflows run on our GitHub fork. PDF exporter dir is analysis-skipped but WILL be present in the
tree after checkout. **Proposed**: pull it (parity; it is `workflow_dispatch`-gated upstream — 2c
verifies the trigger; if it runs on push, add to `run_exclusions.txt` instead).
RESOLUTION: PULL FULLY / VERBATIM (user directive). Pull `.github/workflows/pdf_test.yml` exactly as
upstream ships it, whatever the trigger. No local exclusion, no modification.

---

## 3. Shadow ports (PORT — Stage 3 mechanical, literal edits authored in 2c)

> **§9 has the authoritative literal recipes** (exact anchors, file:line, edits, verify commands),
> written against the real file anchors. Where a §3/§4 table note and §9 differ, **§9 wins**.

| # | Shadow (edit target) | Upstream source | Change to port | Structural refactor check |
|---|---|---|---|---|
| S1 | `db/rpd/rpd_to_lookup.py` | `db/epd/epd_to_lookup.py` | add `use_raw_sql=True` to `sync_lookup_column(...)` call | none found |
| S2 | `db/tpd/tpd_to_lookup.py` | `db/epd/epd_to_lookup.py` | same as S1 | none found |
| S3 | `db/lookup/help_abbrev_add_to_lookup_ru.py` | `db/lookup/help_abbrev_add_to_lookup.py` | `removesuffix(".")` idiom; drop `ensure_abbrev_other_column` + its sqlalchemy imports if present in RU copy; D7 path fallout | YES — dead-code removal (ALTER hack) + idiom modernisation |
| S4 | `exporter/deconstructor/deconstructor_exporter_ru.py` | `deconstructor_exporter.py` | header rendered once per run: replace `DeconstructorDataRu._generate_header` override with a RU module-level `generate_deconstructor_header_ru(jinja_env)` (ru template + CSSManager), `DeconstructorData(i)` new signature | YES — header-once refactor, constructor signature change (upstream `data_classes.py` is pulled verbatim; RU subclass MUST adapt or import error/TypeError at runtime) |
| S5 | `exporter/goldendict/export_rpd.py` | `export_epd.py` | empty-db early-return; header rendered once (`squash_whitespaces` hoisted); inline html_string build replacing per-entry `EpdData`→ adapt to `RpdData`/`rpd_unpack`/`rpd_ru.jinja` | YES — header-once + ViewModel-to-inline refactor |
| S6 | `exporter/grammar_dict/grammar_dict_ru.py` | `grammar_dict.py` | `generate_grammar_header(jinja_env)` once; `GrammarData(lookup_entry, header)` new signature — `GrammarDataRu.__init__` must adapt | YES — same header-once refactor; pulled `data_classes.py` changes base constructor |
| S7 | `exporter/kindle/kindle_exporter_ru.py` | `kindle_exporter.py` | adopt `friendly` dict pattern (`_make_friendly`/`html_friendly` now in `exporter/kindle/data_classes.py`): remove local `html_friendly` + ORM `setattr` mutation loop (line ~214); `render_ebook_entry` drops `pth` param upstream — mirror where RU signature matches; `save_abbreviations_xhtml_page` gains `isinstance(value, str)` guard; extend friendly handling to `i.ru.ru_notes` equivalent | YES — no-ORM-mutation refactor + moved helper |
| S8 | `exporter/kindle/ru_components/templates/ebook_ru_example.jinja`, `ebook_ru_grammar.jinja` | `templates/ebook_example.jinja`, `ebook_grammar.jinja` | switch mutated-attr reads to `friendly.<attr>` for the 12 `_FRIENDLY_ATTRS` fields, mirroring upstream template diff, adapted to RU variable names | YES — paired with S7 |
| S9 | `exporter/kindle/ru_components/epub/OEBPS/Text/titlepage.xhtml` | `epub/.../titlepage.xhtml` | **NO-OP** — upstream change is date/time only; registry documents this intentional non-port | none found (data-only) |
| S10 | `gui2/dps_example_field.py` | `gui2/dpd_fields_examples.py` | swap `from tools.cst_source_sutta_example import ...` → `from tools.cst_source import ...` (old module is deleted by P0 pass — REQUIRED or import error); upstream's other edits (coding cookie, `book_codes` iteration) apply only if same code exists in DPS copy | YES — module split |
| S11 | `gui2/dps_example_stash_manager.py` | `gui2/example_stash_manager.py` | port structural bits adapted to dict payload: `except (json.JSONDecodeError, OSError)` / `except OSError` narrowing, `Optional`→`| None`, optional `stash_path` ctor param; `last_commentary` property SKIP (DPS view has no commentary-stash flow) with reason recorded | YES — exception narrowing + typing modernisation |
| S12 | `scripts/server/update-dpd-sbs.sh` | `scripts/server/update-dpd.sh` | `dpd.db.tar.bz2 \| tar -xj` → `dpd.db.tar.xz \| tar -xJ` — **paired with I14** (our release must actually publish .xz before the server script expects it) | none found |
| S13 | `tools/ru_spelling.py` | `tools/spelling.py` | port sorted/deduped rewrite-on-save into `add_to_ru_dictionary` (read-add-sort-write with `key=lambda w: (w.lower(), w)`) | none found (behavioral feature) |

## 4. Inspired backports (evaluate → decision recorded)

| # | Local file | Upstream source | Decision | Structural refactor check |
|---|---|---|---|---|
| I1 | `exporter/goldendict/export_dpd_ru.py` | `export_dpd.py` | **PORT architecture** — ProcessPoolExecutor + `_worker_init`/`_render_batch`, preloaded `fc/fi/fs` family maps (replaces per-headword `get_family_compounds/idioms/set`), `_dedupe_keys`, `_base_dpd_query` + `_iter_dpd_row_pages` keyset low-mem paging, streaming progress; synonyms contraction single-pass. Layer RU: `rupth`, `joinedload(DpdHeadword.ru)`, `Russian.id.isnot(None)` filter, RU templates env in `_worker_init` | YES — full parallelism rewrite; the largest item of this sync |
| I2 | `exporter/goldendict/export_dpd_sbs.py` | `export_dpd.py` | **PORT architecture** — same as I1, layering SBS: `dpspth`, `.ru/.ta/.sbs` joinedloads, locale flags threaded through worker render data (`show_sbs_data`, `show_ru_data`, `show_ta_data`, `show_grammar`), `sbs_templates/` env | YES — same |
| I3 | `exporter/goldendict/export_epd_sbs.py` | `export_epd.py` | **PORT adapted** — empty-db early-return + header-once; keep EpdDataSBS merge logic (RU/TPD merging is per-entry, header is not) — 2c reads the file and decides how much of the inline refactor applies | YES — header-once |
| I4 | `exporter/goldendict/export_help_ru.py` | `export_help.py` | **PORT adapted** — header-once in abbrev/help loops; `list_open` fix in `add_bibliography` + `add_thanks` (registry: these two are structurally similar to upstream — the old `zip(x, x[1:])` loop drops the last `</ul>`/misses categories) | YES — header-once + loop-correctness fix |
| I5 | `exporter/goldendict/export_help_sbs.py` | `export_help.py` | **PORT adapted** — same as I4 with `show_ru_data` flag preserved | YES — same |
| I6 | `exporter/goldendict/export_variant_spelling_ru.py` | `export_variant_spelling.py` | **PORT adapted** — `continue`-on-error dedupe fixes in `test_and_make_*` dicts; header-once where the RU structure matches (RU already passes vars directly) | YES — validation-loop fix |
| I7 | `exporter/goldendict/main_ru.py` | `exporter/goldendict/main.py` | **PORT adapted** — `@dataclass GlobalVars` + `build_global_vars()` factory, adding `rupth: RuPaths` field; call-site update in `main()` | YES — class→dataclass refactor |
| I8 | `exporter/goldendict/main_sbs.py` | `exporter/goldendict/main.py` | **PORT adapted** — same, adding `dpspth` + locale config flags as fields | YES — same |
| I9 | `gui2/dps_fields.py` | `gui2/dpd_fields.py` | **SKIP (no-op)** — upstream changes are upstream-only automation surfaces absent in DPS: kammadhāraya autofill on lemma submit, `vyagra + varga` sanskrit cleanup, synonym flip-flop fix (`make_dpd_headword_from_dict`), lambda reformatting | YES upstream, but confined to non-mirrored handlers — no DPS counterpart exists |
| I10 | `gui2/dps_view.py` | `gui2/pass2_add_view.py` | **SKIP (no-op)** — queue-count tooltips, clone simplification, BLE001 noqa, `pass2_x_manager` path via toolkit are all upstream queue/automation features intentionally absent in DPS view (registry watch_for confirms) | YES upstream, non-mirrored surface |
| I11 | `scripts/bash/generate_components.sh` | `scripts/bash/generate_components.py` | **PORT** — remove `deconstructor_extract_archive.py` + `deconstructor_output_add_to_db.py` steps if present (upstream dropped both; Go deconstructor covers it) — 2c verifies exact lines in the .sh | none found beyond step removal |
| I12 | `tools/paths_ru.py` | `tools/paths.py` | **SKIP (no-op)** except D7 fallout — upstream pruned ~47 dead `*_templ_path` attrs (RU exporters still use their RuPaths equivalents — do NOT prune); new attrs (analysis/audio/whitney/ai_models) serve upstream-only features — not needed. If D7(a): rename help_ru-based attrs | YES upstream (reorg+prune), deliberately not mirrored — divergence_reason: RU attrs still live |
| I13 | `tools/paths_dps.py` | `tools/paths.py` | **SKIP (no-op)** — same reasoning as I12 (`main_sbs.py` still uses `dpspth.templates_dir`) | YES upstream, deliberately not mirrored |
| I14 | `.github/workflows/ru_release.yml`, `ru_release_test.yml` | `draft_release.yml` | **PORT partial** — `dpd.db.tar.bz2`→`dpd.db.tar.xz` in asset upload steps (3 lines per file; `tarball_db.py` pulled this sync produces .xz, so release breaks without this). **SKIP** Typst/PDF export steps (PDF exporter not in RU release scope). Paired with S12 + docs track | none found (asset rename) |
| I15 | `docs_rus/technical/local_server_setup.md`, `quick_start.md`, `use_db.md` | `docs/technical/*` | **DOCS TRACK** — bz2→xz command/text updates (3 files, 1-2 lines each), via `docs_translation_plan.md` | none found |

## 5. Mirror — pulled verbatim by `execute_sync.py` (classification: mirror)

Everything below has no fork edits since the last sync (verified by local-commit sweep) unless noted.

- **Fan-out mirrors (local follow-up required in Stage 3):**
  - `tools/ai_manager.py` — upstream renamed `load_models_from_json` → `_load_models_from_json`
    and routed the JSON path through `ProjectPaths` (new `ai_models_json_path`). Local callers to
    update after pull: `tests/tools/test_ai_manager.py` (import + call),
    `kamma/translate/scripts/ai_generate_translation.py` (aliased import). (`kamma/` is no_sync —
    untouched by checkout, edited manually.)
  - `tools/cst_source/` (new package, 14 files) + P0 deletion of `tools/cst_source_sutta_example.py`
    — local follow-ups: S10 (`dps_example_field.py`), `tests/test_shadow_parity.py` reference,
    registry watch_for wording for `gui2/dps_example_field.py`.
  - `exporter/deconstructor/data_classes.py`, `exporter/grammar_dict/data_classes.py`,
    `exporter/kindle/data_classes.py` — constructor/signature changes drive S4, S6, S7.
  - `shared_data/reference/` (7 new files) + P0 deletion of `shared_data/help/` (7 files) — D7.
  - `scripts/build/tarball_db.py` (bz2→xz) — drives S12 + I14 + I15.
  - `db/epd/epd_to_lookup.py`, `db/lookup/help_abbrev_add_to_lookup.py` — drive S1-S3.
- **Plain mirrors:** `.github/workflows/draft_release.yml`, `mobile_release.yml`; `CONTRIBUTING.md`;
  `justfile` (new); `audio/error_check/*` (2); `db/app/create_app_db.py`; `db/backup_tsv/dpd_headwords_part_00{1,2,3}.tsv`;
  `db/grammar/grammar_to_lookup.py`; `db/inflections/*` (3 py + xlsx); `db/lookup/transliterate_lookup_table.py`;
  `db/sanskrit/root_families_sanskrit.tsv` (upstream data-ahead, includes local viśvāsa addition — verified);
  `db/variants/*` (2); `exporter/analysis/*` (15 — plain verbatim pull; **D9 CORRECTED**: unregistered →
  zero local divergence, so the local `example_bolding.py` crash-fix delta is DROPPED, not re-applied;
  raise it upstream as a separate PR if still valid. `ui_utils.py` collision is byte-identical, acknowledged);
  `go_modules/**` (34 incl. new test/helper files); `gui2/daily_log.py`, `gui2/data/{additions_added,corrections_added,pass2_exceptions}.json`,
  `gui2/data/in_commentary_exceptions.txt` (new), `gui2/dpd_fields.py`, `gui2/dpd_fields_commentary.py`,
  `gui2/dpd_fields_examples.py`, `gui2/dpd_fields_functions.py`, `gui2/example_stash_manager.py`,
  `gui2/flet_functions.py`, `gui2/pass2_add_view.py`, `gui2/pass2_auto_control.py`, `gui2/pass2_pre_*.py` (4),
  `gui2/pass2x/*` (4 new), `gui2/paths.py`; `scripts/add/vagga_codes/*` (5); `scripts/bash/generate_components.py`;
  `scripts/build/*` (6); `scripts/export/{db_filter_export,sanskrit_export}.py`; `scripts/extractor/*` (2);
  `scripts/fix/fix_synonym_entries.py`, `scripts/fix/pass2exceptions.{py,json}` (new);
  `scripts/info/suffix_counter.py`; `scripts/onboarding/*` (2); `scripts/server/update-dpd.sh`;
  `scripts/tutorial/quick_start.py`; `shared_data/deconstructor/*` (3); `shared_data/user_dictionary.txt`;
  `tools/ai_antigravity_cli.py` (**D10 CORRECTED**: unregistered → take upstream verbatim, i.e. the
  commented-out `pr.green(...antigravity-cli...)` line; drop the local uncommented delta),
  `tools/ai_antigravity_cli_models.py`, `tools/ai_deepseek_manager.py` (both verified byte-identical already),
  `tools/bjt.py`, `tools/compound_type_manager.tsv`, `tools/configger.py`, `tools/css_manager.py`,
  `tools/deconstructed_words.py`, `tools/docs_changelog_and_release_notes.py`, `tools/goldendict_exporter.py`,
  `tools/lookup_sync.py` (new `_raw_sql_sync` + optional `use_raw_sql` param — backward compatible, verified),
  `tools/meaning_construction.py`, `tools/paths.py`, `tools/proofreader.py`, `tools/script_runner.py`,
  `tools/spelling.py`, `tools/tokenizer.py`; `uv.lock` (then regen per D6);
  `docs/technical/*.md` (3 — mirrors into `docs/`; RU translations via I15).
- **Submodule pointers:** `resources/deconstructor_output`, `resources/other-dictionaries`,
  `resources/tpr_downloads` — gitlink updates to upstream-pinned SHAs are part of Commit 1
  (they come from upstream, unlike locally-dirty submodule states, which stay excluded).
- **Blast-radius verified:** no breaking signature changes in shared `tools/` modules used by
  shadows (`sync_lookup_column` param is optional; `zip_dictfile` unchanged;
  `make_deconstructor_words_set` typing only). `gui2/mixins.py` byte-identical to target.
  Pruned `ProjectPaths` attrs are referenced only by `scripts/dps_archive/` (archived, exempt) —
  `main_sbs.py`'s `templates_dir` is on `DPSPaths` (ours), unaffected.

## 6. Deletions & upstream-deleted orphans

| Path | Classification |
|---|---|
| `shared_data/help/*` (7) | delete-to-match (P0 pass) — acknowledged blockers; local RU reader uses `help_ru/`, not `help/` (2c re-greps before pull) |
| `tools/cst_source_sutta_example.py` | delete-to-match (P0) — fan-outs S10 + test reference |
| `scripts/build/deconstructor_extract_archive.py` | delete-to-match (P0) — upstream removed as dead; also drop from unregistered list |
| `audio/bhashini/bhashini_generate_{dpd,single}.py` | D12 APPROVED — delete-to-match, `audio/` always synced. **NOT covered by P0** (deleted upstream before last-accepted SHA) — explicit Stage 3 `git rm` (see D12 CORRECTION) |

## 7. Registry updates (mechanical edits in Stage 3; D8 registry entry must land BEFORE `execute_sync.py`)

**`unique_paths` additions** (no upstream counterpart, verified):
`.github/workflows/anki_release.yml`; `db/tpd/__init__.py`; `gui2/data/addition_processed.json`;
`gui2/data/addition_replaced.json`; `gui2/data/corrections_processed.json`;
`gui2/data/dps_example_stash.json`; `gui2/data/dps_history.json`; `misc/ebt-md/` (5 files — register
dir); `resources/anki/collection_media.tar.gz`; `resources/anki/seed_collection.anki2.tar.gz`;
`scripts/export/add_combined_view.py`; `scripts/export/sbs_anki_schema_snapshot.json`;
`shared_data/russian_words_user_dict.txt`; `shared_data/tamil/` (2 files — register dir);
`shared_data/tpr_parsing_errors.tsv`.

**`inspired_by_upstream` addition:** `.github/workflows/ru_release_kindle.yml`
(upstream `draft_release.yml`; RU kindle release variant).

**`russian_copies` addition:** `exporter/deconstructor/deconstructor_header_ru.jinja`
(upstream counterpart CONFIRMED: `exporter/deconstructor/deconstructor_header.jinja` — NOT under a
`templates/` subdir; verified via `git ls-tree -r be49bffe -- exporter/deconstructor`). Pairs with S4.

**D11 RESOLVED — NO registry entries for any of these (all handled by removal/relocation, per 2b):**
- `docs/pics/kindle/*.png` (5): `docs/` is upstream-only. 2c grep (below) checks for local refs; if
  unreferenced → REMOVE so `docs/` matches upstream; if referenced by `docs_rus/` → surface to user
  before removing. No `unique_paths` entry.
- `docs_setup_guide.md` (repo root): MOVE to `temp/` (out of tracked tree). No registry entry.
- `scripts/extractor/README.md`, `scripts/patch/README.md`, `scripts/project_management/README.md`,
  `scripts/server/README.md`: REMOVE all 4 (upstream sync targets). No `unique_paths` entries.

**Entry updates:** `shared_data/help_ru/` upstream pointer (per D7);
`gui2/dps_example_field.py` watch_for wording (`cst_source_sutta_example` → `tools/cst_source`);
D8 `tools/ai_models.json` new `modified_upstream_files` entry (`sync_rule: PRESERVE`,
`discuss: false` — always stays local; NOT `unique_paths`, see D8 RESOLUTION).

**Needs-classification upstream additions** (34: go test/helper files, `gui2/pass2x/`,
`gui2/data/in_commentary_exceptions.txt`, `scripts/fix/pass2exceptions.*`, `shared_data/reference/`,
`tools/cst_source/`): all classified **mirror** — plain upstream Tier-1 files, pulled verbatim,
no registry entries needed (registry tracks only local specials).

Then: `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` must pass.

## 8. Verification battery (Stage 3, after all edits)

1. `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py -v`
2. `uv run python3 tests/check_shadow_modifications.py`
3. `uv run python tests/smoke_test_sync.py`
4. `uv run python3 kamma/upstream_sync/scripts/validate_registry.py`
5. `uv run ruff check` + `uv run ruff format` + `uv run pyright` on every hand-edited file
6. `uv run pytest tests/tools/test_ai_manager.py -v` (ai_manager fan-out)
7. Import smoke for rewired modules: `uv run python -c "import exporter.goldendict.export_dpd_ru, exporter.goldendict.export_dpd_sbs, exporter.goldendict.export_rpd, exporter.grammar_dict.grammar_dict_ru, exporter.deconstructor.deconstructor_exporter_ru, exporter.kindle.kindle_exporter_ru"`
8. Full RU/SBS exporter run deferred to Stage 4 manual verification (user builds + GoldenDict check)

---

## 9. Literal edit recipes (Stage 3 — FAST execution)

Authored in 2c from the upstream diffs (`OLD=518672a65fa3`, `NEW=be49bffe2c2c`) and the local shadow
anchors (line numbers at HEAD; **shadow `*_ru.py`/`*_sbs.py` files are NOT touched by
`git restore --source as_upstream --worktree -- .`, so their line numbers stay valid through the
pull** — only shared upstream-path files such as `data_classes.py` are overwritten). Anchor primarily by function/class
name; line numbers are a hint. Each item: upstream reference → exact change → verify.

### Registry-flagged manual merges (D1–D8, D13)
- **D1 `.gitignore`** — apply the 5 upstream additions (`dpd.db.tar.bz2`→`.xz`; `+exporter/pdf/typst_chunk_*`;
  `+gui2/data/commentary_stash.json`; `+gui2/pass2x/data/`; `+/scripts/fix/pass2exceptions.json`); leave
  the local DPS/SBS/RU block untouched. Ref: `git diff OLD NEW -- .gitignore`.
- **D2 `.pre-commit-config.yaml`** — set top `exclude:` to
  `^(archive|scripts/archive|scripts/bash|tools/writemdict)/`; KEEP the local pyrefly hook (after pyright).
- **D3 `AGENTS.md`** — apply the KEEP/DROP list authored in §D3 above. Merge KEEP sections verbatim into
  the upstream portion; drop the DROP sections and the removed Gemini section; keep all fork-local
  sections. Add the noted concise lines to `CLAUDE.md` "Project Rules (from original upstream)".
- **D4 `db/models.py`** — apply the 3 upstream hunks: (1) `import inspect`;
  (2) module-level `transliterate.getmembers = lru_cache(maxsize=None)(inspect.getmembers)` + comment
  block before `class DpdHeadword`; (3) `@lru_cache _lemma_ipa_transliterate()` helper and
  `lemma_ipa` returns `_lemma_ipa_transliterate(self.lemma_clean)`. Preserve all local
  SBS/Russian/Tamil/Sinhala tables, relationships, and the `paragraphs_are_similar` import. No rebuild.
  Ref: `git diff OLD NEW -- db/models.py`. Verify: `uv run python -c "import db.models"`.
- **D5 `gui2/main.py`** — per D5 RESOLUTION above: `import re`; instantiate `Pass2xInCommentaryView`;
  insert the **Pass2x** tab between Pass2Pre and Pass2Auto; set `tab_to_view = {3: self.pass1_add_view,
  7: self.pass2_add_view}`; make `_get_current_lemma` return `lemma_clean` (regex strip); remove the
  `print(f"snakeviz ...")` line. Keep the local DpsView tab + font-scaler + `fast_api_utils_dps` import.
  Verify: `uv run python -c "import gui2.main"`; `uv run ruff check gui2/main.py`.
- **D6 `pyproject.toml`** — per D6 RESOLUTION (2c VERIFIED block): take upstream `[project].dependencies`,
  `[dependency-groups]`, `[tool.ruff]`/`[tool.pyright]`/pytest sections verbatim; re-add ONLY
  `num2words>=0.5.14` + `pyrefly>=1.1.1`; keep local pyrefly pre-commit hook; then `uv lock` +
  `uv sync --all-groups`. Verify: `uv run python -c "import psutil, natsort, num2words"`.
- **D8 `tools/ai_models.json`** — PRESERVE local, permanently. **Registry entry must land in
  `modified_upstream_files` (`sync_rule: PRESERVE`, `discuss: false`) BEFORE `execute_sync.py`**,
  then rerun `prep_analyzer.py`, THEN clear `discuss_paths` (ordering per §0.3). Do not overwrite
  with upstream's model list; no per-sync review needed.
- **D13 `.github/workflows/pdf_test.yml`** — pull verbatim (mirror); no local edit.

### Shadow ports S1–S13
- **S1 `db/rpd/rpd_to_lookup.py`** — add `use_raw_sql=True` to the `sync_lookup_column(...)` call
  (mirror `db/epd/epd_to_lookup.py`). Ref: `git diff OLD NEW -- db/epd/epd_to_lookup.py`.
- **S2 `db/tpd/tpd_to_lookup.py`** — same one-arg addition as S1.
- **S3 `db/lookup/help_abbrev_add_to_lookup_ru.py`** — mirror upstream `help_abbrev_add_to_lookup.py`:
  (a) delete function `ensure_abbrev_other_column` (RU lines 28-37) and its call in `main()` (RU line 83);
  (b) delete `from sqlalchemy import inspect as sa_inspect, text` (RU line 6);
  (c) replace the key-suffix idiom with `key.removesuffix(".")`;
  (d) the line reading `g.pth.abbreviations_other_tsv_path` (RU line 60) goes away with the dropped
  abbrev_other flow — confirm against upstream diff. D7 path fallout is handled by RuPaths value updates
  (attr NAMES unchanged), so no other change here. Ref: `git diff OLD NEW -- db/lookup/help_abbrev_add_to_lookup.py`.
  Verify: `uv run ruff check db/lookup/help_abbrev_add_to_lookup_ru.py`; `uv run python -c "import db.lookup.help_abbrev_add_to_lookup_ru"`.
- **S4 `exporter/deconstructor/deconstructor_exporter_ru.py`** — upstream dropped
  `DeconstructorData.__init__(pth, jinja_env)` → now `(result)` only, header moved to module-level
  `generate_deconstructor_header(jinja_env)`. So the RU subclass `DeconstructorData_ru` (line 28) +
  `_generate_header` override (lines 29-34) will `TypeError` after the pull. **Eliminate the subclass**:
  add a module-level `generate_deconstructor_header_ru(jinja_env)` (copy upstream's function body but
  `get_template("deconstructor_header_ru.jinja")`); in the loop (lines 76-79) compute
  `header = generate_deconstructor_header_ru(jinja_env_header)` ONCE before the loop, then
  `data = DeconstructorData(i)` and `html_string = header + minify(template.render(data=data))`.
  Ref: `git diff OLD NEW -- exporter/deconstructor/data_classes.py exporter/deconstructor/deconstructor_exporter.py`.
  Verify: `uv run python -c "import exporter.deconstructor.deconstructor_exporter_ru"`.
- **S5 `exporter/goldendict/export_rpd.py`** (66 lines) — mirror upstream export_epd.py refactor:
  (a) add empty-db early-return (`if not lookup_db: pr.yes(0); return ...`);
  (b) hoist header once: `header = RpdData(lookup_db[0], pth, jinja_env).header; header_squashed = squash_whitespaces(header)`;
  (c) in the loop (lines 39-49) replace the per-entry `data.header` with `header_squashed`, and (if the
  RpdData html-string logic is a simple join like `epd_unpack`) inline it via `rpd_unpack` + `rpd_ru.jinja`;
  if RpdData's html-string is non-trivial, keep constructing `RpdData` for the body but reuse the hoisted
  header. Ref: `git diff OLD NEW -- exporter/goldendict/export_epd.py`. Verify: import smoke (§8.7).
- **S6 `exporter/grammar_dict/grammar_dict_ru.py`** — upstream base `GrammarData.__init__` changed to
  `(lookup_entry, header)`; new module-level `generate_grammar_header(jinja_env)`. `GrammarData_ru`
  (line 24) has NO `_generate_header` override (used base header all along). Port: `from
  exporter.grammar_dict.data_classes import GrammarData, generate_grammar_header`; compute
  `header = generate_grammar_header(jinja_env)` once before the loop (line ~103); change the construction
  (line 108) to `data = GrammarData_ru(lookup_entry, header)`. If a `grammar_dict_header_ru.jinja`
  exists in the RU env, `generate_grammar_header(jinja_env)` resolves it automatically (env is passed);
  else it uses base — FAST confirms at runtime. Ref: `git diff OLD NEW -- exporter/grammar_dict/data_classes.py exporter/grammar_dict/grammar_dict.py`.
  Verify: `uv run python -c "import exporter.grammar_dict.grammar_dict_ru"`.
- **S7 `exporter/kindle/kindle_exporter_ru.py`** (502 lines) — adopt the no-ORM-mutation pattern:
  (a) delete local `html_friendly` (lines 376-383); `from exporter.kindle.data_classes import KindleData, html_friendly`;
  (b) delete the ORM `setattr` mutation loop (lines 198-216); instead build a friendly dict per entry
  (`friendly = _make_friendly(i)` extended to include the RU `i.ru.ru_notes` equivalent) and pass
  `friendly=friendly` into the RU template renders — mirror upstream `data_classes.KindleData`;
  (c) in `save_abbreviations_xhtml_page` loop (lines 280-288) add `if not isinstance(value, str): continue`;
  (d) `render_ebook_entry_ru` (lines 178-183) already has no `pth` param — no signature change needed.
  Pairs with S8 (RU templates switch mutated reads → `friendly.<attr>`). Ref:
  `git diff OLD NEW -- exporter/kindle/data_classes.py exporter/kindle/kindle_exporter.py`.
  Verify: `uv run python -c "import exporter.kindle.kindle_exporter_ru"`; `uv run pytest tests/test_template_syntax.py -v`.
- **S8 `exporter/kindle/ru_components/templates/ebook_ru_example.jinja`, `ebook_ru_grammar.jinja`** —
  switch the 12 `_FRIENDLY_ATTRS` reads (root_base, construction, sanskrit, compound_type, phonetic,
  example_1/2, sutta_1/2, commentary, notes, cognate) from direct `i.<attr>` to `friendly.<attr>`,
  mirroring the upstream template diff, adapted to RU variable names. Ref:
  `git diff OLD NEW -- exporter/kindle/templates/ebook_example.jinja exporter/kindle/templates/ebook_grammar.jinja`.
- **S9 `exporter/kindle/ru_components/epub/OEBPS/Text/titlepage.xhtml`** — **NO-OP** (upstream change is
  date/time only). Record intentional non-port in registry watch_for.
- **S10 `gui2/dps_example_field.py`** — replace `from tools.cst_source_sutta_example import ...` with
  `from tools.cst_source import ...` (old module deleted by P0 — REQUIRED or ImportError). Apply
  upstream's other edits (coding cookie / `book_codes` iteration) only if the same code exists locally.
  Verify: `uv run python -c "import gui2.dps_example_field"`.
- **S11 `gui2/dps_example_stash_manager.py`** — port structural bits adapted to dict payload:
  `except (json.JSONDecodeError, OSError)` / `except OSError` narrowing; `Optional`→`| None`; optional
  `stash_path` ctor param. SKIP the `last_commentary` property (DPS view has no commentary-stash flow) —
  record reason in registry. Ref: `git diff OLD NEW -- gui2/example_stash_manager.py`.
- **S12 `scripts/server/update-dpd-sbs.sh`** — `dpd.db.tar.bz2 | tar -xj` → `dpd.db.tar.xz | tar -xJ`
  (paired with I14). Verify: `bash -n scripts/server/update-dpd-sbs.sh`.
- **S13 `tools/ru_spelling.py`** — rewrite `add_to_ru_dictionary` (lines 67-78) to read existing words,
  add, sort+dedupe, write, mirroring upstream `tools/spelling.py add_to_dictionary`: read the user_dict
  file, `words = sorted(set(existing) | {word}, key=lambda w: (w.lower(), w))`, rewrite the file (keep
  the `RuSpellChecker._lock` guard and the `self.spell.word_frequency.load_words([word])` call). Ref:
  `git diff OLD NEW -- tools/spelling.py`. Verify: `uv run python -c "import tools.ru_spelling"`.

### Inspired backports I1–I15
- **I1 `exporter/goldendict/export_dpd_ru.py`** (315 lines; currently `multiprocessing.Process`, funcs
  `render_pali_word_dpd_html`@78, `_parse_batch_top_level`@168, `generate_dpd_html`@197) — PORT the new
  architecture from upstream `export_dpd.py`: `ProcessPoolExecutor` + `_worker_init`/`_render_batch`,
  preloaded `fc/fi/fs` family maps via `_lookup_family_compounds/idioms/set` + `_dedupe_keys` (replaces
  per-headword `get_family_compounds/idioms/set` @265-267), `_base_dpd_query` + `_iter_dpd_row_pages`
  keyset paging, streaming progress, single-pass synonyms contraction. **Layer RU**: keep
  `joinedload(DpdHeadword.ru)` and the `Russian` outerjoin (add `Russian.id.isnot(None)` filter),
  `rupth`, and load the RU templates env inside `_worker_init`. Ref:
  `git diff OLD NEW -- exporter/goldendict/export_dpd.py` (largest item this sync — treat upstream's new
  file as the structural template, re-layer RU). Verify: import smoke (§8.7) + a small `--limit` run in
  Stage 4 manual check.
- **I2 `exporter/goldendict/export_dpd_sbs.py`** (340 lines) — same architecture port as I1, layering
  SBS: `dpspth`; `.ru`/`.ta`/`.sbs` joinedloads (query @258-271); thread the locale flags
  (`show_sbs_data`/`show_ru_data`/`show_ta_data`/`show_grammar`, @73-76) through the worker render data;
  `sbs_templates/` env in `_worker_init`.
- **I3 `exporter/goldendict/export_epd_sbs.py`** — MINIMAL port (2c decision): apply upstream
  export_epd.py's (a) empty-db early-return and (b) header-once hoist (compute `header` once from the
  first entry instead of per-entry `data.header` inside the loop). **Do NOT** adopt the inline
  `epd_unpack` f-string rewrite — the SBS `EpdDataSBS` merge logic (Russian RPD + Tamil TPD merged into
  `epd_dict`, lines ~60-93) is structurally different and per-entry; keep it. `EpdDataSBS(EpdData)`
  still inherits `.header`, so hoisting is safe. Ref: `git diff OLD NEW -- exporter/goldendict/export_epd.py`.
  Verify: import smoke + Stage 4 spot check that SBS EPD output is unchanged.
- **I4 `exporter/goldendict/export_help_ru.py`** (360 lines) — apply header-once in the abbrev/help
  loops (per-entry `XData(...).header` at RU lines ~174, 224 → compute once, render dict `{"header":"", ...}`).
  **The `zip(...[1:])` bibliography/thanks bug is ABSENT in the RU copy** (verified — no such pattern) →
  the I4 "list_open fix" is N/A; do NOT introduce it. Compare RU `add_bibliography`@250 / `add_thanks`@310
  against upstream's fixed version and align ONLY if the RU loop structure matches the old buggy shape;
  otherwise SKIP with reason. Ref: `git diff OLD NEW -- exporter/goldendict/export_help.py`.
- **I5 `exporter/goldendict/export_help_sbs.py`** (353 lines) — same as I4 (header-once; zip-fix
  verify-then-likely-skip), preserving the `show_ru_data` flag usage (lines 56/72/76/147/172/198/220).
- **I6 `exporter/goldendict/export_variant_spelling_ru.py`** (195 lines) — RU has only
  `test_and_make_variant_dict`@59 and `test_and_make_spelling_dict`@124 (NO `see`). Apply the
  `continue`-on-error fix: replace the `else:` add-block at lines 77-79 (variant) and 142-144 (spelling)
  with an early `continue` after each error check + an unconditional add. Apply header-once in
  `generate_variant_data_list`@84 and `generate_spelling_data_list`@151 (per-entry `data.header` @94-95,
  161-162 → once). Ref: `git diff OLD NEW -- exporter/goldendict/export_variant_spelling.py`.
- **I7 `exporter/goldendict/main_ru.py`** (207 lines) — convert `GlobalVars` (plain `__init__` @38-60)
  to `@dataclass` + `build_global_vars()` factory (mirror upstream main.py), adding a `rupth: RuPaths`
  field; mirror the `speech_marks`/`SpeechMarksDict` import + field change; update `main()` (@71) to
  `g = build_global_vars()`. Ref: `git diff OLD NEW -- exporter/goldendict/main.py`.
  Verify: `uv run python -c "import exporter.goldendict.main_ru"`.
- **I8 `exporter/goldendict/main_sbs.py`** (226 lines) — same dataclass+factory conversion (GlobalVars
  @35-74), adding `dpspth: DPSPaths` and the 4 locale-flag fields (`show_sbs_data`/`show_ru_data`/
  `show_ta_data`/`show_grammar`, default False via `field`/factory); update `main()` (@85) to
  `g = build_global_vars()`.
- **I9 `gui2/dps_fields.py`** — SKIP (no-op): upstream changes are non-mirrored automation surfaces
  (kammadhāraya autofill, sanskrit cleanup, synonym flip-flop fix, lambda reformat). No DPS counterpart.
- **I10 `gui2/dps_view.py`** — SKIP (no-op): upstream queue-count/clone/BLE001/toolkit-path changes are
  intentionally absent in DPS view (registry watch_for confirms).
- **I11 `scripts/bash/generate_components.sh`** — delete lines 42-43 (`uv run python
  scripts/build/deconstructor_extract_archive.py` and `... deconstructor_output_add_to_db.py`); upstream
  dropped both (Go deconstructor covers it) and P0 deletes `deconstructor_extract_archive.py`, so leaving
  the line would break the run. Verify: `bash -n scripts/bash/generate_components.sh`.
- **I12 `tools/paths_ru.py`** — SKIP the upstream prune/reorg (RU exporters still use their RuPaths
  attrs). ONLY the D7 change applies: update the 5 attr VALUES from `shared_data/help_ru/...` →
  `shared_data/reference_ru/...` (attr names abbreviations_tsv_path/abbreviations_other_tsv_path/
  bibliography_tsv_path/help_tsv_path/thanks_tsv_path unchanged; lines 15-21).
- **I13 `tools/paths_dps.py`** — SKIP (no-op): `main_sbs.py` still uses `dpspth.templates_dir`; do not
  mirror the upstream prune.
- **I14 `.github/workflows/ru_release.yml`, `ru_release_test.yml`** — `dpd.db.tar.bz2`→`dpd.db.tar.xz`
  in the asset-upload steps (3 lines each). SKIP Typst/PDF export steps (out of RU release scope). Pairs
  with S12 + I15. Ref: `git diff OLD NEW -- .github/workflows/draft_release.yml`.
- **I15 `docs_rus/technical/local_server_setup.md`, `quick_start.md`, `use_db.md`** — bz2→xz text (1-2
  lines each) — handled via the Docs Translation Track, not Stage 3.

### D7 rename fan-out (mirror the rename; acknowledge 7 deletion blockers)
1. `git mv shared_data/help_ru shared_data/reference_ru` (7 files).
2. `tools/paths_ru.py` lines 15-21: update the 5 path VALUES `shared_data/help_ru/` →
   `shared_data/reference_ru/` (see I12).
3. `db/lookup/help_abbrev_add_to_lookup_ru.py`: reads via `g.rupth.*` attrs (names unchanged) — no path
   edit needed beyond S3's dead-code removal.
4. Registry `russian_copies`: update the `shared_data/help_ru/` entry → new local path
   `shared_data/reference_ru/`, upstream pointer `shared_data/reference/`.
5. Confirmed: NO other local reader of `shared_data/help/` exists (git grep clean outside kamma/docs/
   scripts/archive). Acknowledge the 7 `shared_data/help/*` deletion blockers in
   `run_acknowledged_blockers.txt` (+ the byte-identical `exporter/analysis/ui_utils.py` collision).

### D11 removal/relocation actions (no registry entries)
- `docs/pics/kindle/*.png` (5): `git grep -n "kindle/.*\.png\|pics/kindle" HEAD -- docs_rus` first; if no
  local ref → `git rm` them to match upstream; if referenced by `docs_rus/` → STOP and surface to user.
- `docs_setup_guide.md`: `git mv docs_setup_guide.md temp/` (relocate out of tracked tree).
- `scripts/{extractor,patch,project_management,server}/README.md`: `git rm` all 4.
- `audio/bhashini/bhashini_generate_{dpd,single}.py`: **explicit** `git rm` of both files —
  NOT covered by P0 (deleted upstream before last-accepted SHA; see D12 CORRECTION).
