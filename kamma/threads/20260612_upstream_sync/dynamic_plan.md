# Dynamic Plan — Upstream Sync 2026-06-12

**Stage 2a — Impact Assessment (ADVANCED / Opus).**
Classification only. No mechanical edits, no file copies, no `execute_sync.py`.

## Range
- From: `0ea5883380f56b682cf8574043afb8e66cca3260`
- To:   `518672a65fa3ea7c36c4c754dc5276bb41f92da7` (`upstream/main`)
- Total changed upstream paths: 178 · deleted: 2 · blockers: 9 · discuss: 3 · needs-classification: 7

---

## Classification legend

| Bucket | Meaning | Stage 3 action |
|---|---|---|
| **mirror** | Plain upstream file, no local divergence. `execute_sync` restores it to the upstream version automatically. | None (verify only). |
| **port** | Upstream file with a registered shadow copy (`*_ru/_sbs/_dps/_ta`) and/or a `modified_upstream_files` divergence. Upstream source is taken verbatim; the **shadow / divergent copy** is manually merged. | Manual shadow/divergence port per Iron Rule. |
| **inspired** | `inspired_by_upstream` local file. No strict parity; review upstream diff and backport only useful improvements. | Selective backport (judgement). |
| **preserve** | Local-protected file (`modified_upstream_files` / `no_sync_files`). `execute_sync` restores local version; upstream change merged manually only if wanted. | Manual merge if applicable. |
| **discuss** | `discuss: true`. Deferred to Stage 2b. | — (resolve in 2b). |
| **skip** | `skip_sync_patterns`, submodule pointers, or irrelevant. Not a sync action. | None. |
| **docs** | `docs/` file → Stage 4 docs-parity / `docs_rus/` translation. | Stage 4. |

---

## Decision log (resolved before 2a)

### D1 — `exporter/analysis/` cluster → OVERWRITE WITH UPSTREAM (user, 2026-06-12)

User instruction, verbatim: *"exporter/analysis/ fully need to be synced with the upstream — any changes should overwrite all existing one!"*

Context: upstream and the local `sbs-ru` branch did **parallel refactors** of the same analysis work.
- Local refactor commits (`afd98268 split translate_core into specialized modules`, `e3c312ac`, `14a6eb4e`, `6813429d remove AnalysisView`) split logic into `types.py` and added `ai_response.py`, `prompts.py`, `ranking.py`, `rendering.py`, `retry.py`, `scoring.py`.
- Upstream split the same work into `analysis_types.py` + `_base.py` and added the same six module names.

