# Handoff: Upstream Sync 2026-06-12

## Status

Stage 2d COMPLETE — approval gate passed (ADVANCED/Opus, 2026-06-13). User approved the
full plan and all 4 surfaced decisions (B6.4 SKIP, B6.10 SKIP, tpr_headword_ru.jinja
REGISTER, B5.8 APPLY-BY-ANALOGY). Resolution recorded in `dynamic_plan.md` "Stage 2d —
APPROVAL GATE RESOLVED". Next: **Stage 3 = Batch 0** (`execute_sync.py`, Commit 1) — FAST.

## Current Stage

Stage 2 (all sub-stages 2a–2d) COMPLETE. `dynamic_plan.md` is the approved, self-contained
execution plan (Batches 0–6). Next: **Stage 3 (FAST)** — execute Batch 0 first
(`execute_sync.py` → Commit 1), then hard stop per the Commit-1 session boundary.

## Stage 2c progress (batch ledger — full detail in dynamic_plan.md "Batch ledger")

- **DONE Batch 0** — execute_sync pre-flight + Commit 1 mechanics (blockers txt list,
  resources/* exclusion handling, post-pull verification, types.py deletion check).
- **DONE Batch 1** — deterministic reconciliation edits: db/models.py surgical variant
  rename + the **5-file variant fan-out** (CATCH: `exporter/webapp/data_classes.py:88` is
  modified_upstream/preserved and was MISSED in the 2b handoff — it ALSO needs the rename;
  full set = models.py + data_classes.py + data_classes_ru.py + tpr_exporter_ru.py +
  tbw_exporter_ru.py); pyproject.toml merge (num2words preserved, typst dedup); uv.lock
  REGENERATE via `uv lock`; manual delete `exporter/analysis/types.py`.
- **DONE Batch 2** — db/families port recipes ×5 (compound, idiom, root, set, word).
  Established the global RU divergence carve-outs (in-place update = N-A delete-insert;
  PRESERVE html_ru/data_ru/joinedload(.ru)). family_idiom_ru: skip sync_idiom_numbers +
  update_db_cache (both absent). family_root_ru: skip update_lookup_table/root_matrix/
  matrix-anki (absent) — mostly N-A.
- **DONE Batch 3** — db/ + tools/ remaining ports ×7. KEY FINDINGS: (1) epd→rpd/tpd +
  help_abbrev→_ru ADOPT the new `tools/lookup_sync.sync_lookup_column` (verified safe:
  `is_another_value` is column-dynamic; `rpd_pack`/`tpd_pack`/`help_pack`/`abbrev_pack`/
  `abbrev_other_pack` exist; `clear_stale=True` reproduces old delete-first behavior).
  epd→rpd/tpd is a HEAVY refactor (GlobalVars→@dataclass, config-check+DB-load moved into
  main(), POS_EXCLUDE frozenset, setdefault, drop update_test_add/is_another_value) — Iron-Rule
  hard-stop flagged. (2) `tools/spelling.py`→`ru_spelling.py` is a CONFIRMED NO-OP (shadow already
  has encoding="utf-8" on all opens). (3) `tools/utils.py` adds generic `extract_body` → utils_sbs
  needs NO code change; instead WHITELIST `"extract_body"` in `tests/test_shadow_parity.py` line ~329
  (all upstream callers import extract_body from tools.utils, and utils_sbs already whitelists
  list_into_batches/squash_whitespaces). CROSS-BATCH FLAG: Batch 4/5 localized goldendict exporters
  must import extract_body from tools.utils. (4) `backup_dps.py` PORT = add encoding="utf-8" to all
  4 TSV-write open() calls (Cyrillic/Tamil data). (5) version→version_ru = structural cleanup (drop
  tomlkit/rich/local printer→pr.summary, drop update_project_version), PRESERVE 3-tuple+version_ru+
  dpd_sbs_release_version+RU metadata.
- **DONE Batch 4** — exporter/goldendict: `data_classes.py` → `data_classes_dps.py` (heavy,
  348 lines, triple-locale: _NewlineView refactor + _render_header helpers + type hints;
  PRESERVE _convert_newlines_ru/_sbs, all RU/SBS/Tamil fields); `export_epd.py` →
  `export_rpd.py` (extract_body adoption + type hint modernization); **10 templates** →
  `ru_components/templates/` + `sbs_templates/` (8 files get `<body>` comment, 2 dpd_header
  files get `and d.i.freq_data` guard; 6 fragment templates SKIP — no `<body>`);
  `grammar_dict.py` → `grammar_dict_ru.py` (make_mdict simplification + type hints +
  delete commit_db + list append).
- **DONE Batch 5** — exporter/kindle + tbw + tpr + webapp + gui2 + scripts/build. KEY FINDINGS:
  (1) **tbw_exporter_ru** (ProgData_ru): `.all()` on dpd query, type hints ×13, setdefault/`.append`,
  `&`→`and`, `.open(encoding)` — all map cleanly; variant rename at L194 already in B1.2; FDG-only
  (no save_js_files_for_tbw). (2) **tpr_exporter_ru**: drop coding header + `import os`/`import re`
  (+`from pathlib import Path`), type hints, `.append`, `os.stat`→`.stat()`, `.open(encoding)`,
  `except Exception`→`IndexError`, `re.sub("'")`→`.replace`. **⚠️ COUPLED TEMPLATE EDIT** — deleting
  the `i.compound_type_has_digit` helper FORCES `exporter/tpr/templates/tpr_headword_ru.jinja:48`
  guard simplification (`{%- if i.compound_type and not i.compound_type_has_digit -%}` →
  `{%- if i.compound_type -%}`), mirroring the upstream `tpr_headword.jinja` change. **That RU
  template has NO registry/SMD entry — flagged for registration (russian_copies).** copy_zip RU
  body diverges (N-A on version/beta logic). (3) **kindle_exporter_ru** (heavy, Roman-only): real
  logic = deconstructor-loop guard removal (safe — shadow pre-filters `Lookup.lookup_key.in_(chunk)`),
  `print`→`pr.white(escape())`, `Path(pth.epub_dir)`→`pth.epub_dir` (+ drop unused `from pathlib import
  Path`), 5× `.open(encoding)`, `+= [x]`→`.append`, `jinja_env: Environment` type hints; N-A =
  script_attr/SCRIPT_CONFIG/render_epd (shadow uses render_rpd_xhtml_ru + Lookup.rpd). (4)
  **webapp/main_ru**: 3× css/js `open(encoding)`; 8× `TemplateResponse` request→first positional arg
  (sites L99/115/131/157/224/254/304/570). PRESERVE templates_ru/_sbs split + 127.0.0.1. (5)
  **preloads_ru** = CONFIRMED NO-OP (never had make_roots_count_dict; main_ru imports it from mirror
  preloads.py which re-exports post-Commit-1). (6) **data_classes_ru** = NO-OP beyond B1.2 (only range
  change to data_classes.py is the 1-line variant rename, already fanned out in B1.2; no HeadwordData
  field additions). (7) **gui2/dps_example_field** = CONFIRMED NO-OP — inherits `choose_example`
  (MAX_SEARCH_RESULTS=100 + amber warning), not overridden; no shadow edit, no json entry needed.
  (8) **db_rebuild_from_tsv_dps**: strict port = L178 `read_tsv_files` `encoding="utf-8"`; ANALOGOUS
  (B3.7 precedent) = add encoding to 6 localized sbs/russian/tamil TSV reads+writes (Cyrillic/Tamil
  materiality) — flagged for 2d confirm. (9) **families_to_json_ru**: GlobalVars→@dataclass refactor
  (mirror upstream) + `json_dumper` `dict`→`data`/`write_text(encoding)` + `-> None`; PRESERVE
  paths=rupth(RuPaths)/data_ru_unpack×5/root_ru_meaning. (10) **titlepage.xhtml** = SKIP (date-only
  per SMD).
- **DONE Batch 6** — INSPIRED backports ×10 (judgement). Read all 10 upstream diffs for range R and
  grounded each against the actual inspired target. **Net recommended work: only 2 backports** — (a)
  `extract_body` adoption in 7 goldendict exporters (export_dpd_ru/_sbs, export_epd_sbs, export_help_ru/_sbs,
  export_roots_ru/_sbs — each has exactly 1 `body_start` site + imports from `tools.utils`; exact import +
  block anchors in dynamic_plan B6 "extract_body adoption" table); (b) the roots **N+1→1 query** fix
  (`defaultdict` pre-group of FamilyRoot) in export_roots_ru/_sbs. **All other inspired changes = SKIP/N-A**:
  CI workflow (RU release has no mobile/prepare_sources), export_variant_spelling_ru (builds HTML inline, no
  `<body>` find), main_ru/_sbs (**`self.paths` removal is N-A — divergence point, PRESERVE**), dps_fields (no
  sanskrit handlers), dps_fields_lists (no COMPOUND_FIELDS), generate_components.sh (pytest gate = 2d
  judgement). Type-hint/dataclass/zip/pathlib cosmetics all SKIP (no functional gain on diverged files).
  **Two opt-in judgement calls deferred to 2d:** B6.4 help refactors (zip cleanup / drop unused
  `__db_session__`), B6.10 `uv run pytest tests/` gate in generate_components.sh — both default SKIP.
- **TODO Batch 7** — 2d approval gate (present full plan; surface the 4 explicit 2d decisions).

### Pre-gathered facts for later batches (avoid re-running)
- **Template diffs (Batch 4):** 9 of 10 add one line before `<body>`:
  `{# do not change <body> — the export code splits header/body on this exact string (tools/utils.py extract_body) #}`
  (files: dpd_headword, dpd_root, dpd_see, dpd_spelling_mistake, dpd_variant_reading, epd,
  help_abbrev, help_abbrev_other, help_help). EXCEPTION `dpd_header.jinja`:
  `{% if d.i.needs_frequency_button %}` → `{% if d.i.needs_frequency_button and d.i.freq_data %}`.
  Shadow template names differ (`_ru.jinja`/`_sbs.jinja`) — Batch 4 must map by inspecting
  `ru_components/templates/` + `sbs_templates/` for the matching files & anchors.
- **db/epd diff is 130 lines, family-style refactor;** rpd/tpd shadows diverge heavily
  (SMD db.md: rpd uses Lookup.rpd + ru_meaning; tpd uses Lookup.tpd + ta_meaning, headwords only).
  Likely uses the new `tools/lookup_sync.sync_lookup_column` — check whether shadows adopt it.

## Stage 2b Decisions (recorded in dynamic_plan.md)

- **`db/models.py` → PORT rename surgically.** Apply ONLY the `Lookup` method rename `variants_pack`→`variant_pack` / `variants_unpack`→`variant_unpack` (param `dict`→`data`, comment fix) to the local file; preserve all localized tables/columns. Forced because synced callers adopt new names. Shadow callers `tpr_exporter_ru.py`, `tbw_exporter_ru.py`, `data_classes_ru.py` must be updated to the new name in Stage 3.
- **`pyproject.toml` → merge all upstream + preserve `num2words>=0.5.14` + drop duplicate `typst>=0.13.2` from tools group** (upstream adds `typst>=0.14.9` to project deps). `google-generativeai`→`google-genai` is needed (local already imports `from google import genai`). `uv.lock` must be REGENERATED via `uv lock` in Stage 3, NOT taken upstream verbatim.
- **`AGENTS.md` → keep local as-is, backport nothing.** User: "AGENTS.md stays the same as now locally." Stage 3 verify the local file is unchanged after the pull.

## Stage 2a Decisions (recorded in dynamic_plan.md)

- **D1 — `exporter/analysis/` → OVERWRITE WITH UPSTREAM** (user instruction 2026-06-12). Upstream and local did parallel refactors; local refactor is discarded in favor of upstream. All analysis files that exist upstream are taken verbatim (mirror, auto via execute_sync). Local-only `exporter/analysis/types.py` must be **manually deleted** in Stage 3 (git restore won't remove it — not in upstream tree). Upstream uses `analysis_types.py`+`_base.py` instead. Blast radius verified clean: only cross-cluster importer of local `types` was `tests/exporter/analysis/test_analyzer.py`, which is itself overwritten to upstream (imports `analysis_types`).
- **D2 — `tools/ai_antigravity_cli.py` + `ai_antigravity_cli_models.py`** → plain upstream, mirror/overwrite. Local-only AI tooling is in `unique_paths`, untouched by pull.
- **Blocker plan**: all 9 blockers cleared via one `run_acknowledged_blockers.txt` (runtime treats collision + deletion blockers identically — confirmed in `sync_runtime.py`). List: 6 analysis collisions + `tools/ai_antigravity_cli.py` + 2 upstream deletions.
- **needs_classification (7)**: all plain upstream-only → mirror; NO registry/SMD entry required (those trees are not registered shadow categories; they won't re-flag next sync).
- **resources/* (4 submodule pointers)**: SKIP — exclude from Commit 1 per project Commit-Scope rule (add to `run_exclusions.txt` or leave unstaged).
- **D3 — last-5-commits `#197` cluster → take upstream wholesale** (user, 2026-06-12). Scoped to exactly the 5 latest upstream commits (`19b46cf2~1..518672a6`): all analysis/AI/tools/tests files taken verbatim, exception `pyproject.toml` (registry rule). Confirmed all those files were already `mirror` in the plan, so no conflict. `db/models.py` and `AGENTS.md` are NOT in these 5 commits and stay `discuss`/normal-rules. `types.py → analysis_types.py` is a confirmed rename (R100). Full table in `dynamic_plan.md` §D3.

## Post-Sync Improvement Log (deal with AFTER sync is finished)

> Do NOT act on these during the sync. Revisit once the sync is complete; some may yield a process/tooling improvement worth promoting to `new_improvements.md` / the guide.

- **[FEATURE IDEA — user, Stage 2d, 2026-06-13]** Build a *registry → corresponding-tests
  mapping script*: read `registry.json`, resolve each shadow/localized file to its matching
  test(s), and run ONLY those targeted tests for shadow copies + localized files. Goal: a
  scoped verification command that never touches the full `pytest tests/` suite (avoids the
  memory-explosion failure mode). Deferred as new tooling — out of scope for executing this
  sync. Build after the sync lands. Note: the existing Stage 3 verification already uses a
  fixed targeted suite list, so this script is an ergonomics/coverage improvement, not a gap.

- **[CRITICAL ERROR — agent, Stage 2a, 2026-06-12]** When the user scoped the "take upstream wholesale" instruction to **exactly the last 5 upstream commits** (exception: `pyproject.toml`), the agent over-extended that scope to the entire 145-commit change set and proposed treating `db/models.py` (NOT in those 5 commits) under it. Blindly taking upstream `db/models.py` would have deleted the fork's localized `SBS`/`Russian`/`Tamil`/`Sinhala` tables and `*_ru` columns. The agent caught and corrected the data-loss risk, but only after wrongly widening the user's scope and burning a round-trip. User flagged it as a critical error.
  - **Root cause:** treated a scope-qualified instruction ("last 5 commits") as a general rule; did not first nail down the exact member set before classifying/recommending.
  - **Correct behavior (now in memory `feedback_apply_scoped_instructions_literally`):** when an instruction names a scope, resolve the exact file set first (`git diff <first>~1..<tip> --name-status`), state it back, and reason only about that set. Risks on out-of-scope files are a *separate* observation, never folded into the scoped instruction.
  - **Possible process improvement to evaluate post-sync:** have Stage 2a/2c explicitly compute and pin a "last-N-commits scope" file list when the user gives one, and/or add a guide note that scope qualifiers must be resolved to a concrete path set before classification. Consider whether `prep_analyzer`/`dynamic_plan` should surface per-commit file groupings to make scoped instructions unambiguous.

## Last upstream sync

- **Commit / tag**: `0ea5883380f5`
- **Full SHA**: `0ea5883380f56b682cf8574043afb8e66cca3260`
- **Date**: `2026-06-01T10:21:25+05:30`
- **Ref**: `upstream/main`

## Target upstream SHA

`518672a65fa3ea7c36c4c754dc5276bb41f92da7` (`upstream/main`)

## Completed Work

- Stage 1.1 Environmental Check: PASS
- Stage 1.2 Shadow Health Check: PASS (reviewed no-op added in prior session)
- Stage 1.3 Validation: PASS (both scripts pass)
- Stage 1.4 Factual Diff: PASS — prep artifacts generated

## Commands Run This Dispatch

1. `uv run python3 kamma/upstream_sync/scripts/validate_registry.py`
   - Result: `registry.json is valid`

2. `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py`
   - Result: `SMD coverage complete` (75 entries, 0 gaps, 0 mismatches, 0 unregistered, 0 rubric failures)

3. `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py kamma/threads/20260612_upstream_sync`
   - Result: Wrote `prep_report.md` and `prep_manifest.json` to thread dir.

## Files Changed

- `kamma/threads/20260612_upstream_sync/handoff.md` (this file, updated)
- `kamma/threads/20260612_upstream_sync/prep_report.md` (generated by prep_analyzer)
- `kamma/threads/20260612_upstream_sync/prep_manifest.json` (generated by prep_analyzer)

## Prep Manifest Summary

- **Total changed upstream files**: 178
- **Deleted upstream paths**: 2
  - `exporter/kindle/tests/test_epd.py`
  - `tools/update_test_add.py`

### blocker_paths (9)

Files that are DELETED upstream or otherwise flag as blockers:

```
exporter/analysis/ai_response.py
exporter/analysis/prompts.py
exporter/analysis/ranking.py
exporter/analysis/rendering.py
exporter/analysis/retry.py
exporter/analysis/scoring.py
exporter/kindle/tests/test_epd.py
tools/ai_antigravity_cli.py
tools/update_test_add.py
```

### discuss_paths (3)

Files flagged `discuss: true` in registry — require orchestrator/ADVANCED decision before sync:

```
AGENTS.md
db/models.py
pyproject.toml
```

### needs_classification_paths (7)

New upstream files not yet in registry — require classification before sync:

```
.github/workflows/mobile_release.yml
exporter/analysis/_base.py
exporter/analysis/analysis_types.py
scripts/fix/sanskrit_sutra_bsk.py
scripts/project_management/project_health_check.py
tools/ai_antigravity_cli_models.py
tools/lookup_sync.py
```

## Open Decisions (require orchestrator/ADVANCED before Stage 2)

1. **discuss_paths (3 files)**: `AGENTS.md`, `db/models.py`, `pyproject.toml` — each is flagged `discuss: true` in registry. ADVANCED must decide per-file: upstream-copy, shadow-merge, or skip.

2. **needs_classification_paths (7 files)**: New upstream files not in registry. ADVANCED must classify each (upstream_only, local_ignore, new shadow, etc.) and update `registry.json` before execute_sync.py can proceed cleanly.

3. **blocker_paths (9 files)**: `exporter/analysis/` subset plus two deleted files. The deleted files (`test_epd.py`, `update_test_add.py`) need removal decisions. The `exporter/analysis/` blockers and `tools/ai_antigravity_cli.py` need ADVANCED assessment of local impact.

## Analytical Context for Stage 2 (from orchestrator, Opus)

- **gui2 reviewed no-op (done in Stage 1.2):** Added an entry to
  `kamma/upstream_sync/reviewed_shadow_noops.json` for
  `sync_commit 5799afbb57f493accda30813e32982112c6e18c7`,
  source `gui2/dpd_fields_examples.py` -> shadow `gui2/dps_example_field.py`.
  Rationale: `DpsExampleField` subclasses upstream `DpdExampleField` and imports
  `book_codes`; the 5799afbb changes (added book codes, `_toggle_tools_visibility`
  signature tightening, import whitespace) are all inherited/imported, so no shadow
  edit was needed. User confirmed. This is PRIOR-sync drift, unrelated to the new
  `gui2/dpd_fields_examples.py` change in THIS range (MAX_SEARCH_RESULTS=100 + amber
  warning) — that new change is a `dps_copies` item to handle normally in Stage 2/3
  and will also be inherited by the shadow.

- **exporter/analysis/ restructure (HIGH ATTENTION):** Upstream appears to have
  restructured `exporter/analysis/`: new files `_base.py` and `analysis_types.py`
  (needs_classification), and `ai_response.py`, `prompts.py`, `ranking.py`,
  `rendering.py`, `retry.py`, `scoring.py` flagged as blockers (likely deleted/merged
  upstream). This overlaps RECENT LOCAL WORK on `sbs-ru`:
  `6813429d remove: eliminate AnalysisView from gui2`,
  `63abb626 analysis: planning size error solution`,
  `14a6eb4e refactor: reconcile ai_manager deps with upstream`,
  `e3c312ac fix: apply final tie-break logic and finalize translate_core refactor`.
  Stage 2 MUST diff each of these against the registry (and against local divergence)
  before deciding port/skip — do not blindly accept upstream deletions here.
  `tools/ai_antigravity_cli.py` (blocker) + new `tools/ai_antigravity_cli_models.py`
  (needs_classification) are part of the same AI-tooling change set.

- **Deleted upstream files (deletion blockers):** `exporter/kindle/tests/test_epd.py`
  and `tools/update_test_add.py`. If accepted, acknowledge by creating
  `kamma/threads/20260612_upstream_sync/run_acknowledged_blockers.txt` (one path per
  line) so `verify_manifest` warns but does not block.

- **Stale command note:** Plan step 1.1's `ruff check ... --select F821,E999` errors
  because ruff removed the `E999` rule. FAST fell back to `--select F821` (only legacy
  hits in `scripts/dps_archive/`). The guide/plan command should be updated to drop
  `E999` in a future cleanup (out of scope for this sync unless user requests).

## Next Action

Stage 2 is fully COMPLETE and APPROVED (2026-06-13). Next is **Stage 3 = Batch 0** (FAST):
run `execute_sync.py` to perform the upstream pull, then prepare Commit 1 and HARD STOP
(Commit-1 is a mandatory session boundary). Execute Batch 0 exactly as written in
`dynamic_plan.md` "BATCH 0 — execute_sync pre-flight & Commit 1":

1. **B0.1** — create `run_acknowledged_blockers.txt` with the 9 listed paths.
2. **B0.2** — do NOT add `resources/*` to `run_exclusions.txt`; leave pointer changes unstaged.
3. **B0.3** — `uv run python3 kamma/upstream_sync/scripts/execute_sync.py kamma/threads/20260612_upstream_sync` (leaves changes unstaged).
4. **B0.4** — post-pull verification (2 deletions propagated; `analysis_types.py`/`_base.py` present;
   local `types.py` still present → delete in B1.4; `db/models.py`/`pyproject.toml`/`AGENTS.md`
   show NO pull changes — if any changed, STOP → ADVANCED). Confirm `resources/*` NOT staged.
   Then stage `git add .` and commit:
   `#sync: upstream pull 0ea58833..518672a6, <N> files, 2026-06-13` (`<N>` from `git diff --cached --stat | tail -1`).

After Commit 1: HARD STOP, restart a fresh FAST session for Batch 1 (reconciliation edits).

**Approved 2d decisions carried into Stage 3:** B6.4 SKIP · B6.10 SKIP (no full-suite pytest) ·
register `tpr_headword_ru.jinja` (`russian_copies`) during B5.2 · B5.8 apply-by-analogy (6 TSV opens).

## Next Model

FAST — Stage 3, Batch 0 only. Mechanical execution of the approved plan; no analysis or
judgment. STOP and hand to ADVANCED on any missing anchor, preservation failure (B0.4 step 5),
or test failure not covered by the plan.

## Restart Prompt

```text
Switch to FAST. Start a fresh session.

Continue upstream sync thread: kamma/threads/20260612_upstream_sync (Stage 3, Batch 0 — FAST).
First read:
1. kamma/threads/20260612_upstream_sync/handoff.md (Next Action = Batch 0 mechanics)
2. kamma/upstream_sync/guide.md (Stage 1 §3 Automated Pull + Stage 3)
3. kamma/threads/20260612_upstream_sync/dynamic_plan.md ("BATCH 0 — execute_sync pre-flight & Commit 1")

Task: Execute Stage 3 Batch 0 ONLY:
- B0.1 write run_acknowledged_blockers.txt (9 paths).
- B0.3 run execute_sync.py (leaves changes unstaged).
- B0.4 post-pull verification, then stage `git add .` and prepare Commit 1
  `#sync: upstream pull 0ea58833..518672a6, <N> files, 2026-06-13`.
Then HARD STOP (Commit 1 is a session boundary). Write the Batch 1 restart prompt.

R=0ea5883380f56b682cf8574043afb8e66cca3260..518672a65fa3ea7c36c4c754dc5276bb41f92da7

Do NOT proceed to Batch 1 edits. STOP → ADVANCED on any missing anchor, preservation
failure (B0.4 step 5: db/models.py / pyproject.toml / AGENTS.md changed by the pull), or
unexpected test/command failure. Never stage resources/* submodule pointers.
```

Do not continue in this session.
