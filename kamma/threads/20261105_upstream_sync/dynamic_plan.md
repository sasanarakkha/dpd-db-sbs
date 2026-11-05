# Dynamic Plan: Upstream Sync 2026-11-05

- **Range**: `be49bffe2c2c` → `c54f942ee3f6` (`upstream/main`, 530 commits, 592 changed / 202 deleted paths)
- **Upstream themes**: gui2 **Flet 0.28.3 → 1.0.1** migration + contributor-server features (#215,
  84 gui2 files); Kindle **kindlegen → kindling**, form-keyed entries (#217); webapp licence/permalink,
  NOCASE lookup (#277), regex deadlines, lookups_take_turns middleware; TBW Legacy toggle `show_tbw`
  (#252); s.4nt.org links; family singular/plural headings; deconstructor submodule retired
  (`resources/deconstructor_output` → Go/decon cache); inflection templates xlsx → `db/inflections/templates/*.tsv`;
  AI providers consolidated into `tools/ai_openai_compat.py`; TPR monthly export stopped (#279);
  epitaka exporter, newsletter tooling, `scripts/server_contrib/`; tests/ reorganised.
- **Sub-stage status**: 2a classification COMPLETE · 2b discuss COMPLETE (D1–D12 RESOLVED 2026-11-05) · 2c literal edits COMPLETE (§9A–§9F written; session 6) · **2d APPROVED (user, 2026-11-05: "proceed all" — ⚠ 2c-DEVIATIONs D1, D3, B2, §6/A0 correction, 9, 10, 11 all APPROVED; plan approved for Stage 3)**
- **Evidence**: per-domain diff analyses (Stage 2a subagents, verified spot checks by ADVANCED) in
  `stage2a_findings/{webapp,kindle,goldendict,gui_tools_scripts,discuss}.md`. 2c authors literal
  recipes from those + the raw diffs (`git diff be49bffe2c2c c54f942ee3f6 -- <path>`).

---

## 0. Execution mechanics (carry-over facts, see 20260709 plan §0)

1. `execute_sync.py` restores worktree from upstream, then restores `modified_upstream_files` +
   `no_sync_files` + `run_exclusions.txt`. Shadows/inspired/unique files are untouched by checkout.
2. P0 deletion pass covers ALL in-range upstream deletions (`--diff-filter=D`, whole tree incl.
   `tests/`), skipping protected (registered) paths. All 19 `unregistered_local_paths` and 182/183
   `upstream_deleted_orphans` are IN RANGE → P0 deletes them (delete-to-match). Only
   `exporter/sutta_central/sc_dict.json` is pre-range (see §6).
3. Discuss gate: after 2b, any registry edit + `prep_analyzer.py` rerun regenerates `discuss_paths`;
   sequence: registry edits → rerun prep → clear `discuss_paths` to `[]` → write
   `run_acknowledged_blockers.txt` → `execute_sync.py`.
4. Blocker acknowledgement: both blockers resolved by analysis (§1) — list both in
   `run_acknowledged_blockers.txt`.

## 1. Blockers (resolved by analysis — no user decision needed)

### B1. `exporter/kindle/templates/ebook_deconstructor_entry.jinja` — ACKNOWLEDGE, delete-to-match
Upstream deleted it in a441f918c (#217: deconstruction folded into headword/form entries). The
manifest maps it to `ru_components/templates/ebook_deconstructor_entry.jinja`, which does NOT exist;
the real RU template is `ebook_ru_deconstructor_entry.jinja`, still used by
`render_deconstructor_entry_ru` in `kindle_exporter_ru.py`. → P0 deletes only the upstream copy; RU
template untouched (unless D6 ports #217).

### B2. `scripts/server/update-dpd.sh` — MOVE upstream → `scripts/server_dpdict/update-dpd.sh`
Local copy is byte-identical to OLD upstream; only registry/thread files reference it. → P0 deletes
it; repoint registry `sbs_copies["scripts/server/update-dpd-sbs.sh"].upstream` →
`scripts/server_dpdict/update-dpd.sh`; port into `update-dpd-sbs.sh` (S-list S12): `set -euo pipefail`,
`update_tmp` temp dir + trap, `uv cache prune`, headword-count sanity check, atomic `mv`. SKIP
docs-site pull and `prepare_webapp_lookup.py` line (paired with D11 webapp decision).

---

## 2. DISCUSS items (resolve in 2b, one at a time)

### D1. `.gitignore` — merge, preserve DPS/SBS/RU block (HEAD lines ~133-163)
Upstream adds: proofreader + gui2/data globs, `search_index.json.br/.gzip/.encodings.json`,
newsletter + kamma benchmark globs, `kindling-cli`, epitaka output, 5 tail lines. Removes:
`typescript`, `exporter/chrome_extension/node_modules/`, `exporter/mcp/output/*`.
**Proposed**: apply all upstream adds/removes (incl. dropping `exporter/mcp/output/*` — `exporter/mcp/`
is deleted by P0, it is unregistered); local block untouched.
**RESOLVED (2b, 2026-11-05): take upstream `.gitignore` verbatim** for every upstream-owned line
(all adds + all removes, incl. `exporter/chrome_extension/node_modules/`, `exporter/mcp/output/*`,
`typescript`). Also DROP local stray `exporter/mcp/input/*` (line ~74, not in upstream). Keep the
`# --- DPS / SBS / RU UNIQUE patterns ---` block as-is. Rationale (user): `exporter/chrome_extension/`
and `exporter/mcp/` are pure-upstream folders with no local use — `skip_sync_patterns` excludes them
from Stage 1 analysis only, they still sync (guide.md:478). Upstream moved both to
`archive/exporter/{chrome_extension,mcp}/` (6aa93a8dd, R100) — `archive/` is not `no_sync`, so the
pull brings them there; nothing local to preserve. `gui2/data/pass1_auto_{dhp,dhpa}.json` are tracked,
so upstream's narrowed `pass1_auto_*` globs do not affect them.

### D2. `AGENTS.md` (`CLAUDE.md` is a symlink to it) — scope-filtered merge
Upstream rewrote its AGENTS.md (+125/-242). No upstream rule currently mirrored in our "Project
Rules (from original upstream)" was removed.
**Proposed KEEP** (govern maintained files/our process): git-safety (no `stash` / `checkout --` /
`reset --hard`); "`.gitignore` ignores all `__init__.py`"; `uv add --no-sync` + `uv sync --all-groups`;
`pyright --project /dev/null` for gui2/tests/cst_source; don't `ruff format` `.json`; WAL/mtime rule
(2c verifies wording/applicability). **DROP**: Go, submodules, CI, Export Flags, Public Page Copy,
contributor-server, webapp GIL sections. Full section list: `stage2a_findings/discuss.md` §2.
**RESOLVED (2b, 2026-11-05): additive merge, do NOT take upstream file.** `AGENTS.md` is on
`modified_upstream_files`/restore path — keep local; add concise bullets ONLY inside
`# Project Rules (from original upstream)`; `# Localized Rules` untouched. Add (2c writes exact text):
1. Git safety: never `git stash` / `git checkout -- <path>` / `git restore` / `git reset --hard`;
   stage by explicit file list (concurrent sessions share the tree).
2. `.gitignore` ignores all `__init__.py` (local line 20) → import from concrete module.
3. `dpd.db` is WAL mode → never use file mtime to decide whether the db changed.
4. `DpdHeadword.inflections_list_all` may yield `""` → filter before dict keys / set members.
5. `uv add`/`uv remove` with `--no-sync`, then `uv sync --all-groups` (upstream `tools` group, via D5).
6. Pre-commit gate: `uv run pyright --project /dev/null <file>` for `gui2/`, `tests/`,
   `tools/cst_source/` (all in `[tool.pyright].exclude`); `ruff check/format --no-force-exclude` for
   `tools/cst_source`; never `ruff format` `.json` fixtures.
7. Flet 1.0 dialog rule (`dialog.open = False` leaves instance on `page._dialogs` → guard reopen;
   Escape handled by `cancel_top_dialog` in `gui2/ui_utils.py`); update local `## Flet` line to note
   gui2 runs Flet 1.0.1 (D4a).
CONFLICTS — keep local, do NOT import: upstream "NEVER `Path(__file__).resolve().parents[n]`" (local
Path Anchoring rule wins); upstream "don't run scripts with uv unless asked" (local validation uses
`uv run`). DROP: Go, submodules, Export Flags, Public Page Copy, CI Workflows, contributor/playwright/
web-mode gui2 notes, GIL rule, upstream Kamma rules, graphify (not used locally), db_tests CRLF and
`pali_sort_key` rules, `just typecheck`.

### D3. `db/models.py` — apply upstream hunks; DATA PRECONDITION
No column/table add/remove/rename. Hunks: new `ix_lookup_key_nocase` index on `lookup` (#277);
`unique=True` on `DpdHeadword.lemma_1`; `SuttaInfo` URL/regex changes; new **`s_4nt_link`** property;
pyrefly comment. Nothing near SBS/Russian/Tamil/Sinhala tables.
**Hard dependency**: upstream webapp/goldendict code pulled verbatim + ported templates use
`d.su.s_4nt_link` → this merge is REQUIRED, not optional.
**Data risk**: live `dpd.db` has duplicate `lemma_1` `hatthaka 3` (ids 70815, 70816); upstream renamed
70815 → `hatthaka 4`. A rebuild with `unique=True` fails until fixed. Index needs creating on the
existing db (rebuild or `CREATE INDEX`).
**Proposed**: apply all hunks; before any rebuild, fix id 70815 lemma_1 → `hatthaka 4` (via data
pipeline, user's call); create the NOCASE index on live db (2c gives exact SQL).
**RESOLVED (2b, 2026-11-05): apply all upstream hunks verbatim + one-time live-db SQL in Stage 3
(after the pull):**
```sql
UPDATE dpd_headwords SET lemma_1 = 'hatthaka 4' WHERE id = 70815 AND lemma_1 = 'hatthaka 3';
CREATE INDEX IF NOT EXISTS ix_lookup_key_nocase ON lookup (lookup_key COLLATE NOCASE);
```
Evidence: only duplicate `lemma_1` in live db is `hatthaka 3` (70815 masc, 70816 adj); upstream
`db/backup_tsv/dpd_headwords_part_*.tsv` (in range) already renames 70815 → `hatthaka 4`, so a
TSV rebuild is clean; `unique=True` only bites on table create. Live `lookup` currently has only
`sqlite_autoindex_lookup_1`. RU/SBS tables key on `id` → unaffected. 2c TODO: grep local
exporters/data for literal `hatthaka 3` before running the UPDATE.

### D4. gui2 Flet 1.0 migration + `gui2/main.py` — ARCHITECTURE FORK (biggest decision)
Upstream migrated all of gui2 to Flet 1.0.1 (`ElevatedButton`→`Button`, `ft.padding/alignment/border.*`
→ classes, Dropdown `on_change`→`on_select`, `.focus()`→`request_focus()`, `field_border()`, no
`self.page=` in Column subclasses), plus lazy tab building, new Sp/Infl tabs, contributor-server
features. Old `tab_to_view` map replaced by index-keyed tables (`_view_builders`, `_TAB_JUMP_KEYS`,
`_CLEAR_ACTIONS`, `_WARMUP_TAB_ORDER`). Unregistered gui2 files are pulled verbatim → they WILL be
Flet 1.0 code. Local 0.28-style files: `gui2/main.py` (registered), `dps_example_field`,
`dps_meaning_field`, `dps_fields`, `dps_view`, `dps_test_manager`, `dps_field_mapping` (+ other
`dps_*.py`). Font-scaler monkeypatch may not survive Flet 1.0 (UNCERTAIN).
**Options**:
(a) **Adopt Flet 1.0** — take upstream `pyproject` pin, merge `gui2/main.py` by appending DpsView as
the LAST tab (index 17, no upstream index renumbering), migrate every `gui2/dps_*.py` to the 1.0 API,
re-verify font scaler. Largest Stage 3 item; requires a GUI manual test.
(b) **Freeze gui2 at 0.28** — keep `flet[all]==0.28.3`, add all upstream gui2 changes to
`run_exclusions.txt` (gui2 stays at previous sync state), skip `gui2/main.py` merge. Diverges further
each sync; upstream gui2 bugfixes lost.
**Recommendation**: (a) — gui2 is an upstream area and freezing it only defers a bigger migration.
(Prior local track `conductor/tracks/flet_1_0_migration_20260217/` may contain prep work — 2c reads it.)
**RESOLVED (2b, 2026-11-05): (a) Adopt Flet 1.0.** Prior conductor track checked: status `new`, never
started, planned a `gui3` worktree + composition refactor superseded by upstream's migration → stale,
no reusable prep. Consequences: D5 takes upstream pyproject (`flet[all]==1.0.1`); D10 proceeds as
proposed; S2/S22 go ahead; Stage 3 migrates `gui2/main.py` merge (DpsView appended as index 17) +
all `gui2/dps_*.py` to the 1.0 API; font-scaler re-verified at runtime; manual GUI test required.

### D5. `pyproject.toml` — merge (depends on D4)
Upstream adds runtime: filelock, regex, starlette, anyio, css-inline, pillow, brotli, thefuzz,
google-api-core; `pyrefly` in dev group; `[tool.pyrefly]`, `[tool.deptry]`; `flet[all]==1.0.1`.
Removes: openai, gitpython, fuzzywuzzy, mcp, google-api-python-client, google-auth-httplib2,
google-auth-oauthlib, markdownify, prompt-toolkit.
Local-only to re-apply: `num2words>=0.5.14` (drop our `pyrefly>=1.1.1`, now upstream dev dep).
**Removed deps still used by surviving LOCAL files** (need a call each):
- `gitpython` — `db/backup_tsv/backup_dps.py` (live DPS backup script; uses `git.Repo` commit). Options:
  re-add `gitpython` with owner comment, or port to `subprocess git` like upstream did (S-item).
- `openai` — `kamma/translate/scripts/ai_batch_openai_meaning.py`; `tools/ai_nvidia.py` (skip-pattern
  local file; upstream ai_manager no longer imports it → dead). Re-add `openai` or retire those files.
**Proposed**: take upstream wholesale (per D4a), re-add `num2words`; re-add only deps the user
confirms for the files above (with owner comments per CLAUDE.md dependency rule); `uv lock` +
`uv sync --all-groups`.
**RESOLVED (2b, 2026-11-05):** take upstream `pyproject.toml` wholesale (flet 1.0.1, new deps,
`tools` group, pyrefly in dev, `[tool.pyrefly]`/`[tool.deptry]`); re-add `num2words>=0.5.14`
(registered unique `scripts/change_in_db/update_yojana_km.py`); drop local runtime `pyrefly>=1.1.1`.
Removed deps — post-pull users checked:
- fuzzywuzzy, mcp, google-api-python-client, google-auth-*, markdownify, prompt-toolkit → all users
  deleted upstream in range (P0) → drop.
- **gitpython → drop; PORT** upstream's `git.Repo` → `subprocess.run(["git","commit","-m",...,"--",*files])`
  change from `backup_dpd_headwords_and_roots.py` into shadow `db/backup_tsv/backup_dps.py` (strict
  parity; new S-item, 2c writes literal edit; update its registry `local_changes`/`watch_for` if needed).
- **openai → drop; RETIRE (user chose a)**: `git mv kamma/translate/scripts/ai_batch_openai_meaning.py`
  and `tests/kamma_tests/translate/test_ai_batch_openai_meaning.py` → `archive/dps/` (no references
  outside kamma/improve notes; `tools/ai_nvidia.py` deleted upstream in range; `ai_openai_compat.py`
  uses `requests`). Update registry if either path is listed; run `validate_registry.py`.
Then `uv lock` + `uv sync --all-groups`.

### D6. Kindle #217 (kindlegen → kindling, form-keyed entries) — port to RU or not
RU exporter (`kindle_exporter_ru.py`) forks the OLD architecture (own `ebook_ru_*.jinja`, no KindleData).
Pulled shared modules do NOT break it (`data_classes.py` unchanged; `RuPaths.kindlegen_path` is ours).
But upstream deleted `exporter/kindle/kindlegen` (tracked binary, P0 would delete it) and
`kindle_exporter_ru.py:364` still runs it on non-Darwin; RU also keeps the homonym-loss bug #217 fixed.
**Options**: (a) minimal — keep `exporter/kindle/kindlegen` (add to `run_exclusions.txt` or register
in `unique_paths`/protected), port only trivial template/CSS bits (S-list); (b) full #217 port (new RU
form-entry template, aliases, OPF `remote_pages`/`dc:type`, RU `toc.ncx`, kindling in
`ru_release_kindle.yml`) — large, own thread.
**Recommendation**: (a) now; open a separate kamma thread for (b).
**RESOLVED (2b, 2026-11-05): (a) minimal.** Register `exporter/kindle/kindlegen` in registry
`unique_paths` BEFORE `execute_sync.py` (so P0 skips it; note "RU Kindle CI converter until #217
port"); verified RU non-Darwin `make_mobi` (`kindle_exporter_ru.py:362-370`) runs it, used by
`ru_release.yml`, `ru_release_test.yml`, `ru_release_kindle.yml`. PORT trivial:
`<body>` → `<body epub:type="dictionary">` in `ru_components/templates/ebook_ru_letter.jinja` and
`ebook_ru_rpd_letter.jinja` (2c verifies `xmlns:epub` is declared). Option (b) deferred to DRAFT
thread `kamma/drafts/20261105_kindle_ru_217_port/handoff.md` (created 2026-11-05).

### D7. TPR monthly export stopped upstream (#279)
Upstream workflows/docs stop monthly TPR export ("keep code until year end"). Local `make_dpd.sh`,
`make_ru_dpd.sh`, `ru_release.yml` still run `tpr_exporter_ru`. **Question**: keep RU TPR export
(default, no change) or stop it to match upstream?
**RESOLVED (2b, 2026-11-05): (b) stop automatic RU TPR export now, mirroring upstream 788e92046**
(upstream spec `kamma/archive/20261103_tpr_stop_monthly/spec.md`: code kept until end-2026, then
removed). Remove ONLY the automatic runs:
- `scripts/bash/make_dpd.sh:47` — `uv run python exporter/tpr/tpr_exporter_ru.py`.
- `scripts/bash/make_ru_dpd.sh:58,60,62` — both `check_tpr_download_index.py` calls + the
  `tpr_exporter_ru.py` call (and the blank lines between them).
- `.github/workflows/ru_release.yml`: drop `resources/tpr_downloads` from the "Sync all submodules"
  loop (l.306; drop the `master` branch special-case l.309-313 → loop over `resources/fdg_dpd` only,
  branch `main`); delete "Run TPR Exporter" step (l.335-336); drop the `tpr_downloads` entry from
  the "Update All Submodules" map (l.347) and its `master` special-case (l.360-364). fdg leg unchanged.
- `.github/workflows/ru_release_test.yml:308-309` — delete "Run TPR Exporter" step.
KEEP (until upstream's year-end removal thread): `exporter/tpr/tpr_exporter_ru.py`,
`scripts/rus_exporter/check_tpr_download_index.py`, `resources/tpr_downloads` submodule, config
`make_tpr`. Next-sync watch item: when upstream removes `exporter/tpr/` + TPR paths/config, archive the
RU TPR exporter + check script and update registry in the same sync. 2c: add this watch note to the
`tpr_exporter_ru.py` registry `watch_for`.

### D8. `resources/deconstructor_output` submodule retired — RU release + generate_components
Upstream deleted the submodule + `scripts/build/tarball_deconstructor_output.py`; deconstructor now
generated (Go / `scripts/build/decon_cache_update.py`). Local `scripts/bash/generate_components.sh`
and all 3 `ru_release*.yml` still unzip the tarball → RU release BREAKS after pull.
**Proposed**: mirror upstream `draft_release.yml` / `generate_components.py` approach in our files
(remove Unzip step, add upstream's generate step, keep `deconstructor_output_add_to_db.py` call);
2c copies exact upstream steps. Also port `GITHUB_TOKEN` env on Audio Index step.
**RESOLVED (2b, 2026-11-05): mirror upstream exactly.**
1. `scripts/bash/generate_components.sh`: l.43 `tarball_deconstructor_output.py` →
   `uv run python scripts/build/deconstructor_output_add_to_db.py`; insert
   `uv run python scripts/build/decon_cache_update.py` between `epd_to_lookup.py` (l.64) and
   `generate_search_index.py` (l.66) (upstream order; cache feeds Flet-1.0 gui2 `initialize_db`).
2. `ru_release.yml` (l.56-59), `ru_release_test.yml` (l.56-59), `ru_release_kindle.yml` (l.53-56):
   delete "Unzip deconstructor_output" step; add upstream step "Generate Deconstructor"
   (`run: go run go_modules/deconstructor/main.go`) immediately before existing "Run Deconstructor"
   (`deconstructor_output_add_to_db.py`). All 3 already have setup-go 1.22.2 (kindle uses
   `setup-go@v5`, others `@v6` — leave as is).
3. `ru_release.yml` + `ru_release_test.yml` "Download Audio Index": add
   `env:\n  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}`.
4. Submodule removal INCLUDED in the sync commit (user explicitly approved overriding the
   `resources/` Commit Scope rule for this one path): `.gitmodules` entry + gitlink
   `resources/deconstructor_output` removed (`git rm resources/deconstructor_output`; clean
   `.git/modules/resources/deconstructor_output` only after commit, ask first). Other dirty
   `resources/*` (e.g. `resources/tpr_downloads`) stay excluded.
Post-pull leftovers are upstream-owned (`tools/paths.py` still defines the old attrs upstream;
`scripts/find/deconstruction_finder.py` upstream ref) → no local action.

### D9. Pre-range test orphans (36 files) — delete-to-match?
Local `tests/` files upstream deleted BEFORE this range (P0 won't touch them), e.g.
`tests/test_mcp_server.py`, `tests/exporter/mcp/*`, golden-master tests upstream dropped
(e0d73ff14), `tests/test_gui2_speech_marks_functions.py` (imports removed `clean_example` etc.).
Several will fail after this pull. List: `stage2a_findings/test_orphans_prerange.txt`.
(+26 in-range orphans P0 deletes automatically.)
**Proposed**: `git rm` all 36 (tests/ is upstream-synced; none registered).
**RESOLVED (2b, 2026-11-05): `git rm` all 36** listed in `stage2a_findings/test_orphans_prerange.txt`
(Stage 3, explicit file list). Verified: none in OLD or NEW upstream (removed by upstream
`adecd45e7`, `9b19e657d`, `5f10334fc`); none registered. Only local edits: `39685f215`
(`tests/exporter/mcp/test_mcp_server.py`, still imports `exporter.mcp.server` which P0 removes) and
`ef4efa371` (`tests/test_audio_query.py`, lint-only, and its `!= None` → `is not None` change was a
SQLAlchemy bug) — nothing to preserve.

### D10. `gui2/pass2_add_view.py` registered entry is obsolete
Registered local edit (`request_dpd_server` → dps utils) no longer applies: NEW upstream has no
`request_dpd_server` reference; local HEAD is already stale vs OLD. **Proposed**: remove from
`modified_upstream_files` BEFORE `execute_sync.py` (so it is pulled verbatim); `dps_view.py` keeps
`fast_api_utils_dps`. Requires D4(a) (file is Flet 1.0 + needs contributor modules).
**RESOLVED (2b, 2026-11-05): (a) take upstream verbatim.** Upstream `5497d80c9` (#215) replaced the
post-commit `request_dpd_server(id)` browser tab with pre-commit `gui2/preview.py`
`preview_and_confirm` (renders upstream webapp DPD template to `gui2/assets/preview/preview_<user>.html`,
Save/Cancel dialog, then `save_router.save_headword`). User: RU/SBS rendering NOT needed in pass2.
Actions: remove `gui2/pass2_add_view.py` from registry `modified_upstream_files` BEFORE
`execute_sync.py`. **Constraint for the D4 `dps_view.py` Flet 1.0 migration:** user DOES need the
RU/SBS rendering after saving in the DPS tab → keep `from tools.fast_api_utils_dps import
request_dpd_server` and the post-commit `request_dpd_server(str(self.headword.id))` call
(`gui2/dps_view.py:18`, `:502`) and `start_dpd_server()` from `fast_api_utils_dps` in `gui2/main.py`
(launches `exporter.webapp.main_ru`, `/sbs/` route). Do not swap these to upstream's preview.

### D11. Webapp RU/SBS feature ports — scope
PORT (correctness/parity, recommended): NOCASE lookup + NUL fallback, `isdecimal` + 18-digit guard,
`.get(q, [])`, dead post-loop block → `RuntimeError` (toolkit_ru); `regex_deadline`/`limit` hardening
in `bd_search`/`tt_search`; bounded audio Range regex; `show_tbw` globals; `data_classes_ru`
`permalink`; template `show_tbw`, s.4nt.org row, PTS/DV split; home Google Fonts / `data-title` /
favicon type; `app.js` 3-way (navigationState/handlePopState/searchURL).
**Owner decisions**: (i) licence `Link` header + `license` JSON field + CORS `expose_headers` on RU
`/sbs/*` routes; (ii) `lookups_take_turns` middleware (must include `/sbs/*` paths);
(iii) `/{headword_id}` permalink route + Permalink/How-to-cite rows in RU feedback (RU feedback is
fully localised → needs RU strings); (iv) `IndexStaticFiles` precompressed mount (needs `brotli`).
**Recommendation**: all of (i)–(iii) for SBS (English UI, verbatim); RU gets (i),(ii) + translated
(iii); skip (iv) unless the user wants it.
**RESOLVED (2b, 2026-11-05): port the default parity list + ALL of (i)–(iv)** to `main_ru.py` /
`toolkit_ru.py` / `data_classes_ru.py` / `ru_templates/` / `sbs_templates/` / `app.js`, layering on
top of existing Russian strings:
- (i) licence: `LICENSE_LINK_HEADER` + `"license": LICENSE_NOTICE` + `encode_search_response` on
  `db_search_json_ru`, `db_search_json_sbs`, `db_search_gd_ru`, `db_search_gd_sbs`,
  `db_search_html_sbs`; CORS `expose_headers=["Link"]`; RU HTML gets the licence equivalent in
  `make_dpd_html_ru` (licence text stays English/upstream). SBS gets it via upstream `make_dpd_html`.
- (ii) `lookups_take_turns` + constants + `lookup_busy_response`; `LOOKUP_PATHS` extended with
  `/sbs/search_json`, `/sbs/gd`, `/sbs/search_html`; busy branch also keys on `/sbs/search_json`.
  `BUSY_MESSAGE` stays English.
- (iii) `HeadwordIdConvertor` + `permalink_page` (→ `/?q=<id>`, 308); Permalink/How-to-cite rows:
  SBS verbatim, RU labels **«Постоянная ссылка»** / **«Как цитировать»** (citation body text: 2c
  translates from upstream, keep URLs/version tokens verbatim).
- (iv) `app.mount("/static", IndexStaticFiles(...))` replaces `StaticFiles` in `main_ru.py`
  (`brotli` via D5; `precompressed_index.py`/`response_encoding.py` pulled verbatim).
Pull together (import-time deps): `tools/paths.py`, `exporter/webapp/static/cc_icons.svg`,
`tools/search_deadline.py`, `tools/server_mode.py`, `tools/version.py`.
Add pyrefly ignore comment on `show_tbw` globals as upstream does.

### D12. Family heading singular/plural + feedback wording in RU JS/templates
Upstream: count-based singular/plural family headings (JS + templates), feedback wording sync,
"Bodhirasa" → "Bodhirasa Bhikkhu". SBS: port verbatim. RU: needs RU translation of the
count-based wording (2 forms or RU 3-form plural?). **Question**: translate for RU (which plural
rule), or only port the `</p>` fix for RU?
**RESOLVED (2b, 2026-11-05): (a) proper Russian 3-form plural.**
- SBS: port `904891e2f` + `3ae112bf9` verbatim (English).
- RU GoldenDict JS (`exporter/goldendict/ru_components/javascript/ru_family_{compound,idiom,root,set,word}_template.js`):
  add helper `ruPlural(n, one, few, many)` (n%10==1 && n%100!=11 → one; n%10 in 2..4 && n%100 not
  in 12..14 → few; else many); replace hedged forms (`составных слов(а) содержат`, `идиом(ы) содержат`,
  `слов в группе`, root/word headings) with participle phrasing that needs no verb agreement, e.g.
  `1 составное слово, содержащее` / `3 составных слова, содержащих` / `5 составных слов, содержащих`.
  Per family, choose singular/plural from that family's own `count` (upstream logic).
- RU webapp `exporter/webapp/ru_templates/dpd_headword.html` (~l.1254, 1274, 1307-1341): Jinja macro
  `ru_plural(n, one, few, many)` with the same rule; same phrasing.
- Port structural fixes to RU: close `</p>` for single-family compound/idiom/set headings; back-to-top
  arrow on every heading in the multi-family compound list.
- Feedback: RU gets only D11(iii) permalink/cite rows; SKIP upstream English feedback-link wording
  (RU feedback is independent). «Дост. Бодхираса» already equals "Bodhirasa Bhikkhu" → no change.
- 2c MUST present the exact RU strings per family type for user review before approval.
- Helper/macro names: `ruPlural` / `ru_plural` (no double-marking issue; `ru` is the locale marker).

---

## 3. Shadow ports (PORT — literal edits authored in 2c)

| # | Local target | Upstream source | Change to port | Structural refactor check |
|---|---|---|---|---|
| S1 | `db/lookup/help_abbrev_add_to_lookup_ru.py` | `tools/tsv_read_write.py` (blast radius) | **BREAKS on pull**: imports removed `read_tsv_as_dict_with_different_key` (lines 14,31,40) → inline local helper or use upstream replacement | n/a (fan-out fix) |
| S2 | `gui2/dps_example_field.py` | `gui2/dpd_fields_examples.py` | **BREAKS on pull**: `clean_example` moved → `from tools.example_cleaning import clean_example`; plus D4 Flet 1.0 API changes | YES — helper move + Flet API |
| S3 | `scripts/export/list_of_words_from_txt.py` (unique), `tests/test_vib_rule_workflow.py` | `tools/cst_sc_text_sets.py` | **BREAKS**: `make_cst_text_list_from_file` removed → port to `make_cst_text_list`/equivalent (2c reads new signature) | n/a (fan-out fix) |
| S4 | `db/families/family_set_ru.py` | `db/families/family_set.py` | `SMALL_SET_EXCEPTIONS` + `and not sf.startswith(...)` (~l.213) | none found |
| S5 | `exporter/goldendict/ru_components/javascript/family_{compound,idiom,root,set}_template.js` | same names | `</p>` fix (compound/idiom/set); count-based wording per D12 | none found |
| S6 | `exporter/goldendict/sbs_*` family JS (4) + SBS feedback JS | upstream JS | verbatim port (singular/plural, `</p>`, permalink, docs/cite/contribute lines) | none found |
| S7 | `exporter/goldendict/ru_components/templates/dpd_headword*.jinja`, `sbs_templates/dpd_headword*.jinja` | `templates/dpd_headword.jinja` | `d.su.tbw_legacy and show_tbw`; s.4nt.org row (after SC Voice); PTS heading + separate DV block (RU ~l.662-690, SBS ~l.681-700) | none found |
| S8 | `exporter/grammar_dict/grammar_dict_ru.py`, `exporter/deconstructor/deconstructor_exporter_ru.py` | upstream | SKIP — author-name string only | none found |
| S9 | `exporter/tpr/tpr_exporter_ru.py` | `tpr_exporter.py` | SKIP — beta/uposatha/index + `version` param refactor of `copy_zip_to_tpr_downloads` not used by RU (subject to D7) | YES upstream (signature), not mirrored — RU path differs |
| S10 | `scripts/build/families_to_json_ru.py`, `tools/degree_of_completion_ru.py` | upstream | SKIP — Mapping typing / docstring only | typing only — optional |
| S11 | `exporter/kindle/ru_components/templates/ebook_ru_letter.jinja`, `ebook_ru_rpd_letter.jinja`; `ru_components/epub/OEBPS/Styles/dpd_kindle.css`; `.../Text/nav.xhtml` | kindle templates/epub | `<body epub:type="dictionary">` (l.20); 5-line hanging-indent CSS; nav dead-link cleanup (structure differs — 2c authors); titlepage SKIP (date only) | none found (D6 governs #217) |
| S12 | `scripts/server/update-dpd-sbs.sh` | `scripts/server_dpdict/update-dpd.sh` | see B2 | none found |
| S13 | `tools/translit_ru.py` | `tools/translit.py` | `not any(char.isalpha())` clause | none found |
| S14 | `tools/ru_spelling.py` | `tools/spelling.py` | guard `check_sentence` against `None` | none found |
| S15 | `db/backup_tsv/backup_dps.py` | `backup_dpd_headwords_and_roots.py` | path-limited `git commit -- <files>`; upstream dropped GitPython (subprocess) → tie to D5 | YES — GitPython → subprocess |
| S16 | `tools/utils_sbs.py` | `tools/utils.py` | optional `cast` typing fix | typing only |
| S17 | `scripts/build/db_rebuild_from_tsv_dps.py`, `scripts/fix/character_replacer_sbs.py` | upstream | SKIP — cosmetic only (2c confirms no structural change) | none found |
| S18 | `shared_data/reference_ru/{abbreviations,abbreviations_other,bibliography}.tsv` | `shared_data/reference/*` | local text edits, NO LLM: ṁ→ṃ (1 pāli cell + 34 meaning cells, 3 PTS keys); bibliography +5 rows (Levman×2, Malalasekera, Oberlies×2) + Deokar heading rename; RU columns unchanged (new rows need RU translation → translate pipeline/manual) | none found |
| S19 | `exporter/webapp/main_ru.py`, `toolkit_ru.py`, `data_classes_ru.py`, `ru_templates/*`, `sbs_templates/*` | webapp upstream | per D11 | YES — dead-code removal, `isdecimal` |
| S20 | `exporter/webapp/data_classes.py` (registered modified) | upstream | 2 disjoint lines: `make_permalink` import + `self.permalink` — clean 3-way | none found |
| S21 | `exporter/webapp/static/app.js` (registered modified) | upstream | 3-way: navigationState / handlePopState rewrite / `searchURL()`; verify SBS link + `/sbs/search_json` branch survive | YES — handlePopState refactor |
| S22 | `gui2/dps_meaning_field.py`, `dps_fields.py`, `dps_view.py`, `dps_test_manager.py`, `dps_field_mapping.py`, other `dps_*.py` | gui2 upstream | Flet 1.0 API migration per D4(a); feature diffs in dps_fields/dps_view remain SKIP (upstream-only automation, as in prior syncs) | YES — Flet API |

## 4. Inspired backports

| # | Local file | Upstream source | Decision | Structural refactor check |
|---|---|---|---|---|
| I1 | `exporter/goldendict/export_dpd_ru.py`, `export_dpd_sbs.py` | `export_dpd.py` | PORT `show_tbw` (TypedDict field, `config_test("dictionary","show_tbw","yes")`, render_data, `_worker_init` globals) — paired with S7 | none found |
| I2 | `export_help_ru.py`, `export_help_sbs.py` | `export_help.py` | `add_citation` help entry: PORT to SBS; RU skip or translate (fold into D12 answer) | none found |
| I3 | `main_ru.py`, `main_sbs.py` (goldendict) | `main.py` | SBS: "Bodhirasa Bhikkhu" in description/author; RU skip | none found |
| I4 | `scripts/bash/generate_components.sh` | `generate_components.py` | per D8 | none found |
| I5 | `scripts/bash/make_dpd.sh`, `make_ru_dpd.sh` | `makedict.py` | per D7 (TPR); otherwise SKIP | none found |
| I6 | `.github/workflows/ru_release*.yml` (3) | `draft_release.yml` | per D8 + `GITHUB_TOKEN` env on Audio Index step; SKIP submodule push / macOS / action versions; kindling step only if D6(b) | none found |
| I7 | `mkdocs_ru.yaml` | `mkdocs.yaml` | DOCS TRACK — add 6 nav entries only as each page lands in `docs_rus/` | none found |
| I8 | `tools/fast_api_utils_dps.py` | `fast_api_utils.py` | SKIP — self-contained; removed upstream `request_bold_def_server` has no callers | YES upstream (dead-code removal) — local copy unaffected |
| I9 | `tools/paths_ru.py`, `tools/paths_dps.py` | `tools/paths.py` | SKIP — 11 removed attrs not read by local files; standalone classes | YES upstream (prune), deliberately not mirrored |
| I10 | `gui2/dps_fields.py`, `dps_fields_lists.py`, `dps_view.py`, `dps_test_manager.py` | gui2 upstream | feature SKIP (upstream-only automation); Flet API per S22 | see S22 |
| I11 | `docs_rus/**` | `docs/**` (~50 md + images) | DOCS TRACK (`docs_translation_queue.md` already updated by prep) | n/a |

## 5. Mirror — pulled verbatim (unregistered → zero local divergence)

All other changed upstream paths (`changed_upstream_paths` minus §1–§4 targets): gui2 (Flet 1.0 —
see D4), `tools/**` (incl. `ai_manager.py` + new `ai_openai_compat.py`, `tsv_read_write.py`,
`cst_sc_text_sets.py`, `version.py`, `paths.py`, `configger.py`), `exporter/analysis/**`,
`exporter/webapp/{precompressed_index,response_encoding,generate_search_index}.py`, `cc_icons.svg`,
`go_modules/**`, `db/**` non-shadow, `db/backup_tsv/*.tsv`, `scripts/**` non-shadow, `audio/**`,
`shared_data/deconstructor/*`, `identity/css/*`, `justfile`, `README.md`, `CONTRIBUTING.md`,
`.github/ISSUE_TEMPLATE/*`, `.github/workflows/{draft_release,mobile_release}.yml`, submodule pointers
(`resources/*` gitlinks from upstream), `uv.lock` (regenerated after D5).
**Needs-classification (250 new upstream files)**: all **mirror**, no registry entries
(registry tracks local specials only): `db/inflections/templates/*.tsv`, `exporter/epitaka/`,
`newsletter/`, `scripts/server_contrib/`, `scripts/server_dpdict/update-dpd.sh`, new gui2/tools
modules, go tests, `.github/workflows/typecheck.yml` (triggers on push to `main` / PRs only — our
branch `sbs-ru` unaffected on push), `CITATION.cff`, `.zenodo.json`, `LICENSE`, `.graphifyignore`.

**Verified compatibility (ADVANCED spot checks)**:
- `tools/ai_manager.py` rewrite keeps `AIManager`, `.request()`, `AIResponse`,
  `_load_models_from_json`, provider names `deepseek`/`antigravity_cli` → kamma/translate callers OK;
  `tools/ai_models.json` stays PRESERVE (upstream dropped `antigravity_cli_work_models`; upstream
  ai_manager ignores it; `batch_runner.py` reads only `default_models`). Update registry note wording.
- Blast-radius import scan of all local-only `.py` vs NEW upstream: only S1, S2, S3 break (excl.
  expected `db.models` local tables, restored file). Shared webapp deps (`tools/version.make_permalink`,
  `ProjectPaths().webapp_cc_icons_path`, `cc_icons.svg`) all arrive in the same pull.
- `tools/goldendict_exporter.py` imports `pyglossary.glossary_v2` — 2c verifies locked pyglossary version.
- **Pre-existing breakages (NOT caused by this sync, out of scope — report only)**:
  `kamma/translate/scripts/ai_generate_translation.py:17` imports `load_models_from_json` (renamed last
  sync; already missing at OLD); `tests/tools/test_proofreader_output.py` (`save_results`),
  `tests/tools/test_sbs_table_functions.py` (`tools.sbs_table_functions`), `tests/test_model_eval.py`
  (`scripts.other.ai_translate_evaluator`).

## 6. Deletions & orphans

| Path | Classification |
|---|---|
| 19 `unregistered_local_paths` (db_tests_gui/*, `tools/ipa.py`, `db/inflections/inflection_templates.xlsx`, `inflections_raw.py`, scripts/fix/*, …) | delete-to-match (P0, in range). No local consumers (verified import scan; `db/models.py` only has a commented `tools.ipa` line). **Except** `exporter/kindle/kindlegen` → D6 and `scripts/server/update-dpd.sh` → B2 |
| 182 in-range `upstream_deleted_orphans` (syāmaraṭṭha_1927 texts, `exporter/mcp/`, `scripts/cl/*`, `scripts/add/vagga_codes/`, tools/*, `gui2/ai_search.py`, workflows `opencode`/`pdf_test`) | delete-to-match (P0). Local follow-up: none required (no local importers; `scripts/cl_dps/` is our replacement for `scripts/cl/`) |
| `exporter/sutta_central/sc_dict.json` (19 MB, pre-range orphan) | delete-to-match: explicit `git rm` in Stage 3 (upstream stopped tracking in aeaf84e9d; RU exporter writes `sc_pli2ru_dpd_json`, not this) |
| `.github/workflows/submodules_update.yml` | already absent locally; remove from registry (line ~600) |
| 36 pre-range test orphans | D9 |

## 7. Registry updates (Stage 3; entries affecting the restore set land BEFORE `execute_sync.py`)

- `sbs_copies["scripts/server/update-dpd-sbs.sh"].upstream` → `scripts/server_dpdict/update-dpd.sh` (B2).
- Remove `.github/workflows/submodules_update.yml` reference (line ~600).
- Remove `scripts/cl/dpd-gui2` reference (line ~699) if it points at a deleted path (2c checks context).
- D10: remove `gui2/pass2_add_view.py` from `modified_upstream_files` (if approved) — BEFORE execute_sync.
- D6(a): protect `exporter/kindle/kindlegen` (`run_exclusions.txt` or registry) — BEFORE execute_sync.
- `tools/ai_models.json` note: upstream dropped `antigravity_cli_work_models`.
- Update `exporter/webapp/data_classes.py` / `app.js` entries' line refs after merge.
- Then `uv run python3 kamma/upstream_sync/scripts/validate_registry.py`.

## 8. Verification battery (Stage 3)

1. `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py -v`
2. `uv run python3 tests/check_shadow_modifications.py`
3. `uv run python tests/smoke_test_sync.py`
4. `uv run python3 kamma/upstream_sync/scripts/validate_registry.py`
5. ruff check/format + pyright + pyrefly on every hand-edited file
6. Import smoke: `uv run python -c "import db.lookup.help_abbrev_add_to_lookup_ru, gui2.dps_example_field, exporter.webapp.main_ru, exporter.goldendict.export_dpd_ru, exporter.goldendict.export_dpd_sbs, exporter.kindle.kindle_exporter_ru"`
7. `uv run pytest tests/tools/test_ai_manager.py -v`; `uv run python -c "from tools.ai_manager import AIManager, AIResponse, _load_models_from_json"`
8. GUI launch (if D4a) + webapp RU/SBS + GoldenDict manual check deferred to Stage 4.

## 9. Literal edit recipes

Conventions for every recipe below:
- `OLD=be49bffe2c2c`, `NEW=c54f942ee3f6`. Run from repo root. `S=<scratchpad dir>` = any
  session scratch dir (never repo root; `temp/20261105_sync/` is acceptable, delete after).
- "Verify" commands must succeed exactly as written; if any anchor is missing, STOP and request
  ADVANCED (guide.md Stage 3 stop rule).
- Every edited `.py`: `uv run ruff check --fix <f>`, `uv run ruff format <f>`, `uv run pyright <f>`
  (`uv run pyright --project /dev/null <f>` for `gui2/` and `tests/`), and
  `uv run --with pyrefly pyrefly check --min-severity warn <f>` — all clean.
- **2c deviations from 2b resolutions** (need explicit approval at 2d) are marked **⚠ 2c-DEVIATION**.

### 9A. Pre-pull gate (BEFORE `execute_sync.py`)

**A0. Registry edits** (`kamma/upstream_sync/registry.json`, edit with Edit tool, keep 2-space JSON):
1. `modified_upstream_files`: delete the whole object whose `"path": "gui2/pass2_add_view.py"` (D10).
2. `unique_paths`: delete the line `".github/workflows/submodules_update.yml",` (§6 correction: the
   file IS present locally, byte-identical to OLD upstream, checks out `digitalpalidictionary/dpd-db`
   — useless on the fork; upstream deleted it in 76d69f0e6 → unregistering lets P0 delete it).
3. `unique_paths`: delete the line `"scripts/cl/dpd-gui2",` (stale duplicate of
   `scripts/cl_dps/dpd-gui2`; all other `scripts/cl/*` are upstream-deleted by P0). File removed in A8.
4. `unique_paths`: add `"exporter/kindle/kindlegen",` immediately after the line
   `"tools/cst_source/__init__.py"` (add a comma to that line; new line is the last element) — D6(a).
5. `sbs_copies["scripts/server/update-dpd-sbs.sh"]`: change `"upstream": "scripts/server/update-dpd.sh"`
   → `"upstream": "scripts/server_dpdict/update-dpd.sh"` (B2).
6. `modified_upstream_files[path=="pyproject.toml"]`: in `discuss_reason` replace
   `(currently num2words>=0.5.14, pyrefly>=1.1.1)` → `(currently num2words>=0.5.14)`; in
   `local_changes[0]` replace ``Current set: `num2words>=0.5.14`, `pyrefly>=1.1.1`.`` →
   ``Current set: `num2words>=0.5.14`.``
7. `modified_upstream_files[path=="tools/ai_models.json"]`: append to `watch_for`:
   `"2026-11-05 sync: upstream dropped the `antigravity_cli_work_models` key; upstream `ai_manager.py` no longer reads it. Local key kept (read only by local tooling); `batch_runner.py` reads only `default_models`."`
8. `russian_copies["exporter/tpr/tpr_exporter_ru.py"]`: append to `watch_for`:
   `"Upstream stopped the monthly TPR export (788e92046, #279) and will delete `exporter/tpr/` + TPR paths/config after end-2026. When that lands: archive `tpr_exporter_ru.py`, `tpr_headword_ru.jinja` and `scripts/rus_exporter/check_tpr_download_index.py` to `archive/dps/` and update this registry in the same sync. Automatic RU TPR runs were removed in the 2026-11-05 sync (D7)."`
- Verify: `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` passes;
  `rg -c 'pass2_add_view|submodules_update|scripts/cl/dpd-gui2' kamma/upstream_sync/registry.json`
  → only the `gui2/dps_view.py` `"upstream": "gui2/pass2_add_view.py"` line remains (count 1).

**A1. Rerun prep + gate files**
1. `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py kamma/threads/20261105_upstream_sync`
2. If `prep_manifest.json` `discuss_paths` is non-empty: all are RESOLVED in §2 → set it to `[]`
   (Edit tool, only that key).
3. Write `kamma/threads/20261105_upstream_sync/run_acknowledged_blockers.txt`:
   ```
   # B1/B2 resolved by analysis, dynamic_plan.md §1
   exporter/kindle/templates/ebook_deconstructor_entry.jinja
   scripts/server/update-dpd.sh
   ```
4. Do NOT create `run_exclusions.txt` (kindlegen is protected via `unique_paths`).
- Verify: `uv run python3 kamma/upstream_sync/scripts/execute_sync.py kamma/threads/20261105_upstream_sync --dry-run`
  (if the flag name differs, read `execute_sync.py` argparse; dry-run must print "Dry run").

**A2. Clean tree (⛔ USER)** — `execute_sync.py` refuses a dirty tree. The user commits the A0 registry
edits + `kamma/upstream_sync/docs_translation_queue.md` + thread files (suggested message:
`#sync: pre-pull registry updates 2026-11-05`). `resources/tpr_downloads` gitlink drift is the user's
call (Commit Scope rule) — must be resolved by the user before the run.

**A3. Run** `uv run python3 kamma/upstream_sync/scripts/execute_sync.py kamma/threads/20261105_upstream_sync`.
Verify: `git ls-files exporter/kindle/kindlegen` prints the path; `test ! -e .github/workflows/submodules_update.yml`;
`test -e scripts/server_dpdict/update-dpd.sh`; `test ! -e scripts/server/update-dpd.sh`.

### 9B. Post-pull: restored upstream-modified files (D1, D2, D3, D5)

**B1. `.gitignore` (D1)** — build from NEW upstream + local block:
```
git show c54f942ee3f6:.gitignore > $S/gi_new
sed -n '133,163p' .gitignore > $S/gi_local_block      # '# --- DPS / SBS / RU UNIQUE patterns ---' .. 'dpd.db-wal'
{ cat $S/gi_new; printf '\n'; cat $S/gi_local_block; } > .gitignore
```
Precheck before running: `sed -n '133p;163p' .gitignore` prints exactly
`# --- DPS / SBS / RU UNIQUE patterns ---` and `dpd.db-wal`.
Then **⚠ 2c-DEVIATION (D1)**: upstream line 5 is `.claude/`; the fork tracks `.claude/` (agents,
commands, settings.json) and the local block's `!.claude/agents/` re-include cannot work under an
excluded parent dir. Replace the exact line `.claude/` (line 5) with `.claude/scheduled_tasks.lock`
(the pre-sync local value). Effect of the rebuild otherwise = D1: all upstream adds/removes,
`exporter/mcp/input/*` dropped, duplicated pass2x tail lines collapsed into upstream's copy.
- Verify: `diff <(git show c54f942ee3f6:.gitignore) <(head -n $(git show c54f942ee3f6:.gitignore | wc -l) .gitignore)`
  shows only the line-5 change; `rg -n '^exporter/mcp/input' .gitignore` → no match;
  `git check-ignore -q .claude/agents/sync-fast.md; test $? -eq 1`; `git status --short | rg '^\?\?' | head` shows
  no newly-surfaced tracked-intent files.

**B2. `AGENTS.md` (D2)** — additive. Edit tool:
- Replace line `- When answering questions about Flet refer to the /resources/flet-docs folder.` with:
  ```
  - When answering questions about Flet refer to the /resources/flet-docs folder.
  - gui2 runs **Flet 1.0.1**. Closing a dialog with `dialog.open = False` leaves the instance on `page._dialogs`; a later `page.show_dialog` of the same instance raises "Dialog is already opened" — guard reopen paths. Escape on modal dialogs is handled once, globally, by `cancel_top_dialog` in `gui2/ui_utils.py`; new popups only need a "Cancel" or "Close" button.
  ```
- Insert immediately BEFORE the line `# Localized Rules (local fork)` (keep one blank line before it):
  ```
  ## Git Safety (shared working tree)
  - NEVER run `git stash`, `git checkout -- <path>`, `git restore`, or `git reset --hard` — they operate on the whole tree and destroy other sessions' uncommitted work. Stage by explicit file list.

  ## Repo Gotchas
  - `.gitignore` ignores ALL `__init__.py` files, so a package `__init__.py` re-export can never be committed. Import new symbols from their concrete module.
  - `dpd.db` runs in WAL mode: writes land in `dpd.db-wal` and the main file's mtime does not move. Never use the timestamp to decide whether the database changed — read the data.
  - `DpdHeadword.inflections_list_all` yields `""` entries when either inflections column is empty — filter empty strings before using inflections as dict keys or set members.
  - `uv add` / `uv remove` sync only the default groups and uninstall the `tools` group. Always pass `--no-sync`, then run `uv sync --all-groups`.
  - For files under `gui2/`, `tests/` or `tools/cst_source/`, plain `uv run pyright <file>` analyses nothing (all are in `[tool.pyright].exclude`) yet prints "0 errors". Use `uv run pyright --project /dev/null <file>`. Lint `tools/cst_source` with `uv run ruff check --no-force-exclude <file>` (same flag for `ruff format`).
  - Never `ruff format` `.json` fixtures — it adds trailing commas that break parsing.

  ```
- Verify: `rg -c 'Flet 1.0.1|## Git Safety|## Repo Gotchas|--project /dev/null|inflections_list_all' AGENTS.md` ≥ 5;
  `rg -n 'parents\[' AGENTS.md` unchanged vs before (no upstream Path-anchoring conflict imported).

**B3. `db/models.py` (D3)** — take NEW upstream verbatim, then re-apply local tables:
1. Show the 3-way: `git diff be49bffe2c2c c54f942ee3f6 -- db/models.py > $S/models_up.diff`
2. `git apply --3way $S/models_up.diff` on the restored local file (local divergences — `Russian`,
   `SBS`, `Tamil`, `Sinhala` models, `*_ru` columns, `.ru`/`.sbs` relationships — are disjoint from the
   upstream hunks per 2a: lookup NOCASE index, `unique=True` on `lemma_1`, `SuttaInfo` URL/regex,
   `s_4nt_link`, pyrefly comment). If `--3way` leaves conflict markers: STOP → ADVANCED.
- Verify: `rg -n 'ix_lookup_key_nocase|s_4nt_link|unique=True' db/models.py` (3 kinds present);
  `rg -n '^class (Russian|SBS|Tamil|Sinhala)\b' db/models.py` (4); `uv run python -c "import db.models"`.
3. Live-db fix (once, after verifying no writer is running):
   ```
   sqlite3 dpd.db "UPDATE dpd_headwords SET lemma_1 = 'hatthaka 4' WHERE id = 70815 AND lemma_1 = 'hatthaka 3';"
   uv run tools/prepare_webapp_lookup.py dpd.db
   ```
   (**⚠ 2c-DEVIATION (D3)**: index created by upstream's own idempotent `tools/prepare_webapp_lookup.py`
   — pulled verbatim — instead of the raw `CREATE INDEX` SQL; same DDL, plus NUL-key and definition checks.)
   `hatthaka 3` grep: only hits are `exporter/sutta_central/sc_dict.json` (deleted in C10) and external
   `resources/*` builds → nothing local to update.
- Verify: `sqlite3 dpd.db "SELECT lemma_1 FROM dpd_headwords WHERE id IN (70815,70816);"` → `hatthaka 4`,
  `hatthaka 3`; `sqlite3 dpd.db "SELECT lemma_1, COUNT(*) c FROM dpd_headwords GROUP BY lemma_1 HAVING c>1;"` → empty;
  `sqlite3 dpd.db "PRAGMA index_list(lookup);" | rg ix_lookup_key_nocase`.

**B4. `pyproject.toml` + lock (D5)**
1. `git show c54f942ee3f6:pyproject.toml > pyproject.toml`
2. Edit: replace the line `    "brotli>=1.2.0,<2",` with
   ```
       "brotli>=1.2.0,<2",
       # fork-local: scripts/change_in_db/update_yojana_km.py (registered unique)
       "num2words>=0.5.14",
   ```
3. `uv lock` then `uv sync --all-groups`.
- Verify: `diff <(git show c54f942ee3f6:pyproject.toml) pyproject.toml` shows only the 2 added lines;
  `uv run python -c "import flet, num2words, brotli; print(flet.version.version if hasattr(flet,'version') else flet.__version__)"`
  prints `1.0.1`; `uv run python -c "import git" 2>&1 | rg ModuleNotFoundError` (gitpython gone).
- Note: `[tool.pyrefly].project-excludes` now lists `gui2/**` and `kamma/**`; explicit-file pyrefly runs
  still check named files.

### 9C. Post-pull: small shadow ports, data, deletions

**C1. S1 `db/lookup/help_abbrev_add_to_lookup_ru.py`** — upstream removed
`read_tsv_as_dict_with_different_key` (5875fdc0e, zero upstream callers). Local fix: module-local copy of
the OLD upstream function (behaviour-identical, typed).
- Replace `from tools.tsv_read_write import read_tsv_as_dict_with_different_key, read_tsv_dict` with
  `from tools.tsv_read_write import read_tsv_dict` and add `import csv` and `from pathlib import Path`
  above `from dataclasses import dataclass` (stdlib group, alphabetical: `import csv`,
  `from dataclasses import dataclass`, `from pathlib import Path`).
- Insert after the `GlobalVars` dataclass (before `def normalize_other_abbreviation_key`):
  ```python
  def read_tsv_as_dict_with_different_key(
      file_path: Path, key_index: int
  ) -> dict[str, dict[str, str]]:
      """Read a TSV into {row[key_index]: {header: value}} without the key column.

      Local copy of the helper upstream removed from tools/tsv_read_write.py."""
      dict_result: dict[str, dict[str, str]] = {}
      with open(file_path, encoding="utf-8") as tsv_file:
          tsv_reader = csv.reader(tsv_file, delimiter="\t")
          headers = next(tsv_reader)
          for row in tsv_reader:
              key = row[key_index]
              if key:
                  dict_result[key] = {
                      headers[i]: value for i, value in enumerate(row) if i != key_index
                  }
      return dict_result


  ```
- Verify: `uv run python -c "import db.lookup.help_abbrev_add_to_lookup_ru as m; from tools.paths_ru import RuPaths; d=m.read_tsv_as_dict_with_different_key(RuPaths().help_tsv_path, 2); print(len(d))"` prints a number > 0.
- Structural refactor check: n/a (fan-out fix).

**C2. S3 `scripts/export/list_of_words_from_txt.py` + `tests/test_vib_rule_workflow.py`** — upstream
removed `make_cst_text_list_from_file` and extracted `hyphenated_parts_adder` (NEW
`tools/cst_sc_text_sets.py:70`). Local fix: move the function into the (unique) script, reusing upstream's
helper.
- In the script replace `from tools.cst_sc_text_sets import make_cst_text_list_from_file` with
  ```python
  from tools.clean_machine import clean_machine
  from tools.cst_sc_text_sets import hyphenated_parts_adder
  ```
  and add `import re` as the first stdlib import (before `from typing import Any`).
- Insert before `def make_field_conditions`:
  ```python
  def make_cst_text_list_from_file(
      dpspth: DPSPaths,
      niggahita: str = "ṃ",
      dedupe: bool = True,
      add_hyphenated_parts: bool = True,
  ) -> list[str]:
      """Make an ordered list of words from dpspth.text_to_add_path.

      Moved here from tools/cst_sc_text_sets.py (removed upstream)."""
      words_list: list[str] = []
      if dpspth.text_to_add_path:
          try:
              with open(dpspth.text_to_add_path, "r", encoding="utf-8") as f:
                  text_string = re.sub(r"\(.+?\)", "", f.read())
                  text_string = clean_machine(
                      text_string,
                      niggahita=niggahita,
                      remove_hyphen=not add_hyphenated_parts,
                  )
                  words_list.extend(text_string.split())
          except FileNotFoundError:
              pr.red(f"file {dpspth.text_to_add_path} does not exist")
              return words_list

      if add_hyphenated_parts:
          words_list = hyphenated_parts_adder(words_list)

      if dedupe:
          return list(dict.fromkeys(words_list))
      return words_list


  ```
  (`dict.fromkeys` keeps first-occurrence order = OLD loop semantics.)
- Test: replace `from tools.cst_sc_text_sets import make_cst_text_list_from_file` with
  `from scripts.export.list_of_words_from_txt import make_cst_text_list_from_file`.
- Verify: `uv run pytest tests/test_vib_rule_workflow.py -v` (all pass; `test_clitics_*` exercise the move).

**C3. S4 `db/families/family_set_ru.py`** (upstream `family_set.py`):
- Insert immediately before `def add_sf_to_db(` (local l.197):
  ```python
  # Sets that are legitimately complete with fewer than 3 members,
  # matched by prefix. Short saṃyuttas contain only one or two vaggas.
  SMALL_SET_EXCEPTIONS: tuple[str, ...] = ("vaggas of Saṃyutta Nikāya",)


  ```
- Replace `            if count < 3:` with `            if count < 3 and not sf.startswith(SMALL_SET_EXCEPTIONS):`
  (only occurrence; confirm loop variable is named `sf` in the RU file first: `sed -n 200,215p` — if
  not `sf`, STOP).
- Verify: `rg -n 'SMALL_SET_EXCEPTIONS' db/families/family_set_ru.py` → 2 lines.

**C4. S13 `tools/translit_ru.py`** — in `auto_translit_to_roman`, replace
`        or is_cyrillic(text)  # if Cyrillic` with
```python
        or is_cyrillic(text)  # if Cyrillic
        # numbers and punctuation have no script, aksharamukha only warns
        or not any(char.isalpha() for char in text)
```
- Verify: `uv run python -c "from tools.translit_ru import auto_translit_to_roman as f; assert f('12.3') == '12.3'"`.

**C5. S14 `tools/ru_spelling.py`** — None guard only (upstream's ASCII `_english_words` filter is
English-specific, not ported):
- `    def check_sentence(self, sentence: str) -> Dict[str, List[str]]:` →
  `    def check_sentence(self, sentence: str | None) -> Dict[str, List[str]]:`
- `                c if c.isalpha() or c.isspace() else " " for c in sentence` →
  `                c if c.isalpha() or c.isspace() else " " for c in (sentence or "")`
- Verify: `uv run python -c "from tools.ru_spelling import RuSpellChecker as R; assert R().check_sentence(None) == {}"`.

**C6. S15 `db/backup_tsv/backup_dps.py`** (D5: GitPython → subprocess, path-limited commit):
- Replace `from git import Repo` with `import subprocess` placed after `import csv` (stdlib block);
  keep the blank line before `from sqlalchemy...`.
- Replace the whole `def git_commit_dps():` function body (through `index.commit("backup russian & sbs")`) with:
  ```python
  def git_commit_dps() -> None:
      pr.green_tmr("committing changes to GitHub")
      files_to_add = [
          "db/backup_tsv/russian.tsv",
          "db/backup_tsv/sbs.tsv",
          "db/backup_tsv/ru_roots.tsv",
      ]
      try:
          # Path-limited commit (upstream backup_dpd_headwords_and_roots.py): commits exactly
          # these files and ignores whatever else other sessions have staged.
          subprocess.run(
              ["git", "commit", "-m", "backup russian & sbs", "--", *files_to_add],
              check=True,
              capture_output=True,
              text=True,
          )
          pr.yes("ok")
      except subprocess.CalledProcessError as e:
          pr.no(e.stderr.strip())
      except FileNotFoundError as e:
          pr.no(f"{e}")
  ```
  (No `check_no_duplicate_lemma_1` port: `backup_dps` does not write `dpd_headwords`.)
- Registry `dps_copies["db/backup_tsv/backup_dps.py"].local_changes`: append
  `"`git_commit_dps` uses upstream's path-limited `subprocess git commit -- <files>` (GitPython dropped upstream, 2026-11-05)."`
- Verify: `rg -n 'from git import|Repo\(' db/backup_tsv/backup_dps.py` → none;
  `uv run python -c "import db.backup_tsv.backup_dps"`; `uv run pytest tests/test_shadow_parity.py -k backup_dps -v`.
- Structural refactor check: YES (GitPython → subprocess) — ported.

**C7. S12 / B2 `scripts/server/update-dpd-sbs.sh`** — replace the whole file with:
```bash
#!/bin/bash

# DPD-SBS Database Update & App Restart Script
# This script is intended to be run from the parent directory (e.g., ~/) on the server.

set -euo pipefail  # Exit on any error, including inside a pipe

echo "=== 1. Entering DPD-SBS Repository ==="
cd dpd-db-sbs
echo "Current directory: $(pwd)"

# Cleared first in case a killed run left it behind.
rm -rf update_tmp
mkdir update_tmp
trap 'rm -rf update_tmp' EXIT

echo "=== 2. Updating Code from GitHub ==="
if ! git pull --no-recurse-submodules; then
    echo "=== 2b. Syncing Submodules (fixing stale state) ==="
    rm -fr resources/dpd_submodules resources/tipitaka_translation_db
    git submodule sync
    git submodule update
fi

echo "=== 3. Updating Dependencies with uv ==="
uv sync
uv cache prune

echo "=== 4. Updating Data (Audio & Translations) ==="
uv run python audio/db_release_download.py
# uv run python resources/tipitaka_translation_db/download_and_unzip_db.py

echo "=== 5. Downloading Latest dpd.db ==="
wget -qO update_tmp/dpd.db.tar.xz https://github.com/sasanarakkha/dpd-db-sbs/releases/latest/download/dpd.db.tar.xz
tar -xJf update_tmp/dpd.db.tar.xz -C update_tmp
uv run python -c "import sqlite3, sys; n = sqlite3.connect(sys.argv[1]).execute('SELECT COUNT(*) FROM dpd_headwords').fetchone()[0]; sys.exit(0 if n else 'Error: new dpd.db has no headwords')" update_tmp/dpd.db
uv run tools/prepare_webapp_lookup.py update_tmp/dpd.db
mv update_tmp/dpd.db dpd.db
uv run exporter/webapp/generate_search_index.py

echo "=== 6. Killing Uvicorn Webapp ==="
pkill -f "uvicorn exporter.webapp.main_ru:app" || echo "No existing uvicorn process found."

# Wait a moment for ports to clear
sleep 2

# Start the app in the background using uv
# Ensure the logs directory exists in the dpd-db root
mkdir -p logs
LOG_FILE="logs/$(date '+%Y-%m-%d_%H-%M-%S').uvicorn.log"

echo "=== 7. Starting Uvicorn Webapp ==="
nohup uv run uvicorn exporter.webapp.main_ru:app --host 0.0.0.0 --port 8081 > "$LOG_FILE" 2>&1 &

echo "=== DONE ==="
echo "App started in background."
echo "Check logs with: tail -f $LOG_FILE"
ps -ef | grep uvicorn | grep -v grep

# scp scripts/server/update-dpd-sbs.sh django@85.215.66.115:~/update-dpd-sbs.sh
# cp scripts/server/update-dpd-sbs.sh ~/update-dpd-sbs.sh
```
**⚠ 2c-DEVIATION (B2)**: B2 said SKIP the `prepare_webapp_lookup.py` line; D11 later adopted the NOCASE
lookup for `toolkit_ru`, so the server db needs the index → line INCLUDED. Docs-site pull still skipped.
(`echo` is the established style of this server script, not a repo bash script under the ask.py rule.)
- Registry `sbs_copies["scripts/server/update-dpd-sbs.sh"].local_changes`: append
  `"Keeps the `git pull` failure fallback (submodule sync) that upstream does not have; no docs-site pull."`
- Verify: `bash -n scripts/server/update-dpd-sbs.sh`; `rg -c 'update_tmp' scripts/server/update-dpd-sbs.sh` ≥ 5.

**C8. S18 `shared_data/reference_ru/*`** (no LLM):
- `bibliography.tsv` (local == OLD upstream byte-for-byte, no RU columns):
  `git show c54f942ee3f6:shared_data/reference/bibliography.tsv > shared_data/reference_ru/bibliography.tsv`
- `abbreviations_other.tsv` (local == OLD upstream data, only CRLF line endings differ):
  `git show c54f942ee3f6:shared_data/reference/abbreviations_other.tsv > shared_data/reference_ru/abbreviations_other.tsv`
  (adopts upstream LF endings).
- `abbreviations.tsv` (has a local RU translation on row `abhi` → do NOT copy): replace the single
  occurrence `napuṁsakaliṅga` with `napuṃsakaliṅga` (line 149).
- Verify: `rg -c 'ṁ' shared_data/reference_ru/abbreviations.tsv shared_data/reference_ru/abbreviations_other.tsv`
  → no matches; `rg -c 'Oberlies|Levman|Malalasekera' shared_data/reference_ru/bibliography.tsv` ≥ 5;
  `rg -n '"абхи"' shared_data/reference_ru/abbreviations.tsv` still present.

**C9. D7 — stop automatic RU TPR export**
- `scripts/bash/make_dpd.sh`: delete line `uv run python exporter/tpr/tpr_exporter_ru.py` (l.47) and
  the blank line after it.
- `scripts/bash/make_ru_dpd.sh`: delete these lines and the blank line following each (l.58-63):
  `uv run python scripts/rus_exporter/check_tpr_download_index.py`,
  `uv run python exporter/tpr/tpr_exporter_ru.py`,
  `uv run python scripts/rus_exporter/check_tpr_download_index.py --skip-reset`.
- `.github/workflows/ru_release.yml`:
  - "Sync all submodules with Upstream" step: replace the loop body (l.306-318) with:
    ```yaml
            for submodule in resources/fdg_dpd; do
              echo "Syncing $submodule..."
              cd "$submodule"
              branch="main"
              git fetch origin $branch
              git checkout $branch
              git reset --hard origin/$branch
              cd ../..
            done
    ```
  - Delete the step `- name: Run TPR Exporter` + its `run:` line (l.335-336) and the blank line after.
  - "Update All Submodules": delete the line
    `          ["resources/tpr_downloads"]="tpr https://github.com/bksubhuti/tpr_downloads"`, and replace
    ```
              if [ "$path" = "resources/tpr_downloads" ]; then
                branch="master"
              else
                branch="main"
              fi
    ```
    with `          branch="main"` (same indentation as the surrounding `git checkout $branch`).
- `.github/workflows/ru_release_test.yml`: delete `    - name: Run TPR Exporter` + its `run:` line (l.308-309) and the blank line after.
- Verify: `rg -n 'tpr' scripts/bash/make_dpd.sh scripts/bash/make_ru_dpd.sh .github/workflows/ru_release.yml .github/workflows/ru_release_test.yml`
  → no matches; `uv run python -c "import yaml,sys; [yaml.safe_load(open(f)) for f in sys.argv[1:]]" .github/workflows/ru_release.yml .github/workflows/ru_release_test.yml`;
  `bash -n scripts/bash/make_dpd.sh scripts/bash/make_ru_dpd.sh`; `uv run pytest tests/scripts/bash -v` (if TPR assertions fail there, STOP → ADVANCED).
  Registry: in `inspired_by_upstream` entries for `scripts/bash/make_dpd.sh` / `make_ru_dpd.sh`, remove
  `tpr_exporter_ru.py` from the exporter-sequence `local_changes` strings (lines ~255, ~271).

**C10. D8 — deconstructor submodule retired**
- `scripts/bash/generate_components.sh`: replace line `uv run python scripts/build/tarball_deconstructor_output.py`
  with `uv run python scripts/build/deconstructor_output_add_to_db.py`; insert
  `uv run python scripts/build/decon_cache_update.py` + blank line between
  `uv run python db/epd/epd_to_lookup.py` and `uv run python exporter/webapp/generate_search_index.py`.
- `ru_release.yml`, `ru_release_test.yml` (l.56-61), `ru_release_kindle.yml` (l.53-58): delete the whole step
  ```yaml
      - name: Unzip deconstructor_output
        run: |
          cd ${{ github.workspace }}/resources/deconstructor_output
          tar -xzvf deconstructor_output.json.tar.gz
          ls -la
          cd ${{ github.workspace }}/
  ```
  (plus the trailing whitespace-only line). In all 3, immediately before `    - name: Run Deconstructor` insert:
  ```yaml
      - name: Generate Deconstructor
        run: go run go_modules/deconstructor/main.go

  ```
- `ru_release.yml`, `ru_release_test.yml`: after `      run: uv run python audio/index_release_download.py` add
  ```yaml
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  ```
- Submodule removal: `git rm resources/deconstructor_output` (also drops the `.gitmodules` entry; if
  `.gitmodules` still contains `deconstructor_output`, delete its 3-line block). Do NOT touch
  `.git/modules/...` (ask user after commit).
- `git rm exporter/sutta_central/sc_dict.json` (§6).
- Verify: `rg -n 'deconstructor_output\.json|tarball_deconstructor' scripts/bash .github/workflows` → none;
  `rg -c 'Generate Deconstructor' .github/workflows/ru_release*.yml` → 1 each; `rg -n deconstructor_output .gitmodules` → none;
  yaml parse as in C9 for all 3 workflows.

**C11. D9 — pre-range test orphans**: `git rm` every path in
`kamma/threads/20261105_upstream_sync/stage2a_findings/test_orphans_prerange.txt` (36 lines), as an
explicit list: `git rm $(cat kamma/threads/20261105_upstream_sync/stage2a_findings/test_orphans_prerange.txt)`.
Paths already deleted by P0 → drop them from the argument list and rerun.
- Verify: `for f in $(cat .../test_orphans_prerange.txt); do test ! -e $f || echo LEFT $f; done` prints nothing.

**C12. D5 openai retirement**
```
mkdir -p archive/dps/kamma_translate archive/dps/tests
git mv kamma/translate/scripts/ai_batch_openai_meaning.py archive/dps/kamma_translate/ai_batch_openai_meaning.py
git mv tests/kamma_tests/translate/test_ai_batch_openai_meaning.py archive/dps/tests/test_ai_batch_openai_meaning.py
```
- Verify: `rg -n 'ai_batch_openai_meaning' --glob '!archive/**' --glob '!kamma/threads/**' --glob '!kamma/archive/**' .`
  → only kamma/improve notes (no code/registry hits); `rg -n '^import openai|^from openai' --glob '!archive/**' .` → none.

**C13. Stale-reference cleanup**
- `git rm scripts/cl/dpd-gui2` (A0.3). Then `test ! -d scripts/cl || ls scripts/cl` → empty/absent.
- `kamma/upstream_sync/guide.md:375`: `scripts/cl/dpd-build-db` → `scripts/cl_dps/dpd-build-db`.
- Verify: `rg -n 'scripts/cl/' kamma/upstream_sync/ .claude/ scripts/ --glob '!**/archive/**'` → none.

### 9D. Webapp (D11, D12-webapp, S19, S20, S21)

Prereq: §9A pull done (brings `tools/{paths,version,search_deadline,server_mode,tipitaka_db,bold_definitions_search,configger,prepare_webapp_lookup}.py`,
`exporter/webapp/{toolkit,main,precompressed_index,response_encoding,generate_search_index}.py`, `static/cc_icons.svg`,
shared static css/js) and §9B B3/B4 (models `s_4nt_link`, `brotli`). `exporter/webapp/static/home.js` is registered
but unchanged upstream in range → no action.

**D-1. S20 `exporter/webapp/data_classes.py`** (registered, restored local):
`git diff be49bffe2c2c c54f942ee3f6 -- exporter/webapp/data_classes.py | git apply --3way`
- Verify: `rg -n 'make_permalink' exporter/webapp/data_classes.py` → 2 lines; local `config_test`/`self.ru`/`self.sbs` lines still present.

**D-2. S21 `exporter/webapp/static/app.js`** (registered, restored local):
`git diff be49bffe2c2c c54f942ee3f6 -- exporter/webapp/static/app.js | git apply --3way` — conflict markers → STOP → ADVANCED.
- Verify: `rg -c 'navigationState|searchURL|hasActiveQuery' exporter/webapp/static/app.js` ≥ 6;
  `rg -n '/sbs/search_json|sbs-pali-dictionary|devamitta.github.io/dpd.rus' exporter/webapp/static/app.js` → all 3 present;
  `node --check exporter/webapp/static/app.js`.
- Registry: update `modified_upstream_files[app.js].local_changes` line refs only if they cite line numbers.

**D-3. `exporter/webapp/data_classes_ru.py`**:
- **Q1 RESOLVED (user, 2026-11-05):** RU permalinks use `https://ru.dpdict.net/<id>` (served by the D-4
  `permalink_page` route in `main_ru.py`; same host as `tools/version_ru.py` `website` DbInfo). Do NOT import
  upstream `tools.version.make_permalink` (it yields English `https://dpdict.net/<id>`).
- After the last top-level import line of `data_classes_ru.py`, insert (blank line before and after):
  `RU_PERMALINK_BASE = "https://ru.dpdict.net"`
- After `        self.date = year_month_day_dash()` (inside `HeadwordData.__init__`, first occurrence) insert
  `        self.permalink = f"{RU_PERMALINK_BASE}/{i.id}"`
- Verify: `rg -n 'RU_PERMALINK_BASE' exporter/webapp/data_classes_ru.py` → 2 lines;
  `rg -n 'make_permalink' exporter/webapp/data_classes_ru.py` → 0 lines.
- Registry: add to `russian_copies[exporter/webapp/data_classes_ru.py].local_changes`:
  "`HeadwordData.permalink` uses local `RU_PERMALINK_BASE = https://ru.dpdict.net` instead of upstream
  `tools.version.make_permalink` (dpdict.net)." — then `validate_registry.py`. (If the path is in a different
  copies category, add it there; do not move it.)
- Verify: `uv run python -c "import exporter.webapp.data_classes_ru"`.

**D-4. `exporter/webapp/main_ru.py`** (Edit tool, in order):
1. Imports — replace
   ```python
   from fastapi.responses import HTMLResponse, Response, JSONResponse
   from fastapi.staticfiles import StaticFiles
   from fastapi.templating import Jinja2Templates
   from sqlalchemy.orm import sessionmaker
   ```
   with
   ```python
   from fastapi.responses import (
       HTMLResponse,
       JSONResponse,
       RedirectResponse,
       Response,
   )
   from exporter.webapp.precompressed_index import IndexStaticFiles
   from fastapi.templating import Jinja2Templates
   from sqlalchemy.exc import OperationalError
   from starlette.convertors import Convertor, register_url_convertor
   from sqlalchemy.orm import sessionmaker
   ```
   Add `import anyio` after `from contextlib import contextmanager` + blank line (i.e. first line of the
   third-party block, before `import uvicorn`). After `from audio.db.db_helpers import get_audio_record` add
   `from exporter.webapp.response_encoding import encode_search_response`. Replace
   `from exporter.webapp.toolkit import make_dpd_html` with
   ```python
   from exporter.webapp.toolkit import (
       LICENSE_LINK_HEADER,
       LICENSE_NOTICE,
       make_dpd_html,
   )
   ```
   After `from tools.pali_text_files import cst_texts` add
   `from tools.search_deadline import BUSY_MESSAGE, SearchStopped, regex_deadline, sub`; after
   `from tools.tipitaka_db import search_all_cst_texts, search_books` add `from tools.configger import config_test`.
2. Replace `app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])` with
   ```python
   # Link is not a CORS-safelisted response header, so without expose_headers the
   # licence notice is unreadable to cross-origin browser clients.
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_methods=["GET"],
       expose_headers=["Link"],
   )
   ```
   and `app.mount("/static", StaticFiles(directory=str(pth.webapp_static_dir)), name="static")` with
   ```python
   app.mount(
       "/static", IndexStaticFiles(directory=str(pth.webapp_static_dir)), name="static"
   )
   ```
3. After `templates_sbs = Jinja2Templates(directory=str(rupth.webapp_sbs_templates_dir))` insert:
   ```python
   # pyrefly: ignore  # jinja2 leaves Environment.globals unannotated, so its value
   # type infers as the union of jinja's own defaults; extending it is the
   # documented usage.
   templates_ru.env.globals["show_tbw"] = config_test("dictionary", "show_tbw", "yes")
   # pyrefly: ignore  # see above
   templates_sbs.env.globals["show_tbw"] = config_test("dictionary", "show_tbw", "yes")
   ```
4. `db_search_html_sbs`: in its `templates_sbs.TemplateResponse(...)` call, after the context dict's closing
   `},` add `        headers=LICENSE_LINK_HEADER,`. Same for `db_search_gd_ru` (`templates_ru.TemplateResponse`
   with `"home_simple_css": home_simple_css,` + `},`) and `db_search_gd_sbs`.
5. `db_search_json_ru` and `db_search_json_sbs` — replace in each (2 occurrences, use replace_all):
   ```python
       response_data = {"summary_html": summary_html, "dpd_html": dpd_html}
       headers = {"Accept-Encoding": "gzip"}
       return JSONResponse(content=response_data, headers=headers)
   ```
   with
   ```python
       response_data = {
           "summary_html": summary_html,
           "dpd_html": dpd_html,
           "license": LICENSE_NOTICE,
       }
       return encode_search_response(
           request, JSONResponse(content=response_data, headers=LICENSE_LINK_HEADER)
       )
   ```
6. Insert `BD_DISPLAY_LIMIT = 100` + 2 blank lines immediately before `@app.get("/bd_search", response_class=HTMLResponse)`.
   In `db_search_bd` replace from `    results = bd_searcher.search(q1, q2, option)` through the end of the
   `# trim to 100 results` block (`        too_many_results = True`) with:
   ```python
       too_many_results = False
       with regex_deadline() as deadline:
           try:
               # one row past the display limit tells us there are more
               results = bd_searcher.search(q1, q2, option, limit=BD_DISPLAY_LIMIT + 1)
               too_many_results = len(results) > BD_DISPLAY_LIMIT
               results = results[:BD_DISPLAY_LIMIT]

               if results:
                   count = f"{BD_DISPLAY_LIMIT}+" if too_many_results else len(results)
                   message = f"<b>{count}</b> результатов найдено"
               else:
                   message = "<b>0</b> результатов найдено - расширьте поиск или попробуйте опцию нечёткого поиска"

               # highlight search_2
               if q2:
                   # only the plain option treats q2 as text, not as a pattern
                   highlight = re.escape(q2) if option == "plain" else q2
                   for result in results:
                       result.commentary = sub(
                           f"({highlight}?)",  # Add ? to make quantifiers non-greedy
                           r"<span class='hi'>\g<1></span>",
                           result.commentary,
                       )
           except (SearchStopped, OperationalError):
               # SQLite wraps an error raised inside REGEXP, so ask the deadline
               if deadline.stopped is None:
                   raise
               results = []
               too_many_results = False
               message = deadline.stopped.message

       history_list = update_history(q1, q2, option)
   ```
   (the existing `history_list = update_history(q1, q2, option)` line between them is absorbed — ensure it
   appears exactly once afterwards; `deadline.stopped.message` stays English = upstream `BUSY`-style text.)
7. `tt_search`: replace
   ```python
       # Parse books (comma-separated list)
       books = [b.strip() for b in book.split(",") if b.strip()]
   ```
   with
   ```python
       q = q.strip()
       if not q:
           return JSONResponse(content={"total": 0, "results": []})

       # Parse books (comma-separated list), each searched once
       books = list(dict.fromkeys(b.strip() for b in book.split(",") if b.strip()))
   ```
   and replace
   ```python
       # Perform search
       if "all" in books:
           results = search_all_cst_texts(q, search_column=search_column)
       else:
           results = search_books(books, q, search_column=search_column)
   ```
   with
   ```python
       # Perform search. One row past the limit tells us there are more.
       try:
           with regex_deadline():
               if "all" in books:
                   results = search_all_cst_texts(
                       q, search_column=search_column, limit=limit + 1
                   )
               else:
                   results = search_books(
                       books, q, search_column=search_column, limit=limit + 1
                   )
       except SearchStopped as stopped:
           return JSONResponse(
               content={"total": 0, "results": [], "error": stopped.message}
           )
   ```
8. `get_audio`: `re.match(r"bytes=(\d+)-(\d*)", range_header)` → `re.match(r"bytes=(\d{1,15})-(\d{0,15})", range_header)`.
9. Insert immediately before `@app.middleware("http")` / `async def track_performance` the whole upstream block
   from NEW `exporter/webapp/main.py` comment `# Dictionary lookups take turns.` through the end of
   `async def lookups_take_turns` (copy literally: `git show c54f942ee3f6:exporter/webapp/main.py | sed -n '/^# Dictionary lookups take turns/,/^        lookup_limiter.release()/p'`), then apply exactly two local changes to the copy:
   - `LOOKUP_PATHS = {"/search_json", "/search_html", "/gd"}` →
     `LOOKUP_PATHS = {"/search_json", "/gd", "/sbs/search_json", "/sbs/search_html", "/sbs/gd"}`
     (`/search_html` does not exist in main_ru).
   - `    if path == "/search_json":` → `    if path in ("/search_json", "/sbs/search_json"):`
10. Insert immediately before `# Proactively monitor memory and performance` (the line above
    `Instrumentator().instrument(app).expose(app)`) the upstream block from `class HeadwordIdConvertor` through
    `    return RedirectResponse(url=f"/?q={headword_id}", status_code=308)` + 2 blank lines (copy literally:
    `git show c54f942ee3f6:exporter/webapp/main.py | sed -n '/^class HeadwordIdConvertor/,/status_code=308)/p'`).
- Verify: `rg -n 'StaticFiles\(|Accept-Encoding' exporter/webapp/main_ru.py` → only `IndexStaticFiles(`;
  `rg -c 'LICENSE_LINK_HEADER' exporter/webapp/main_ru.py` ≥ 6; `uv run python -c "import exporter.webapp.main_ru"`;
  then with the server (`uv run uvicorn exporter.webapp.main_ru:app --port 8099` in background):
  `curl -sI 'http://127.0.0.1:8099/search_json?q=dhamma' | rg -i '^link:'`,
  `curl -s 'http://127.0.0.1:8099/sbs/search_json?q=dhamma' | rg -c '"license"'`,
  `curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' http://127.0.0.1:8099/24043` → `308 .../?q=24043`,
  `curl -s 'http://127.0.0.1:8099/tt_search?q=%20&book=all&lang=P%C4%81%E1%B8%B7i'` → `{"total":0,"results":[]}`; stop server.
- Structural refactor check: YES (Accept-Encoding removal, bd body restructure, `re.sub`→`sub`) — included.

**D-5. `exporter/webapp/toolkit_ru.py`** (Edit tool, in order):
1. Dead-code removal FIRST: delete from the line `        dpd_html = ""` that directly follows
   `            time.sleep(0.1 * (attempt + 1))  # Exponential backoff` through the line
   `    return dpd_html, summary_html` that directly precedes `def find_closest_matches(` (local l.288–483),
   and put in their place (after a blank line following `time.sleep(...)`):
   ```python

       # Unreachable: the body returns on success and the handler re-raises on the
       # final attempt. Explicit rather than returning names bound in the `with`.
       raise RuntimeError(f"make_dpd_html_ru exhausted {retries} retries for {q!r}")
   ```
   Precheck: `sed -n 286,292p` shows `raise e` / `time.sleep` / `dpd_html = ""` / `summary_html = ""` / `q = q.replace(` /
   `q = q.casefold()`; `sed -n 481,486p` shows `return dpd_html, summary_html` then `def find_closest_matches(`.
2. `from sqlalchemy import or_` → `from sqlalchemy import literal_column, or_`; after
   `from exporter.webapp.data_classes_ru import (...)` block add `from exporter.webapp.toolkit import LICENSE_HTML`.
3. After `                    summary_html = ""` (inside the retry loop) insert
   ```python
                       # Set when the query fell through to suggestions, so the licence
                       # is not stamped on a "no results" page.
                       only_suggestions = False
   ```
4. Replace the live lookup query
   ```python
                       lookup_results = (
                           db_session.query(Lookup)
                           .filter(
                               or_(
                                   Lookup.lookup_key.ilike(q),
                                   Lookup.lookup_key.ilike(q + "."),
                               )
                           )
                           .all()
                       )
   ```
   with the upstream block (NEW `toolkit.py`, from `lookup_query = db_session.query(Lookup)` through
   `).all()` after `literal_column("lookup.rowid")`), indentation identical (20 spaces). Local
   `q = q.casefold()` stays (registered RU divergence; NOCASE covers it).
5. `                    if lookup_results:` → (with the 2 upstream comment lines)
   ```python
                       # a bare number is always a permalink to a headword id, so it
                       # skips the lookup table, where "3" is an abbreviation
                       if lookup_results and not q.isdecimal():
   ```
6. Replace
   ```python
                       elif q.isnumeric():  # eg 78654
                           search_term = int(q)
                           headword_result = (
                               db_session.query(DpdHeadword)
                               .filter(DpdHeadword.id == search_term)
                               .options(joinedload(DpdHeadword.ru))
                               .first()
                           )
   ```
   with
   ```python
                       # isdecimal, not isnumeric: "½" and "²" are numeric but int() rejects them
                       elif q.isdecimal():  # eg 78654
                           # 18 digits always fit SQLite's integer; a longer number
                           # is never an id, and would overflow the query
                           headword_result = (
                               db_session.query(DpdHeadword)
                               .filter(DpdHeadword.id == int(q))
                               .options(joinedload(DpdHeadword.ru))
                               .first()
                               if len(q) <= 18
                               else None
                           )
   ```
7. After each of the 3 remaining `dpd_html = find_closest_matches(` calls in `make_dpd_html_ru` add
   `only_suggestions = True` at the same indentation as `dpd_html` on the line after the call's closing `)`.
   Before `                    return dpd_html, summary_html` insert
   ```python
                       if dpd_html and not only_suggestions:
                           dpd_html += LICENSE_HTML

   ```
8. `find_closest_matches`: `    ascii_matches = ascii_to_unicode_dict[q]` →
   ```python
       # .get, not [q]: indexing a defaultdict would store an entry per distinct miss
       ascii_matches = ascii_to_unicode_dict.get(q, [])
   ```
- Verify: `rg -c 'isnumeric|ilike\(q\)' exporter/webapp/toolkit_ru.py` → 0 outside the NUL branch (`ilike(q_like`
  allowed); `rg -c 'only_suggestions = True' exporter/webapp/toolkit_ru.py` → 3; `wc -l` ≈ 360 (was 533);
  `uv run python -c "from exporter.webapp.toolkit_ru import make_dpd_html_ru"`; server check via D-4 curl:
  `curl -s 'http://127.0.0.1:8099/search_json?q=Dhamma' | rg -c license-line` ≥ 1 and
  `curl -s 'http://127.0.0.1:8099/search_json?q=zzqx' | rg -c license-line` → 0.
- Registry `russian_copies["exporter/webapp/toolkit_ru.py"].local_changes`: replace any line-number refs that
  pointed into the deleted dead block; add `"Imports `LICENSE_HTML` from upstream toolkit (no duplicate constants)."`
- Structural refactor check: YES (dead-code removal, isdecimal, `.get`) — included.

**D-6. `exporter/webapp/sbs_templates/dpd_headword.html`** (SBS = upstream English, port verbatim; Edit tool):
1. `        {% if d.su.tbw_legacy %}` → `        {% if d.su.tbw_legacy and show_tbw %}` (1 occurrence, l.449).
2. After the SC Voice row (the `{% endif %}` closing `{% if d.su.sc_voice_link %}`, l.494) + blank line insert the
   upstream `s_4nt_link` block (12 lines, `{% if d.su.s_4nt_link %}` … `{% endif %}` + blank line, as in NEW
   `templates/dpd_headword.html` l.482-493).
3. PTS/DV: replace (l.724-745)
   ```
           <!-- DV catalogue -->

           {% if not is_vagga and not is_samyutta %}

           {% if d.su.dv_exists %}
           <tr>
               <th class="heading" colspan="2">
                   Dhamma Vinaya Tools: Sutta Catalogue
               </th>
           </tr>
           {% endif %}

           {% if d.su.dv_pts %}
           <tr>
   ```
   with
   ```
           <!-- PTS concordance -->

           {% if not is_vagga and not is_samyutta %}

           {% if d.su.dv_pts %}
           <tr>
               <th class="heading" colspan="2">
                   Pali Text Society
               </th>
           </tr>
           <tr>
   ```
   and after that PTS row's closing `        {% endif %}` (the one following `{{ d.su.dv_pts }}` … `</tr>`) + blank line insert
   ```
           <!-- DV catalogue -->

           {% if d.su.dv_exists %}
           <tr>
               <th class="heading" colspan="2">
                   Dhamma Vinaya Tools: Sutta Catalogue
               </th>
           </tr>
           {% endif %}

   ```
4. l.1487 `            compounds which contains` (single-family block) →
   `            {% if d.fc[0].count == 1 %}compound which contains{% else %}compounds which contain{% endif %}`.
5. Multi-family block (l.1524-1527): move `            <a class="jump" href="#{{d.i.lemma_1_}}cf_top"> ⤴ </a>` from
   before `            {% endif %}` to after it (i.e. lines become `{% endif %}` then the `<a class="jump"...> ⤴ </a>`).
6. Feedback (l.1688-1691): before `    <div id="feedback_{{d.i.lemma_1_}}" class="dpd content hidden">` insert the upstream
   Jinja comment (5 lines `{# The feedback wording ... on purpose. #}`, from NEW l.1564-1568); after
   `        <p>ID <b>{{d.i.id}}</b></p>` insert
   ```
           <p>Permalink <a class="dpd-link" href="{{d.permalink}}"
                   target="_blank">{{d.permalink}}</a>
           </p>
   ```
7. Replace
   ```
                   . Did you spot a mistake in the dictionary? Have something
                   to
                   add?
   ```
   with `                . Did you spot a mistake in the dictionary?`.
8. Insert before the `<p>` that contains `Get involved` the upstream "How to cite" `<p>` (9 lines, NEW l.1625-1633),
   then replace the Get-involved `<a ...>Get involved</a><span>...</span>` content with upstream's
   ```
               <a class="dpd-link"
                   href="https://digitalpalidictionary.github.io/contributing/#offer-your-help"
                   target="_blank">
                   Contribute to DPD
               </a>
               <span>
                   . Contribute your time, skills or resources to the project.
                   Please use the form.
               </span>
   ```
   SBS-only feedback lines (SBS example mistake links) untouched.
- Verify: `rg -c 'show_tbw|s_4nt_link|Pali Text Society|Permalink|How to cite|Contribute to DPD' exporter/webapp/sbs_templates/dpd_headword.html`
  ≥ 6; `rg -n 'Have something|Get involved' exporter/webapp/sbs_templates/dpd_headword.html` → none;
  `uv run pytest tests/test_template_syntax.py -v`.

**D-7. `exporter/webapp/ru_templates/dpd_headword.html`** (RU layout differs; Edit tool):
1. l.425 `                {% if d.su.tbw_legacy %}` → `                {% if d.su.tbw_legacy and show_tbw %}`.
2. Inside the same `<td>`, after
   ```
                   {% if d.su.sc_voice_link %}
                   <a href="{{ d.su.sc_voice_link }}" target="_blank">sc-voice.net</a><br>
                   {% endif %}
   ```
   insert
   ```
                   {% if d.su.s_4nt_link %}
                   <a href="{{ d.su.s_4nt_link }}" target="_blank">s.4nt.org</a><br>
                   {% endif %}
   ```
   (`s_4nt_link` requires `sc_code`, so the enclosing `{% if d.su.sc_code %}` is correct.)
3. PTS/DV (l.641-660) — same transform as D-6.3 with RU headings: new PTS heading text
   `                Pali Text Society` (proper name, untranslated, as RU keeps "PTS"); moved DV heading keeps
   `                Дхамма Виная: Каталог Сутт`; RU comment `<!-- DV catalogue -->` → `<!-- PTS concordance -->` at top.
4. D12 RU plural — add at the very top of the file (line 1, before existing content):
   ```
   {% macro ru_plural(n, one, few, many) -%}
   {%- if n % 10 == 1 and n % 100 != 11 -%}{{ one }}
   {%- elif n % 10 in [2, 3, 4] and n % 100 not in [12, 13, 14] -%}{{ few }}
   {%- else -%}{{ many }}{%- endif -%}
   {%- endmacro %}
   ```
   then replace (strings for user review, see §9E table):
   - l.1255 `        слов(а) относящиеся к семье` →
     `        {{ ru_plural(d.i.fw.count, "слово, относящееся к семье", "слова, относящихся к семье", "слов, относящихся к семье") }}`
   - l.1275 `        составных содержащих` (single-family) →
     `        {{ ru_plural(d.fc[0].count, "составное слово, содержащее", "составных слова, содержащих", "составных слов, содержащих") }}`
   - l.1308-1312 (`{% if f.count == 1 %}` … `составное содержащее` … `{% else %}` … `составных содержащих` … `{% endif %}`) →
     `        {{ ru_plural(f.count, "составное слово, содержащее", "составных слова, содержащих", "составных слов, содержащих") }}`
   - l.1341-1345 (idiom `{% if f.count == 1 %}` … `идиоматическое выражение, которое содержит` … `{% endif %}`) →
     `        {{ ru_plural(f.count, "идиоматическое выражение, содержащее", "идиоматических выражения, содержащих", "идиоматических выражений, содержащих") }}`
   Multi-family ⤴ jump is already outside the if/else in RU (l.1314) → no move needed.
5. Feedback: after `    <p>ID <b>{{d.i.id}}</b></p>` (l.1463) insert
   ```
       <p>Постоянная ссылка <a class="dpd-link" href="{{d.permalink}}"
               target="_blank">{{d.permalink}}</a>
       </p>
   ```
   and before the `<p>` containing `Помощь проекту` insert
   ```
       <p>
           <a class="dpd-link" href="https://digitalpalidictionary.github.io/how_to_cite/" target="_blank">
               Как цитировать
           </a>
           <span>
               . DPD обновляется каждый месяц, поэтому, пожалуйста, указывайте версию, которой вы пользовались.
           </span>
       </p>
   ```
   (link target = upstream English page; no RU how-to-cite page exists in `docs_rus/` — Docs Track may add one later.)
- Verify: `rg -c 'show_tbw|s_4nt_link|Pali Text Society|ru_plural|Постоянная ссылка|Как цитировать' exporter/webapp/ru_templates/dpd_headword.html` ≥ 8;
  `rg -n 'слов\(а\)|составных содержащих$' exporter/webapp/ru_templates/dpd_headword.html` → none; render check via D-4 curl:
  `curl -s 'http://127.0.0.1:8099/search_json?q=dhamma%201' | rg -o 'составн[а-я ]+слов[а-я]*, содерж[а-я]+' | head -3`.

**D-8. Home templates** (Edit tool):
- `ru_templates/home.html` and `sbs_templates/home.html`:
  1. After the `<title>…</title>` line (l.8) insert the 3 upstream lines
     ```
         <link rel="preconnect" href="https://fonts.googleapis.com" />
         <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
         <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&amp;family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,700;1,8..60,400;1,8..60,700&amp;display=swap" />
     ```
  2. `<link rel="icon" type="image/png" href="/static/dpd-logo-dark.svg" />` → `type="image/svg+xml"`.
  3. Clear-history button: `title="Отчистить историю"` → `data-title="Отчистить историю"` (RU);
     `title="Clear history"` → `data-title="Clear history"` (SBS).
  4. Footer GitHub link (RU l.224, SBS l.223): `title="` → `data-title="` on that line only.
- SBS footer (l.217-221) additionally: replace
  ```
              <a href="https://digitalpalidictionary.github.io/webapp/" target="_blank">
                  read the docs
              </a>.
  ```
  with
  ```
              <a href="https://digitalpalidictionary.github.io/webapp/" target="_blank"
                  data-title="How to use the webapp, search syntax and features">
                  read the docs
              </a>
              &nbsp;|&nbsp;
              <a href="https://digitalpalidictionary.github.io/how_to_cite/" target="_blank"
                  data-title="DPD is revised every month — cite the version you used">
                  how to cite
              </a>
              &nbsp;|&nbsp;
              <span data-title="the release you are using">{{ dpd_release_version }}</span>
              &nbsp;|&nbsp;
  ```
- RU footer (l.219-222): add `data-title="Как пользоваться веб-приложением, синтаксис поиска и функции"` to the
  docs `<a>` (new line after `target="_blank"`), and after its `&nbsp;|&nbsp;` insert
  ```
              <span data-title="версия, которой вы пользуетесь">{{ dpd_release_version }}</span>
              &nbsp;|&nbsp;
  ```
  (RU "how to cite" footer link SKIPPED — it is in the feedback block, D-7.5.)
- TT footer Pa Auk→OpenTipitaka: neither local template has the Pa Auk link → SKIP.
- `ru_templates/home_simple.html` and `sbs_templates/home_simple.html`: after `<title>…</title>` (l.8) insert
  ```
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&amp;display=swap">
  ```
- Verify: `rg -c 'fonts.googleapis.com/css2' exporter/webapp/{ru,sbs}_templates/home*.html` → 1 per file (4);
  `rg -n 'image/png' exporter/webapp/{ru,sbs}_templates/home.html` → none; `uv run pytest tests/test_template_syntax.py -v`.

---
### 9E. GoldenDict + RU plural JS + Kindle (D12, S5, S6, S7, S11, I1, I2, I3)

Prereq: §9A pull done (models `s_4nt_link` via §9B B3; `tools/version.py` AUTHOR/DOI/EXAMPLE_*/make_citation/
make_permalink; `tools/configger.py` DEFAULT_CONFIG `dictionary.show_tbw`). All JS files below are hand-edited
(no 3-way possible: local files carry `ru_`/`sbs_` ids). Every JS file after editing: `node --check <file>`.
2c re-verified (session 5): RU/SBS GoldenDict sutta-info blocks are byte-identical to OLD upstream (offset +2 RU,
+17 SBS) → `patch` applies cleanly; RU kindle CSS is byte-identical to OLD upstream; upstream
`family_word_template.js`, `webapp/templates/root.html` and `goldendict/templates/root*.jinja` are unchanged in range.

**E-1. RU plural helper — `exporter/goldendict/ru_components/javascript/ru_main.js`** (loaded by both
`dpd_header.jinja` and `root_header.jinja`, same as `ru_superScripter`). Insert immediately after the closing `}` of
`function ru_superScripter(text) {` (+ blank line):
```js
// Russian count agreement: 1, 21, 101 → one; 2-4, 22-24 → few; 0, 5-20, 11-14, 25 → many.
// Mirrors the ru_plural Jinja macro in exporter/webapp/ru_templates/dpd_headword.html.
function ruPlural(n, one, few, many) {
    const mod10 = n % 10;
    const mod100 = n % 100;
    if (mod10 == 1 && mod100 != 11) return one;
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
    return many;
}
```
- Verify: `node -e "$(cat exporter/goldendict/ru_components/javascript/ru_main.js | sed -n '/^function ruPlural/,/^}/p'); for (const n of [1,2,5,11,12,21,22,25,101,111]) console.log(n, ruPlural(n,'one','few','many'))"`
  → `1 one`, `2 few`, `5 many`, `11 many`, `12 many`, `21 one`, `22 few`, `25 many`, `101 one`, `111 many`.

**E-2. D12/S5 `ru_family_compound_template.js`** — after `        itemTag = item.replace(/ /g, "_")` (inside
`familyCompoundList.forEach`, l.20) insert
```js
        const compounds = ruPlural(fc.count, "составное слово, содержащее", "составных слова, содержащих", "составных слов, содержащих")
```
then replace `` html += `<b>${fc.count}</b> составных слов(а) содержат `; `` (l.25) →
`` html += `<b>${fc.count}</b> ${compounds} `; `` and replace the single-family pair (l.31-32)
```js
            html += `<b>${fc.count}</b> составное слово содержащее `;
            html += `<b>${ru_superScripter(item)}</b>`;
```
with
```js
            html += `<b>${fc.count}</b> ${compounds} `;
            html += `<b>${ru_superScripter(item)}</b></p>`;
```
(the second line closes the missing `</p>` — upstream 904891e2f fix.)

**E-3. D12/S5 `ru_family_idiom_template.js`** — same shape. After `        itemTag = item.replace(/ /g, "_")` (l.20) insert
```js
        const idioms = ruPlural(fi.count, "идиома, содержащая", "идиомы, содержащие", "идиом, содержащих")
```
`` `<b>${fi.count}</b> идиом(ы) содержат ` `` (l.25) → `` `<b>${fi.count}</b> ${idioms} ` ``; single-family pair (l.31-32)
`` `<b>${fi.count}</b> идиома содержащая ` `` + `` `<b>${ru_superScripter(item)}</b>` `` →
`` `<b>${fi.count}</b> ${idioms} ` `` + `` `<b>${ru_superScripter(item)}</b></p>` ``.

**E-4. D12 `ru_family_root_template.js`** — replace the two lines (each ends with ONE trailing space)
```
            <b>${fr.count}</b> 
            слов(а) принадлежат к семье корня 
```
with
```
            <b>${fr.count}</b> ${ruPlural(fr.count, "слово, относящееся к семье корня", "слова, относящихся к семье корня", "слов, относящихся к семье корня")} 
```
(keep one trailing space so the following `<b>root</b>` stays separated).

**E-5. D12 `ru_family_word_template.js`** — replace (each ends with ONE trailing space)
```
            <b>${fw.count}</b> 
            слов(а), которые принадлежат к семье 
```
with
```
            <b>${fw.count}</b> ${ruPlural(fw.count, "слово, относящееся к семье", "слова, относящихся к семье", "слов, относящихся к семье")} 
```
(same wording as the webapp D-7.4 word-family heading.)

**E-6. D12/S5 `ru_family_set_template.js`** — replace both occurrences (replace_all) of
`` html += `<b>${fs.count}</b> слов в группе `; `` with
`` html += `<b>${fs.count}</b> ${ruPlural(fs.count, "слово в группе", "слова в группе", "слов в группе")} `; ``;
then in the single-set branch replace `` html += `<b>${item}</b>`; `` that directly follows the `_fs_top>` id line
(l.34, the 2nd occurrence — the 1st, l.28, is followed by the ⤴ jump line) with `` html += `<b>${item}</b></p>`; ``.

- Verify E-1…E-6: `rg -n 'слов\(а\)|идиом\(ы\)|содержат ' exporter/goldendict/ru_components/javascript/` → none;
  `rg -c 'ruPlural' exporter/goldendict/ru_components/javascript/ru_family_*_template.js` → compound 1, idiom 1,
  root 1, word 1, set 2; `node --check` on all 6 files.

**E-7. D12 RU feedback `ru_feedback_template.js`** (permalink + cite rows only; rest of RU text untouched; RU
GoldenDict feedback has no ID line, `data.id` is in the `rudata_` JSON from `dpd_header.jinja:43`):
- After the intro paragraph's closing line `    Список литературы можно увидеть в статье <b>литература</b>.</p>` insert
  ```
      <p>Постоянная ссылка <a class="dpd-link" href="https://ru.dpdict.net/${data.id}" target="_blank">https://ru.dpdict.net/${data.id}</a></p>
  ```
- Immediately before the `    <p>` whose next lines contain `href="mailto:devamitta@sasanarakkha.org">` insert
  ```
      <p>
          <a class="dpd-link"
          href="https://digitalpalidictionary.github.io/how_to_cite/">
          Как цитировать</a><span>. DPD обновляется каждый месяц, поэтому, пожалуйста, указывайте версию, которой вы пользовались.</span>
      </p>
  ```
- Verify: `rg -c 'ru.dpdict.net/\$\{data.id\}|Как цитировать' exporter/goldendict/ru_components/javascript/ru_feedback_template.js` → 2.

**E-8. S6 SBS family JS** (`exporter/goldendict/sbs_templates/javascript/`, English verbatim from upstream 904891e2f):
1. `sbs_family_compound_template.js`: after `    itemTag = item.replace(/ /g, "_");` (inside forEach, l.20) insert
   ```js
       const compounds =
         fc.count == 1 ? "compound which contains" : "compounds which contain";
   ```
   `` `<b>${fc.count}</b> compounds which contain ` `` → `` `<b>${fc.count}</b> ${compounds} ` ``;
   `` `<b>${fc.count}</b> compound which contains ` `` → `` `<b>${fc.count}</b> ${compounds} ` ``; and in the
   single-family branch the next line `` html += `<b>${superScripter(item)}</b>`; `` (the one directly before the
   branch's closing `    }`) → `` html += `<b>${superScripter(item)}</b></p>`; ``.
2. `sbs_family_idiom_template.js`: after `    itemTag = item.replace(/ /g, "_");` (l.20) insert
   ```js
       const idioms =
         fi.count == 1
           ? "idiomatic expression which contains"
           : "idiomatic expressions which contain";
   ```
   `` }</b> idiomatic expressions which contain <b>${superScripter(item)}</b>`; `` → `` }</b> ${idioms} <b>${superScripter(item)}</b>`; ``;
   `` }</b> idiomatic expression which contains <b>${superScripter(item)}</b>`; `` → `` }</b> ${idioms} <b>${superScripter(item)}</b></p>`; ``.
3. `sbs_family_root_template.js`: replace the line (ends with one trailing space)
   `            <b>${fr.count}</b> words belong to the root family ` with the 3 upstream lines
   ```
               <b>${fr.count}</b> ${
                 fr.count == 1 ? "word belongs" : "words belong"
               } to the root family 
   ```
4. `sbs_family_set_template.js`: the 2nd occurrence (single-set branch, l.32) of
   `` html += `<b>${lemma}</b> belongs to the set of <b>${setName}</b>`; `` →
   `` html += `<b>${lemma}</b> belongs to the set of <b>${setName}</b></p>`; `` (the 1st, l.27, is followed by the ⤴ line — unchanged).
- `sbs_family_word_template.js`: no upstream change in range → untouched.
- Verify: `rg -c 'compounds which contain|idiomatic expressions which contain|words belong' exporter/goldendict/sbs_templates/javascript/sbs_family_{compound,idiom,root}_template.js`
  → 1 each (inside the ternaries); `node --check` on the 4 files.

**E-9. S6 SBS feedback `sbs_feedback_template.js`** (upstream 3ae112bf9, df11da4e2, a5249fd37, 196f0e734):
1. Insert at line 1 (before `function sbs_makeFeedback(data) {`) the 5 upstream comment lines from NEW
   `exporter/goldendict/javascript/feedback_template.js` l.1-5 (`git show c54f942ee3f6:exporter/goldendict/javascript/feedback_template.js | sed -n 1,5p`).
2. After `    ID <b>${data.id}</b>` insert
   `    <p>Permalink <a class="dpd-link" href="https://dpdict.net/${data.id}" target="_blank">https://dpdict.net/${data.id}</a></p>`
   (SBS ids are DPD ids; same base as SBS webapp `d.permalink`, D-1).
3. `        Visit the DPD docs website</a><span>. Get more detailed information about installation and upgrades, advanced settings and features.</span>` →
   `        Read the docs</a><span>. Get more detailed information about installation on your devices, upgrades, advanced settings and features.</span>`
4. Replace the two `<p>` blocks "Help with coding" and "Help with Pāḷi" (l.48-57, the `mailto:` links with
   `help%20with%20code` / `help%20with%20DPD`) with upstream's "How to cite" + "Contribute to DPD" blocks — copy literally
   from NEW `feedback_template.js` (the two `<p>` blocks after "Read the docs"). "Join the mailing list" and all SBS-only
   form URLs stay.
- Verify: `rg -c 'Permalink|Read the docs|How to cite|Contribute to DPD' exporter/goldendict/sbs_templates/javascript/sbs_feedback_template.js` → 4;
  `rg -n 'Help with coding|Help with Pāḷi|Visit the DPD docs' …/sbs_feedback_template.js` → none; `node --check`.

**E-10. S7 GoldenDict headword templates** (`show_tbw`, `s_4nt_link` row, PTS/DV split) — apply upstream hunks by offset:
```
git diff be49bffe2c2c c54f942ee3f6 -- exporter/goldendict/templates/dpd_headword.jinja > $S/gd_hw.diff
patch --dry-run exporter/goldendict/ru_components/templates/dpd_headword_ru.jinja < $S/gd_hw.diff
patch --dry-run exporter/goldendict/sbs_templates/dpd_headword_sbs.jinja < $S/gd_hw.diff
```
Both dry-runs must report `Hunk #1..#4 succeeded` with offsets only (RU +2, SBS +17) and **no fuzz/FAILED** — else STOP →
ADVANCED. Then run the same two commands without `--dry-run`; delete any `*.orig` files. Headings stay English in RU
(RU GoldenDict sutta-info headings are already English: "Dhamma Vinaya Tools: Sutta Catalogue", "General Theme").
- Verify: `rg -c 'tbw_legacy and show_tbw|s_4nt_link|Pali Text Society|PTS concordance' exporter/goldendict/ru_components/templates/dpd_headword_ru.jinja exporter/goldendict/sbs_templates/dpd_headword_sbs.jinja`
  → ≥ 5 per file; `uv run pytest tests/test_template_syntax.py -v`.

**E-11. I1 `show_tbw` — `exporter/goldendict/export_dpd_ru.py` and `export_dpd_sbs.py`** (same 4 edits in each; template
dir string differs: RU `exporter/goldendict/ru_components/templates`, SBS `exporter/goldendict/sbs_templates`):
1. `DpdHeadwordRenderDataBase`: after `    show_id: bool` insert `    show_tbw: bool`.
2. `_worker_init`: replace the 4-line `# cast: …` comment + the whole `_WORKER_RENDER_DATA = cast(DpdHeadwordRenderData, {…},)`
   statement with (strict parity with upstream; `<TEMPLATE_DIR>` = the file's existing dir string):
   ```python
       jinja_env = get_jinja2_env("<TEMPLATE_DIR>")
       # pyrefly: ignore  # jinja2 leaves Environment.globals unannotated, so its
       # value type infers as the union of jinja's own defaults; extending it is
       # the documented usage.
       jinja_env.globals["show_tbw"] = render_data["show_tbw"]
       _WORKER_RENDER_DATA = DpdHeadwordRenderData(
           **render_data,
           pth=path,
           jinja_env=jinja_env,
       )
   ```
   Then `from typing import TypedDict, cast` → `from typing import TypedDict` **only if** `rg -n '\bcast\(' <file>` is empty
   after the edit (ruff F401 decides). If pyright/pyrefly reject the constructor form, STOP → ADVANCED (do not restore
   the cast silently).
3. `generate_dpd_html`: after `    show_id: bool = config_test("dictionary", "show_id", "yes")` insert
   `    show_tbw: bool = config_test("dictionary", "show_tbw", "yes")`.
4. `render_data` dict: after `        "show_id": show_id,` insert `        "show_tbw": show_tbw,`.
- Verify: `rg -c 'show_tbw' exporter/goldendict/export_dpd_ru.py exporter/goldendict/export_dpd_sbs.py` → 5 each; ruff/pyright/pyrefly
  clean on both; `uv run python -c "import exporter.goldendict.export_dpd_ru, exporter.goldendict.export_dpd_sbs"`.
- Registry: append to `local_changes` of both entries (whichever copies category they are in):
  "`show_tbw` render-data field + `jinja_env.globals` (upstream #252); `_worker_init` uses the TypedDict constructor like upstream."

**E-12. I2 citation help entry**
- **SBS `exporter/goldendict/export_help_sbs.py` — PORT:**
  1. Imports: after `from tools.goldendict_exporter import DictEntry` … insert `from tools.configger import config_read` before it
     (alphabetical in the `tools.` block) and after `from tools.tsv_read_write import …` add
     ```python
     from tools.version import (
         AUTHOR,
         DOI,
         EXAMPLE_ID,
         EXAMPLE_LEMMA,
         make_citation,
         make_permalink,
     )
     ```
     (ruff isort decides final order; run `ruff check --fix`.)
  2. In `generate_help_html`, after the `thanks` block (`    size_dict["help"] += len(str(thanks))`) insert
     ```python

         citation = add_citation(header)
         help_data_list.extend(citation)
         size_dict["help"] += len(str(citation))
     ```
  3. Append upstream `def add_citation(header: str) -> list[DictEntry]:` at end of file — copy literally:
     `git show c54f942ee3f6:exporter/goldendict/export_help.py | sed -n '/^def add_citation/,$p'`.
  - Verify: `uv run python -c "from exporter.goldendict.export_help_sbs import add_citation; e=add_citation('<html><head></head>'); print(e[0].word, len(e[0].definition_html))"` → `cite <n>`.
- **RU `export_help_ru.py` — SKIP (recommendation, confirm at 2d):** the entry cites the English DPD (AUTHOR, DOI,
  version, dpdict.net permalink, "second line after the feedback button" — RU GoldenDict feedback has no ID line).
  RU readers get the «Как цитировать» link via E-7 / D-7.5.

**E-13. I3 `exporter/goldendict/main_sbs.py`**: l.178 `<p>Digital Pāḷi Dictionary by Bodhirasa</p>` →
`<p>Digital Pāḷi Dictionary by Bodhirasa Bhikkhu</p>`; l.187 `author="Bodhirasa, SBS fork by Devamitta",` →
`author="Bodhirasa Bhikkhu, SBS fork by Devamitta",`. RU (`main_ru.py`, `grammar_dict_ru.py`, `deconstructor_exporter_ru.py`):
SKIP (S8 — «Дост. Бодхираса» already localised).
- Verify: `rg -c 'Bodhirasa Bhikkhu' exporter/goldendict/main_sbs.py` → 2.

**E-14. S11 Kindle RU (D6 minimal)**
1. `exporter/kindle/ru_components/templates/ebook_ru_letter.jinja` and `ebook_ru_rpd_letter.jinja`: line 20 `<body>` →
   `<body epub:type="dictionary">` (both already declare `xmlns:epub="http://www.idpf.org/2007/ops"` on l.12 — verified).
2. `exporter/kindle/ru_components/epub/OEBPS/Styles/dpd_kindle.css`: precheck
   `diff <(git show be49bffe2c2c:exporter/kindle/epub/OEBPS/Styles/dpd_kindle.css) exporter/kindle/ru_components/epub/OEBPS/Styles/dpd_kindle.css`
   → empty; then `git show c54f942ee3f6:exporter/kindle/epub/OEBPS/Styles/dpd_kindle.css > exporter/kindle/ru_components/epub/OEBPS/Styles/dpd_kindle.css`
   (only upstream change in range = 5-line hanging indent on `.body-space`, used by `ebook_ru_entry.jinja:12`).
3. `ru_components/epub/OEBPS/Text/nav.xhtml`: **SKIP — no dead links.** RU nav has only 4 links (titlepage,
   abbreviations, `0_a.xhtml`, `rpd_0_а.xhtml`); RU still generates `titlepage.xhtml` (`kindle_exporter_ru.py:298-305`)
   and lists it in `ebook_ru_content_opf.jinja` manifest/spine; no `#toc_id_*` fragments, no `21_dh` entry, no landmarks.
4. `titlepage.xhtml`: SKIP (upstream date-only; RU renders its own).
- Verify: `rg -c 'epub:type="dictionary"' exporter/kindle/ru_components/templates/ebook_ru_{letter,rpd_letter}.jinja` → 1 each;
  `rg -c 'hanging indent' exporter/kindle/ru_components/epub/OEBPS/Styles/dpd_kindle.css` → 1;
  `uv run pytest tests/test_kindle_jinja.py -v`.

**E-15. Smoke (Stage 3, after E-1…E-14):** `uv run python tests/smoke_test_sync.py` (covers RU JS presence + GoldenDict
RU/SBS export on the mini DB); manual GoldenDict check of a headword with 1 / 3 / 5+ compound-family members deferred to Stage 4.

#### RU strings for 2d review (D12; one vocabulary across webapp D-7.4 and GoldenDict E-2…E-7)

| Where | 1 (21, 101…) | 2–4 (22…) | 5+ / 11–14 / 0 | Was |
|---|---|---|---|---|
| Compound family (web + GD) | составное слово, содержащее | составных слова, содержащих | составных слов, содержащих | GD «составных слов(а) содержат» / «составное слово содержащее»; web «составных содержащих» |
| Idiom family (GD) | идиома, содержащая | идиомы, содержащие | идиом, содержащих | «идиом(ы) содержат» / «идиома содержащая» |
| Idiom family (web, D-7.4) | идиоматическое выражение, содержащее | идиоматических выражения, содержащих | идиоматических выражений, содержащих | «идиоматических выражений, которые содержат» |
| Word family (web + GD) | слово, относящееся к семье | слова, относящихся к семье | слов, относящихся к семье | GD «слов(а), которые принадлежат к семье»; web «слов(а) относящиеся к семье» |
| Root family (GD only) | слово, относящееся к семье корня | слова, относящихся к семье корня | слов, относящихся к семье корня | «слов(а) принадлежат к семье корня» |
| Set (GD only) | слово в группе | слова в группе | слов в группе | «слов в группе» (always genitive plural) |
| Feedback (web + GD) | «Постоянная ссылка» https://ru.dpdict.net/&lt;id&gt; · «Как цитировать» + «. DPD обновляется каждый месяц, поэтому, пожалуйста, указывайте версию, которой вы пользовались.» | | | — (new) |

Example renders: «**1** составное слово, содержащее **dhamma**», «**3** составных слова, содержащих **dhamma**»,
«**25** составных слов, содержащих **dhamma**», «**21** слово в группе …».
**RESOLVED (user, 2026-11-05):** GD idioms keep «идиома» — «идиома, содержащая / идиомы, содержащие / идиом, содержащих»
(E-3). Webapp D-7.4 keeps its existing «идиоматическое выражение» vocabulary. E-12 RU cite-entry SKIP approved; E-11
constructor swap approved; root.html item acknowledged (no action).
Out of scope, reported only: `exporter/webapp/ru_templates/root.html:44-46` still uses «слов(а) произошли от корня» —
upstream `root.html` is unchanged in range, so it is not part of this sync.

---
### 9F. gui2 Flet 1.0 (D4, D10, S2, S22, I10)

Prereq: §9A pull done; §9B B4 (`pyproject.toml` → `flet[all]==1.0.1`, `uv lock`, `uv sync --all-groups`) done.
All unregistered gui2 files (incl. `gui2/ui_utils.py`, `gui2/dpd_fields_classes.py`, `gui2/dpd_fields_examples.py`,
`gui2/mixins.py`, `gui2/pass2_add_view.py` per D10) are already upstream-verbatim from the pull. This section edits
only `gui2/main.py` (registered, restored to local by `execute_sync.py`) and the local `gui2/dps_*.py` files.

**2c facts (session 6, verified empirically in an isolated `uv run --no-project --with flet==1.0.1` env, plus an AST
scan of every `ft.*` attribute/constructor kwarg in `gui2/dps_*.py` against 1.0.1):**
- REMOVED in 1.0.1: `ft.ElevatedButton`, `ft.padding.all`, `ft.alignment.center`, `ft.app`, `Page.set_clipboard`,
  `Page.open`, `Dropdown(on_change=)` (→ `on_select`), `TextField.error_text` (→ `error`; assigning `error_text` on a
  bare `ft.TextField` is silently accepted and does nothing; `hasattr(bare_textfield, "error_text")` is `False`).
- DEPRECATED since 1.0.0, removed in 1.3.0: `border_color` / `border_radius` / `border_width` on TextField/Dropdown
  (upstream replaced all with `border=field_border(...)`).
- `Control.focus()` is a coroutine (un-awaited = silent no-op) → `gui2.ui_utils.request_focus`. `Control.page` is a
  property that raises `RuntimeError` when unmounted, so `self.page = ...` in an `ft.Column` subclass breaks.
- `DpdTextField`, `DpdExampleField` (base of `DpsExampleField`) and `DpsMeaningField` keep an `error_text`
  property that forwards to `error` → their call sites need no change.
- Font-scaler monkeypatch (`_make_font_scaler`) still works on 1.0.1: `ft.Text(size=10).size == 14`,
  `ft.TextStyle(size=10).size == 14`, `ft.TextField(text_size=10).text_size == 14`.
- `ft.dropdown.Option`, `Dropdown(editable=, enable_filter=, text_size=, hint_text=)`, `RadioGroup(on_change=)`,
  `IconButton(style=)`, `ButtonStyle(padding=, overlay_color=)`, `ft.Border/BorderSide` positional args,
  `ft.Button("text", width=, height=, tooltip=)` are all valid on 1.0.1.
- Still-valid upstream dependencies: `gui2.history.HistoryManager(toolkit, max_size=)` + `_history_path`/`_load()`/
  `register_refresh_callback` (unchanged in range); `gui2.dpd_fields_functions.clean_lemma_1`; `book_codes`;
  `db_tests.db_tests_manager.InternalTestRow`; `tools/cst_source/__init__.py` (registered unique) re-exports
  `CstSourceSuttaExample`/`find_cst_source_sutta_example`/`make_book_parser`/`make_cst_soup` → all exist at NEW;
  `tools/ai_related.py` is registered unique (not deleted by P0).
- **2a corrections:** (a) the `if clean_word:` guard needs NO local edit — it lives in the base
  `_handle_hyphens_and_apostrophes`, which `DpsExampleField` inherits (not overridden) → arrives with the pull.
  (b) 2a missed `self._page.set_clipboard(...)` in `dps_view.py` (removed API → AttributeError after every
  successful "Update DB") and the bare-TextField `error_text` rename (DPS test-failure highlighting in
  `dps_test_manager.py` and error clearing in `dps_fields.py` silently stop working). (c) `book_dropdown` in
  `dps_example_field.py` passes no `on_change` → nothing to rename. (d) `dps_view.py` stores `self._page` (not
  `self.page`) and all its init-time updates go through `self._page.update()` (Page object) → safe to build
  unmounted / off-thread, as upstream's lazy builder does.
- Type checks: `gui2/**` is in both `[tool.pyright].exclude` and `[tool.pyrefly].project-excludes`; run
  `uv run pyright --project /dev/null <f>` and `uv run --with pyrefly pyrefly check --min-severity warn <f>` on every
  file below. Baseline at HEAD (flet 0.28) is 0 errors for all of them. If either checker reports anything after the
  edits that a recipe below does not cover: STOP → ADVANCED (no `# type: ignore` / `# noqa`).

**F-1. D4 `gui2/main.py`** — rebuild from NEW, then re-apply the DPS layers. DpsView becomes tab **index 17**
(appended last; upstream indices 0–16 unchanged). Structural refactor check: YES — upstream rewrote the file
(lazy `_view_builders`, `TabBar`/`TabBarView`, async `on_keyboard`, `ft.run`); the local layers are re-applied on top,
not merged hunk-by-hunk.
1. `git show c54f942ee3f6:gui2/main.py > gui2/main.py`
2. Replace `from tools.fast_api_utils import start_dpd_server` → `from tools.fast_api_utils_dps import start_dpd_server`
   (D10: launches `exporter.webapp.main_ru`, keeps `/sbs/`).
3. After the line `from gui2.contributor_tabs import allowed_tabs, resolve_extra_tabs` insert
   `from gui2.dpd_fields_classes import DpdTextField`.
4. Immediately before the line `# Tab order must match the App._view_builders index keys.` insert (verbatim from
   HEAD, followed by two blank lines):
   ```python
   # DPS local: runtime font scaling — adjust _DPS_FONT_SCALE to retune
   _DPS_FONT_SCALE: float = 1.4


   def _make_font_scaler(original_init, attrs: tuple[str, ...], scale: float):
       def _scaled_init(self, *args, **kwargs):
           for attr in attrs:
               v = kwargs.get(attr)
               if isinstance(v, (int, float)):
                   kwargs[attr] = round(v * scale)
           original_init(self, *args, **kwargs)

       return _scaled_init


   ft.Text.__init__ = _make_font_scaler(ft.Text.__init__, ("size",), _DPS_FONT_SCALE)
   ft.TextStyle.__init__ = _make_font_scaler(
       ft.TextStyle.__init__, ("size",), _DPS_FONT_SCALE
   )
   ft.TextField.__init__ = _make_font_scaler(
       ft.TextField.__init__, ("text_size",), _DPS_FONT_SCALE
   )
   ft.Dropdown.__init__ = _make_font_scaler(
       ft.Dropdown.__init__, ("text_size",), _DPS_FONT_SCALE
   )

   _orig_dpd_tf_init = DpdTextField.__init__


   def _dpd_tf_init_scaled(self, *args, **kwargs):
       _orig_dpd_tf_init(self, *args, **kwargs)
       if self.text_size is None:
           self.text_size = round(14 * _DPS_FONT_SCALE)


   DpdTextField.__init__ = _dpd_tf_init_scaled
   ```
5. In `TAB_LABELS`, replace
   ```python
       "Infl",
   ]
   ```
   with
   ```python
       "Infl",
       "DPS",  # DPS local: index 17, appended last so upstream indices never shift
   ]
   ```
6. In `_WARMUP_TAB_ORDER`, replace `        15,\n    )` with `        15,\n        17,  # DPS local\n    )`
   (⚠ 2c-DEVIATION 9: keeps DPS pre-built like the old eager construction; upstream also leaves 16 out — drop this
   step if the user prefers DPS to build on first click).
7. In `App.__init__`'s local-import block, after `        from gui2.bold_search_view import BoldSearchView` insert
   `        from gui2.dps_view import DpsView`.
8. In `_view_builders`, after `            16: lambda: InflectionTemplatesTabView(self.page, self.toolkit),` insert
   `            17: lambda: DpsView(self.page, self.toolkit),  # DPS local`.
9. Profiler pyright fix (local, as at HEAD): after `    profile_file = Path("gui2_profile.prof")` insert
   `    profiler: cProfile.Profile | None = None`; replace `    if enable_profiling:\n        profiler.disable()` with
   `    if enable_profiling and profiler is not None:\n        profiler.disable()`.
10. Run the type checkers on `gui2/main.py`. If (and only if) they flag the `view.<name>(...)` calls inside
    `on_keyboard`'s Ctrl+S branch (attribute access on `ft.Control | None`), rewrite each flagged call to the HEAD
    pattern: `view._on_save_changes(None)` → `getattr(view, "_on_save_changes")(None)`, and
    `await view.test_and_add_to_db()` → `await getattr(view, "test_and_add_to_db")()` (same for each flagged
    name). Anything else flagged → STOP.
- Dropped from HEAD (superseded by upstream, no consumers — `rg "\.dps_view\b" -g '*.py'` hits only `main.py`):
  `self.dps_view` attribute, the `ft.Tab(text="DPS", content=self.dps_view)` entry, `ft.Theme(font_family="Inter")`
  one-liner (upstream two-line form kept).
- SKIP: Alt+X `_CLEAR_ACTIONS[17]` and an Alt jump key for DPS (new behaviour, not requested). Ctrl+S on DPS stays a
  no-op (DpsView has none of the probed methods). Page Up/Down now scrolls DPS for free (`DpsView._middle_section`
  is a scrollable `ft.Column`). `on_tab_focus` is `getattr`-guarded upstream → no DPS stub needed.
- Verify: `rg -n "fast_api_utils_dps import start_dpd_server|_DPS_FONT_SCALE: float = 1.4|\"DPS\",  # DPS local|17: lambda: DpsView|from gui2.dps_view import DpsView" gui2/main.py`
  → 5 hits; `rg -c "tools.fast_api_utils import" gui2/main.py` → 0;
  `diff <(git show c54f942ee3f6:gui2/main.py) gui2/main.py | rg -c '^[<>]'` → only the lines added above (plus any
  step-10 rewrites); `uv run python -c "import gui2.main as m; print(len(m.TAB_LABELS), m.TAB_LABELS[17])"` →
  `18 DPS`.
- Registry (Stage 3, §7): update `modified_upstream_files["gui2/main.py"].local_changes` line refs: import swap
  (~l.22), `DpdTextField` import, font-scaler block before `TAB_LABELS`, `"DPS"` label index 17, `_WARMUP_TAB_ORDER`
  17, local `DpsView` import in `App.__init__`, `_view_builders[17]`, profiler guard; set `discuss: false`,
  `sync_rule: "PORT"`; add `watch_for`: "upstream adding/reordering tabs must keep DPS last (index =
  len(upstream TAB_LABELS)); renumber `17` in TAB_LABELS/_view_builders/_WARMUP_TAB_ORDER if upstream adds a tab".

**F-2. S2 + S22 `gui2/dps_example_field.py`** (dps copy of `dpd_fields_examples.py`). Structural refactor check: YES —
cleaning helpers moved to `tools/example_cleaning.py`; Flet 1.0 API (borders, Button, page property, focus).
1. Replace `from gui2.dpd_fields_functions import clean_example` → `from tools.example_cleaning import clean_example`.
2. After `from gui2.toolkit import ToolKit` insert `from gui2.ui_utils import compact_button_style, field_border, request_focus`.
3. Delete the line `        self.page: ft.Page = ui.page` (after `ft.Column.__init__(self, expand=True)`).
4. `bold_field`: after the line `                "",` that opens `self.bold_field = ft.TextField(` insert
   `                border=field_border(),` (upstream parity; size/label values stay local).
5. `book_dropdown`: replace the three lines
   ```python
                   border_color=ft.Colors.GREY_800,
                   border_radius=20,
                   border_width=1,
   ```
   with `                border=field_border(color=ft.Colors.GREY_800),`.
6. `word_to_find_field`: replace `                border_radius=20,` (the line after
   `on_submit=self._click_search_dialog_ok,`) with `                border=field_border(),`.
7. `_actions_row`: replace every `ft.ElevatedButton(` (7×) with `ft.Button(` and add `style=compact_button_style()`
   to each, i.e. the seven entries become:
   ```python
                       ft.Button(
                           "Clean",
                           on_click=self.click_clean_example,
                           style=compact_button_style(),
                       ),
                       ft.Button(
                           "Delete",
                           on_click=self.click_delete_example,
                           style=compact_button_style(),
                       ),
                       ft.Button(
                           "Swap",
                           on_click=self.click_swap_example,
                           style=compact_button_style(),
                       ),
                       ft.Button(
                           "Stash",
                           on_click=self._click_stash_example,
                           style=compact_button_style(),
                       ),
                       ft.Button(
                           "Reload",
                           on_click=self._click_reload_example,
                           style=compact_button_style(),
                       ),
                       ft.Button(
                           "Last",
                           on_click=self._click_last_example,
                           style=compact_button_style(),
                       ),
                       ft.Button(
                           "Arch",
                           on_click=self._click_arch_example,
                           style=compact_button_style(),
                       ),
   ```
8. Replace `            self.word_to_find_field.focus()  # Focus on the field for quick editing` with
   `            request_focus(self.word_to_find_field)  # Focus on the field for quick editing`.
- Unchanged on purpose: `_active_page` (`cast(ft.Page, self.page)`) now reads the Column `page` property — only
  called from event handlers (mounted). Registry-documented omissions ([] / <b> buttons) stay omitted;
  `collapse_tools()` / `shift_enter` / `toolkit.example_stash_manager` SKIP (2a).
- Verify: `rg -c "ElevatedButton|border_radius|border_color|border_width|self\.page: ft\.Page|\.focus\(\)|dpd_fields_functions" gui2/dps_example_field.py`
  → 0; `rg -c "style=compact_button_style\(\)" gui2/dps_example_field.py` → 7;
  `uv run python -c "import gui2.dps_example_field"`.

**F-3. S22 `gui2/dps_meaning_field.py`** (dps copy of `dpd_fields_meaning.py`). Structural refactor check: YES —
upstream made the three handlers async + `asyncio.to_thread` spell check; SKIP that part (registry: local spell
check writes `error_text` directly, no `_skip_spell_check`); port only the 1.0-forced items.
1. After `from gui2.dpd_fields_classes import DpdTextField` insert
   `from gui2.ui_utils import field_border, is_mounted, request_focus`.
2. Delete the line `        self.page: ft.Page = self.ui.page`.
3. In `self.add_to_dict_field = ft.TextField(`, insert `            border=field_border(),` before
   `            label="Add Russian spelling ",`.
4. Replace `            self.meaning_field.focus()` with `            request_focus(self.meaning_field)`.
5. At the end of `_handle_spell_check`, replace the final
   ```python
               field.error_text = None
           self.page.update()
   ```
   with
   ```python
               field.error_text = None
           if is_mounted(self):
               self.page.update()
   ```
   (`_handle_add_to_dict_submit`'s `self.page.update()` stays: submit only fires on a mounted field.)
- Verify: `rg -c "self\.page: ft\.Page|\.focus\(\)" gui2/dps_meaning_field.py` → 0;
  `rg -n "border=field_border\(\)|request_focus\(self.meaning_field\)|if is_mounted\(self\):" gui2/dps_meaning_field.py`
  → 3 hits.

**F-4. S22 `gui2/dps_field_mapping.py`** (unique). Structural refactor check: none (config only).
1. After `import flet as ft` (and its blank line) insert `from gui2.ui_utils import field_border` above
   `from gui2.dps_example_field import DpsExampleField` (keep one blank line between the `flet` and `gui2` groups).
2. In `common_params`, replace
   ```python
       "border_color": ft.Colors.BLUE_200,
       "border_radius": 20,
   ```
   with `    "border": field_border(color=ft.Colors.BLUE_200),`.
- Consequence (accepted, upstream behaviour): the internal `DpdTextField`s of `DpsExampleField`/`DpsMeaningField`
  receive this border via `setattr`, but upstream `DpdTextField.before_update` resets them to grey
  `field_border()` (red on error) on every update → those 12 fields render grey instead of blue. Bare
  `ft.TextField`/`ft.Dropdown` DPS fields keep the blue border.
- Golden test follow-up = F-8.

**F-5. S22/I10 `gui2/dps_fields.py`** (inspired). Structural refactor check: YES upstream (lazy `page`, variant →
var_text) — no DPS anchor, SKIP; port only 1.0-forced items.
1. After `from gui2.toolkit import ToolKit` insert `from gui2.ui_utils import set_error`.
2. Replace `                        params["on_change"] = self._handle_sbs_chant_change` with
   `                        params["on_select"] = self._handle_sbs_chant_change`.
3. Replace all 5 `ft.ElevatedButton(` in `add_to_ui` with `ft.Button(` (args unchanged).
4. In `clear_all_fields`, replace the first branch
   ```python
               if isinstance(field, (ft.TextField, ft.Text)):
                   field.value = ""
                   field.error_text = None
   ```
   with
   ```python
               if isinstance(field, (ft.TextField, ft.Text)):
                   field.value = ""
                   if isinstance(field, ft.TextField):
                       field.error = None
   ```
5. In the `DpsExampleField` branch, replace `                    field.word_to_find_field.error_text = None` with
   `                    set_error(field.word_to_find_field, None)` (base class uses `set_error` on this bare
   field; its resting border is `field_border()` after F-2.6).
- Verify: `rg -c "ElevatedButton|params\[\"on_change\"\]" gui2/dps_fields.py` → 0;
  `rg -c "ft\.Button\(" gui2/dps_fields.py` → 5; `rg -n "field.error = None|set_error\(field.word_to_find_field, None\)" gui2/dps_fields.py` → 2 hits.

**F-6. S22/D10/I10 `gui2/dps_view.py`** (inspired). Structural refactor check: YES upstream (preview/save_router,
async handlers, PopupMenu) — SKIP per D10/registry; D10 constraint kept: `from tools.fast_api_utils_dps import
request_dpd_server` and the post-commit `request_dpd_server(str(self.headword.id))` stay untouched.
1. After `from gui2.toolkit import ToolKit` insert `from gui2.ui_utils import field_border`.
2. `_message_field`: replace
   ```python
               border_color=ft.Colors.BLUE_200,
               border_radius=20,
               border=ft.InputBorder.OUTLINE,
   ```
   with `            border=field_border(color=ft.Colors.BLUE_200),`.
3. `_enter_id_or_lemma_field`: replace (the pair after `            autofocus=True,`)
   ```python
               border_color=ft.Colors.BLUE_200,
               border_radius=20,
   ```
   with `            border=field_border(color=ft.Colors.BLUE_200),`.
4. `_history_dropdown`: replace `            border_radius=20,` with `            border=field_border(),` and
   `            on_change=self._handle_history_selection,` with `            on_select=self._handle_history_selection,`
   (the `RadioGroup`'s `on_change=self._handle_filter_change` stays — still valid).
5. Replace both `                padding=ft.padding.all(4), overlay_color=ft.Colors.TRANSPARENT` with
   `                padding=ft.Padding.all(4), overlay_color=ft.Colors.TRANSPARENT`; replace
   `            padding=ft.padding.all(10),` with `            padding=ft.Padding.all(10),`; replace
   `            alignment=ft.alignment.center,` with `            alignment=ft.Alignment.CENTER,`.
6. Replace all 5 `ft.ElevatedButton(` with `ft.Button(` (args unchanged).
7. Clipboard (removed `Page.set_clipboard`): replace
   ```python
                   self._page.set_clipboard(
                       self.headword.lemma_1
                   )  # Copy headword to clipboard
   ```
   with
   ```python
                   self._page.run_task(
                       self._copy_to_clipboard, self.headword.lemma_1
                   )  # Copy headword to clipboard
   ```
   and add this method directly before `    def _update_russian_table(self, headword_id: int) -> None:`:
   ```python
       async def _copy_to_clipboard(self, text: str) -> None:
           # Flet 1.0 removed Page.set_clipboard; the Clipboard service is async.
           await ft.Clipboard().set(text)

   ```
   (`_click_update_db` stays synchronous so the DB commit + `request_dpd_server` HTTP call keep running off the event
   loop; `run_task` sets the page context the `Clipboard` service registers against — verified in flet 1.0.1
   `Page.run_task` / `Service.__post_init__` source. Upstream uses `await ft.Clipboard().set(...)` in async handlers.)
- Verify: `rg -c "ElevatedButton|ft\.padding\.|ft\.alignment\.|border_radius|border_color|InputBorder\.OUTLINE|set_clipboard|on_change=self._handle_history_selection" gui2/dps_view.py`
  → 0; `rg -n "request_dpd_server" gui2/dps_view.py` → 2 hits (import + call, D10).

**F-7. S22/I10 `gui2/dps_test_manager.py`** (inspired). Structural refactor check: none found (upstream only added
`open_test_file`, SKIP per 2a).
1. After `from gui2.mixins import PopUpMixin` insert `from gui2.ui_utils import request_focus`.
2. In `run_all_tests`, replace
   ```python
               if isinstance(field, ft.TextField) and hasattr(field, "error_text"):
                   field.error_text = None
   ```
   with
   ```python
               if isinstance(field, ft.TextField):
                   field.error = None
   ```
   and replace
   ```python
                       if isinstance(field, ft.TextField) and hasattr(field, "error_text"):
                           field.error_text = f.test_name
   ```
   with
   ```python
                       if isinstance(field, ft.TextField):
                           field.error = f.test_name
   ```
   (on 1.0 `hasattr(bare_textfield, "error_text")` is False → highlighting silently stopped; `error` is the 1.0
   name on every `TextField`, incl. `DpdTextField`).
3. In `_handle_edit`, replace `                    field.focus()  # type: ignore` with `                    request_focus(field)`
   (the `hasattr(field, "focus")` guard above it stays — it skips the Column-based composite fields).
- Verify: `rg -c "error_text|\.focus\(\)" gui2/dps_test_manager.py` → 0 (the `error_text` hits were only these two
  pairs — re-check with `rg -n error_text gui2/dps_test_manager.py` before editing; if other hits exist, STOP).

**F-8. Tests touched by the 1.0 switch.**
1. `tests/gui2/test_dps_field_mapping.py` + `test_dps_field_mapping_fixtures.json` (local golden master; breaks on
   the pull anyway: control qualnames move `flet.core.*` → `flet.controls.material.*`, and `str(ft.Colors.X)` is now
   `"Colors.X"`). ⚠ 2c-DEVIATION 10 (test edit):
   - In the test, add `import flet as ft` after `from typing import Any` (+ blank line), and in `_serialize` insert
     before the `elif hasattr(value, "name") ...` branch:
     ```python
                 elif isinstance(value, ft.OutlineInputBorder):
                     ser_params[key] = {
                         "border_radius": value.border_radius,
                         "color": str(value.side.color) if value.side else None,
                     }
     ```
   - Transform the fixture deterministically (no regeneration from the mapping) with a scratch script under
     `temp/20261105_sync/` (delete after): for every entry, `params.pop("border_color")` and
     `params.pop("border_radius")`, then `params["border"] = {"border_radius": 20, "color": "Colors.BLUE_200"}`;
     map `control` `flet.core.textfield.TextField` → `flet.controls.material.textfield.TextField` and
     `flet.core.dropdown.Dropdown` → `flet.controls.material.dropdown.Dropdown`; write back with
     `json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"`. Before writing, assert every entry had
     `border_color == "blue200"` and `border_radius == 20`; if not, STOP.
   - Verify: `uv run pytest tests/gui2/test_dps_field_mapping.py -v` → 2 passed.
2. `tests/gui2/test_main.py` (NEW upstream, arrives with the pull; hard-codes the 17 upstream `TAB_LABELS` and asserts
   `tab_selection()` returns `range(len(TAB_LABELS))`) → fails once DPS is index 17. ⚠ 2c-DEVIATION 11: in the
   test's `TAB_LABELS` list replace `    "Infl",\n]` with `    "Infl",\n    "DPS",\n]`, and register
   `tests/gui2/test_main.py` in `modified_upstream_files` (`sync_rule: "PORT"`, `discuss: false`,
   `local_changes: ["\"DPS\" appended to TAB_LABELS (DPS tab index 17, see gui2/main.py)."]`,
   `watch_for: ["Keep TAB_LABELS in step with gui2/main.py TAB_LABELS."]`) so the next sync restores it.
   Verify: `uv run pytest tests/gui2/test_main.py -v`. Any failure not caused by the 17→18 label count → STOP.
3. `uv run pytest tests/test_dps_exporters_functional.py -k TestGuiMain -v` and `uv run pytest tests/test_dps_imports.py -v`
   (both import `gui2.main`). Failure → STOP.

**F-9. Headless construction check (Stage 3, after F-1…F-8)** — builds the DPS view exactly as the lazy builder does,
on the live `dpd.db` (reads only, same as a normal GUI launch):
`uv run python -c "from unittest.mock import MagicMock; from gui2.main import App; a = App(MagicMock()); v = a._view(17); print(type(v).__name__, len(v.dps_fields.fields))"`
→ `DpsView 61`. Exception → STOP.
Then `uv run python tests/smoke_test_sync.py` (Phase 3.3 GUI check).

**F-10. Manual GUI test (Stage 4, user):** `uv run python gui2/main.py` → DPS tab is last; fonts scaled 1.4×; load a
headword by id; SBS chant dropdown auto-fills chant_eng/chapter; history dropdown reloads a word; example tools
(toggle, book+word search, Clean/Swap/Stash/Reload/Last/Arch); Russian spell-check error under the meaning field;
Test with a deliberate failure → field highlighted + failure dialog Edit focuses the field; Update DB → RU/SBS
browser tab opens (`request_dpd_server`, `/sbs/`) and lemma lands on the clipboard; Clear All clears errors.
