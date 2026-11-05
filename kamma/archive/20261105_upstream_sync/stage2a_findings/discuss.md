# Upstream sync discuss analysis, OLD=be49bffe2c2c NEW=c54f942ee3f6 (read-only)

Note: `CLAUDE.md` at repo root is a SYMLINK to `AGENTS.md` (same file). Local AGENTS.md has a condensed "Project Rules (from original upstream)" section plus "Localized Rules".

### 1. .gitignore

Upstream diff (OLD->NEW), every change:
REMOVED: `exporter/chrome_extension/node_modules/`, `exporter/mcp/output/*`, `gui2/data/pass1_auto_*.json` (replaced by narrower globs), `typescript`.
ADDED:
- `exporter/kindle/kindling-cli`
- `exporter/epitaka/output/`
- `exporter/webapp/static/search_index.json.br`, `.json.gzip`, `.json.encodings.json`
- `go_modules/deconstructor/output/worker_tmp_*/`
- `gui2/assets/preview/`
- `gui2/data/pass1_auto_removed_*.json`, `gui2/data/pass1_auto_retired/`, `gui2/data/pass1_auto_text.json`, `gui2/data/user_dictionary_*.txt`, `gui2/data/checked_*.csv`, `gui2/data/manual_corrections_*.tsv`, `gui2/data/variant_readings_*.tsv`, `gui2/data/spelling_mistakes_*.tsv`
- `tools/proofreader.tsv` (+ `.lock`, `.tmp`), `tools/proofreader_checked.json` (+ `.tmp`), `tools/proofreader_meaning_lit.tsv` (+ `.lock`, `.tmp`), `tools/proofreader_meaning_lit_checked.json` (+ `.tmp`), `tools/proofreader_meaning_2.tsv` (+ `.lock`, `.tmp`), `tools/proofreader_meaning_2_checked.json` (+ `.tmp`)
- `kamma/threads/*/benchmarks/results/`
- `newsletter/*/preview.html`, `newsletter/*/preview.tmp`, `newsletter/*/pics/`
- a blank line before `scripts/extractor/extract_cone.tsv` and before `shared_data/changed_headwords`
- `scripts/fix/ati_prefix_to_compound.tsv`
- tail (after `/scripts/fix/pass2exceptions.json`): `/gui2/data/pass2_eg_words.json`, `/gui2/data/pass2_x_words.json`, `/gui2/data/pass2_x_words.json.tmp`, `/gui2/data/pass2_x_words_done.json`, `/audio/mp3_errors`

Local block: `# --- DPS / SBS / RU UNIQUE patterns ---` is at HEAD lines 133-163 (the `.claude/settings.local.json` ... `dpd.db-wal` run). It sits BEFORE the upstream tail section (`# pass2x diagnostic step TSVs` at line 165, `gui2/pass2x/data/`, `/scripts/fix/pass2exceptions.json`). Local also differs from OLD above the block: `.claude/` replaced by `.claude/scheduled_tasks.lock`; added `exporter/mcp/input/*`, `/.qwen`; removed the three `exporter/analysis/*` slash-terminated lines (they reappear without slash in the local block).

Proposed: 3-way merge by hand. Apply all upstream ADDED lines at their upstream positions in the alphabetical part (above the local block); append the 5 tail lines after `/scripts/fix/pass2exceptions.json` (after the local block, end of file). Keep the local block verbatim. Upstream removals: dropping `typescript` and `exporter/chrome_extension/node_modules/` is safe only if those paths no longer exist locally. UNCERTAIN, check `ls exporter/chrome_extension`. `exporter/mcp/output/*`: upstream deleted the mcp exporter (`exporter/mcp/server.py` absent in NEW) but local still has it, so KEEP the local line. KEEP local `.claude/scheduled_tasks.lock` and `exporter/mcp/input/*`.
Risks: low. Do not take upstream's file wholesale (loses the DPS/SBS/RU block). `gui2/data/*` new globs could hide local-tracked files; check `git ls-files gui2/data` matches after merge.

### 2. AGENTS.md (symlinked as CLAUDE.md)

Upstream rewrote and reorganised the whole file. Section-by-section (OLD -> NEW) with proposal:

