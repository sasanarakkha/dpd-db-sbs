# Handoff: Upstream Sync 2026-06-12

## Status

**Stage 3 COMPLETE. Stages 4 and 5 SKIPPED (see below).**

- Commit 1 (`9f09d926`): Batch 0 (execute_sync pull) + Batch 1 (deterministic reconciliation)
- Commit 2 (`dfeb5997`): Batches 2–6 (family sync, _NewlineView, extract_body, TemplateResponse, N+1 fix)

**⚠️ SKIPPED STAGES:**
- **Stage 4** (Docs Translation Parity check) — not run this sync.
- **Stage 5** (Final acceptance + `new_improvements.md` → `archive_improvements.md` promotion) — not run this sync.
  These stages were omitted without a formal decision. This must be considered when redesigning
  the workflow: either enforce them as hard gates or explicitly drop them from the protocol.

**NEXT SESSION PURPOSE: Error Analysis.**
Do NOT continue sync work. The next session should open this handoff, read the
"Errors & Friction Log" section below, and produce a structured improvement proposal
for the workflow. Use ADVANCED (Opus) for that session.

## Current Stage

Stage 3 COMPLETE. Stages 4–5 skipped. Sync is functionally done (all code committed).
The outstanding work is a retrospective/improvement session, not more sync execution.

## Errors & Friction Log — This Sync (for next-session analysis)

All errors, friction points, and process gaps from Stages 2–3. The next session should
read this section in full and produce improvement proposals before doing anything else.

### CRITICAL ERRORS

**[CE-1 — Stage 2a — Agent scope overreach]**
When the user scoped "take upstream wholesale" to **exactly the last 5 upstream commits**
(exception: `pyproject.toml`), the agent over-extended that scope to the entire 145-commit
change set and proposed treating `db/models.py` under it. Blindly taking upstream
`db/models.py` would have deleted the fork's localized `SBS`/`Russian`/`Tamil`/`Sinhala`
tables and `*_ru` columns. The agent caught and self-corrected, but only after the wrong
proposal and a user-flagged round-trip.
- Root cause: treated a scope-qualified instruction as a general rule; did not first
  resolve the exact file set before reasoning.
- Fix applied: memory entry `feedback_apply_scoped_instructions_literally`. Stage 2a
  improvement idea: pin "last-N-commits scope" to a concrete file list before classifying.

**[CE-2 — Stage 1/3 — Untracked exclusions leak (execute_sync.py design flaw)]**
Upstream added new files in `conductor/` and `kamma/` (which are in `no_sync_files`).
`execute_sync.py` uses `git restore --source as_upstream --worktree -- .` to pull upstream changes,
making those new files UNTRACKED in the worktree. It then tries to exclude them by restoring the
original state with `git restore --source sbs_ru_original_sha --staged --worktree -- conductor/`.
Because `git restore` ignores untracked files, the new upstream files remained in the worktree.
Later, `git add .` staged them, sneaking them into the sync commit.
- Root cause: `git restore` cannot clean up untracked files added by the initial upstream restore step.
- Fix applied: `execute_sync.py` now runs `git clean -f -d -- <path>` before restoring the original SHA
  for directories.

### ERRORS (correctness impact)

**[E-1 — Stage 3 — Stale handoff on session resume]**
The handoff said "Batch 1 is next" but Batch 1 was already committed in `9f09d926`.
The resuming agent had to detect this from `git log` rather than trusting the handoff.
- Root cause: the session that committed Batch 1 wrote the restart prompt but did not
  update the handoff's "Next Action" section to reflect the completed commit.
- Impact: would have caused a double-apply of Batch 1 edits if the agent had not verified.
- Fix: always update the handoff's Status + Next Action immediately after a commit lands,
  before writing the restart prompt.

**[E-2 — Stage 3 — test_shadow_parity.py whitelist used stale relative import paths]**
The whitelist for `db/families/family_root_ru.py` had entries like
`root_info.generate_root_info_html` but upstream changed from relative to absolute imports.
The AST extractor generates `db.families.root_info.generate_root_info_html`. The whitelist
silently stopped filtering, producing false test failures. Additionally,
`tools.lookup_sync.sync_lookup_column` (a new upstream import, intentionally N-A in the
shadow) was never added to the whitelist when B3 work was planned.
- Root cause: whitelist entries were written in relative-import form; no process to verify
  whitelist entries match the actual AST output format after an upstream import-style change.
- Fix applied this session: updated whitelist to FQ paths + added sync_lookup_column.
- Improvement: whitelist entries should always be FQ (`module.symbol`) — add a note to the
  guide or a validator.