Decision consequences:
1. Every `exporter/analysis/*` file that exists upstream is taken **verbatim from upstream** (classification: **mirror** — handled automatically by `execute_sync`'s `git restore --source as_upstream`). This discards the local analysis refactor in favor of upstream. User has accepted this.
2. `exporter/analysis/types.py` is **local-only** (no upstream counterpart). `git restore --source as_upstream` will NOT touch it. It must be **manually deleted** in Stage 3.
3. Upstream's `analysis_types.py` + `_base.py` are new files (in `needs_classification`); they arrive as plain upstream files. No registry entry needed (the `exporter/analysis/` tree is not registered as shadow/inspired — it is plain upstream territory).

Blast-radius verification (done in 2a):
- Only importer of the doomed local `exporter.analysis.types` outside the cluster is `tests/exporter/analysis/test_analyzer.py` (`from exporter.analysis.types import AnalysisOption`). Upstream's own `tests/exporter/analysis/test_analyzer.py` imports `from exporter.analysis.analysis_types import AnalysisOption`. **`tests/` is synced by `execute_sync`** (it is in `skip_sync_patterns`, which only excludes from Stage-1 *reporting*, not from the pull). So the test file is overwritten to the upstream version and the import is consistent after sync. No manual test edit required beyond confirming the overwrite landed.
- `exporter/analysis/analyzer.py` (overwritten) → upstream version imports `analysis_types`, not `types`. Consistent.
- No other repo path imports `exporter.analysis.types`. (`scripts/dps_archive/*` and `exporter/mcp/server.py` import `analyzer` / `translate_core` symbols, all of which survive in the upstream versions.)

### D2 — `tools/ai_antigravity_cli.py` + `tools/ai_antigravity_cli_models.py`

Both are plain upstream files (not registered shadows). `ai_antigravity_cli.py` is a collision blocker (added upstream, already present locally); `ai_antigravity_cli_models.py` is a new upstream file (`needs_classification`). Both classify as **mirror** — overwrite/accept upstream. Local-only AI tooling (`ai_batch_processor.py`, `ai_json_parser.py`, `ai_llm_factory.py`, `ai_meaning_checker.py`, `ai_openai_manager.py`, `ai_related.py`) is in `unique_paths`, is not in the upstream tree, and is therefore untouched by the pull.

### D3 — Last-5-commits `#197` cluster → TAKE UPSTREAM WHOLESALE (user, 2026-06-12)

User scoped the "take upstream, no local merge" instruction to exactly the **last 5 upstream commits** (all `#197` AI/analysis work):

```
19b46cf2  tools: rename antigravity_cli_models to ai_antigravity_cli_models
b852a8d7  ai: fix antigravity probe, request delay, timeouts
0f894745  deps: switch from google-generativeai to google-genai
a7ad58b3  analysis: break circular imports with _base module
518672a6  ai: fall back to default agy model, fix gatha example crash
```

Files touched by these 5 commits (`git diff 19b46cf2~1..518672a6`), **all taken upstream verbatim, exception `pyproject.toml`**:

| File | Status in 5 commits | Classification |
|---|---|---|
| `exporter/analysis/_base.py` | added | mirror |
| `exporter/analysis/types.py → analysis_types.py` | **rename (R100)** | mirror (see D1) |
| `exporter/analysis/ai_response.py`, `analyzer.py`, `prompts.py`, `ranking.py`, `rendering.py`, `retry.py`, `scoring.py`, `translate_core.py` | modified | mirror (D1) |
| `gui2/ai_search.py`, `gui2/pass1_auto_view.py`, `gui2/pass2_auto_view.py` | modified | mirror |
| `tools/ai_antigravity_cli.py` | modified | mirror (D2) |
| `tools/antigravity_cli_models.py → ai_antigravity_cli_models.py` | rename (R063) | mirror (D2) |
| `tools/ai_deepseek_manager.py`, `ai_manager.py`, `ai_models.json`, `cst_source_sutta_example.py` | modified | mirror |
| `tests/exporter/analysis/test_analyzer.py`, `test_passage_regression.py` | modified | mirror (synced) |
| `tests/tools/test_ai_antigravity_cli.py`, `test_antigravity_cli_models.py → test_ai_antigravity_cli_models.py` | modified / rename | mirror (synced) |
| `pyproject.toml` | modified | **EXCEPTION → registry rule (discuss, see 2b)** |
| `uv.lock` | modified | mirror — but keep consistent with the `pyproject.toml` 2b decision |

**Consistency note:** every file above (except `pyproject.toml`) was already classified `mirror` in this plan, so D3 introduces no conflict — it confirms the existing classification and scopes the "no local merge" rule. `db/models.py` and `AGENTS.md` are **NOT** in these 5 commits and remain `discuss` under normal sync rules.

**`types.py` rename mechanics (refines D1):** upstream renamed `exporter/analysis/types.py` → `analysis_types.py`. At the pinned `as_upstream` SHA, `types.py` does not exist. Local also has a `types.py` (from the discarded local refactor). Stage 3 must verify after `execute_sync` that `analysis_types.py` exists and `exporter/analysis/types.py` is gone — manually delete the local copy if the restore did not remove it (it is not in the upstream tree, so auto-removal is not guaranteed).

---

## Blocker resolution plan (9 paths)

All nine clear via a single `run_acknowledged_blockers.txt` in the thread dir (the runtime removes any acknowledged path from `effective_blockers`, collision or deletion alike — confirmed in `sync_runtime.py`).

| Blocker path | Type | Classification | Why acknowledging is correct |
|---|---|---|---|
| `exporter/analysis/ai_response.py` | collision | mirror | D1 — overwrite with upstream. |
| `exporter/analysis/prompts.py` | collision | mirror | D1. |
| `exporter/analysis/ranking.py` | collision | mirror | D1. |
| `exporter/analysis/rendering.py` | collision | mirror | D1. |
| `exporter/analysis/retry.py` | collision | mirror | D1. |
| `exporter/analysis/scoring.py` | collision | mirror | D1. |
| `tools/ai_antigravity_cli.py` | collision | mirror | D2 — plain upstream file, overwrite. |
| `exporter/kindle/tests/test_epd.py` | deletion | skip (delete) | Upstream removed it; propagate deletion. |
| `tools/update_test_add.py` | deletion | skip (delete) | Upstream removed it; propagate deletion. |

**Stage 3 mechanical note:** create `kamma/threads/20260612_upstream_sync/run_acknowledged_blockers.txt` listing all 9 paths (one per line) before running `execute_sync.py`.

---

## `needs_classification` resolution (7 paths)

All seven are new upstream-only files with no local collision. They are plain upstream files; the `exporter/analysis/` and `tools/` trees they sit in are not registered shadow categories, so **no `registry.json`/SMD entry is required**. They will not re-flag on the next sync (they will already be in the synced baseline). Classification = **mirror** (accept verbatim).

| Path | Classification | Note |
|---|---|---|
| `.github/workflows/mobile_release.yml` | mirror | New upstream CI workflow; no local counterpart. |
| `exporter/analysis/_base.py` | mirror | D1 — part of upstream analysis refactor. |
| `exporter/analysis/analysis_types.py` | mirror | D1 — upstream's `types.py` equivalent. |
| `scripts/fix/sanskrit_sutra_bsk.py` | mirror | New upstream script. |
| `scripts/project_management/project_health_check.py` | mirror | New upstream script (new dir). |
| `tools/ai_antigravity_cli_models.py` | mirror | D2 — companion to `ai_antigravity_cli.py`. |
| `tools/lookup_sync.py` | mirror | New upstream tool. |

---

## PORT — shadow sources & divergent upstream files (Stage 3 manual merge)

Upstream source taken verbatim; the listed shadow/divergent copy(ies) must be manually merged per the Iron Rule. **Structural-refactor check (guide §2.1):** for each, Stage 2c must diff the upstream change and, if it includes type-hint modernisation / `os`→`pathlib` / `print`→`pr.*` / dead-code removal, carry those into the shadow too — not just feature changes.

| Upstream source | Shadow / divergent target(s) | Category |
|---|---|---|
| `db/backup_tsv/backup_dpd_headwords_and_roots.py` | `scripts/backup/backup_dps.py` | dps_copies |
| `db/epd/epd_to_lookup.py` | `db/rpd/rpd_to_lookup.py`, `db/tpd/tpd_to_lookup.py` | russian_copies, tamil_copies |
| `db/families/family_compound.py` | `db/families/family_compound_ru.py` | russian_copies |
| `db/families/family_idiom.py` | `db/families/family_idiom_ru.py` | russian_copies |
| `db/families/family_root.py` | `db/families/family_root_ru.py` | russian_copies |
| `db/families/family_set.py` | `db/families/family_set_ru.py` | russian_copies |
| `db/families/family_word.py` | `db/families/family_word_ru.py` | russian_copies |
| `db/lookup/help_abbrev_add_to_lookup.py` | `db/lookup/help_abbrev_add_to_lookup_ru.py` | russian_copies |
| `exporter/deconstructor/deconstructor_exporter.py` | `exporter/deconstructor/deconstructor_exporter_ru.py` | russian_copies |
| `exporter/goldendict/data_classes.py` | `exporter/goldendict/data_classes_dps.py` | dps_copies |
| `exporter/goldendict/export_epd.py` | `exporter/goldendict/export_rpd.py` | russian_copies (also inspired_sbs below) |
| `exporter/goldendict/templates/dpd_header.jinja` | `ru_components/templates/dpd_header.jinja`, `sbs_templates/dpd_header.jinja` | russian/sbs |
| `exporter/goldendict/templates/dpd_headword.jinja` | `ru_components/templates/…`, `sbs_templates/…` | russian/sbs |
| `exporter/goldendict/templates/dpd_root.jinja` | `ru_components/templates/…`, `sbs_templates/…` | russian/sbs |
| `exporter/goldendict/templates/dpd_see.jinja` | `ru_components/templates/…`, `sbs_templates/…` | russian/sbs |
| `exporter/goldendict/templates/dpd_spelling_mistake.jinja` | `ru_components/templates/…`, `sbs_templates/…` | russian/sbs |
| `exporter/goldendict/templates/dpd_variant_reading.jinja` | `ru_components/templates/…`, `sbs_templates/…` | russian/sbs |
| `exporter/goldendict/templates/epd.jinja` | `ru_components/templates/…`, `sbs_templates/…` | russian/sbs |
| `exporter/goldendict/templates/help_abbrev.jinja` | `ru_components/templates/…`, `sbs_templates/…` | russian/sbs |
| `exporter/goldendict/templates/help_abbrev_other.jinja` | `ru_components/templates/…`, `sbs_templates/…` | russian/sbs |
| `exporter/goldendict/templates/help_help.jinja` | `ru_components/templates/…`, `sbs_templates/…` | russian/sbs |
| `exporter/grammar_dict/grammar_dict.py` | `exporter/grammar_dict/grammar_dict_ru.py` | russian_copies |
| `exporter/kindle/epub/OEBPS/Text/titlepage.xhtml` | `exporter/kindle/ru_components/epub/OEBPS/Text/titlepage.xhtml` | russian_copies |
| `exporter/kindle/kindle_exporter.py` | `exporter/kindle/kindle_exporter_ru.py` | russian_copies |
| `exporter/tbw/tbw_exporter.py` | `exporter/tbw/tbw_exporter_ru.py` | russian_copies |
| `exporter/tpr/tpr_exporter.py` | `exporter/tpr/tpr_exporter_ru.py` | russian_copies |
| `exporter/webapp/data_classes.py` | `exporter/webapp/data_classes_ru.py` **+ self (modified_upstream, discuss:false)** | russian_copies + modified_upstream |
| `exporter/webapp/main.py` | `exporter/webapp/main_ru.py` | russian_copies |
| `exporter/webapp/preloads.py` | `exporter/webapp/preloads_ru.py` | russian_copies |
| `gui2/dpd_fields_examples.py` | `gui2/dps_example_field.py` | dps_copies |
| `scripts/build/db_rebuild_from_tsv.py` | `scripts/build/db_rebuild_from_tsv_dps.py` | dps_copies |
| `scripts/build/families_to_json.py` | `scripts/build/families_to_json_ru.py` | russian_copies |
| `tools/spelling.py` | `tools/ru_spelling.py` | russian_copies |
| `tools/utils.py` | `tools/utils_sbs.py` | sbs_copies |
| `tools/version.py` | `tools/version_ru.py` | russian_copies |

**Note on `gui2/dpd_fields_examples.py`:** the new upstream change in this range (MAX_SEARCH_RESULTS=100 + amber warning) is inherited by the `DpsExampleField` subclass via import — confirm in Stage 2c whether any shadow edit is even needed (likely a reviewed no-op, mirroring the prior-sync pattern recorded in `reviewed_shadow_noops.json`).

---

## INSPIRED — backport selectively (Stage 3, judgement)

`inspired_by_upstream`: no strict parity. Stage 2c must read each upstream diff and decide what (if anything) to backport.

| Upstream source | Inspired local target(s) |
|---|---|
| `.github/workflows/draft_release.yml` | `.github/workflows/ru_release.yml`, `.github/workflows/ru_release_test.yml` |
| `exporter/goldendict/export_dpd.py` | `export_dpd_ru.py`, `export_dpd_sbs.py` |
| `exporter/goldendict/export_epd.py` | `export_epd_sbs.py` (RU side is the strict `export_rpd.py` shadow above) |
| `exporter/goldendict/export_help.py` | `export_help_ru.py`, `export_help_sbs.py` |
| `exporter/goldendict/export_roots.py` | `export_roots_ru.py`, `export_roots_sbs.py` |
| `exporter/goldendict/export_variant_spelling.py` | `export_variant_spelling_ru.py` |
| `exporter/goldendict/main.py` | `main_ru.py`, `main_sbs.py` |
| `gui2/dpd_fields.py` | `gui2/dps_fields.py` |
| `gui2/dpd_fields_lists.py` | `gui2/dps_fields_lists.py` |
| `scripts/bash/generate_components.py` | `scripts/bash/generate_components.sh` |

---

## DISCUSS — RESOLVED in Stage 2b (user, 2026-06-12)

All three are in `modified_upstream_files`, so `execute_sync` **preserves the local version** automatically; the discuss decision was only about whether/how to merge the upstream change on top.

### `db/models.py` — RESOLVED: PORT the rename surgically (user: "all good")

Upstream change in range is ONLY a `Lookup` method rename: `variants_pack` → `variant_pack`, `variants_unpack` → `variant_unpack` (param `dict` → `data`, comment `# variants pack unpack` → `# variant pack unpack`). **Surgically apply this exact 10-line diff to the local file; preserve everything else** (all localized SBS/Russian/Tamil/Sinhala tables and `*_ru` columns are untouched by this diff). Do NOT blind-overwrite the file.

**Why forced:** synced callers adopt the new names after Commit 1 — `db/variants/add_to_db.py` + `exporter/variants/variants_exporter.py` (mirror) and `exporter/tpr/tpr_exporter.py`, `exporter/tbw/tbw_exporter.py`, `exporter/webapp/data_classes.py` (port sources, taken verbatim). Keeping old names = `AttributeError`.

**Stage 3 follow-on (record in 2c):** shadow callers `exporter/tpr/tpr_exporter_ru.py`, `exporter/tbw/tbw_exporter_ru.py`, `exporter/webapp/data_classes_ru.py` currently call `variants_unpack` — update each to `variant_unpack` during their port.

Exact local edit anchors (current local `db/models.py`):
- L305 `    # variants pack unpack` → `    # variant pack unpack`
- L306 `    def variants_pack(self, dict) -> None:` → `    def variant_pack(self, data) -> None:`
- body `if dict:` → `if data:`; `json.dumps(dict, ...)` → `json.dumps(data, ...)`
- L313 `    def variants_unpack(self) -> dict:` → `    def variant_unpack(self) -> dict:`

### `pyproject.toml` — RESOLVED: merge all upstream changes, preserve `num2words`, dedup typst (user: "all good")

Apply every upstream hunk literally; **preserve local-only `num2words>=0.5.14`** in `[project] dependencies`. Reconcile typst:
- Add upstream `typst>=0.14.9` to `[project] dependencies`.
- **Remove the now-redundant `typst>=0.13.2`** from the `tools` group (avoid duplicate dep).

Upstream hunks to apply: dev group `- pylama>=8.4.1` / `+ httpx2>=2.3.0`; tools `anki>=23.10.1` → `anki>=23.10.1,<25.3` (+ comment); tools `google-generativeai>=0.8.4` → `google-genai>=1.0.0` (needed — local code already imports `from google import genai`); pyright `exclude += "exporter/anki"`; ruff `exclude += "tools/cst_source_sutta_example.py"` + `force-exclude = true`; ruff.lint `extend-select = ["PLW1514"]` + `preview = true` + `explicit-preview-rules = true`; new `[tool.pytest.ini_options]` (`addopts = "--import-mode=importlib"`, `testpaths = ["tests"]`).

**`uv.lock`:** do NOT take upstream verbatim. After editing pyproject, Stage 3 regenerates with `uv lock` (local has `num2words`). Reclassify `uv.lock` from mirror → regenerate-in-Stage-3.

### `AGENTS.md` — RESOLVED: keep local as-is, backport NOTHING (user: "AGENTS.md stays the same as now locally")

Skip all 5 upstream prose additions (Kamma Finalize, Kamma Checkpoints, SQLAlchemy ORM Objects, pre-commit gate rewrite, Pipeline Improvement). `execute_sync` already preserves the local file; no merge action. Stage 3 = verify the local `AGENTS.md` is unchanged after the pull.

---

## DOCS — Stage 4

| Path | Target |
|---|---|
| `docs/technical/quick_start.md` | `docs_rus/technical/quick_start.md` (Stage 4 docs-parity / RU translation). |

---

## SKIP — submodule pointers & non-actions

| Path(s) | Reason |
|---|---|
| `resources/deconstructor_output`, `resources/fdg_dpd`, `resources/other-dictionaries`, `resources/tpr_downloads` | Submodule pointer changes. Per project Commit-Scope rule, never stage/commit `resources/*` pointer changes. **Stage 3:** add these four to `run_exclusions.txt` so `execute_sync` restores local pointers, OR leave unstaged and exclude from Commit 1. Report separately. |
| `exporter/kindle/tests/test_epd.py`, `tools/update_test_add.py` | Upstream deletions (acknowledged blockers) — propagate removal. |

---

## MIRROR — plain upstream, accept verbatim (no Stage 3 work)

`execute_sync`'s `git restore --source as_upstream --worktree -- .` overwrites all of these with the upstream version automatically. Stage 3 = verify only. Grouped for readability; every path below is in `changed_upstream_paths`.

**audio/**: `archive/generate_audio_11_labs.py`, `bhashini/generate_dpd.py`, `db_create.py`, `db_release_upload.py`, `error_check/delete_silent_files.py`, `error_check/trim_audio.py`

**db/** (non-shadow): `backup_tsv/dpd_headwords_part_001.tsv`, `…_002.tsv`, `…_003.tsv`, `backup_tsv/dpd_roots_part_001.tsv`, `bold_definitions/extract_bold_definitions.py`, `db_helpers.py`, `grammar/grammar_to_lookup.py`, `inflections/create_inflection_templates.py`, `inflections/generate_inflection_tables.py`, `inflections/inflections_to_headwords.py`, `inflections/transliterate_inflections.py`, `lookup/see.py`, `lookup/spelling_mistakes.py`, `lookup/transliterate_lookup_table.py`, `sanskrit/root_families_sanskrit.tsv`, `suttas/suttas_to_lookup.py`, `suttas/suttas_update.py`, `variants/add_to_db.py`, `variants/extract_variants_from_bjt.py`, `variants/extract_variants_from_cst.py`, `variants/extract_variants_from_sc.py`, `variants/extract_variants_from_sya.py`, `variants/find_examples.py`, `variants/main.py`, `variants/variants_modules.py`

**db_tests_gui/**: `add_antonyms.py`, `add_antonyms_sync.py`, `add_hyphenations.py` (not in `skip_sync_patterns`; `db_tests/` is, `db_tests_gui/` is not)

**exporter/analysis/** (D1 overwrite): `README.md`, `_base.py`, `ai_response.py`, `analysis_types.py`, `analyzer.py`, `example_bolding.py`, `prompts.py`, `ranking.py`, `rendering.py`, `retry.py`, `scoring.py`, `study_passage.py`, `translate_core.py` — plus all other already-tracked analysis files restored to upstream.

**exporter/** (other non-shadow): `goldendict/helpers.py`, `tpr/templates/tpr_headword.jinja`, `txt/export_txt.py`, `variants/variants_exporter.py`, `webapp/generate_search_index.py`, `webapp/scripts/process_logs.py`

**go_modules/**: `frequency/main.go`

**gui2/** (non-shadow plain upstream): `additions_manager.py`, `ai_search.py`, `corrections_manager.py`, `daily_log.py`, `data/pass2_exceptions.json`, `database_manager.py`, `dpd_fields_commentary.py`, `filter_presets_manager.py`, `global_tab_view.py`, `mixins.py`, `pass1_auto_controller.py`, `pass1_auto_view.py`, `pass2_auto_control.py`, `pass2_auto_view.py`, `sandhi_files_manager.py`, `utilities/find_words_with_examples.py`

**scripts/build/** (non-shadow): `api_ca_eva_iti_iva_hi.py`, `config_github_release.py`, `config_quick_profile.py`, `config_uposatha_day.py`, `cst4_xml_to_txt.py`, `dealbreakers.py`, `deconstructor_extract_archive.py`, `deconstructor_output_add_to_db.py`, `docs_add_indexes.py`, `ebt_counter.py`, `newsletter_scraper.py`, `root_has_verb_updater.py`, `sanskrit_root_families_updater.py`, `tarball_db.py`, `tarball_deconstructor_output.py`, `transliterate_bjt.py`, `zip_goldendict_mdict.py`

**scripts/** (other): `export/sanskrit_export.py`, `extractor/_output.py`, `extractor/extract_cone.py`, `extractor/extract_cpd.py`, `fix/fix_synonym_entries.py`, `fix/sanskrit_sutra_bsk.py`, `onboarding/desktop_shortcut.py`, `project_management/project_health_check.py`

**shared_data/**: `deconstructor/manual_corrections.tsv`, `user_dictionary.txt`

**tools/** (non-shadow): `ai_antigravity_cli.py`, `ai_antigravity_cli_models.py`, `ai_deepseek_manager.py`, `ai_gpt_manager.py`, `ai_manager.py`, `ai_models.json`, `all_tipitaka_words.py`, `bjt.py`, `bold_definitions_search.py`, `cache_load.py`, `compound_type_manager.tsv`, `configger.py`, `css_manager.py`, `cst_sc_text_sets.py`, `cst_source_sutta_example.py`, `docs_changelog_and_release_notes.py`, `docs_update_abbreviations.py`, `docs_update_bibliography.py`, `docs_update_thanks.py`, `lookup_sync.py`, `phonetic_changes.tsv`, `script_runner.py`, `speech_marks.json`, `tsv_read_write.py`, `uposatha_day.py`, `wordfinder_manager.py`

**root**: `.github/workflows/mobile_release.yml`, `uv.lock` (downstream of `pyproject.toml` discuss — re-resolve only if deps change in 2b)

> ⚠️ Blast-radius note for MIRROR `tools/` and `db/` files: several are shared modules imported widely. Stage 3 verification (`smoke_test_sync.py` + shadow-parity suite) must pass; if a shadow breaks because its upstream source changed contract, fix the shadow per the Iron Rule — do not patch the upstream file.

---

## Stage 2a summary counts

- **mirror**: ~110 (incl. analysis cluster overwrite, ai_antigravity pair, 7 needs-classification)
- **port** (shadow/divergent): 34 upstream sources → ~45 shadow targets
- **inspired**: 10 upstream sources → ~16 inspired targets
- **discuss**: 3 (→ 2b)
- **docs**: 1 (→ Stage 4)
- **skip**: 4 submodule pointers + 2 upstream deletions
- **manual delete**: 1 (`exporter/analysis/types.py`, local-only)

---

## HARD STOP — end of Stage 2a

Next: **Stage 2b — Discuss resolution** (ADVANCED, fresh session). Resolve `AGENTS.md`, `db/models.py`, `pyproject.toml` with the user one at a time; mark each RESOLVED here; then 2c literal-plan authoring.

Do NOT in this session: run `execute_sync.py`, copy/edit files, create `run_acknowledged_blockers.txt`, or resolve discuss items.

### Restart prompt (Stage 2b)

```text
Continue upstream sync thread: kamma/threads/20260612_upstream_sync (Stage 2b, ADVANCED/Opus).
First read:
1. kamma/threads/20260612_upstream_sync/handoff.md
2. kamma/upstream_sync/guide.md (Stage 2 + Discussion Flag Protocol)
3. kamma/threads/20260612_upstream_sync/dynamic_plan.md

Task: Stage 2b discuss resolution. Resolve the 3 discuss_paths (AGENTS.md,
db/models.py, pyproject.toml) with the user ONE AT A TIME. For each, present the
upstream diff for this range + the registry discuss_reason, get an explicit
decision, and mark it RESOLVED in dynamic_plan.md with the agreed merge strategy.
Then hard stop before Stage 2c (literal plan authoring).

Do not perform mechanical edits, file copies, or run execute_sync.py.
```
```

---
---

# Stage 2c — Literal Execution Plan (FAST-executable)

**Authoring status (batched).** This section is authored in domain batches per the
guide ("split again after each major domain if context grows, then hard stop").
Approach approved by user (2026-06-12): deterministic items get literal edits;
medium/heavy shadow ports get a self-contained **Iron-Rule recipe** (exact source
path, post-Commit-1 diff command, an explicit *port / N-A* hunk classification
derived from the SMD divergences, SMD reference, and verify commands). A pure
"zero-judgement literal anchor edit" is impractical for the 100–170 line upstream
refactors; the recipe + verify gates + Iron-Rule hard-stop are the safety mechanism.

**Batch ledger:**
- [x] Batch 0 — execute_sync pre-flight & Commit 1 mechanics (deterministic). *Authored.*
- [x] Batch 1 — deterministic reconciliation edits (models.py + variant fan-out, pyproject, uv.lock, manual delete). *Authored.*
- [x] Batch 2 — db/families port recipes ×5. *Authored.*
- [x] Batch 3 — db/ + tools/ remaining ports (epd→rpd/tpd, help_abbrev→ru, spelling→ru_spelling, utils→utils_sbs, version→ru_version, backup→backup_dps). *Authored.*
- [x] Batch 4 — exporter/goldendict: data_classes→_dps, export_epd→export_rpd, 10 templates → ru_components + sbs_templates, grammar_dict→_ru. *Authored.*
- [x] Batch 5 — exporter/kindle + tbw + tpr + webapp (main/preloads/data_classes_ru) + gui2/dpd_fields_examples + scripts/build (db_rebuild, families_to_json). *Authored.*
- [x] Batch 6 — INSPIRED backports ×10 (judgement). *Authored.* Net: extract_body ×7 files + roots N+1 fix ×2; all else SKIP/N-A.
- [ ] Batch 7 — 2d approval gate (present full plan).

---

## Stage 3 commit structure (reference)

- **Commit 1 — `#sync: upstream pull <from>..<to>, <N> files, 2026-06-12`**: the
  `execute_sync.py` automated pull (mirror overwrites + propagated deletions).
  Leaves changes unstaged; review `git diff`, then stage with `git add .`.
- **Commit 2 — reconciliation**: all manual deterministic edits + shadow/inspired
  ports (Batches 1–6). Message drafted at Stage 3 end (separate session per guide).
- **Commit 3 — `#docs:` …**: Stage 4 docs translation parity.

`resources/*` submodule pointers are NEVER staged (project Commit-Scope rule).

---

## Recipe format key (for shadow/inspired ports)

Each port recipe below has these fixed fields. FAST executes them literally:

- **SOURCE (new)**: upstream file, already at its new version in the worktree after Commit 1.
- **SHADOW**: the local file to edit.
- **DIFF CMD**: run to see the authoritative upstream change for this range.
- **PORT (apply to shadow)**: the upstream hunks that are *shared logic* and MUST appear in the shadow.
- **N-A (do NOT apply)**: upstream hunks that do not apply because the shadow diverges per SMD (with the SMD reason).
- **PRESERVE**: the shadow's local layering that must survive (from SMD "Local Changes").
- **VERIFY**: commands to confirm the port landed.

`DIFF CMD` range token (reuse verbatim):
`R=0ea5883380f56b682cf8574043afb8e66cca3260..518672a65fa3ea7c36c4c754dc5276bb41f92da7`

**Iron-Rule hard-stop:** if a PORT hunk does not map cleanly onto the shadow's
localized code, STOP and hand to ADVANCED — do not improvise.

---

## BATCH 0 — execute_sync pre-flight & Commit 1 (deterministic)

**B0.1 — Create `kamma/threads/20260612_upstream_sync/run_acknowledged_blockers.txt`** with exactly these 9 lines (one path per line, no comments needed):

```
exporter/analysis/ai_response.py
exporter/analysis/prompts.py
exporter/analysis/ranking.py
exporter/analysis/rendering.py
exporter/analysis/retry.py
exporter/analysis/scoring.py
tools/ai_antigravity_cli.py
exporter/kindle/tests/test_epd.py
tools/update_test_add.py
```

**B0.2 — `resources/*` exclusions.** Do NOT add `resources/*` to `run_exclusions.txt`
(they are submodule pointers, not synced files). After `execute_sync.py`, if `git diff`
shows any `resources/*` pointer change, leave it UNSTAGED and exclude from Commit 1.
Report separately. (Confirm with `git status --short resources/` before staging.)

**B0.3 — Run the pull (Commit 1 gate):**
```
uv run python3 kamma/upstream_sync/scripts/execute_sync.py kamma/threads/20260612_upstream_sync
```
Leaves changes unstaged. Then review and verify (B0.4) BEFORE staging.

**B0.4 — Post-pull verification (before staging Commit 1):**
1. `git status --short | rg '^.D'` — confirm `exporter/kindle/tests/test_epd.py` and
   `tools/update_test_add.py` show as deletions (propagated). 
2. `test -f exporter/analysis/analysis_types.py && echo OK` — upstream rename landed.
3. `test -f exporter/analysis/_base.py && echo OK`.
4. `test -f exporter/analysis/types.py && echo "STILL PRESENT — delete in B1.4" || echo "gone"`
   — local-only `types.py` is NOT in the upstream tree, so the restore will NOT remove it.
   It is handled in B1.4, not here.
5. `git diff --stat db/models.py pyproject.toml AGENTS.md` — these are `modified_upstream`;
   confirm they show **no changes** from the pull (local versions preserved). If any of the
   three changed, STOP → ADVANCED (preservation failed).
6. Stage with `git add .` (respects `.gitignore`); confirm `resources/*` is NOT staged
   (`git status --short resources/`). Commit 1 message:
   `#sync: upstream pull 0ea58833..518672a6, <N> files, 2026-06-12`
   (substitute `<N>` = file count from `git diff --cached --stat | tail -1`).

> Note: Commit 1 is a session boundary (guide Hard-Stop Triggers). After Commit 1,
> hard stop and restart a fresh FAST session for Batch 1 reconciliation edits.

---

## BATCH 1 — deterministic reconciliation edits (Commit 2, post-Commit-1)

These are `modified_upstream`/local files preserved by `execute_sync`; apply the
edits manually. All anchors are in files untouched by Commit 1, so they are stable.

### B1.1 — `db/models.py` surgical `Lookup` variant rename

Local anchors confirmed at lines 304–313. Apply these exact replacements (the ONLY
change; preserve all localized SBS/Russian/Tamil/Sinhala schema):

1. `    # variants pack unpack` → `    # variant pack unpack`
2. Replace the `variants_pack` method block:
```python
    def variants_pack(self, dict) -> None:
        if dict:
            self.variant = json.dumps(dict, ensure_ascii=False)
```
→
```python
    def variant_pack(self, data) -> None:
        if data:
            self.variant = json.dumps(data, ensure_ascii=False)
```
3. `    def variants_unpack(self) -> dict:` → `    def variant_unpack(self) -> dict:`

### B1.2 — variant-rename fan-out to preserved callers (ATOMIC with B1.1)

After B1.1, the OLD name `variants_unpack` survives ONLY in these preserved local
files (all upstream/mirror callers — `tpr_exporter.py`, `tbw_exporter.py`,
`webapp/data_classes.py`'s upstream twin, `variants/variants_exporter.py`,
`db/variants/add_to_db.py` — adopt the new name automatically via Commit 1 overwrite).
Edit each:

| File:line | Change |
|---|---|
| `exporter/webapp/data_classes.py:88` | `result.variants_unpack` → `result.variant_unpack` |
| `exporter/webapp/data_classes_ru.py:89` | `result.variants_unpack` → `result.variant_unpack` |
| `exporter/tpr/tpr_exporter_ru.py:167` | `i.variants_unpack[0]` → `i.variant_unpack[0]` |
| `exporter/tbw/tbw_exporter_ru.py:194` | `i.variants_unpack[0]` → `i.variant_unpack[0]` |

> `exporter/webapp/data_classes.py` is `modified_upstream` (preserved), so its 2-line
> upstream diff (the same rename) is NOT auto-applied — this row IS its full port.

**VERIFY B1.1+B1.2:** `rg -n "variants_pack|variants_unpack" -g '*.py' | rg -v dps_archive`
must return **zero** rows. Then `uv run pyright db/models.py exporter/webapp/data_classes.py exporter/webapp/data_classes_ru.py exporter/tpr/tpr_exporter_ru.py exporter/tbw/tbw_exporter_ru.py`.

### B1.3 — `pyproject.toml` merge

Apply each upstream hunk literally, but PRESERVE local-only `num2words>=0.5.14` and
DEDUP typst. Concretely:

1. `[project] dependencies` — add `"typst>=0.14.9",` after `"requests>=2.32.3",`.
   Keep the existing local `"num2words>=0.5.14",` line (do NOT remove).
2. `[dependency-groups] dev` — remove `"pylama>=8.4.1",`; add `"httpx2>=2.3.0",` (after `"pre-commit>=4.5.1",`).
3. `tools` group:
   - `"anki>=23.10.1",` → 
     ```
     # anki 25.7+ ships protobuf-6 gencode; pin until anki resolves upstream
     "anki>=23.10.1,<25.3",
     ```
   - `"google-generativeai>=0.8.4",` → `"google-genai>=1.0.0",`
   - **Remove** the now-duplicate `"typst>=0.13.2",` line from this `tools` group
     (typst now lives in `[project] dependencies` at 0.14.9).
4. `[tool.pyright]` exclude → add `, "exporter/anki"` to the list.
5. `[tool.ruff]` exclude → add `, "tools/cst_source_sutta_example.py"`; add `force-exclude = true` line after `exclude`.
6. `[tool.ruff.lint]` → after `ignore = ["E501"]` add:
   ```
   extend-select = ["PLW1514"]
   preview = true
   explicit-preview-rules = true
   ```
7. Append new section at end of file:
   ```
   [tool.pytest.ini_options]
   addopts = "--import-mode=importlib"
   testpaths = ["tests"]
   ```

> Before editing, `rg -n 'typst|num2words' pyproject.toml` to locate the exact local
> lines (local may order deps differently than the upstream diff context). If
> `num2words` or a second `typst` is not where expected, STOP → ADVANCED.

### B1.4 — regenerate `uv.lock` (do NOT take upstream verbatim)

After B1.3: `uv lock` (regenerates lock with local `num2words`). Do NOT `git restore`
or accept the upstream `uv.lock`. **VERIFY:** `uv lock --check` exits 0;
`rg -n 'num2words' uv.lock` returns ≥1 row; `rg -n 'google-genai' uv.lock` returns ≥1.

### B1.5 — manual delete local-only `exporter/analysis/types.py`

Upstream renamed `types.py` → `analysis_types.py`; the local-only `types.py`
(discarded local refactor) is not in the upstream tree, so the pull does not remove it.
```
git rm exporter/analysis/types.py
```
(If `git rm` errors "did not match", it was already removed by the pull — verify with
`test -f exporter/analysis/types.py && echo PRESENT || echo gone`; if `gone`, skip.)
**VERIFY:** `rg -n "from exporter.analysis.types|exporter\.analysis\.types\b" -g '*.py'`
returns zero rows (all importers now use `analysis_types`).

---

## BATCH 2 — db/families port recipes (×5)

All five `_ru` shadows are `russian_copies` (PORT). They share these **global RU
divergences** (per SMD db.md) that recur in every recipe's PRESERVE/N-A — stated once here:

- **PRESERVE-ALL:** RU imports (`ru_degree_of_completion`, `make_short_ru_meaning`,
  `ru_replace_abbreviations`, etc.); `joinedload(DpdHeadword.ru)` on the DB query;
  writing `html_ru`/`data_ru` (and `root_ru_meaning`/`set_ru` where applicable) columns.
- **N-A-ALL:** the upstream **`db_session.query(Table).delete()` / `add_all` / bulk
  delete-insert** pattern. Every `_ru` shadow uses **in-place update** (lookup existing
  row, assign, commit). Do NOT introduce delete-insert. The upstream
  `db_session.execute(Table.__table__.delete())` → `db_session.query(Table).delete()`
  refactor therefore has NO target in the shadow.

The **DO-PORT shared-logic** changes common to the family files (apply wherever the
shadow has the matching code): add `from sqlalchemy.orm import Session`; add return/param
**type hints** (`-> None`, `dict[str, dict]`, `list[DpdHeadword]`, `Session`, etc.);
replace `for __counter__, x in enumerate(...)` → `for x in ...`; move `family_updater`
import to a **lazy import inside the `if config_test("anki",...)` block**; `db_session.close()`
relocated to `main()` after the add step.

### B2.1 — `db/families/family_compound_ru.py` (SMD db.md → family_compound_ru)
- **SOURCE (new):** `db/families/family_compound.py`
- **DIFF CMD:** `git diff $R -- db/families/family_compound.py`
- **PORT:** global shared-logic list above **plus**: dead-comment cleanup in
  `compile_cf_html` (merge the `# data` / `# anki data` blocks under a single
  `if i.meaning_1:` with `construction = i.construction_clean`); in `update_db_cache`
  use `cf_set = set(cf_dict)` and `json.dumps(sorted(cf_set), …)` (was `list(cf_set)`).
- **N-A:** N-A-ALL (delete-insert). The `from exporter.anki.anki_updater import family_updater`
  top-level import removal → lazy import: apply ONLY if the shadow imports it at top level
  (check first).
- **PRESERVE:** PRESERVE-ALL (`html_ru`, `data_ru`, RuPaths per SMD item 2).
- **VERIFY:** `uv run ruff check db/families/family_compound_ru.py && uv run pyright db/families/family_compound_ru.py`

### B2.2 — `db/families/family_idiom_ru.py` (SMD db.md → family_idiom_ru)
- **SOURCE (new):** `db/families/family_idiom.py`
- **DIFF CMD:** `git diff $R -- db/families/family_idiom.py`
- **PORT:** global shared-logic list **plus**: in `compile`/`add` use local var
  `for idiom, data in idioms_dict.items(): if data["data"]: …` (was `idioms_dict[idiom][...]`);
  regex modernisation `re.findall("\\d", …)` → `re.search(r"\d", …)` and
  `re.findall("\\bcomp\\b", …)` → `re.search(r"\bcomp\b", …)`; string fixes
  `"idioms" not in i.pos` → `"idiom" not in i.pos` — **BUT only inside
  `sync_idiom_numbers_with_family_compound`, which the RU shadow does NOT have (SMD item 5).**
- **N-A:** N-A-ALL (delete-insert). **`sync_idiom_numbers_with_family_compound` is
  ENTIRELY ABSENT in the RU shadow (SMD item 5) — skip ALL hunks inside it** (the regex/
  string fixes above live there; they do not apply). **`update_db_cache` is ABSENT in the
  RU shadow (SMD "Watch For": no `update_db_cache()` — removed May 2026) — skip the
  `sorted(idioms_set)` cache hunk entirely. Do NOT re-add the function.**
- **PORT (net):** after the N-A carve-outs, the RU-applicable changes are: `Session`
  import + type hints + `.items()` iteration in `add_idioms_to_db` + `db_session.close()`
  placement. (Most of upstream's idiom diff is in the two absent functions.)
- **PRESERVE:** PRESERVE-ALL; in-place update; NO `update_db_cache`; NO idiom auto-sync.
- **VERIFY:** ruff + pyright on the shadow; confirm `rg -n "update_db_cache|sync_idiom_numbers" db/families/family_idiom_ru.py` still returns **zero** rows.

### B2.3 — `db/families/family_root_ru.py` (SMD db.md → family_root_ru) — heavy, mostly N-A
- **SOURCE (new):** `db/families/family_root.py`
- **DIFF CMD:** `git diff $R -- db/families/family_root.py`
- **N-A (large):** The RU shadow OMITS `update_lookup_table()`, `generate_root_info_html`,
  `generate_root_matrix`, and the Root-Matrix anki deck (SMD items 5–6). Therefore SKIP:
  - the import swaps `tools.update_test_add`/`tools.lookup_is_another_value` → `tools.lookup_sync.sync_lookup_column` (the whole `update_lookup_table` rewrite is N-A);
  - the `root_info`/`root_matrix` import path change `from root_info` → `from db.families.root_info` (N-A — shadow doesn't import them);
  - `make_anki_matrix_data` signature change + None-guard (N-A — no matrix deck).
  - N-A-ALL delete-insert.
- **PORT (net, the RU-applicable subset):** `from sqlalchemy.orm import Session` + type
  hints; lazy `family_updater` import inside the anki block; `make_anki_data(pth, rf_dict)`
  → `make_anki_data(rf_dict)` (drop the unused `pth` param) — **only if the shadow's
  `make_anki_data` takes `pth`; check**; `compile_rf_html` dead-guard removal (the
  `if i.lemma_1 in rf_dict[family]["headwords"]:` wrapper is dropped, de-indenting its body);
  removed `"meaning": i.rt.root_meaning` dict entry; **but the RU shadow has a custom
  `make_root_header_ru()` (SMD item 4)** — the upstream `make_root_header` change
  `rf_dict[rf]['meaning']` → `rf_dict[rf]['root_meaning']` applies to the RU custom header
  ONLY if it reads that dict key; inspect `make_root_header_ru` and align the key name to
  whatever the shadow's dict now stores.
- **PRESERVE:** PRESERVE-ALL; `root_ru_meaning`/`html_ru`/`data_ru`; `make_root_header_ru`;
  single anki deck; NO lookup-table sync.
- **Iron-Rule note:** this is the highest-divergence family file — if the `compile_rf_html`
  de-indent or the header dict-key change does not map cleanly, STOP → ADVANCED.
- **VERIFY:** ruff + pyright; `rg -n "sync_lookup_column|update_lookup_table|root_matrix|make_anki_matrix_data" db/families/family_root_ru.py` must return **zero**.

### B2.4 — `db/families/family_set_ru.py` (SMD db.md → family_set_ru)
- **SOURCE (new):** `db/families/family_set.py`
- **DIFF CMD:** `git diff $R -- db/families/family_set.py`
- **PORT:** global shared-logic list **plus**: `errors_list += [sf]` → `errors_list.append(sf)`;
  `if errors_list != []:` → `if errors_list:`; `db_session.close()` moved from
  `add_sf_to_db` to `main`. (Note upstream added `db_session.close()` in `main` and removed
  it from `add_sf_to_db`; the RU shadow uses in-place update so mirror the close placement
  to its `main`.)
- **N-A:** N-A-ALL (the `db_session.execute(FamilySet.__table__.delete())` → `query().delete()`
  hunk — shadow uses in-place update + `populate_set_ru_and_check_errors`).
- **PRESERVE:** PRESERVE-ALL; `set_ru`/`html_ru`/`data_ru`; `populate_set_ru_and_check_errors()` call.
- **VERIFY:** ruff + pyright on the shadow.

### B2.5 — `db/families/family_word_ru.py` (SMD db.md → family_word_ru)
- **SOURCE (new):** `db/families/family_word.py`
- **DIFF CMD:** `git diff $R -- db/families/family_word.py`
- **PORT:** global shared-logic list **plus** two real logic changes:
  1. `make_word_fam_dict` no longer creates an `"anki": []` dict key; `compile_wf_html`
     no longer accumulates `wf_dict[wf]["anki"]` and drops the
     `if i.lemma_1 in wf_dict[wf]["headwords"]:` guard (de-indent body).
  2. `make_anki_data` now reads the **`data`** rows (unpacked as
     `headword, pos, meaning, degree`) instead of a separate `anki` list, and renders
     `degree` in the last cell (was `construction`).
  Apply both to the shadow, preserving the RU anki tuple fields (SMD item 4 — "Anki data
  tuple includes Russian data fields"): if the shadow's anki tuple carries extra RU fields,
  keep them while switching the source to the `data` rows + `degree`.
- **N-A:** N-A-ALL (delete-insert → shadow in-place).
- **PRESERVE:** PRESERVE-ALL; `html_ru`/`data_ru`; RU anki tuple fields.
- **Iron-Rule note:** the anki-data restructure (item 2) interacts with the RU anki tuple —
  if the field count/order does not map cleanly, STOP → ADVANCED.
- **VERIFY:** ruff + pyright on the shadow.

---

## BATCH 3 — db/ + tools/ remaining ports (Commit 2, post-Commit-1)

All seven shadows below were read against their NEW upstream sources (diffs gathered
at range `R`) during authoring. Two upstream changes in this batch (`spelling.py`,
`utils.py`) are structural-only with **no SBS/RU divergence**, so they resolve to a
no-op / whitelist; the other five are real ports. Each recipe is FAST-executable.

> **`sync_lookup_column` adoption (B3.1/B3.2/B3.3):** upstream replaced the
> `update_test_add` + `is_another_value` + manual `add_all`/`delete` loops with a
> single `sync_lookup_column(db_session, "<col>", data)` call (new module
> `tools/lookup_sync.py`, arrives as plain-upstream mirror in Commit 1). Verified safe
> for the shadow columns: `tools/lookup_is_another_value.is_another_value` iterates
> `Lookup.__table__.columns` dynamically (handles `rpd`/`tpd`/`help`/`abbrev`/
> `abbrev_other` with no per-column wiring), and `sync_lookup_column`'s
> `pack_attr` defaults to `f"{column}_pack"` → `rpd_pack`/`tpd_pack`/`help_pack`/
> `abbrev_pack`/`abbrev_other_pack`, all of which already exist on `Lookup` (the
> shadows currently call them). `clear_stale=True` (default) reproduces the old
> "delete stale rows first" behavior. So the shadows ADOPT `sync_lookup_column`.

### B3.1 — `db/rpd/rpd_to_lookup.py` (russian_copies; SMD db.md → rpd_to_lookup)
- **SOURCE (new):** `db/epd/epd_to_lookup.py`
- **SHADOW:** `db/rpd/rpd_to_lookup.py`
- **DIFF CMD:** `git diff $R -- db/epd/epd_to_lookup.py`
- **PORT (adopt upstream structure — open the new upstream source and mirror it function-by-function):**
  1. **Imports:** DROP `from tools.lookup_is_another_value import is_another_value`,
     `from tools.update_test_add import update_test_add`, and `Lookup` from the
     `db.models` import (no longer referenced). ADD `from dataclasses import dataclass, field`
     and `from tools.lookup_sync import sync_lookup_column`. KEEP `import re`,
     `joinedload`, `Session`, `DpdHeadword`, `DpdRoot`, `config_read`, `pali_sort_key`,
     `ProjectPaths`, `pr`, and the RU import `ru_replace_abbreviations`.
  2. **Module constant:** add `POS_EXCLUDE = frozenset({"abbrev", "cs", "letter", "root", "suffix", "ve"})`.
  3. **`GlobalVars` → `@dataclass`** with fields ONLY:
     `db_session: Session`, `dpd_db: list[DpdHeadword]`, `roots_db: list[DpdRoot]`,
     `rpd_data_dict: dict[str, list[tuple[str, str, str]]] = field(default_factory=dict)`.
     Remove ALL module-level side effects from the class body **and** delete the top-of-file
     `if config_read(...) == "no": ... raise SystemExit(0)` block (moves into `main()`).
  4. **`main()`** (mirror upstream): `pr.tic()`; `pr.green_title("generating rpd data for lookup table")`;
     `if config_read("generate", "rpd", "yes") == "no": pr.green_title("disabled in config.ini"); pr.toc(); return`;
     build `pth`, `db_session`, then
     `dpd_db = sorted(db_session.query(DpdHeadword).options(joinedload(DpdHeadword.ru)).all(), key=lambda x: pali_sort_key(x.lemma_1))`,
     `roots_db = db_session.query(DpdRoot).all()`,
     `g = GlobalVars(db_session=db_session, dpd_db=dpd_db, roots_db=roots_db)`;
     then `compile_headwords_data(g)`, `compile_roots_data(g)`, `add_to_lookup_table(g)`, `pr.toc()`.
  5. **`compile_headwords_data(g) -> None`:** use `POS_EXCLUDE`; HOIST `meaning_plus_case`,
     `ru_pos`, `rpd_data` out of the meanings loop (they don't depend on `meaning`); body:
     `for meaning in make_clean_meaning_list(i): if meaning: g.rpd_data_dict.setdefault(meaning, []).append(rpd_data)`;
     `pr.counter(counter, len(g.dpd_db), i.lemma_1)`.
  6. **`compile_roots_data(g) -> None`:** HOIST `rpd_data = (i.root, "корень", i.root_ru_meaning)`
     out of the inner loop; `g.rpd_data_dict.setdefault(root_meaning, []).append(rpd_data)`.
  7. **`make_clean_meaning_list`:** delete the `# remove ?` + `ru_meanings_clean = re.sub(r"\\?", "", ...)`
     lines (mirror upstream removal of the buggy regex). KEEP every other RU regex.
  8. **`make_meaning_plus_case(i: DpdHeadword) -> str`** (type hint only).
  9. **`add_to_lookup_table(g) -> None`:** replace the entire update/test/add/commit body with:
     ```
     pr.green_title("saving to Lookup table")
     pr.white_tmr("syncing rpd column")
     result = sync_lookup_column(g.db_session, "rpd", g.rpd_data_dict)
     pr.yes(result.updated + result.inserted)
     ```
- **N-A:** none beyond locale — the whole `update_test_add`/`is_another_value`/`add_all`/`delete`
  block is REPLACED, not preserved.
- **PRESERVE (RU layering, Iron Rule re-apply):** `joinedload(DpdHeadword.ru)`;
  `if i.ru and i.ru.ru_meaning and i.pos not in POS_EXCLUDE:`; `ru_pos = ru_replace_abbreviations(i.pos, "gram")`
  and `rpd_data = (i.lemma_clean, ru_pos, meaning_plus_case)`; all RU regexes + `.casefold()` in
  `make_clean_meaning_list` (except the deleted `\\?` line); RU `make_meaning_plus_case` body
  (`ru_replace_abbreviations(i.plus_case, "gram")`, `i.ru.ru_meaning`); roots
  `i.root_ru_meaning.split(", ")` + `"корень"` + `i.root_ru_meaning`; column `"rpd"`; config key `"rpd"`.
- **Iron-Rule note:** the `GlobalVars`→dataclass + `main()` loader restructure is large. If the RU
  `joinedload`/guard does not map cleanly onto the new `main()` loader, STOP → ADVANCED.
- **VERIFY:** `uv run ruff check db/rpd/rpd_to_lookup.py && uv run pyright db/rpd/rpd_to_lookup.py`;
  `rg -n "update_test_add|is_another_value|add_all" db/rpd/rpd_to_lookup.py` → **zero**;
  `rg -n "sync_lookup_column" db/rpd/rpd_to_lookup.py` → **1**.

### B3.2 — `db/tpd/tpd_to_lookup.py` (tamil_copies; SMD db.md → tpd_to_lookup)
- **SOURCE (new):** `db/epd/epd_to_lookup.py`
- **SHADOW:** `db/tpd/tpd_to_lookup.py`
- **DIFF CMD:** `git diff $R -- db/epd/epd_to_lookup.py`
- **PORT (same structural mirror as B3.1, Tamil variant — headwords only, NO roots):**
  1. **Imports:** DROP `is_another_value`, `update_test_add`, and `Lookup` from `db.models`
     (TPD imports `DpdHeadword` only — no `DpdRoot`). ADD `from dataclasses import dataclass, field`,
     `from tools.lookup_sync import sync_lookup_column`. KEEP `joinedload`, `Session`,
     `DpdHeadword`, `config_read`, `pali_sort_key`, `ProjectPaths`, `pr`.
  2. `POS_EXCLUDE = frozenset({"abbrev", "cs", "letter", "root", "suffix", "ve"})`.
  3. **`GlobalVars` → `@dataclass`** fields ONLY: `db_session: Session`,
     `dpd_db: list[DpdHeadword]`,
     `tpd_data_dict: dict[str, list[tuple[str, str, str]]] = field(default_factory=dict)`.
     Remove module-level side effects + the top-of-file config-check block.
  4. **`main()`:** `pr.tic()`; `pr.green_title("generating tpd data for lookup table")`;
     `if config_read("generate", "tpd", "yes") == "no": pr.green_title("disabled in config.ini"); pr.toc(); return`;
     `dpd_db = sorted(db_session.query(DpdHeadword).options(joinedload(DpdHeadword.ta)).all(), key=lambda x: pali_sort_key(x.lemma_1))`;
     `g = GlobalVars(db_session=db_session, dpd_db=dpd_db)`; then `compile_headwords_data(g)`,
     `add_to_lookup_table(g)`, `pr.toc()`. (NO roots load, NO `compile_roots_data`.)
  5. **`compile_headwords_data(g) -> None`:** use `POS_EXCLUDE`; HOIST
     `tpd_data = (i.lemma_clean, i.pos, i.ta.ta_meaning)` out of the meanings loop;
     `for meaning in meanings_list: if meaning: g.tpd_data_dict.setdefault(meaning, []).append(tpd_data)`;
     `pr.counter(counter, len(g.dpd_db), i.lemma_1)`.
  6. **`add_to_lookup_table(g) -> None`:** replace body with:
     ```
     pr.green_title("saving to Lookup table")
     pr.white_tmr("syncing tpd column")
     result = sync_lookup_column(g.db_session, "tpd", g.tpd_data_dict)
     pr.yes(result.updated + result.inserted)
     ```
- **N-A:** roots processing (Tamil has no roots — SMD item 3); POS abbreviation replacement
  (no Tamil abbrev map — SMD item 4 → keep `i.pos`, do NOT add `ru_replace_abbreviations`).
- **PRESERVE (Tamil layering):** `joinedload(DpdHeadword.ta)`;
  `if i.ta and i.ta.ta_meaning and i.pos not in POS_EXCLUDE:`;
  `ta_meanings_clean = i.ta.ta_meaning.casefold()` + `meanings_list = [m.strip() for m in ta_meanings_clean.split(";")]`;
  `tpd_data = (i.lemma_clean, i.pos, i.ta.ta_meaning)`; column `"tpd"`; config key `"tpd"`.
- **VERIFY:** `uv run ruff check db/tpd/tpd_to_lookup.py && uv run pyright db/tpd/tpd_to_lookup.py`;
  `rg -n "update_test_add|is_another_value|DpdRoot|add_all" db/tpd/tpd_to_lookup.py` → **zero**;
  `rg -n "sync_lookup_column" db/tpd/tpd_to_lookup.py` → **1**.

### B3.3 — `db/lookup/help_abbrev_add_to_lookup_ru.py` (russian_copies; SMD db.md)
- **SOURCE (new):** `db/lookup/help_abbrev_add_to_lookup.py`
- **SHADOW:** `db/lookup/help_abbrev_add_to_lookup_ru.py`
- **DIFF CMD:** `git diff $R -- db/lookup/help_abbrev_add_to_lookup.py`
- **PORT (adopt upstream structure):**
  1. **Imports:** DROP `from rich import print`, `create_engine` (keep `inspect as sa_inspect, text`),
     `from db.models import Lookup`, `from tools.lookup_is_another_value import is_another_value`.
     ADD `from dataclasses import dataclass`, `from sqlalchemy.orm import Session`,
     `from tools.lookup_sync import sync_lookup_column`. KEEP `ProjectPaths`, `RuPaths`, `pr`,
     `read_tsv_as_dict_with_different_key, read_tsv_dict`.
  2. **`GlobalVars` → `@dataclass`:** `pth: ProjectPaths`, `rupth: RuPaths`, `db_session: Session`.
  3. **`ensure_abbrev_other_column(g) -> None`:** replace the `create_engine(...)` + `with engine.connect()`
     block with `insp = sa_inspect(g.db_session.get_bind())`, and inside the `if`:
     `g.db_session.execute(text("ALTER TABLE lookup ADD COLUMN abbrev_other TEXT DEFAULT ''"))`,
     `g.db_session.commit()`, `pr.green("added abbrev_other column to lookup")`.
  4. **`add_help_ru(g) -> None`:** `pr.green("adding help (ru)")`; KEEP
     `ru_help_data = read_tsv_as_dict_with_different_key(g.rupth.help_tsv_path, 2)`; replace the
     stale-delete loop + per-key upsert + commit with:
     ```
     data = {key: v["ru_meaning"] for key, v in ru_help_data.items()}
     sync_lookup_column(g.db_session, "help", data)
     ```
  5. **`add_abbreviations_ru(g) -> None`:** `pr.green("adding abbreviations (ru)")`; KEEP
     `ru_abbrevs = read_tsv_as_dict_with_different_key(g.rupth.abbreviations_tsv_path, 5)`; replace
     the stale-delete + upsert + commit with `sync_lookup_column(g.db_session, "abbrev", ru_abbrevs)`.
  6. **`add_abbreviations_other_ru(g) -> None`:** `print("[green]...")` → `pr.green("adding abbreviations other")`;
     DELETE the stale-delete loop (`Lookup.abbrev_other != ""` query + for-loop); KEEP the
     `read_tsv_dict` + `.sort` + `grouped` build verbatim; replace the per-key upsert loop + commit with
     `sync_lookup_column(g.db_session, "abbrev_other", grouped)`.
  7. **`main() -> None`:** `print("[bright_yellow]...")` → `pr.yellow_title("adding help and abbreviations to lookup (ru)")`;
     `pth = ProjectPaths()`; `g = GlobalVars(pth=pth, rupth=RuPaths(), db_session=get_db_session(pth.dpd_db_path))`.
- **N-A:** none beyond locale — all three stale-delete/upsert blocks are REPLACED by `sync_lookup_column`.
- **PRESERVE (RU layering):** `rupth`/`RuPaths`; `read_tsv_as_dict_with_different_key(..., 2)` (help col 2)
  and `(..., 5)` (abbrev col 5); `v["ru_meaning"]` for help; `_ru` function names + the `(ru)` log strings;
  `add_abbreviations_other_ru` reads `g.pth.abbreviations_other_tsv_path` (upstream path — unchanged).
- **VERIFY:** `uv run ruff check db/lookup/help_abbrev_add_to_lookup_ru.py && uv run pyright db/lookup/help_abbrev_add_to_lookup_ru.py`;
  `rg -n "is_another_value|create_engine|from rich import print" db/lookup/help_abbrev_add_to_lookup_ru.py` → **zero**;
  `rg -c "sync_lookup_column" db/lookup/help_abbrev_add_to_lookup_ru.py` → **3**.

### B3.4 — `tools/version_ru.py` (russian_copies; SMD tools.md → version_ru)
- **SOURCE (new):** `tools/version.py`
- **SHADOW:** `tools/version_ru.py`
- **DIFF CMD:** `git diff $R -- tools/version.py`
- **PORT (structural cleanup — mirror upstream):**
  1. DELETE header lines `# -*- coding: utf-8 -*-`, `import tomlkit`, `from rich import print`.
  2. DELETE the local `def printer(key, value):` function.
  3. Replace EVERY `printer(...)` call with `pr.summary(...)` (precondition: `pr.summary` exists in
     `tools/printer.py` — upstream `tools/version.py`, mirrored in Commit 1, calls it; confirm before edit).
  4. DELETE the `def update_project_version(...)` function entirely (unused; mirrors upstream removal).
  5. Type hints: `make_version() -> tuple[str, str, str]` (3-tuple — RU divergence, NOT upstream's 2-tuple),
     `update_db_version(pth: ProjectPaths, version: str) -> None`, `main() -> None`.
  6. In `main()`, DELETE the commented `# update_project_version(pth, version_light)` line (mirror upstream).
- **N-A:** upstream's 2-tuple `make_version` return — RU keeps the 3-tuple (extra `version_ru`).
- **PRESERVE (RU layering):** `version_ru = f"ru_v{major}.{minor}.{patch}"` + the 3-tuple return +
  `pr.summary("version ru", version_ru)`; `update_db_version` uses `dpd_sbs_release_version` key and ALL
  RU metadata rows (author Bodhirasa, `devamitta@sasanarakkha.org`, `https://ru.dpdict.net`,
  `https://devamitta.github.io/dpd.rus/`, sasanarakkha github + releases, license, `___`);
  `config_update("version", "version", version_ru, silent=True)`; the existing commented
  `# update_db_version(pth, version)` line is pre-existing RU-local dead code — LEAVE it (out of scope).
- **VERIFY:** `uv run ruff check tools/version_ru.py && uv run pyright tools/version_ru.py`;
  `rg -n "tomlkit|from rich import print|def printer\(" tools/version_ru.py` → **zero**;
  `rg -c "pr.summary" tools/version_ru.py` → **≥4**; `rg -n "dpd_sbs_release_version|version_ru" tools/version_ru.py` → **≥2**.

### B3.5 — `tools/ru_spelling.py` (russian_copies; SMD tools.md → ru_spelling) — CONFIRMED NO-OP
- **SOURCE (new):** `tools/spelling.py`
- **SHADOW:** `tools/ru_spelling.py`
- **DIFF CMD:** `git diff $R -- tools/spelling.py`
- **Upstream change:** add `encoding="utf-8"` to the read (`open(self.user_dict, "r", ...)`) and append
  (`open(self.user_dict, "a", ...)`) calls — that is the ENTIRE diff.
- **PORT:** **NONE.** The shadow already has `encoding="utf-8"` on all three `open()` calls
  (read line ~35, create line ~41, append line ~75). The upstream change is already present.
- **PRESERVE:** file unchanged.
- **Out of scope (do NOT touch):** the shadow uses legacy `Dict`/`List` typing imports; this is NOT
  in the upstream diff for this range — leave it unless the user explicitly requests modernization.
- **VERIFY:** `rg -n 'open\(' tools/ru_spelling.py` → every line shows `encoding="utf-8"` (no edit needed).

### B3.6 — `tools/utils_sbs.py` (sbs_copies; SMD tools.md → utils_sbs) — WHITELIST-ONLY
- **SOURCE (new):** `tools/utils.py`
- **SHADOW:** `tools/utils_sbs.py`
- **DIFF CMD:** `git diff $R -- tools/utils.py`
- **Upstream change:** adds a single new generic function `extract_body(html: str) -> str` to
  `tools/utils.py` (entire diff).
- **DECISION (ADVANCED):** `extract_body` is GENERIC — no SBS divergence. ALL upstream callers import it
  from `tools.utils` (verified at target SHA: `export_dpd.py`, `export_epd.py`, `export_help.py`,
  `export_roots.py`, `export_variant_spelling.py`). `utils_sbs.py` is a PARTIAL shadow that already
  *whitelists* the other generic utils funcs (`list_into_batches`, `squash_whitespaces`) rather than
  duplicating them. Therefore DO **NOT** add `extract_body` to `utils_sbs.py`.
- **PORT (to `utils_sbs.py`):** NONE.
- **REQUIRED parity-infra edit** (`tests/test_shadow_parity.py` is fork-local infra; survives Commit 1):
  at the `WHITELIST` entry (currently line ~329) change
  ```
  "tools/utils_sbs.py": {"functions": ["list_into_batches", "squash_whitespaces"]},
  ```
  →
  ```
  "tools/utils_sbs.py": {"functions": ["list_into_batches", "squash_whitespaces", "extract_body"]},
  ```
  Without this, `test_shadow_copy_parity` reports `extract_body` as a missing function (it computes
  `upstream.functions - shadow.functions - whitelist`).
- **PRESERVE:** `utils_sbs.py` untouched (`paragraphs_are_similar_sbs`, `RenderedSizes` + `sbs_example`,
  `default_rendered_sizes`, `sum_rendered_sizes`).
- **CROSS-BATCH FLAG (Batch 4/5):** the localized goldendict exporters that split header/body —
  `export_dpd_ru`, `export_dpd_sbs`, `export_epd_sbs`, `export_help_ru`, `export_help_sbs`,
  `export_roots_ru`, `export_roots_sbs`, `export_rpd`, `export_variant_spelling_ru` — must add
  `extract_body` to their `from tools.utils import (...)` line and use it wherever the upstream
  counterpart now calls `extract_body(html)`. This is handled in Batches 4/5 from those files' own
  diffs; noted here only because the function originates in this batch's source.
- **VERIFY:** `uv run pytest tests/test_shadow_parity.py -k utils_sbs -v` passes (runs post-Commit-1,
  when the new `tools/utils.py` with `extract_body` is present).

### B3.7 — `scripts/backup/backup_dps.py` (dps_copies; SMD scripts.md → backup_dps)
- **SOURCE (new):** `db/backup_tsv/backup_dpd_headwords_and_roots.py`
- **SHADOW:** `scripts/backup/backup_dps.py`
- **DIFF CMD:** `git diff $R -- db/backup_tsv/backup_dpd_headwords_and_roots.py`
- **Upstream change:** add `encoding="utf-8"` to the two TSV-write `open(..., "w", newline="")` calls.
- **PORT:** add `, encoding="utf-8"` to ALL FOUR TSV-write `open()` calls in the shadow (the DPS backup
  writes Cyrillic/Tamil/SBS data, so the encoding fix is materially important here):
  - `open(russian_path, "w", newline="")` → `open(russian_path, "w", newline="", encoding="utf-8")`
  - `open(sbs_path, "w", newline="")` → `…, encoding="utf-8")`
  - `open(tamil_path, "w", newline="")` → `…, encoding="utf-8")`
  - `open(ru_root_path, "w", newline="")` → `…, encoding="utf-8")`
- **N-A:** upstream `split_tsv_file()` chunking is NOT in this range's diff and is intentionally absent
  per SMD item 5 — do not add it.
- **PRESERVE:** the 4 backup functions (`backup_ru`/`backup_sbs`/`backup_ta`/`backup_roots_ru`),
  empty-table abort guards, single-file TSV writes, `git_commit_dps`.
- **VERIFY:** `uv run ruff check scripts/backup/backup_dps.py`;
  `rg -n 'open\(.*"w", newline=""\)' scripts/backup/backup_dps.py` → **zero** (no unencoded writes left);
  `rg -c 'encoding="utf-8"' scripts/backup/backup_dps.py` → **4**.

---

## Stage 2c — HARD STOP (end of Batch 3)

Batches 0–3 authored. Remaining: Batch 4 (goldendict data_classes→_dps, export_epd→export_rpd,
10 templates → ru_components + sbs_templates, grammar_dict→_ru), Batch 5
(kindle/tbw/tpr/webapp/gui2/scripts), Batch 6 (inspired ×10), then Batch 7 (2d approval).
See handoff.md for the restart prompt.

**Carry-forward into Batch 4/5 (from B3.6):** `extract_body` now lives in `tools/utils.py`. Each
localized goldendict exporter that the upstream counterpart updated to call `extract_body(html)` must
import it `from tools.utils` and apply the same call — confirm per-file from each shadow's own diff.

Do NOT in this session: run `execute_sync.py`, copy/edit source files, or begin Batch 4.

---

## BATCH 4 — exporter/goldendict ports (Commit 2, post-Commit-1)

This batch covers the goldendict domain: the heavy `data_classes_dps.py` triple-locale
shadow, `export_rpd.py`, the 10 upstream template changes → shadow templates in
`ru_components/templates/` and `sbs_templates/`, and `grammar_dict_ru.py`.

> **`extract_body` adoption (carry-forward from B3.6):** upstream added
> `extract_body(html: str) -> str` to `tools/utils.py`. The upstream `export_epd.py`
> now calls `extract_body(html_rendered)` instead of `html_rendered.find("<body>")`.
> The shadow `export_rpd.py` must adopt this. Additionally, the **`<body>` comment**
> in 9 templates (see B4.3) documents this contract for future maintainers.

> **`_NewlineView` refactor (B4.1):** upstream replaced the mutating
> `_convert_newlines()` static method with a read-only `_NewlineView` proxy class
> (uses `__getattr__` delegation). The DPS shadow has THREE `_convert_newlines*`
> methods (base, `_ru`, `_sbs`). See recipe B4.1 for the decision on each.

### B4.1 — `exporter/goldendict/data_classes_dps.py` (dps_copies; SMD exporter.md → data_classes_dps)

- **SOURCE (new):** `exporter/goldendict/data_classes.py`
- **SHADOW:** `exporter/goldendict/data_classes_dps.py`
- **DIFF CMD:** `git diff $R -- exporter/goldendict/data_classes.py`

**Summary of upstream changes (all classes):**
1. New `from jinja2 import Environment` import; `from typing import Set` removed.
2. New module-level helpers: `_render_header(jinja_env, template_name, style, context)`,
   `_render_plain_header(jinja_env, style)`.
3. New `_NewlineView` class — replaces the mutating `_convert_newlines` static method in
   `HeadwordData`. `HeadwordData.__init__` now calls `self.i = _NewlineView(i)`.
4. `RootsData.__init__`: `self.r = r` (no longer calls `_convert_newlines`); `self.date = year_month_day_dash()`.
5. `_convert_newlines` static methods DELETED from `HeadwordData` and `RootsData`.
6. `_generate_header` in `HeadwordData`, `RootsData` → delegate to `_render_header(...)`.
7. All `_generate_header` in `EpdData`, `VariantData`, `SeeData`, `SpellingData`,
   `AbbreviationsData`, `AbbrevOtherData`, `HelpData` → delegate to `_render_plain_header(...)`.
8. Type hints everywhere: `jinja_env` → `jinja_env: Environment`, `Set[str]` → `set[str]`,
   `__init__(...) -> None:`, all methods get `-> None` / `-> str`.
9. `EpdData._generate_html_string` → generator expression inside `"<br>".join(...)`.

**PORT (apply to shadow — shared logic):**
1. **Imports:** ADD `from jinja2 import Environment`. REMOVE `from typing import Set`.
   Keep ALL locale imports (Russian, SBS, Tamil, DPSPaths, RuPaths, etc.).
2. **Module-level helpers:** ADD `_render_header(...)` and `_render_plain_header(...)` (copy
   verbatim from upstream). These are generic — no locale divergence.
3. **`_NewlineView` class:** ADD the class verbatim from upstream. Used by `HeadwordData`
   for the base (English) newline conversion.
4. **`HeadwordData.__init__`:** change `self.i = self._convert_newlines(i)` →
   `self.i = _NewlineView(i)`. DELETE the `_convert_newlines` static method (the base
   one that handles the 9 English attrs). Type-hint the constructor: `jinja_env: Environment`,
   `cf_set: set[str]`, `idioms_set: set[str]`, `) -> None:`.
5. **`HeadwordData._generate_header`:** replace body with
   `return _render_header(self.jinja_env, "dpd_header.jinja", "dpd", {"d": self})`.
6. **`RootsData.__init__`:** `self.r = r` (no `_convert_newlines`); `self.date = year_month_day_dash()`.
   Type-hint: `jinja_env: Environment`, `) -> None:`. DELETE the `_convert_newlines`
   static method from `RootsData`.
7. **`RootsData._generate_header`:** replace body with
   `return _render_header(self.jinja_env, "root_header.jinja", "root", {"d": self})`.
8. **`EpdData`:** type-hint `__init__(self, ..., jinja_env: Environment) -> None:`.
   `_generate_html_string` → `return "<br>".join(f"..." for ... in self.epd_entries)`.
   `_generate_header` → `return _render_plain_header(self.jinja_env, "primary")`.
9. **`RpdData`, `TpdData`:** inherit from `EpdData` — no change needed (the parent's
   updated methods propagate). Optionally add `-> None:` to `__init__` if missing.
10. **`VariantData`, `SeeData`, `SpellingData`:** type-hint `jinja_env: Environment`,
    `-> None:` on `__init__`. `_generate_header` → `return _render_plain_header(self.jinja_env, "primary")`.
11. **`AbbreviationsData`, `AbbrevOtherData`, `HelpData`:** type-hint `jinja_env: Environment`,
    `-> None:` on `__init__`. `_generate_header` → `return _render_plain_header(self.jinja_env, "secondary")`.

**N-A (do NOT apply):**
- upstream deletion of `_convert_newlines` from `RootsData` removes the newline handling for
  `panini_root`, `panini_sanskrit`, `panini_english`. The DPS shadow's `RootsData._convert_newlines`
  does the same thing as upstream's deleted version — but check whether the upstream `RootsData`
  now relies on some other mechanism (it doesn't — upstream just drops it). **Mirror upstream:
  delete `_convert_newlines` from `RootsData` too, set `self.r = r`.** (This is actually PORT, not N-A.)

**PRESERVE (DPS layering, Iron Rule):**
- `_convert_newlines_ru(obj)` static method — KEEP. This handles `ru_notes` newline replacement
  (`"\n, "` → `"<br>"`). Upstream has no RU equivalent. The call
  `self.ru = self._convert_newlines_ru(ru) if ru else None` stays.
- `_convert_newlines_sbs(obj)` static method — KEEP. This handles ~10 SBS string fields.
  The call `self.sbs = self._convert_newlines_sbs(sbs) if sbs else None` stays.
- ALL Russian fields in `HeadwordData.__init__` (`ru_pos`, `ru_plus_case`, `ru_meaning`,
  `ru_summary`, `ru_complete`, `ru_grammar`, `ru_base`, `ru_phonetic`,
  `ru_inflections_html`, `ru_is_ai_translation`).
- ALL SBS fields (`sbs_meaning`, `sbs_notes`, `sbs_index`, `sbs_class`, etc.).
- ALL Tamil fields (`self.ta`, `show_ta_data`).
- ALL extra constructor params (`ru`, `sbs`, `ta`, `show_grammar`, `show_sbs_data`,
  `show_ru_data`, `show_ta_data`).
- `RootsData`: `self.ru_root_info`, `self.ru_root_matrix` Russian field assignments.
- ALL locale imports (`Russian`, `SBS`, `Tamil`, `DPSPaths`, `RuPaths`,
  `ru_replace_abbreviations`, `make_ru_meaning_html`, `ru_make_grammar_line`,
  `degree_of_completion_ru`, `summarize_construction`).

**Iron-Rule note:** this is the highest-complexity shadow (348 lines, 3 locales). The
`_NewlineView` refactor affects only the base English attrs; the RU/SBS `_convert_newlines_*`
methods are orthogonal and PRESERVED. If the `_render_header` helper does not map cleanly
onto the DPS header template names (`dpd_header.jinja` in `ru_components/templates/` or
`sbs_templates/`), STOP → ADVANCED. (The DPS shadow uses the SAME template name
`dpd_header.jinja` — just from a different Jinja env — so `_render_header` works as-is.)

**VERIFY:**
- `uv run ruff check exporter/goldendict/data_classes_dps.py && uv run pyright exporter/goldendict/data_classes_dps.py`
- `rg -n "_convert_newlines\b" exporter/goldendict/data_classes_dps.py` → returns ONLY
  `_convert_newlines_ru` and `_convert_newlines_sbs` (base `_convert_newlines` gone).
- `rg -n "_NewlineView\|_render_header\|_render_plain_header" exporter/goldendict/data_classes_dps.py` → ≥3 rows.
- `rg -n "from typing import Set" exporter/goldendict/data_classes_dps.py` → **zero**.

---

### B4.2 — `exporter/goldendict/export_rpd.py` (russian_copies; SMD exporter.md → export_rpd)

- **SOURCE (new):** `exporter/goldendict/export_epd.py`
- **SHADOW:** `exporter/goldendict/export_rpd.py`
- **DIFF CMD:** `git diff $R -- exporter/goldendict/export_epd.py`

**Summary of upstream changes:**
1. REMOVE `from typing import List, Tuple`.
2. ADD `extract_body` to the `from tools.utils import (...)` line.
3. Type hints: `Tuple[List[DictEntry], RenderedSizes]` → `tuple[list[DictEntry], RenderedSizes]`;
   `List[DictEntry]` → `list[DictEntry]`.
4. Body split: `body_start = html_rendered.find("<body>"); body = html_rendered[body_start:]`
   → `body = extract_body(html_rendered)`.

**PORT (apply to shadow):**
1. **Imports:** REMOVE `from typing import List, Tuple`. ADD `extract_body` to the
   `from tools.utils import (...)` line → becomes:
   `from tools.utils import RenderedSizes, default_rendered_sizes, extract_body, squash_whitespaces`.
2. **Type hints:** `Tuple[List[DictEntry], RenderedSizes]` → `tuple[list[DictEntry], RenderedSizes]`
   (return type of `generate_epd_html`). `List[DictEntry]` → `list[DictEntry]` (L33).
3. **Body split (lines 43–44):** replace
   ```python
       body_start = html_rendered.find("<body>")
       body = html_rendered[body_start:]
   ```
   with
   ```python
       body = extract_body(html_rendered)
   ```

**N-A:** none — all upstream changes apply 1:1.

**PRESERVE (RU layering):**
- `rupth: RuPaths` parameter in `generate_epd_html` signature.
- `from tools.paths_ru import RuPaths`.
- `from exporter.goldendict.data_classes_dps import RpdData` (not upstream's `EpdData`).
- Jinja env → `"exporter/goldendict/ru_components/templates"`.
- Template → `"rpd_ru.jinja"`.
- Query filter → `Lookup.rpd != ""`.
- `data = RpdData(lookup_entry, pth, jinja_env)`.

**VERIFY:**
- `uv run ruff check exporter/goldendict/export_rpd.py && uv run pyright exporter/goldendict/export_rpd.py`
- `rg -n "from typing import" exporter/goldendict/export_rpd.py` → **zero**.
- `rg -n "extract_body" exporter/goldendict/export_rpd.py` → **1** (import) + **1** (usage) = 2.
- `rg -n "html_rendered.find" exporter/goldendict/export_rpd.py` → **zero**.

---

### B4.3 — Templates: `ru_components/templates/` + `sbs_templates/` (russian_copies + sbs_copies; SMD exporter.md)

**SOURCE (new):** upstream `exporter/goldendict/templates/*.jinja` (10 files changed)
**DIFF CMD:** `git diff $R -- exporter/goldendict/templates/`

**Summary of upstream template changes (two types):**

**Type A — `<body>` comment (9 templates):** add one Jinja comment line BEFORE `<body>`:
```
{# do not change <body> — the export code splits header/body on this exact string (tools/utils.py extract_body) #}
```
Upstream files: `dpd_headword.jinja`, `dpd_root.jinja`, `dpd_see.jinja`,
`dpd_spelling_mistake.jinja`, `dpd_variant_reading.jinja`, `epd.jinja`,
`help_abbrev.jinja`, `help_abbrev_other.jinja`, `help_help.jinja`.

**Type B — `dpd_header.jinja` freq_data guard:** change line ~79 from
`{% if d.i.needs_frequency_button %}` → `{% if d.i.needs_frequency_button and d.i.freq_data %}`.

**Shadow template mapping and PORT decisions:**

The `<body>` comment is relevant ONLY for templates that contain `{{ d.header }}` followed
by `<body>` (i.e., full-page templates where `extract_body` splits on `<body>`). Shadow
templates that are body-only fragments (no `{{ d.header }}`, no `<body>`) do NOT need this
comment.

| Upstream template | RU shadow | Has `<body>`? | PORT action |
|---|---|---|---|
| `dpd_headword.jinja` | `ru_components/templates/dpd_headword_ru.jinja` | YES (L6) | ADD comment before `<body>` at L6 |
| `dpd_headword.jinja` | `sbs_templates/dpd_headword_sbs.jinja` | YES (L6) | ADD comment before `<body>` at L6 |
| `dpd_root.jinja` | `ru_components/templates/root_headword_ru.jinja` | YES (L2) | ADD comment before `<body>` at L2 |
| `dpd_root.jinja` | `sbs_templates/root_headword_sbs.jinja` | YES (L2) | ADD comment before `<body>` at L2 |
| `epd.jinja` | `ru_components/templates/rpd_ru.jinja` | YES (L2) | ADD comment before `<body>` at L2 |
| `epd.jinja` | `sbs_templates/epd_sbs.jinja` | YES (L2) | ADD comment before `<body>` at L2 |
| `help_abbrev_other.jinja` | `ru_components/templates/help_abbrev_other_ru.jinja` | YES (L2) | ADD comment before `<body>` at L2 |
| `help_abbrev_other.jinja` | `sbs_templates/help_abbrev_other_sbs.jinja` | YES (L2) | ADD comment before `<body>` at L2 |
| `dpd_see.jinja` | — (no RU/SBS shadow) | — | SKIP |
| `dpd_spelling_mistake.jinja` | `ru_components/templates/dpd_spelling_mistake_ru.jinja` | NO (fragment) | SKIP |
| `dpd_variant_reading.jinja` | `ru_components/templates/dpd_variant_reading_ru.jinja` | NO (fragment) | SKIP |
| `help_abbrev.jinja` | `ru_components/templates/help_abbrev_ru.jinja` | NO (fragment) | SKIP |
| `help_abbrev.jinja` | `sbs_templates/help_abbrev_sbs.jinja` | NO (fragment) | SKIP |
| `help_help.jinja` | `ru_components/templates/help_help_ru.jinja` | NO (fragment) | SKIP |
| `help_help.jinja` | `sbs_templates/help_help_sbs.jinja` | NO (fragment) | SKIP |

**Total `<body>` comment edits: 8 files** (4 RU, 4 SBS).

The comment is identical for all — insert this line immediately before the `<body>` line:
```
{# do not change <body> — the export code splits header/body on this exact string (tools/utils.py extract_body) #}
```

**Type B — `dpd_header.jinja` freq_data guard:**

| Shadow | Current line | PORT action |
|---|---|---|
| `ru_components/templates/dpd_header.jinja` L70 | `{% if d.i.needs_frequency_button %}` | → `{% if d.i.needs_frequency_button and d.i.freq_data %}` |
| `sbs_templates/dpd_header.jinja` L70 | `{% if d.i.needs_frequency_button %}` | → `{% if d.i.needs_frequency_button and d.i.freq_data %}` |

**PRESERVE (both RU and SBS template dirs):**
- All `ru_`/`sbs_` prefixed IDs, CSS classes, and JS calls.
- Sequential `onload`-chaining IIFE in `dpd_header.jinja` (SMD exporter.md item 3 for
  `ru_components/templates/` — do NOT replace with upstream's parallel `forEach`).
- `stopImmediatePropagation` in SBS/RU main.js.
- `fr !== undefined` guard in SBS/RU `loadButtonContent`.
- All RU/SBS/Tamil-specific template rows and blocks.

**N-A:** The `dpd_see.jinja` has no RU/SBS shadow. The 6 fragment-only templates
(`dpd_spelling_mistake_ru`, `dpd_variant_reading_ru`, `help_abbrev_ru`, `help_help_ru`,
`help_abbrev_sbs`, `help_help_sbs`) don't have `<body>` tags, so the comment is irrelevant.

**VERIFY:**
- `rg -c "do not change.*body" exporter/goldendict/ru_components/templates/ exporter/goldendict/sbs_templates/` → **8 files** with 1 match each.
- `rg -n "needs_frequency_button and d.i.freq_data" exporter/goldendict/ru_components/templates/dpd_header.jinja exporter/goldendict/sbs_templates/dpd_header.jinja` → **2** matches.
- `rg -n "needs_frequency_button %}" exporter/goldendict/ru_components/templates/dpd_header.jinja exporter/goldendict/sbs_templates/dpd_header.jinja` → only the `and d.i.freq_data` version (no bare `needs_frequency_button %}` left).

---

### B4.4 — `exporter/grammar_dict/grammar_dict_ru.py` (russian_copies; SMD exporter.md → grammar_dict_ru)

- **SOURCE (new):** `exporter/grammar_dict/grammar_dict.py`
- **SHADOW:** `exporter/grammar_dict/grammar_dict_ru.py`
- **DIFF CMD:** `git diff $R -- exporter/grammar_dict/grammar_dict.py`

**Summary of upstream changes:**
1. `GlobalVars.__init__`: `if config_test(...): self.make_mdict = True else: ...` → 
   `self.make_mdict = config_test("dictionary", "make_mdict", "yes")` (1 line replaces 4).
2. `close_db` type hint: `def close_db(self)` → `def close_db(self) -> None`.
3. DELETE `commit_db` method entirely.
4. `main()` → `main() -> None`.
5. `generate_html_from_lookup` → `generate_html_from_lookup(g: ...) -> None`.
6. `pr.yes(f"{len(lookup_results)}")` → `pr.yes(len(lookup_results))`.
7. `html_dict = {}` → `html_dict: dict[str, str] = {}`.
8. `make_data_lists` → `make_data_lists(g: ...) -> None`.
9. `dict_data += [DictEntry(...)]` → `dict_data.append(DictEntry(...))`.
10. `prepare_gd_mdict_and_export` → `prepare_gd_mdict_and_export(g: ...) -> None`.

**PORT (apply to shadow):**
1. **`ProgData_ru.__init__`:** simplify the `make_mdict` assignment:
   `self.make_mdict = config_test("dictionary", "make_mdict", "yes")` (replace 4 lines with 1).
2. **`close_db`:** add `-> None` type hint.
3. **DELETE `commit_db`** method entirely.
4. **`main()`** → `main() -> None`.
5. **`generate_html_from_lookup(g: ProgData_ru)`** → add `-> None`.
6. **`pr.yes(f"{len(lookup_results)}")`** → `pr.yes(len(lookup_results))`.
7. **`html_dict = {}`** → `html_dict: dict[str, str] = {}`.
8. **`make_data_lists(g: ProgData_ru)`** → add `-> None`.
9. **`dict_data += [DictEntry(...)]`** → `dict_data.append(DictEntry(...))`.
10. **`prepare_gd_mdict_and_export(g: ProgData_ru)`** → add `-> None`.

**N-A:** none — all upstream changes apply cleanly. The RU shadow's class is `ProgData_ru`
(not `GlobalVars`), but the methods are structurally identical.

**PRESERVE (RU layering):**
- `ProgData_ru` class name (not `GlobalVars`).
- `self.rupth = RuPaths()` in constructor.
- `from tools.paths_ru import RuPaths` import.
- `from tools.tools_for_ru_exporter import (ru_replace_abbreviations, load_abbreviations_dict)` import.
- `GrammarData_ru` subclass with `_process_grammar` override (Russian POS/component translation).
- `load_abbreviations_dict(g.rupth.abbreviations_tsv_path)` call in `generate_html_from_lookup`.
- `data = GrammarData_ru(lookup_entry, g.pth, jinja_env)` (not `GrammarData`).
- The 3 `entry_html.replace(...)` calls for Russian column headers (`"of"→"для"`, `"pos ⇅"→"чр ⇅"`, `"word ⇅"→"слово ⇅"`).
- Russian `DictInfo` metadata (`"DPD Грамматика"`, Russian author/description/website).
- `target_lang="ru"`.
- `dict_name = "ru-dpd-grammar"`.

**VERIFY:**
- `uv run ruff check exporter/grammar_dict/grammar_dict_ru.py && uv run pyright exporter/grammar_dict/grammar_dict_ru.py`
- `rg -n "def commit_db" exporter/grammar_dict/grammar_dict_ru.py` → **zero**.
- `rg -n "-> None" exporter/grammar_dict/grammar_dict_ru.py` → **≥5** (`close_db`, `main`, `generate_html_from_lookup`, `make_data_lists`, `prepare_gd_mdict_and_export`).

---

## Stage 2c — HARD STOP (end of Batch 4)

(Batch 4 hard stop. Batch 5 below was authored in the next ADVANCED session.)

---

## BATCH 5 — exporter/kindle + tbw + tpr + webapp + gui2 + scripts/build ports (Commit 2, post-Commit-1)

This batch covers the remaining exporter shadows (kindle / tbw / tpr / webapp), the gui2
example-field shadow, and two `scripts/build` shadows. Most upstream changes here are
**structural** (type hints, `open(...)` → `Path.open(..., encoding="utf-8")`, `+= [x]` → `.append(x)`,
`GlobalVars` → `@dataclass`) plus a few real logic changes. Per guide §2.1, structural refactors
ARE ported into the registered shadows.

> **Variant rename already done (B1.2) — do NOT re-apply.** `i.variants_unpack` →
> `i.variant_unpack` at `tbw_exporter_ru.py:194` and `tpr_exporter_ru.py:167` was applied in
> Batch 1. Batch 5 ports only the *surrounding* modernization (type hints, `.append`).

> **⚠️ COUPLED TEMPLATE EDIT (B5.2) — registry/SMD gap flagged.** The tpr Python change deletes
> the per-row `i.compound_type_has_digit` helper AND upstream simplifies the template guard
> `{%- if i.compound_type and not i.compound_type_has_digit -%}` → `{%- if i.compound_type -%}`
> in `exporter/tpr/templates/tpr_headword.jinja` (mirror, auto in Commit 1). The RU shadow template
> `exporter/tpr/templates/tpr_headword_ru.jinja:48` carries the SAME guard and MUST be simplified
> the same way, or it references a now-missing attribute. **`tpr_headword_ru.jinja` has NO
> `registry.json`/SMD entry** — the edit itself is an unambiguous 1:1 mirror of the upstream
> template change (no divergence list invented), but the missing registration is an open
> Shadow-Documentation-Gate item to resolve in Stage 3 (likely `russian_copies`).

> **`extract_body` carry-forward (B3.6):** none of the Batch 5 shadows split header/body, so no
> `extract_body` adoption is needed here (that carry-forward applies to the goldendict exporters in
> Batches 4/6, not kindle/tbw/tpr/webapp).

### B5.1 — exporter/tbw/tbw_exporter_ru.py (russian_copies; SMD exporter.md → tbw_exporter_ru)
- **SOURCE (new):** `exporter/tbw/tbw_exporter.py`
- **SHADOW:** `exporter/tbw/tbw_exporter_ru.py`
- **DIFF CMD:** `git diff $R -- exporter/tbw/tbw_exporter.py`
- **PORT (apply to shadow):**
  1. **L35** add `.all()`: `dpd_db = self.db_session.query(DpdHeadword)` →
     `dpd_db = self.db_session.query(DpdHeadword).all()`.
  2. **Type hints** `-> None` on all 13 functions (KEEP the `g: ProgData_ru` param type, NOT
     `GlobalVars`): `generate_sc_word_set` (L57), `generate_deconstructed_word_set` (L99),
     `generate_i2h_dict` (L112), `sort_i2h_dict` (L130), `generate_unmatched_word_set` (L139),
     `generate_ebt_headwords_set` (L147), `generate_dpd_ebt_dict` (L156),
     `generate_deconstructor_dict` (L174), `deconstructor_dict_add_variants` (L187),
     `deconstructor_dict_add_spelling_mistakes` (L204), `sort_deconstructor_dict` (L221),
     `save_js_files_for_fdg` (L231), `main` (L247).
  3. **L116** `for __counter__, i in enumerate(g.dpd_db):` → `for i in g.dpd_db:`.
  4. **L121** `if test1 & test2:` → `if test1 and test2:`.
  5. **L123–126** replace the if/else upsert:
     ```python
                if inflection not in g.i2h_dict:
                    g.i2h_dict[inflection] = [i.lemma_1]
                else:
                    g.i2h_dict[inflection] += [i.lemma_1]
     ```
     → `                g.i2h_dict.setdefault(inflection, []).append(i.lemma_1)`.
  6. **L151** `for __key__, values in g.i2h_dict.items():` → `for values in g.i2h_dict.values():`.
  7. **L162** delete the redundant `string = ""` line (it is unconditionally reassigned at L164
     `string = f"{pos_ru}. "`; mirrors upstream's removal of the duplicate init). Result:
     ```python
            pos_ru = ru_replace_abbreviations(i.pos, "gram")
            string = f"{pos_ru}. "
     ```
  8. **L237 / L241** `open()` → `Path.open(..., encoding="utf-8")`:
     - `with open(g.pth.fdg_i2h_js_path, "w") as f:` → `with g.pth.fdg_i2h_js_path.open("w", encoding="utf-8") as f:`
     - `with open(g.rupth.fdg_dpd_ebts_js_ru_path, "w") as f:` → `with g.rupth.fdg_dpd_ebts_js_ru_path.open("w", encoding="utf-8") as f:`
- **N-A:** upstream's `save_js_files_for_tbw` changes (function ABSENT in shadow — FDG-only per SMD
  items 3–4); the variant rename at L194 (already done in B1.2).
- **PRESERVE:** `ProgData_ru` class name; `rupth`; `make_ru_meaning_simpl` + `ru_replace_abbreviations`
  in `generate_dpd_ebt_dict` (`pos_ru`); FDG-only `save_js_files_for_fdg` writing
  `fdg_dpd_ebts_js_ru_path`; the commented `# deconstructor_dict_add_variants(g)` call (L265).
- **VERIFY:** `uv run ruff check exporter/tbw/tbw_exporter_ru.py && uv run pyright exporter/tbw/tbw_exporter_ru.py`;
  `rg -n "__counter__|__key__|test1 & test2" exporter/tbw/tbw_exporter_ru.py` → **zero**;
  `rg -n 'open\(' exporter/tbw/tbw_exporter_ru.py` → **zero** (all `.open`);
  `rg -c "\-> None" exporter/tbw/tbw_exporter_ru.py` → **≥13**.

### B5.2 — exporter/tpr/tpr_exporter_ru.py (russian_copies; SMD exporter.md → tpr_exporter_ru)
- **SOURCE (new):** `exporter/tpr/tpr_exporter.py`
- **SHADOW:** `exporter/tpr/tpr_exporter_ru.py`
- **DIFF CMD:** `git diff $R -- exporter/tpr/tpr_exporter.py`
- **PORT (apply to shadow):**
  1. **L2** delete `# -*- coding: utf-8 -*-`.
  2. **Imports:** delete `import os` (L8) and `import re` (L9); add `from pathlib import Path`
     (place after `import sqlite3`, before `from zipfile import ...`).
  3. **L46** `def make_dpd_db(self):` → `def make_dpd_db(self) -> list[DpdHeadword]:`
     (KEEP the RU body: function-local `from sqlalchemy.orm import joinedload` +
     `joinedload(DpdHeadword.ru)`).
  4. **L56** `def generate_tpr_data(g: GlobalVars):` → `-> None:`.
  5. **L65–76** replace the helper + comment block (removes `re` usage):
     ```python
            # Add helper for template
            i.compound_type_has_digit = bool(re.findall(r"\d", i.compound_type or ""))

            html_string = template.render(i=i, today=TODAY)

            # Original code did some replacements after rendering
            html_string = html_string.replace("\n", "").replace("    ", "")
            # The template already removes the span class='g' part because we don't include it
            # but for 100% byte-parity with the baseline we might need to be careful.

            # Replicate the specific ' quote to ’ replacement
            html_string = re.sub("'", "’", html_string)
     ```
     →
     ```python
            html_string = template.render(i=i, today=TODAY)

            html_string = html_string.replace("\n", "").replace("    ", "")
            html_string = html_string.replace("'", "’")
     ```
  6. **L78–85 and L119–126** `tpr_data_list += [ {...} ]` → `tpr_data_list.append( {...} )`.
  7. **L110** `except Exception:` → `except IndexError:`.
  8. **L135** `def generate_deconstructor_data(g: GlobalVars):` → `-> None:`; **L151–153**
     `deconstructor_data_list += [ {...} ]` → `.append( {...} )`.
  9. **L159** `def add_variants(g):` → `def add_variants(g: GlobalVars) -> None:`; **L168**
     `g.deconstructor_data_list += [{...}]` → `.append({...})`. (L167 `variant_unpack` = B1.2.)
  10. **L173** `def add_spelling_mistakes(g):` → `def add_spelling_mistakes(g: GlobalVars) -> None:`;
      **L182** `+= [{...}]` → `.append({...})`.
  11. **L187** `def add_roots_to_i2h(g):` → `def add_roots_to_i2h(g: GlobalVars) -> None:`.
  12. **L217** `def write_tsvs(g: GlobalVars):` → `-> None:`; **L222**
      `with open(g.pth.tpr_dpd_tsv_path, "w") as f:` → `with g.pth.tpr_dpd_tsv_path.open("w", encoding="utf-8") as f:`
      (L229 deconstructor TSV already has `newline="", encoding="utf-8"` — leave).
  13. **L236** `def copy_to_sqlite_db(g: GlobalVars):` → `-> None:`.
  14. **L296** `def tpr_updater(g: GlobalVars):` → `-> None:`; **L331**
      `with open(g.pth.tpr_sql_file_path, "w") as f:` → `with g.pth.tpr_sql_file_path.open("w", encoding="utf-8") as f:`.
  15. **L343** `def copy_zip_to_tpr_downloads(g: GlobalVars):` → `-> None:`; **L351**
      `with open(g.pth.tpr_download_list_path) as f:` → `with g.pth.tpr_download_list_path.open(encoding="utf-8") as f:`;
      **L361** `def _zip_it_up(file_path, file_name, output_file):` →
      `def _zip_it_up(file_path: Path, file_name: str, output_file: Path) -> None:`;
      **L365–368** replace `_file_size`:
      ```python
            def _file_size(output_file):
                filestat = os.stat(output_file)
                filesize = f"{filestat.st_size / 1000 / 1000:.1f}"
                return filesize
      ```
      →
      ```python
            def _file_size(output_file: Path) -> str:
                filesize = f"{output_file.stat().st_size / 1000 / 1000:.1f}"
                return filesize
      ```
      **L386** `with open(g.pth.tpr_download_list_path, "w") as f:` → `with g.pth.tpr_download_list_path.open("w", encoding="utf-8") as f:`.
  16. **L392** `def main():` → `def main() -> None:`.
- **COUPLED TEMPLATE EDIT (REQUIRED, see batch banner):**
  `exporter/tpr/templates/tpr_headword_ru.jinja:48`
  `{%- if i.compound_type and not i.compound_type_has_digit -%}` → `{%- if i.compound_type -%}`
  (1:1 mirror of the upstream `tpr_headword.jinja` change; forced by deleting the helper in step 5).
  **Flag:** `tpr_headword_ru.jinja` is NOT in `registry.json`/SMD — register it (`russian_copies`)
  per the Shadow Documentation Gate when this edit lands.
- **N-A:** upstream's `copy_zip_to_tpr_downloads` release/beta `version` branching — the RU shadow
  diverges (custom `update_tpr_download_list_ru` + single "DPD with Russian" entry, SMD item 5);
  port ONLY the `open`/`.stat`/type-hint mechanics onto the shadow's existing body, NOT the
  version logic.
- **PRESERVE:** `rupth`; `make_dpd_db` RU body (`joinedload(DpdHeadword.ru)` + lazy import);
  `tpr_headword_ru.jinja` template name; `root_ru_meaning` append (L103–104);
  `update_tpr_download_list_ru` (L336–340); `g.rupth.tpr_with_rus_path` + "DPD with Russian"
  metadata; the commented `# add_variants(g)` call (L409).
- **Iron-Rule note:** if any `+= [...]` block does not map cleanly to `.append(...)` (e.g. multi-key
  dict literals), STOP → ADVANCED rather than guessing.
- **VERIFY:** `uv run ruff check exporter/tpr/tpr_exporter_ru.py && uv run pyright exporter/tpr/tpr_exporter_ru.py`;
  `rg -n "^import os|^import re|# -\*- coding" exporter/tpr/tpr_exporter_ru.py` → **zero**;
  `rg -n "os\.stat|re\.sub|re\.findall|compound_type_has_digit" exporter/tpr/tpr_exporter_ru.py` → **zero**;
  `rg -n 'open\(' exporter/tpr/tpr_exporter_ru.py` → **zero** (all `.open`);
  `rg -n "compound_type_has_digit" exporter/tpr/templates/tpr_headword_ru.jinja` → **zero**.

### B5.3 — exporter/kindle/kindle_exporter_ru.py (russian_copies; SMD exporter.md → kindle_exporter_ru)
- **SOURCE (new):** `exporter/kindle/kindle_exporter.py`
- **SHADOW:** `exporter/kindle/kindle_exporter_ru.py`
- **DIFF CMD:** `git diff $R -- exporter/kindle/kindle_exporter.py`
- **PORT — real logic + I/O changes:**
  1. **Imports (L15):** `from rich import print` → `from rich.markup import escape`. ADD
     `from jinja2 import Environment` (for the type hints in step 7).
  2. **Deconstructor loop guard removal (L152–161)** — the shadow's `deconstructor_db` is already
     pre-filtered by `Lookup.lookup_key.in_(chunk)` (L104–108), exactly like upstream, so the
     `if bool(set(i.lookup_key) & all_words_set):` guard is redundant. Replace:
     ```python
        for counter, i in enumerate(deconstructor_db):
            if bool(set(i.lookup_key) & all_words_set):
                first_letter = find_first_letter(i.lookup_key)
                entry = render_deconstructor_entry_ru(jinja_env, id_counter, i)
                letter_dict[first_letter] += [entry]
                id_counter += 1
            if counter % 5000 == 0:
                pr.counter(counter, len(deconstructor_db), i.lookup_key)
     ```
     →
     ```python
        for counter, i in enumerate(deconstructor_db):
            first_letter = find_first_letter(i.lookup_key)
            entry = render_deconstructor_entry_ru(jinja_env, id_counter, i)
            letter_dict[first_letter].append(entry)
            id_counter += 1
            if counter % 5000 == 0:
                pr.counter(counter, len(deconstructor_db), i.lookup_key)
     ```
  3. **L147** `letter_dict[first_letter] += [entry]` → `letter_dict[first_letter].append(entry)`
     (the "add all words" loop).
  4. **L137** `letter_dict: dict = {}` → `letter_dict: dict[str, list[str]] = {}` (keep the
     existing population loop on L138–139).
  5. **`open()` → `Path.open(..., encoding="utf-8")`** — 5 sites: L172
     (`output_path.open("w", encoding="utf-8")`), L288 (`rupth.epub_abbreviations_path.open(...)`),
     L308 (`rupth.epub_titlepage_path.open(...)`), L321 (`rupth.epub_content_opf_path.open(...)`),
     L450 (`output_path.open("w", encoding="utf-8")`).
  6. **L329 + import** `epub_dir_path = Path(pth.epub_dir)` → `epub_dir_path = pth.epub_dir`; this
     removes the only use of `Path`, so also delete `from pathlib import Path` (L12).
     **Pre-check:** `rg -n "\bPath\b" exporter/kindle/kindle_exporter_ru.py` must show only L12 (import)
     and L329 before editing — if `Path` is used elsewhere, KEEP the import and stop to re-check.
  7. **`make_mobi` `print` → `pr.white(escape(...))`** (L352, L365): `print(line, end="")` →
     `pr.white(escape(line.rstrip()))` (precondition: `pr.white` exists in `tools/printer.py` —
     the mirror `kindle_exporter.py` calls it; confirm before edit).
- **PORT — type-hint modernization (mirror upstream; add `Environment` import from step 1):**
  - `render_dpd_xhtml_ru` (L48) → `-> int` (it returns `id_counter + 1`); KEEP `(pth, rupth)` params.
  - `jinja_env` params → `jinja_env: Environment` on `render_ebook_entry_ru` (L181),
    `render_grammar_templ_ru` (L237), `render_example_templ_ru` (L247),
    `render_deconstructor_entry_ru` (L255), `render_ebook_letter_templ_ru` (L265),
    `render_abbreviation_entry_ru` (L293), `render_rpd_entry_ru` (L457), `render_rpd_letter_templ_ru` (L469).
  - `save_abbreviations_xhtml_page` (L271) → add `id_counter: int` + `-> None`;
    `save_title_page_xhtml` (L299) → `-> None`; `save_content_opf_xhtml` (L314) →
    `current_datetime: datetime` + `-> None`; `zip_epub` (L326) → `-> None`; `make_mobi` (L337) →
    `-> None`; `html_friendly` (L370) → `(text: str) -> str`; `main` (L475) → `-> None`.
  - `render_ebook_entry_ru` `inflections: list` → `inflections: list[str]` (L184);
    `render_abbreviation_entry_ru` `i: dict` → `i: dict[str, str]` (L293).
- **N-A (do NOT apply):** upstream `script_attr` / `lookup_script_attr` / `SCRIPT_CONFIG` /
  `render_epd_xhtml` machinery — the RU fork is Roman-only and uses `render_rpd_xhtml_ru` +
  `Lookup.rpd` + the Russian alphabet (SMD items 1, 5); upstream's `render_deconstructor_entry`
  dropping a `pth` param (the shadow's `render_deconstructor_entry_ru` already has no `pth`).
- **PRESERVE:** all `_ru`-suffixed function/template names; `rupth` outputs; `joinedload(DpdHeadword.ru)`;
  the Russian summary in `render_ebook_entry_ru` (`make_ru_meaning_for_ebook`, `ru_replace_abbreviations`,
  `degree_of_completion_ru`, `ru_make_grammar_line`, the `" & " → " и "` replacements);
  `render_rpd_xhtml_ru` + Russian alphabet + `Lookup.rpd`; `"Сокращения"` abbrev title;
  `ru_components/templates` jinja env; all RU imports.
- **Iron-Rule note:** the deconstructor-guard removal (step 2) is a behavior change — it is safe
  ONLY because the shadow pre-filters `deconstructor_db` with `Lookup.lookup_key.in_(chunk)` (verified
  L104–108). If that pre-filter is not present where you edit, STOP → ADVANCED.
- **VERIFY:** `uv run ruff check exporter/kindle/kindle_exporter_ru.py && uv run pyright exporter/kindle/kindle_exporter_ru.py`;
  `rg -n "from rich import print|from pathlib import Path" exporter/kindle/kindle_exporter_ru.py` → **zero**;
  `rg -n 'open\(' exporter/kindle/kindle_exporter_ru.py` → **zero** (all `.open`);
  `rg -n "print\(line" exporter/kindle/kindle_exporter_ru.py` → **zero**;
  `rg -n "if bool\(set\(i.lookup_key\)" exporter/kindle/kindle_exporter_ru.py` → **zero**.

### B5.4 — exporter/webapp/main_ru.py (russian_copies; SMD exporter.md → main_ru)
- **SOURCE (new):** `exporter/webapp/main.py`
- **SHADOW:** `exporter/webapp/main_ru.py`
- **DIFF CMD:** `git diff $R -- exporter/webapp/main.py`
- **PORT:**
  1. **CSS/JS reads — add `encoding="utf-8"`** (L81, L84, L87):
     `with open(pth.webapp_css_path) as f:` → `with open(pth.webapp_css_path, encoding="utf-8") as f:`
     (and the `webapp_js_path`, `webapp_home_simple_css_path` lines).
  2. **`TemplateResponse` — request as first positional arg** (Starlette 0.29+ signature). For EACH
     of the 8 call sites, move `request` out of the context dict and into the first positional slot:
     ```python
        return templates_XX.TemplateResponse(
            "NAME.html",
            {
                "request": request,
                ...rest...
            },
        )
     ```
     →
     ```python
        return templates_XX.TemplateResponse(
            request,
            "NAME.html",
            {
                ...rest...
            },
        )
     ```
     Call sites (`TemplateResponse` line → `"request": request` line, `templates_XX` is `_ru` or `_sbs`
     as already written — do NOT change which one):
     L99→L102 (`templates_ru`, home.html), L115→L118 (`templates_sbs`, home.html),
     L131→L134 (`templates_ru`, home.html), L157→L160 (`templates_sbs`, home_simple.html),
     L224→L227 (`templates_ru`, bold_definitions.html), L254→L257 (`templates_sbs`, ...),
     L304→L307 (`templates_ru`, ...), L570→L573 (`templates_ru`, status.html).
- **N-A:** main.py has no other range changes. (The `make_roots_count_dict` move is invisible here:
  `main_ru.py:17–20` imports it from the mirror `exporter.webapp.preloads`, which re-exports it from
  `db.db_helpers` post-Commit-1 — see B5.5. No import edit needed.)
- **PRESERVE:** the `templates_ru` / `templates_sbs` split (L73–74) and every route's RU-vs-SBS
  template choice; the `/` → RU, `/sbs` → SBS dual-mode routing; `127.0.0.1` host (never `0.0.0.0`
  /`localhost`); `make_dpd_html_ru` / `db_search_gd_ru` bodies; `main_ru:app` entry point.
- **VERIFY:** `uv run ruff check exporter/webapp/main_ru.py && uv run pyright exporter/webapp/main_ru.py`;
  `rg -n '"request": request' exporter/webapp/main_ru.py` → **zero**;
  `rg -c "TemplateResponse" exporter/webapp/main_ru.py` → **8** (unchanged count, request now positional);
  `rg -n 'open\(pth\.webapp' exporter/webapp/main_ru.py` → all 3 show `encoding="utf-8"`.

### B5.5 — exporter/webapp/preloads_ru.py (russian_copies; SMD exporter.md → preloads_ru) — CONFIRMED NO-OP
- **SOURCE (new):** `exporter/webapp/preloads.py`
- **SHADOW:** `exporter/webapp/preloads_ru.py`
- **DIFF CMD:** `git diff $R -- exporter/webapp/preloads.py`
- **Upstream change:** moves `make_roots_count_dict` out of `preloads.py` into `db/db_helpers.py`
  (mirror) and re-imports it as `from db.db_helpers import make_roots_count_dict as make_roots_count_dict`;
  drops `from typing import Dict`.
- **PORT: NONE.** The shadow never defined `make_roots_count_dict` (it is a *partial* shadow holding
  only `make_headwords_clean_set_ru`) and never imported `typing.Dict`. Confirmed: shadow imports are
  `from sqlalchemy.orm import Session, defer` + `from db.models import DpdHeadword, Lookup` only.
- **Consumer safety:** `main_ru.py` imports `make_roots_count_dict` from the **mirror** `preloads.py`
  (L17–20), not from `preloads_ru.py`; the mirror re-export keeps that import valid post-Commit-1.
- **PRESERVE:** file unchanged.
- **VERIFY:** `rg -n "make_roots_count_dict|from typing import Dict" exporter/webapp/preloads_ru.py` → **zero**.

### B5.6 — exporter/webapp/data_classes_ru.py (russian_copies; SMD exporter.md → data_classes_ru) — NO-OP beyond B1.2
- **SOURCE (new):** `exporter/webapp/data_classes.py`
- **SHADOW:** `exporter/webapp/data_classes_ru.py`
- **DIFF CMD:** `git diff $R -- exporter/webapp/data_classes.py`
- **Upstream change (range):** ONE line — `VariantData.__init__`:
  `self.variants = result.variants_unpack` → `result.variant_unpack` (`--stat` = 1 insertion, 1 deletion).
- **PORT: NONE for Batch 5.** That rename's shadow fan-out (`data_classes_ru.py:89`
  `result.variants_unpack` → `result.variant_unpack`) was already applied in **B1.2**. No
  `HeadwordData` field additions occurred in this range, so the SMD "port new HeadwordData fields"
  watch-item has nothing to apply.
- **PRESERVE:** all RU `HeadwordData` fields per SMD (no change).
- **VERIFY:** `rg -n "variants_unpack" exporter/webapp/data_classes_ru.py` → **zero** (B1.2 must have
  landed first); otherwise no Batch-5 edit.

### B5.7 — gui2/dps_example_field.py (dps_copies; SMD gui.md → dps_example_field) — CONFIRMED NO-OP (inherited)
- **SOURCE (new):** `gui2/dpd_fields_examples.py`
- **SHADOW:** `gui2/dps_example_field.py`
- **DIFF CMD:** `git diff $R -- gui2/dpd_fields_examples.py`
- **Upstream change:** adds module constant `MAX_SEARCH_RESULTS = 100`; in method `choose_example`,
  `self.cst_examples[:50]` → `[:MAX_SEARCH_RESULTS]` and prepends an amber "Showing first 100
  results…" `ft.Text` when results exceed the cap.
- **PORT: NONE.** `DpsExampleField(DpdExampleField)` does **not** override `choose_example` (verified:
  its overrides are `click_choose_example_ok`, `click_clean_example`, `click_swap_example`,
  `_swap_examples`, `click_delete_example`, `_click_stash_example`, `_click_reload_example`,
  `_click_last_example`, `_click_arch_example`, `_handle_archive_example`). The changed
  `choose_example` (and `MAX_SEARCH_RESULTS`, resolved in the parent module's namespace) is inherited
  unchanged after Commit 1 overwrites `dpd_fields_examples.py`. The subclass sets `self.cst_examples`
  (L166), the only attribute the method reads; no new attribute dependency is introduced.
- **No registry/ledger change needed:** this is a Stage-2/3 port decision (inherited no-op), not a
  pre-sync drift no-op; `reviewed_shadow_noops.json` is unrelated. (The earlier prior-sync entry for
  `5799afbb` is a *different* upstream change — see handoff.)
- **VERIFY:** `rg -n "def choose_example|MAX_SEARCH_RESULTS" gui2/dps_example_field.py` → **zero**
  (proves it inherits); `rg -n "def choose_example" gui2/dpd_fields_examples.py` → **1** (parent has it
  post-Commit-1).

### B5.8 — scripts/build/db_rebuild_from_tsv_dps.py (dps_copies; SMD scripts.md → db_rebuild_from_tsv_dps)
- **SOURCE (new):** `scripts/build/db_rebuild_from_tsv.py`
- **SHADOW:** `scripts/build/db_rebuild_from_tsv_dps.py`
- **DIFF CMD:** `git diff $R -- scripts/build/db_rebuild_from_tsv.py`
- **Upstream change (range):** ONE line — `read_tsv_files`: `open(file_path, "r", newline="")` gains
  `encoding="utf-8"`.
- **PORT (strict, upstream parity):** **L178** `with open(file_path, "r", newline="") as tsv_file:` →
  `with open(file_path, "r", newline="", encoding="utf-8") as tsv_file:` (the shadow's `read_tsv_files`,
  identical to upstream).
- **PORT (analogous — B3.7 Cyrillic/Tamil precedent):** the shadow's localized TSV reads/writes lack
  `encoding="utf-8"`, which risks corrupting Russian/SBS/Tamil data on non-UTF-8 default locales.
  Add `encoding="utf-8"` to all six: **L64** `open(dpspth.sbs_path, "r", newline="")`, **L82**
  `open(dpspth.sbs_path, "w", newline="")`, **L97** `open(dpspth.russian_path, "r", newline="")`,
  **L110** `open(dpspth.russian_path, "w", newline="")`, **L117** `open(dpspth.tamil_path, "r", newline="")`,
  **L130** `open(dpspth.tamil_path, "w", newline="")`. (Same rationale already applied in B3.7
  `backup_dps.py`. If the user prefers strict-parity-only, drop this sub-item and keep L178 only.)
- **N-A:** upstream `db_rebuild_from_tsv.py` has no `Russian`/`SBS`/`Tamil` sections — the shadow's
  localized rebuild helpers are local-only (no upstream counterpart to port).
- **PRESERVE:** `make_table_data_ta()` + the Russian/SBS/Tamil rebuild + duplicate/orphan checks (SMD).
- **VERIFY:** `uv run ruff check scripts/build/db_rebuild_from_tsv_dps.py`;
  `rg -n 'newline=""\)' scripts/build/db_rebuild_from_tsv_dps.py` → **zero** (no unencoded TSV opens left,
  if the analogous sub-item is applied; if strict-only, expect 6).

### B5.9 — scripts/build/families_to_json_ru.py (russian_copies; SMD scripts.md → families_to_json_ru)
- **SOURCE (new):** `scripts/build/families_to_json.py`
- **SHADOW:** `scripts/build/families_to_json_ru.py`
- **DIFF CMD:** `git diff $R -- scripts/build/families_to_json.py`
- **PORT (mirror upstream's `GlobalVars` → `@dataclass` refactor; guide §2.1):**
  1. **Imports:** add `from dataclasses import dataclass` and `from sqlalchemy.orm import Session`
     (keep the existing `from tools.paths_ru import RuPaths`).
  2. **Replace the `GlobalVars` class (L15–25)** — drop the import-time side-effect class attrs; use a
     typed dataclass. RU divergence: the `paths` field is `RuPaths` (the shadow sets `paths = rupth`):
     ```python
     @dataclass
     class GlobalVars:
         paths: RuPaths
         db_session: Session
         fc_db: list[FamilyCompound]
         fi_db: list[FamilyIdiom]
         fr_db: list[FamilyRoot]
         fs_db: list[FamilySet]
         fw_db: list[FamilyWord]
     ```
  3. **`main()` (L28–37)** → build paths + session + query rows explicitly:
     ```python
     def main() -> None:
         pr.tic()
         pr.yellow_title("exporting families .json")
         paths = ProjectPaths()
         rupth = RuPaths()
         db_session = get_db_session(paths.dpd_db_path)
         g = GlobalVars(
             paths=rupth,
             db_session=db_session,
             fc_db=db_session.query(FamilyCompound).all(),
             fi_db=db_session.query(FamilyIdiom).all(),
             fr_db=db_session.query(FamilyRoot).all(),
             fs_db=db_session.query(FamilySet).all(),
             fw_db=db_session.query(FamilyWord).all(),
         )
         export_family_compound(g)
         export_family_idiom(g)
         export_family_root(g)
         export_family_set(g)
         export_family_word(g)
         pr.toc()
     ```
  4. **`json_dumper` (L40–46)** → rename param `dict` → `data`, type `dict[str, object]`, `-> None`,
     and use `Path.write_text`:
     ```python
     def json_dumper(filepath: Path, data: dict[str, object]) -> None:
         js_content = (
             f"""var {filepath.stem} = {json.dumps(data, ensure_ascii=False, indent=1)}"""
         )
         filepath.write_text(js_content, encoding="utf-8")
     ```
  5. **`-> None`** on `export_family_compound` (L49), `export_family_idiom` (L58),
     `export_family_root` (L67), `export_family_set` (L83), `export_family_word` (L92).
- **N-A:** none (coding header already absent from the shadow).
- **PRESERVE (RU layering):** `paths = rupth` (RuPaths, NOT ProjectPaths); `data_ru_unpack` in all five
  exporters (NOT `data_unpack`); `root_ru_meaning` in `export_family_root` (L74); the `from
  tools.paths_ru import RuPaths` import; the `g.paths.family_*_json` write targets.
- **Iron-Rule note:** pyright must resolve `g.paths.family_*_json` against `RuPaths` — if RuPaths does
  not expose those attributes (it does at runtime today), STOP → ADVANCED.
- **VERIFY:** `uv run ruff check scripts/build/families_to_json_ru.py && uv run pyright scripts/build/families_to_json_ru.py`;
  `rg -n "@dataclass" scripts/build/families_to_json_ru.py` → **1**;
  `rg -c "data_ru_unpack" scripts/build/families_to_json_ru.py` → **5**;
  `rg -n "root_ru_meaning" scripts/build/families_to_json_ru.py` → **1**;
  `rg -n 'open\(' scripts/build/families_to_json_ru.py` → **zero**.

### B5.10 — exporter/kindle/ru_components/epub/OEBPS/Text/titlepage.xhtml (russian_copies; SMD exporter.md → ru_components/epub) — SKIP
- **SOURCE (new):** `exporter/kindle/epub/OEBPS/Text/titlepage.xhtml`
- **SHADOW:** `exporter/kindle/ru_components/epub/OEBPS/Text/titlepage.xhtml`
- **DIFF CMD:** `git diff $R -- exporter/kindle/epub/OEBPS/Text/titlepage.xhtml`
- **Upstream change:** date/time-only (`updated on 2026-05-01 … 06:38` → `2026-06-09 … 06:14`).
- **PORT: NONE — SKIP.** Per SMD exporter.md (`exporter/kindle/ru_components/epub/`):
  "`titlepage.xhtml` update date/time is generated locally for the Russian Kindle build; upstream
  date/time-only changes are intentionally not ported." No structural/metadata change in range.
- **VERIFY:** none (no edit).

---

## BATCH 6 — INSPIRED backports (×10 sources → judgement)

`inspired_by_upstream` = **no strict parity**. For each of the 10 upstream sources in the Stage 2a
"INSPIRED — backport selectively" table, the upstream diff for range `R` was read and each local
target inspected for whether the change even applies. Decisions below; **only two backports are
recommended** (`extract_body` adoption + the roots N+1 query fix), everything else is N-A or cosmetic.

**Net Batch-6 work for Stage 3:** edits to **7 goldendict exporters** (extract_body) + the **roots
perf fix** in 2 of them. All other inspired targets = **SKIP** (recorded with reason). The 7 inspired
files are local-only (not in the upstream tree), so Commit 1 does NOT touch them — anchors/line numbers
below are stable from now through Stage 3.

**Two judgement calls to raise at the 2d gate** (B6.4 optional refactors, B6.10 pytest gate) — see below.

### Decision summary

| # | Upstream source | Inspired target(s) | Decision |
|---|---|---|---|
| B6.1 | `.github/workflows/draft_release.yml` | `ru_release.yml`, `ru_release_test.yml` | **SKIP** (N-A) |
| B6.2 | `export_dpd.py` | `export_dpd_ru.py`, `export_dpd_sbs.py` | **PORT extract_body only** |
| B6.3 | `export_epd.py` | `export_epd_sbs.py` | **PORT extract_body only** |
| B6.4 | `export_help.py` | `export_help_ru.py`, `export_help_sbs.py` | **PORT extract_body**; refactors optional (2d) |
| B6.5 | `export_roots.py` | `export_roots_ru.py`, `export_roots_sbs.py` | **PORT extract_body + N+1 query fix** |
| B6.6 | `export_variant_spelling.py` | `export_variant_spelling_ru.py` | **SKIP** (N-A) |
| B6.7 | `main.py` | `main_ru.py`, `main_sbs.py` | **SKIP** (divergence-preserving) |
| B6.8 | `gui2/dpd_fields.py` | `gui2/dps_fields.py` | **SKIP** (N-A) |
| B6.9 | `gui2/dpd_fields_lists.py` | `gui2/dps_fields_lists.py` | **SKIP** (N-A) |
| B6.10 | `scripts/bash/generate_components.py` | `scripts/bash/generate_components.sh` | **SKIP / defer** (2d judgement) |

---

### `extract_body` adoption (shared recipe for B6.2 / B6.3 / B6.4 / B6.5)

Upstream replaced the inline body split
```python
        body_start = html.find("<body>")
        body = html[body_start:]
```
with `body = extract_body(html)` (new helper in `tools/utils.py`, arrives via Commit 1 — confirmed in
the B3.6 / B4 cross-batch flag). Behavioral identity; the value is consistency with the `<body>` comment
guards added to the localized templates in Batch 4, which reference `tools/utils.py extract_body`.

For each file below: **(a)** add `extract_body` to the existing `from tools.utils import …` line
(every target imports at least `squash_whitespaces` from `tools.utils`, so add it there — NOT to
`tools.utils_sbs`, which does not define it); **(b)** replace the single 2-line `body_start` block with
`body = extract_body(<var>)` at the same indentation, using the correct variable name. Each file has
**exactly one** `body_start` site.

| File | tools.utils import anchor | var | body block anchor |
|---|---|---|---|
| `export_dpd_ru.py` | multi-line block (`RenderedSizes,` … `sum_rendered_sizes,`); insert `    extract_body,` after `    default_rendered_sizes,` | `html` | `body_start = html.find("<body>")` / `body = html[body_start:]` |
| `export_dpd_sbs.py` | multi-line `from tools.utils import (\n    list_into_batches,\n    squash_whitespaces,\n)`; insert `    extract_body,` before `    list_into_batches,` | `html` | same as above |
| `export_epd_sbs.py` | `from tools.utils import RenderedSizes, default_rendered_sizes, squash_whitespaces` → add `extract_body,` (e.g. `… default_rendered_sizes, extract_body, squash_whitespaces`) | `html_rendered` | `body_start = html_rendered.find("<body>")` / `body = html_rendered[body_start:]` |
| `export_help_ru.py` | `from tools.utils import RenderedSizes, default_rendered_sizes, squash_whitespaces` → add `extract_body` | `html_rendered` | same as epd_sbs |
| `export_help_sbs.py` | `from tools.utils import squash_whitespaces` → `from tools.utils import extract_body, squash_whitespaces` | `html_rendered` | same as epd_sbs |
| `export_roots_ru.py` | `from tools.utils import RenderedSizes, default_rendered_sizes, squash_whitespaces` → add `extract_body` | `html` | `body_start = html.find("<body>")` / `body = html[body_start:]` |
| `export_roots_sbs.py` | `from tools.utils import squash_whitespaces` → `from tools.utils import extract_body, squash_whitespaces` | `html` | same as roots_ru |

**VERIFY (after Commit 1, when `extract_body` exists in `tools/utils.py`):**
`uv run ruff check exporter/goldendict/export_dpd_ru.py exporter/goldendict/export_dpd_sbs.py exporter/goldendict/export_epd_sbs.py exporter/goldendict/export_help_ru.py exporter/goldendict/export_help_sbs.py exporter/goldendict/export_roots_ru.py exporter/goldendict/export_roots_sbs.py`
then `uv run pyright` on the same set; `rg -n 'body_start' exporter/goldendict/export_{dpd_ru,dpd_sbs,epd_sbs,help_ru,help_sbs,roots_ru,roots_sbs}.py` must return **zero** rows.

---

### B6.1 — CI workflow → **SKIP** (N-A)
- **Upstream diff:** adds a `Prepare dictionary sources` step (`resources/other-dictionaries/scripts/prepare_sources.py`, `working-directory: resources/other-dictionaries`) immediately before the `Export Mobile DB` step.
- **Why N-A:** `ru_release.yml` / `ru_release_test.yml` contain **no** mobile-DB export, no `prepare_sources`, and no `other-dictionaries` reference (`rg` confirmed zero matches). The new step belongs to the mobile pipeline the RU release workflows do not run. No edit.

### B6.2 — `export_dpd_ru.py` / `export_dpd_sbs.py` → **PORT extract_body only**
- **Upstream diff:** `List/Set/Tuple` → `list/set/tuple` type hints, `extract_body` adoption, `show_id` if/else → single `config_test(...)` bool.
- **PORT:** extract_body (shared recipe above) in both files.
- **SKIP (cosmetic, no functional gain on diverged inspired files):** type-hint modernization, `show_id` bool collapse. (These targets carry RU/SBS-specific `data_classes_dps.HeadwordData`, joinedloads, set-name synonyms — the diff's type-hint churn has no behavioral effect here.)

### B6.3 — `export_epd_sbs.py` → **PORT extract_body only**
- **Upstream diff (`export_epd.py`):** type hints + extract_body. (RU side of this source is the **strict** `export_rpd.py` shadow, already handled in Batch 4 — not an inspired target.)
- **PORT:** extract_body (shared recipe). **SKIP:** type hints.

### B6.4 — `export_help_ru.py` / `export_help_sbs.py` → **PORT extract_body; refactors OPTIONAL**
- **Upstream diff (`export_help.py`):** `@dataclass` for `Abbreviation`/`Help` (replaces `__init__`); drops the unused `__db_session__: Session` param from `generate_help_html`; type hints + `Environment` annotations; **extract_body**; bibliography/thanks loops `for x in range(len(...)): … break` → `for i, n in zip(seq, seq[1:])`.
- **PORT (recommended):** extract_body only — 1 site each (the localized help exporters have fewer body-split sites than upstream's 3).
- **OPTIONAL — raise at 2d (default SKIP):**
  - **zip() bibliography/thanks refactor** — both files still use the old `range(len())`+`break` pattern (bibliography & thanks, 2 sites each). Behaviorally identical; cleaner. Low risk, pure readability. Backport only if the user wants it.
  - **drop `__db_session__` param** — both still declare it; it is unused. Dropping it **couples** to the callers: `main_ru.py:97` `generate_help_html(g.db_session, g.pth, g.rupth)` and `main_sbs.py:116` would need the `db_session` arg removed too. Recommend **SKIP** (coupling churn for an already-ignored param).
  - **`@dataclass` conversion** — internal only, no caller impact, but cosmetic. Recommend SKIP.

### B6.5 — `export_roots_ru.py` / `export_roots_sbs.py` → **PORT extract_body + N+1 query fix**
- **Upstream diff (`export_roots.py`):** drops `import re` / adds `from collections import defaultdict`; type hints; **extract_body**; **pre-groups `FamilyRoot` by `root_key` once via `defaultdict`** instead of querying per root inside the loop (N+1 → 1 query); `re.sub("√", "", x)` → `x.replace("√", "")`.
- **PORT 1 — extract_body** (shared recipe), both files.
- **PORT 2 — N+1 query fix** (real performance win; both files have the per-root query at line ~37):
  - Add import `from collections import defaultdict` (group with stdlib imports near the top).
  - After `    roots_db = db_session.query(DpdRoot).all()`, insert:
    ```python
        frs_by_root: dict[str, list[FamilyRoot]] = defaultdict(list)
        for fr in db_session.query(FamilyRoot).all():
            frs_by_root[fr.root_key].append(fr)
    ```
  - Replace the in-loop line
    `frs = db_session.query(FamilyRoot).filter(FamilyRoot.root_key == r.root).all()`
    with `frs = frs_by_root.get(r.root, [])`.
  - **Preserve** the local loop header as-is — `export_roots_ru.py` uses `for counter, r in enumerate(roots_db):` (do NOT change to upstream's `for r in roots_db:`); apply the analogous edit to whatever `export_roots_sbs.py`'s loop header is.
  - `FamilyRoot` is already imported in both (`from db.models import DpdRoot, FamilyRoot`).
- **SKIP (cosmetic):** type hints, `re.sub`→`replace` (leave the local `re` usage and import unless ruff flags `re` as now-unused — it is still used for the synonyms `re.sub("√", …)` block, so keep `import re`).
- **VERIFY (extra):** `rg -n 'query\(FamilyRoot\)\.filter' exporter/goldendict/export_roots_ru.py exporter/goldendict/export_roots_sbs.py` must return **zero** rows; pyright clean.

### B6.6 — `export_variant_spelling_ru.py` → **SKIP** (N-A)
- **Upstream diff (`export_variant_spelling.py`):** type hints; extract_body; `open(...)` → pathlib `.open()`; drops the now-unused `pth` param from `generate_see/variant/spelling_data_list`.
- **Why N-A:** the RU target builds HTML **inline** (`html += "<body>"` … `html += "</body></html>"`) — there is **no `html.find("<body>")` site**, so extract_body does not apply. Per SMD (exporter.md → `export_variant_spelling_ru`) `generate_see_data_list` was removed and templates take direct variables, so the upstream signature `pth`-drops don't map. Only overlap = pathlib `open()` on the two `test_and_make_*_dict` reads (cosmetic). No recommended edit.

### B6.7 — `main_ru.py` / `main_sbs.py` → **SKIP** (divergence-preserving)
- **Upstream diff (`main.py`):** removes `self.paths = self.pth` (uses `g.pth` directly everywhere); type hints; `make_mdict` if/else → bool; `generate_help_html(g.db_session, g.pth)` → `generate_help_html(g.pth)`; pathlib + `encoding="utf-8"` in `write_size_dict` / `write_limited_datalist`.
- **⚠️ N-A — do NOT backport `self.paths` removal:** this is the exact fork divergence point. `main_ru.py:59` sets `self.paths = self.rupth`; `main_sbs.py:73` sets `self.paths = self.pth`. SMD (exporter.md) documents `self.paths` as the localized paths handle that downstream `prepare_export…` calls rely on. Removing it would break the RU/SBS exporters. **PRESERVE.**
- **N-A — `generate_help_html` signature:** stays as-is because B6.4 does **not** drop `__db_session__`. Keep `main_ru.py:97` / `main_sbs.py:116` calls unchanged.
- **SKIP (cosmetic):** type hints, `make_mdict` collapse, `write_size_dict`/`write_limited_datalist` pathlib+encoding (troubleshooting-only helpers). No recommended edit.

### B6.8 — `gui2/dps_fields.py` → **SKIP** (N-A)
- **Upstream diff (`gui2/dpd_fields.py`):** adds `if not sanskrit_field or sanskrit_field.page is None: return` guards to the Sanskrit clean/focus/search handlers and reorders the `sanskrit_done` flag set (crash fix when the field has no page).
- **Why N-A:** the DPS field set has **no Sanskrit auto-search/focus/clean handlers** — `dps_fields.py` only reads `headword.rt.sanskrit_root_ru_meaning` as a string during `populate`. Per SMD (gui.md → `dps_fields`) upstream's field-automation surface is deliberately not mirrored. No edit.

### B6.9 — `gui2/dps_fields_lists.py` → **SKIP** (N-A)
- **Upstream diff (`gui2/dpd_fields_lists.py`):** uncomments `var_phonetic` / `var_text` inside `COMPOUND_FIELDS`.
- **Why N-A:** the DPS file has **no `COMPOUND_FIELDS`** — it defines `ALL_DPS` (55 `dps_` fields), `VIB_FIELDS`, `CLASS_FIELDS` only (SMD gui.md → `dps_fields_lists`; `rg` confirmed zero `COMPOUND_FIELDS`). No edit.

### B6.10 — `scripts/bash/generate_components.sh` → **SKIP / defer (2d judgement)**
- **Upstream diff (`scripts/bash/generate_components.py`):** prepends `"uv run pytest tests/"` to the `COMMANDS` list and changes blank-line separators to `#` comment separators.
- The `#`-separator change is **N-A** (the local file is Bash, not the Python `COMMANDS` list).
- **The pytest gate is a judgement call for 2d:** mirroring it would make the localized component build run the **full test suite first**. The `.sh` already has `set -e` + an explicit dealbreakers status check. Recommend **SKIP** (avoid gating local RU/SBS builds on the entire suite; the build's existing checks suffice), but flag to the user at the 2d gate in case they want build-time parity.

---

## Stage 2c — HARD STOP (end of Batch 6 — Stage 2c authoring COMPLETE)

Batches 0–6 authored. All shadow/inspired ports and deterministic edits now have FAST-executable
recipes. Next: **Batch 7 = the 2d approval gate** — present the full `dynamic_plan.md` to the user for
proceed / skip / objection per item, then hand off to FAST for Stage 3 (starting Batch 0 = `execute_sync`).

**Decisions to surface explicitly at the 2d gate:**
1. **B6.4 optional help refactors** — backport the zip() bibliography/thanks cleanup and/or drop the
   unused `__db_session__` param (couples to `main_ru`/`main_sbs`)? Default = SKIP both.
2. **B6.10 pytest gate** — add `uv run pytest tests/` to `generate_components.sh`? Default = SKIP.
3. **`exporter/tpr/templates/tpr_headword_ru.jinja`** (from Batch 5) needs registering in
   `registry.json`/SMD (`russian_copies`) — the B5.2 coupled edit touches an unregistered shadow
   (Shadow Documentation Gate). Must land in Stage 3.
4. **B5.8 analogous encoding fix** (6 localized TSV opens in `db_rebuild_from_tsv_dps.py`) is an
   extension-by-analogy (B3.7 precedent), not strict upstream parity — apply it or keep strict-parity
   (L178 only)?

Do NOT in this session: run `execute_sync.py`, copy/edit source files, or begin Stage 3.

---

## Stage 2d — APPROVAL GATE RESOLVED (user, 2026-06-13)

User reply: *"About tests, we can just run the targeted tests for the only local copies
and local files only — maybe to have a separate script which would read the registry and
find corresponding tests and run them for the shadow copies and localized files. All the
rest approved."*

Resolution of the 4 surfaced decisions:

1. **B6.4 optional help refactors → SKIP** (default accepted). No zip cleanup, no
   `__db_session__` drop in `export_help_ru/_sbs`.
2. **B6.10 pytest gate → SKIP** (default accepted). Do NOT add `uv run pytest tests/` to
   `generate_components.sh`. Confirmed with user: the plan already runs ONLY targeted suites
   (`test_shadow_parity`, `test_shadow_cleanup`, `test_namespace_isolation`,
   `test_template_syntax` + `check_shadow_modifications.py` + single-process
   `smoke_test_sync.py`) plus per-file ruff/pyright/single-test VERIFY commands. No
   full-suite `pytest tests/` runs anywhere in Stage 3.
3. **`exporter/tpr/templates/tpr_headword_ru.jinja` → REGISTER** (`russian_copies`) in
   `registry.json` + SMD during Stage 3, same change as the B5.2 coupled template edit.
4. **B5.8 → APPLY-BY-ANALOGY** (approved). Add `encoding="utf-8"` to all 6 localized
   SBS/RU/Tamil TSV reads/writes in `db_rebuild_from_tsv_dps.py`, not just upstream's L178.

**Deferred (Post-Sync Improvement Log):** user's idea of a *registry → corresponding-tests
mapping script* that auto-discovers and runs only the tests for shadow/localized files.
New tooling, out of scope for executing this sync; build AFTER the sync lands. The four
hand-picked shadow suites already cover the localized files for this run.

**Stage 2d COMPLETE. Approved to proceed to Stage 3 = Batch 0 (`execute_sync.py`, Commit 1).**