| Upstream section | Change | Propose |
|---|---|---|
| Intro / Project Overview / Project Specs | condensed; adds "hand the user `just gui`", 4 main parts, `docs/technical/project_folder_structure.md` | DROP (cosmetic; `just gui` is upstream workflow) |
| Kamma (was Kamma Finalize + Checkpoints) | NEW rules: SKIP finalize GitHub step (never comment/close issue); text-only remaining work => finalize at once; checkpoint rule unchanged | DROP (local kamma flow is the fork's own; local rules already cover) |
| Concurrent Threads (working tree safety) | NEW: stage by explicit file list; never `git stash`/`checkout --`/`restore`/`reset --hard`; use `git worktree` | KEEP as a one-line add if absent. Global CLAUDE.md already forbids destructive git; low-cost, applies to our sync process. Optional |
| Python Conventions | merges type hints, Path, icecream, no `sys.path`; NEW: `.gitignore` ignores ALL `__init__.py`, import from concrete module | KEEP the `__init__.py` rule only (applies to any new module in fork); rest already in local |
| SQLAlchemy ORM Objects | reworded, same rule | already local, no change |
| Data (new section) | NEW: WAL mode, don't use dpd.db mtime; `db_tests` draft entries are editor checklist; gui2 tests tab rewrites `db_tests_columns.tsv` CRLF; git-tracked data files in `pali_sort_key` order; live-db rule (unchanged) | KEEP WAL/mtime rule (affects our `dpd.db-wal` ignores and sync checks). KEEP sorted-order rule only if fork writes tracked data files (UNCERTAIN). DROP db_tests / gui2 tests-tab items (contributor/editor workflow) |
| Database Model | table trimmed; NEW: empty-string gotcha `inflections_list_all`; contributor corpus slim / `is_headless_server`; playwright-cli gui2 driving; weekly docs checks | KEEP empty-string gotcha only. DROP contributor server and playwright items |
| Shared Tools | db_helpers/configger/printer compressed into prose | DROP (local CLAUDE.md already has a printer section) |
| Go | adds `go run ./go_modules/<pkg>` rule, frequency table positional rule, deconstructor manual_corrections two readers | DROP (we do not maintain Go builds; per rule) |
| Dependencies | adds `uv add/remove --no-sync` then `uv sync --all-groups` (tools group otherwise uninstalled); script hand-off format `uv run <path>.py` | KEEP the `--no-sync` + `uv sync --all-groups` line (pyproject sync step uses it). Rest already in local |
| Docs Lookups | Flet 1.0 dialogs, web reload, preview, Context7 list | DROP Flet 1.0 items unless we adopt Flet 1.0 (see gui2/main.py); local CLAUDE.md keeps Flet-docs and Context7 lines |
| Testing / Pre-commit gate | NEW: gui2/tests/cst_source need `pyright --project /dev/null`; ruff `--no-force-exclude` for cst_source; skip ruff format on `.json`; **NEW `just typecheck` (pyrefly) section** | KEEP the pyright `--project /dev/null` note and the "skip ruff format on .json fixtures" line (apply to files we touch). Pyrefly: local already mandates pyrefly in Pre-Completion Validation; DROP `just typecheck` / CI details (upstream CI) but note upstream now lists pyrefly in `[dependency-groups].dev` |
| GitHub | commit-format rule kept; NEW: never write to GitHub issues unless asked; automated "data update" commit may re-track `git rm --cached` file | DROP (fork uses its own sbs issue mapping; global CLAUDE.md covers commit rules) |
| Performance Work | adds webapp threading/GIL benchmark rule; `lookup` INSERT OR REPLACE and ORM-loop rules kept | DROP the GIL rule (webapp benchmarking). `INSERT OR REPLACE` rule already local |
| Export Flags | NEW: local justfile `export-mobile` vs `build-db` must pass same flags | DROP (upstream mobile/Flutter workflow) |
| other-dictionaries submodule | extra rules: licence terms, ship `.tar.zst` for CI | DROP (submodule maintenance) |
| tipitaka translation db submodule | NEW submodule commit/pointer rules | DROP (submodule maintenance; local Commit Scope already excludes `resources/` pointers) |
| Public Page Copy | NEW promises/no-money/contribution form naming | DROP (upstream website content) |
| CI Workflows | NEW: check default branch before hardcoding; sc-data deletes files in draft_release; test `run:` blocks | DROP (upstream release CI). Possibly relevant only if fork uses these workflows; UNCERTAIN |
| graphify | updated counts, `graphify affected`, `.graphifyignore` load-bearing, prune snapshots | KEEP only if fork uses graphify (UNCERTAIN; local .gitignore has `/graphify-out`). Otherwise DROP |

Local CLAUDE.md "Project Rules (from original upstream)" lines that need updating or removing:
- `## Dependencies / Optional/transitive deps ...` - upstream condensed but did not change the rule; no change.
- `## Flet - When answering questions about Flet refer to /resources/flet-docs` - upstream now says `resources/flet-docs` (no leading slash), same meaning; no change. But upstream moved to Flet 1.0.1; if fork does not move, the `/resources/flet-docs` content may describe 1.0 (UNCERTAIN, verify folder version).
- `## Context7` - unchanged (upstream folded it into Docs Lookups).
- `## Tools/printer.py` - upstream compressed the API description; local pointer to `tools/printer.py` still valid.
- `## Data Verification` - unchanged in upstream (now inside "Data").
- `## Testing` (slow tests) - unchanged in upstream.
- `## Pre-commit gate` - upstream added the three notes above (pyright excludes, `.json` fixtures, `ruff --no-force-exclude`); add as concise bullets.
- `## Performance Work` - unchanged for `INSERT OR REPLACE`.
- `## GitHub (upstream repository)`: upstream now forbids ALL GitHub issue writes unless asked; local says only repo + "Solve" flow. Optional align (global rules already forbid autonomous publish).
- Nothing in upstream was REMOVED that local CLAUDE.md still states, except: upstream removed the `## Tree` weekly-check and `## Database model` weekly-check headings as separate sections (merged into "Database Model" last bullet). Local CLAUDE.md does not carry those lines, so nothing to delete.
- The old upstream `Kamma Finalize` GitHub-comment step is now explicitly SKIPPED upstream; local CLAUDE.md does not mention it.
Proposed: do NOT take the upstream file. Keep local file; add at most 4-6 concise bullets into "Project Rules (from original upstream)" (Concurrent Threads git-safety line, `__init__.py` rule, WAL rule, `uv --no-sync` rule, pyright `--project /dev/null`, `.json` ruff-format exception). Never touch "Localized Rules".
Risks: wholesale overwrite deletes all of Localized Rules and the symlinked CLAUDE.md content (Shadow Documentation Gate, Atomic Rename, Blast-Radius, Clean Root). Low risk if additive only.

### 3. db/models.py

Upstream hunks (OLD->NEW, +137/-11):
1. Import: `from sqlalchemy import DateTime, ForeignKey, Index, and_, case, null` (adds `Index`). Local line 10 is `... and_, case, null, or_` plus line 11 `Column, Integer`; add `Index` there.
2. `Lookup`: adds `__table_args__ = (Index("ix_lookup_key_nocase", lookup_key.collate("NOCASE")),)` after the `thai` column. SCHEMA CHANGE (new index).
3. New module-level constants before `class SuttaInfo`: `_S4NT_KN_BOOKS` (frozenset) and `_S4NT_ANCHOR_OVERRIDES` (45-entry dict). No schema effect.
4. `SuttaInfo.sc_book_code`: regex `r"\d+\.*-*\d*"` -> `r"\d.*"`.
5. `SuttaInfo.dhamma_gift`: `https://find.dhamma.gift/read/?q=` -> `https://dhamma.gift/{sc_code.lower()}`; another link `find.dhamma.gift/bw/...` -> `f.dhamma.gift/bw/...` (two places, iti and generic).
6. New `SuttaInfo.s_4nt_link` cached_property (s.4nt.org links). No schema effect.
7. `SuttaInfo.dv_exists`: drops `self.dv_pts` from the OR chain (column `dv_pts` itself NOT removed).
8. `# pyrefly: ignore` comment above `transliterate.getmembers = lru_cache(...)`.
9. `DpdHeadword.lemma_1`: now `mapped_column(ForeignKey("sutta_info.dpd_sutta"), unique=True, default="")`. SCHEMA CHANGE (UNIQUE constraint).
10. Comment `# TODO DELETE ON NEXT DB MODEL CHANGE` above `variant` column (data migrated to `var_text` on 2026-07-25; column now empty, kept for now). No schema change yet, but a future drop is flagged.
11. `lemma_ipa`: two dead comment lines removed.

SCHEMA: YES, two DDL-level changes, no columns or tables added, removed or renamed:
- new index `ix_lookup_key_nocase` on `lookup(lookup_key COLLATE NOCASE)`; the live `dpd.db` has only `sqlite_autoindex_lookup_1`, so it needs a rebuild (the `create_all` path will not add an index to an existing table) or a manual `CREATE INDEX`. Not blocking functionality.
- UNIQUE on `dpd_headwords.lemma_1`. **BLOCKER FOUND IN LIVE `dpd.db`**: 89154 rows, 89153 distinct `lemma_1`; duplicate is `hatthaka 3` (ids 70815 `masc` and 70816 `adj`). A rebuild from local data with `unique=True` will fail with an IntegrityError. Upstream NEW backup shows `70814 hatthaka 1`, `70815 hatthaka 4`, so upstream renamed/fixed it. The local `dpd_headwords` data (or `db/backup_tsv`) must pick up that fix first (UNCERTAIN whether local TSVs are updated by the data sync; verify duplicates with `cut -f2 ... | sort | uniq -d` on the local TSV parts after sync).
Proximity to local tables: none of the hunks touch SBS/Russian/Tamil/Sinhala classes or the `.sbs/.ru/.ta/.si` relationships or `DpdRoot/FamilyRoot` `*_ru` columns. `SBS`, `Russian`, `Tamil`, `Sinhala` FK to `dpd_headwords.id` only, not `lemma_1`, so the UNIQUE change does not affect them. The `variant` TODO affects `Lookup.variant` NOT, that is a different column (Lookup.variant at local line 245 untouched). Local SBS hybrid properties that read `variant`: UNCERTAIN, grep `.variant` in `sbs_table_functions` / SBS class before any future drop.
Proposed: apply as a patch to local file (not wholesale): hunks 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 are all independent of local blocks. Local import line merge needed for #1 (local has extra `or_` and a `Column, Integer` import). Also the local file may differ in whitespace from upstream (local diff vs OLD is +710 lines of local-only classes), so `git merge-file` 3-way with OLD as base should apply cleanly. Re-run `uv run pytest tests/test_...` for SuttaInfo links if present (UNCERTAIN: tests exist). After merge a DB rebuild (or at least `lookup` index creation) is recommended, but first fix the `hatthaka 3` duplicate.
Risks: HIGH only for the unique constraint on rebuild; link-URL changes (`dhamma.gift`, `s.4nt.org`) change exporter/GUI output; `sc_book_code` regex change alters return values for codes like `SN12.83-92` (now `SN` instead of `SN` plus stray chars; fine), grep callers (`grep -rn sc_book_code` in non-resources .py) before finalising (not done here).

### 4. gui2/main.py

Upstream changes (OLD->NEW, +568/-124) = Flet 1.0 migration plus contributor-server features:
- Imports added: `asyncio`, `threading`, `Callable`, `Any`, `gui2.ai_search_window.launch_ai_search_window`, `gui2.contributor_tabs.allowed_tabs/resolve_extra_tabs`, `gui2.shortcuts_dialog`, `gui2.spelling_find_replace_view.SpellingFindReplaceView`, `gui2.ui_utils.cancel_top_dialog/is_dialog_open/show_global_snackbar`, `tools.printer.printer as pr`, `tools.server_mode.is_headless_server`. Still `from tools.fast_api_utils import start_dpd_server` (local keeps `fast_api_utils_dps`, confirmed at local line 12).
- New module-level `TAB_LABELS` (17 labels) and `tab_selection()`.
- `App`: `_visible`, `_read_only`, `_WARMUP_TAB_ORDER`, lazy view builders `_view_builders` dict keyed by tab index (replaces eager `self.*_view` attributes), background db init + warm-up, `_build_lock`, loading bar, `page.theme_mode = DARK`, `page.show_dialog/pop_dialog` (was `page.open/close`), `await self.page.window.close()`, async `on_keyboard`, new shortcuts (Escape, Alt+jump keys, Alt+X clear, Alt+? popup, Page Up/Down scroll), `_current_index()`, `_on_tab_activated`, `_tab_label`, `claim_session/release_session`, FastAPI server now started AFTER `App(page)`, `ft.app(target=main)` -> `ft.run(main)`.
- Tabs: 1.0 API `ft.Tabs(content=Column[loading bar, TabBar, TabBarView], length=, on_change=)`; `ft.Tab(label=...)` with no content.
- Removed: `tab_clicked`, `tab_to_view` dict (replaced by `_current_index()` + `index in (3, 7)`), `ai_search_popup` use, eager view attributes.

Local tab order at HEAD (16 tabs, from `ft.Tab` lines 258-318): 0 Global, 1 Transl, 2 Pass1Auto, 3 Pass1Add, 4 Pass2Pre, 5 Pass2x, 6 Pass2Auto, 7 Pass2Add, 8 DPS, 9 `'`, 10 Sandhi, 11 DB, 12 Tests, 13 Bold Search, 14 √, 15 CT. Local `tab_to_view = {3: pass1_add_view, 7: pass2_add_view}` (line 229) is unaffected by DPS because DPS follows index 7.
NEW upstream order (17 tabs, `TAB_LABELS`): 0 Global, 1 Transl, 2 Pass1Auto, 3 Pass1Add, 4 Pass2Pre, 5 Pass2x, 6 Pass2Auto, 7 Pass2Add, 8 `'`, 9 Sp (NEW), 10 Sandhi, 11 DB, 12 Tests, 13 Bold Search, 14 √, 15 CT, 16 Infl (NEW).
Local-confirmed items: `fast_api_utils_dps` import, `DpsView` import inside `App.__init__` (line 57) and `self.dps_view` (line 133), `DpdTextField` import + `_make_font_scaler` patch of `ft.Text/TextStyle/TextField/Dropdown.__init__` with `_DPS_FONT_SCALE = 1.4` (module level after imports).

Index map recomputation: upstream no longer has a `tab_to_view` dict; every index-based table is keyed by "tab index" = position in `TAB_LABELS` (`_view_builders`, `_TAB_JUMP_KEYS`, `_CLEAR_ACTIONS`, `_WARMUP_TAB_ORDER`, `_get_current_lemma` `(3, 7)`, `7 in self._visible` for the word finder, `start_index` 3). Two safe options:
(a) RECOMMENDED: add DPS at the END as index 17 (`TAB_LABELS.append("DPS")`, `_view_builders[17] = lambda: DpsView(...)`, optional `_WARMUP_TAB_ORDER` entry 17, optional `_TAB_JUMP_KEYS["P"]` conflict avoided - pick a free key e.g. "H"). No existing index changes, so `allowed_tabs`, `_CLEAR_ACTIONS` etc. stay valid, and contributor_tabs (label based) never sees DPS. Changes tab position (DPS moves from after Pass2Add to last).
(b) Keep DPS after Pass2Add: insert `"DPS"` at index 8 in `TAB_LABELS`, then renumber every upstream key >=8 by +1: `_view_builders` (8->9 ... 16->17), `_TAB_JUMP_KEYS` (`'`:8->9, S:9->10, D:11->12, B:13->14, R:14->15, C:15->16, I:16->17), `_CLEAR_ACTIONS` (8..16 -> 9..17), `_WARMUP_TAB_ORDER` (8..15 -> 9..16), `_get_current_lemma` (3,7 unchanged), the hard-coded `7` stays. Keys 0-7 unchanged. 10 maps to touch; high error rate.

Other required local re-applications: change `start_dpd_server` import to `fast_api_utils_dps`; re-add font scaler block; re-add `DpsView` to `_view_builders`. Existing local `tools/fast_api_utils_dps.py` and the font scaler patch of `ft.Text.__init__` etc. are written for Flet 0.28 and UNCERTAIN under Flet 1.0 (controls are dataclasses; patching `__init__` and `ft.TextStyle.__init__` may not scale). `gui2/dps_*.py` use the 0.28 API (`page.open/close`, `ft.app`); upstream rewrote 84 gui2 files (+10042/-1773) for Flet 1.0.1 (see pyproject). So taking the new main.py requires ALL gui2 files (including DPS ones) to be on Flet 1.0 or the app will not start.
Proposed: DO NOT merge main.py alone. Decision for the user: adopt Flet 1.0 across gui2 (then take upstream main.py and apply: fast_api_utils_dps import, DPS tab via option (a), re-validate font scaler, port `dps_*.py` to 1.0) or pin gui2 at Flet 0.28 (then do not take upstream main.py or gui2 tree; pyproject must keep `flet[all]==0.28.3`).
Risks: very high (app startup, DPS tab breakage, font scaler no-op or crash). Full end-to-end launch required.

### 5. pyproject.toml

Upstream OLD->NEW:
- `authors` name: `Bodhirasa` -> `Bodhirasa Bhikkhu`.
- `[project].dependencies` ADDED: `filelock>=3.29.1`, `regex>=2026.5.9`, `starlette>=1.2.1`, `anyio>=4.13.0`, `css-inline>=0.23.0`, `pillow>=12.3.0`, `brotli>=1.2.0,<2`.
- `[dependency-groups].dev` ADDED: `pyrefly>=1.1.1`.
- `tools` group REMOVED: `openai>=1.54.4`, `gitpython>=3.1.43`, `fuzzywuzzy>=0.18.0`, `mcp>=1.6.0`, `google-api-python-client>=2.167.0`, `google-auth-httplib2>=0.2.0`, `google-auth-oauthlib>=1.3.0`, `markdownify>=1.2.2`, `prompt-toolkit>=3.0.52`.
- `tools` group CHANGED: `flet[all]==0.28.3` -> `flet[all]==1.0.1`.
- `tools` group ADDED: `thefuzz>=0.22.1`, `google-api-core>=2.43.0` (with comment).
- `[tool.pyrefly]` section + `[[tool.pyrefly.sub-config]]` (tests/**) + `[tool.pyrefly.sub-config.errors]` added.
- `[tool.deptry]` + `[tool.deptry.per_rule_ignores]` added.
- Unchanged: ruff, pyright config, pytest.

Local HEAD vs OLD: only +2 lines in `[project].dependencies`: `num2words>=0.5.14`, `pyrefly>=1.1.1`. Everything else equals OLD.
Genuine local-only: `num2words>=0.5.14` (used by `scripts/change_in_db/update_yojana_km.py`). `pyrefly>=1.1.1` is now UPSTREAM (in `dev` group), so DROP the local copy from `[project].dependencies` to avoid duplicating (move to upstream's dev entry). Pyrefly config blocks come with the take.
Deps removed upstream but still imported by files that exist locally (UNCERTAIN, not all verified to still be in use; all are local-only or fork files absent from NEW):
- `openai`: `tools/ai_open_router.py`, `tools/ai_nvidia.py`, `kamma/translate/scripts/ai_batch_openai_meaning.py`, `scripts/dps_archive/*`
- `gitpython` (`git.Repo`): `db/backup_tsv/backup_dps.py`, `db/backup_tsv/backup_dpd_headwords_and_roots.py` (local copy; upstream NEW version of the latter no longer imports git)
- `mcp`: `exporter/mcp/server.py` (deleted upstream)
- `google-api-python-client`, `google-auth-oauthlib`, `markdownify`: `scripts/build/newsletter_scraper.py`
- `prompt-toolkit`: `scripts/fix/fix_synonym_entries.py`
- `fuzzywuzzy`: local `tools/fuzzy_tools.py` imports `fuzzywuzzy`; upstream NEW `tools/fuzzy_tools.py` imports `thefuzz`, so take upstream's file together with pyproject.
Proposed: take upstream `pyproject.toml`, then (1) remove local `pyrefly>=1.1.1` from `dependencies` (now in dev), (2) re-add `num2words>=0.5.14` to `[project].dependencies`, (3) for each removed dep above still needed by a fork-local file, re-add it to the `tools` group (needs a decision per file; a dead file should instead be archived), and optionally add a `[tool.deptry]` DEP002 note. Then `uv lock` + `uv sync --all-groups` (use `--no-sync` for `uv add`, per upstream rule).
Risks: Flet 1.0.1 pin is the big one (see section 4); `gui2` will not run against 0.28 code. If the fork does not adopt Flet 1.0, keep `flet[all]==0.28.3`, `fuzzywuzzy` etc. and do NOT take upstream gui2.

### 6. tools/ai_models.json (PRESERVE)

Top-level keys:
- OLD: `antigravity_cli_work_models`, `default_models`, `grounded_models`
- NEW upstream: `default_models`, `grounded_models` (the `antigravity_cli_work_models` key was REMOVED upstream)
- Local HEAD: `antigravity_cli_work_models`, `default_models`, `grounded_models` (matches OLD)
Upstream NEW `tools/ai_manager.py` reads only `data.get("default_models")` and `data.get("grounded_models")` (lines ~33-34, via `ProjectPaths().ai_models_json_path`), no new key. Upstream now derives agy probe targets from `antigravity_cli` entries inside `DEFAULT_MODELS` (not from a separate key). Each entry may carry optional `timeout`.
Local `tools/ai_manager.py` (HEAD, line 24) still reads `antigravity_cli_work_models`; `kamma/translate/scripts/batch_runner.py:65` and `exporter/analysis/README.md:110` document it, so local key must STAY. `tools/ai_manager.py` is presumably a registered shadow (UNCERTAIN, check registry), so if upstream ai_manager.py is taken, the local `antigravity_cli_work_models` consumer is lost; local needs the work-models list loaded as before.
Proposed: keep local JSON untouched; no new key needed from upstream. Only action: if `tools/ai_manager.py` is replaced with upstream's, re-apply the local `antigravity_cli_work_models` read. Update registry note ("top-level keys share upstream schema") to say upstream dropped `antigravity_cli_work_models`.
Risks: low for the JSON; moderate for ai_manager.py replacement.