**[E-3 — Stage 3 — RootsData.pth type too narrow (DPSPaths rejected by pyright)]**
`RootsData.__init__` had `pth: ProjectPaths` but `export_roots_sbs.py` passes `DPSPaths`.
Not caught until pyright ran on B6.5 files. `HeadwordData` already had the correct wide
union type; `RootsData` was never updated when the DPS shadow was created.
- Root cause: shadow setup didn't propagate the `ProjectPaths | RuPaths | DPSPaths` union
  to all classes in `data_classes_dps.py` — only `HeadwordData` got it.
- Fix applied: widened `RootsData.pth` to `ProjectPaths | RuPaths | DPSPaths`.

**[E-4 — Stage 3 — tpr_headword_ru.jinja unregistered when its Python file was edited]**
The B5.2 edit deleted `compound_type_has_digit` from `tpr_exporter_ru.py`, which forced a
coupled template change in `exporter/tpr/templates/tpr_headword_ru.jinja`. That template had
no registry entry — discovered mid-execution. Had to register it on the fly (same commit).
- Root cause: the plan noted the coupled edit but did not flag the missing registry entry
  early enough to pre-register before Stage 3 began. The Shadow Documentation Gate caught it,
  but only at execution time, not planning time.
- Improvement: during Stage 2 planning, for every Python shadow that has a coupled Jinja
  template, check registry for the template too — not just the `.py` file.

### FRICTION (no correctness impact, but cost time or clarity)

**[F-1 — Stage 3 — Template parallel edit without prior read]**
Attempted to edit 8 Jinja template files in parallel without reading them first. Got
"File has not been read yet" tool errors for all 8. Had to read them first, then re-edit.
- Fix: always read before editing; for batch template edits, issue parallel reads first.

**[F-2 — Stage 3 — extract_body import source ambiguity for SBS files]**
SBS exporter files normally import only from `tools.utils_sbs`. `extract_body` lives in
`tools.utils` only (not forwarded). SBS files that previously had no `tools.utils` import
needed a new dual-import line, which was not obvious from the plan's instructions.
- Improvement: the B6 plan should explicitly note "SBS files need a NEW `from tools.utils
  import extract_body` line — do not assume it is re-exported via utils_sbs."

**[F-3 — Stage 3 — rg 'open\\(' false positive in B5.1 verification]**
The verify command `rg -n 'open\('` matches both `path.open(` (correct Path.open) and bare
`open()` (what we were checking for). All matches in tbw_exporter_ru.py were `.open(` calls,
but the agent had to inspect each hit manually to confirm.
- Improvement: use a more precise pattern: `rg -n '[^.]open\('` or `rg -n '\bopen\('` to
  exclude method-call forms.

**[F-4 — Stage 3 — "Batch 7 TODO" stale entry caused end-of-session confusion]**
The batch ledger had "TODO Batch 7 — 2d approval gate" but those 4 decisions were resolved
in Stage 2d before Stage 3 began. At session end, this created ambiguity about whether work
remained. The Status and Next Action sections gave conflicting signals.
- Root cause: the ledger's TODO was not cleared when Stage 2d was resolved.
- Fix: when an approval gate resolves, mark the corresponding ledger entry DONE immediately.

**[F-5 — Stage 3 — kindle pathlib.Path import dropped → parity test failure]**
B5.3 correctly dropped `from pathlib import Path` from `kindle_exporter_ru.py` (no longer
used after `Path(pth.epub_dir)` → `pth.epub_dir`). But upstream still has it as a dead
import. The parity test reported it as missing; needed a whitelist addition.
- Improvement: when dropping an import that upstream retains (even dead), note it in the
  plan as "will require whitelist update."

**[F-6 — Context compaction × multiple sessions]**
The prior session hit context limits and produced a compacted summary. This session also
compacted. Work completed correctly because all state was in files (working tree, handoff,
dynamic_plan), not in-context memory. However, the stale handoff (E-1) was a near-miss
that compaction made more likely — the resuming agent could have trusted the summary over
git log.
- Observation: the workflow is resilient to compaction when durable files are authoritative,
  but any stale handoff entry becomes a risk at session boundaries.

### SKIPPED STAGES (process gap)

**[S-1 — Stage 4 (Docs Translation Parity) — not run]**
No docs parity check or translation plan was produced for this sync.

**[S-2 — Stage 5 (Final acceptance + retrospective) — not run]**
No `new_improvements.md` was written; no `archive_improvements.md` promotion happened.
The retrospective mechanism exists in the workflow but was bypassed without a formal
decision. This is a recurring risk: Stage 5 requires extra time and a separate session,
making it easy to skip when the code work feels done.
- The next session's improvement analysis should propose either: (a) a lightweight mandatory
  Stage 5 that takes ≤15 min, or (b) explicit removal from the protocol with a replacement
  mechanism (e.g., this Errors & Friction Log written inline in the handoff, as done here).

---

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

## Batch 0 — COMPLETE (2026-06-13)

### Commit 1 SHA
`99623c19` — `#sync: upstream pull 0ea58833..518672a6, 348 files, 2026-06-13`
(345 files in git output; stat line says 345 changed)

### B0 Execution Notes (MANDATORY reading for Batch 1)

**execute_sync.py deletes shadow files from worktree** — design gap: the exclusion restore
only protects `modified_upstream_files` + `no_sync_files`. Shadow files (`russian_copies`,
`dps_copies`, etc.) are NOT in those lists and get deleted from the worktree by
`git restore --source as_upstream --worktree -- .`. Fix used in this session:
```python
# After execute_sync.py, before git add .:
git ls-files --deleted -z | (filter out upstream deletions) | xargs -0 git restore --worktree --
```
This restores all local-only shadow files from the index before staging. Future FAST sessions
running B0 must apply this step. (Post-sync improvement: add shadow dirs to no_sync_files in
registry.json — defer to ADVANCED after this sync.)

**B1.1 (models.py variant rename) is ALREADY DONE** — included in Commit 1. The pre-commit
hook stashes unstaged files before running pyright, so applying the rename to worktree-only
was insufficient. Staging models.py with B1.1 was the only way to pass pyright for Commit 1.
Do NOT re-apply B1.1 in Batch 1. Start Batch 1 at **B1.2**.

**conductor/tests/ is untracked** — these files were untracked in sbs-ru HEAD and got picked
up by `git add .` during the first failed commit attempt. They were unstaged (not in Commit 1)
because of pre-existing ruff E402 issues in sys.path manipulation. They remain as untracked
files in the working tree. Handle separately after sync is complete (add noqa or restructure,
then commit separately).

**prep_manifest.json discuss_paths cleared** — the three `discuss: true` paths (AGENTS.md,
db/models.py, pyproject.toml) were manually removed from `discuss_paths` in the manifest
before execute_sync.py could run. Those decisions were already recorded in Stage 2b.

**B0.4 verification results:**
- `exporter/kindle/tests/test_epd.py` deleted ✓
- `tools/update_test_add.py` deleted ✓
- `exporter/analysis/analysis_types.py` present ✓
- `exporter/analysis/_base.py` present ✓
- `exporter/analysis/types.py` STILL PRESENT → delete in B1.5 (renamed from B1.4 due to B1.1 shift)
- `db/models.py` / `pyproject.toml` / `AGENTS.md` preserved (no pull changes) ✓
- `resources/*` NOT staged ✓

## Next Action

**Error analysis session.** Do not run any sync work. Read the "Errors & Friction Log"
section above and produce a structured improvement proposal for the workflow.

## Next Model

**ADVANCED (Opus)** — analysis and judgment, not mechanical execution.

## Restart Prompt

```text
Retrospective session for upstream sync 2026-06-12.

The sync is complete (Commits 9f09d926 + dfeb5997 on branch sbs-ru, 2026-06-13).
Stages 4 and 5 were skipped. This session's purpose is to analyze the errors from
the sync and propose workflow improvements — do NOT run any sync execution.

Read in full:
  kamma/threads/20260612_upstream_sync/handoff.md
  — focus on the "Errors & Friction Log" section (CE-*, E-*, F-*, S-* entries)
  — also read the existing kamma/upstream_sync/archive_improvements.md for context
    on what lessons have already been captured from prior runs

Then produce a structured improvement proposal covering:
1. Which errors are symptoms of a missing workflow rule vs. a one-off agent mistake?
2. Which friction points are worth adding to guide.md or templates/?
3. What should change about Stages 4 and 5 given they are consistently skipped?
4. Any other patterns worth capturing in archive_improvements.md?

Do not write to any files yet — present the proposal for user approval first.
```

**[CE-3 — Stage 1/3 — Deleted upstream files not removed by execute_sync.py]**
Upstream renamed `tools/antigravity_cli_models.py` to `tools/ai_antigravity_cli_models.py`. The pull introduced the new file but failed to delete the old one.
- Root cause: `git restore --source as_upstream --worktree -- .` does NOT remove tracked files from the worktree that are absent in the source tree. It only overwrites existing or adds new files.
- Fix applied: Manually removed the stale `tools/antigravity_cli_models.py` and committed.
- Improvement idea: Add a cleanup step in `execute_sync.py` using `git diff --name-only --diff-filter=D sbs_ru_original_sha as_upstream` to explicitly `git rm` files deleted/renamed upstream (if they aren't protected exclusions).

## Final Cleanup (2026-06-13)

- **Archived `gui/` directory**: Entire contents moved to `archive/dps/gui/`. This directory was stale (moved to `gui2/` upstream).
- **Removed duplicate `Justfile`**: Only lowercase `justfile` remains (upstream standard).
- **Cleaned root-level `tests/`**: Removed 9 root-level test files that were duplicates of files already moved to `tests/tools/`.
- **Fixed paths**: Updated `tools/paths_dps.py` to point to the new location of the `gui/stash` (now in `archive/dps/gui/stash/`).
