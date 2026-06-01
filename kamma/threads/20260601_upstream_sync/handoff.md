# Handoff: Upstream Sync 2026-06-01

## Status

**Stage 4.B COMPLETE (FAST). Awaiting Stage 5 (ADVANCED).**

- Stage 3 COMPLETE. Commit 1 + Commit 2 prepared/run.
- Stage 4.A COMPLETE: parity report generated, glossary built, `docs_translation_plan.md` written and **user-approved 2026-06-01**.
- Stage 4.B COMPLETE: all 4 tasks executed, parity check run, commit message prepared.

- Phase A: complete, committed.
- Phase B: complete, committed.
- Phase C: execute_sync run (159 files). git rm 3 files. Commit 1 staged/ready.
- Phase D: all manual ports complete (D.1–D.11, D.13, D.14 + 2 unlisted fixes).
- Phase E: all verification passes — 233 pytest, smoke_test 24/0, check_shadow_modifications clean.
- Phase F: `git add .` run. Commit 2 message ready for user.

---

## Stage 4.B Work Completed (FAST)

**Files created/updated:**
1. **CREATED** `docs_rus/install/anki.md` — full translation per glossary + rules.
2. **UPDATED** `docs_rus/abbreviations.md` — inserted `|DNnt|Дигха Никая Новый подкомментарий|` between DNa and DNt rows.
3. **REWROTE** `docs_rus/install/chromebook.md` — full body replaced with approved RU text; H1 = `# Установка на Chromebook`.
4. **UPDATED** `mkdocs_ru.yaml` — inserted `    - Anki: "install/anki.md"` between Kobo and ChromeBook nav entries.

**Parity check result (`--strict`, with thread_dir):**
```
3 stale translations (exit 1)
  STALE    docs_rus/abbreviations.md
  STALE    docs_rus/install/anki.md
  STALE    docs_rus/install/chromebook.md
```

**NOTE on parity check:** The 3 STALE result is expected and correct. `check_docs_parity.py` compares git history between `from_upstream_sha=44a8a00` and `to_upstream_sha=0ea58833`. Those 3 EN docs files changed in that range, so they will always show STALE relative to that range. The script cannot detect that we translated them (it checks git history, not working tree content). **This will clear to 0 stale after `finalize_accepted_sync.py` advances `accepted_sync.json` in Stage 5.** The docs_translation_plan.md "→ must report 0 missing, 0 stale, exit 0" expectation was incorrect about Stage 4.B.

**Commit message (USER-RUN after git add):**
```
git commit -m "#docs: translate/update docs_rus/ for sync 44a8a00..0ea58833"
```

---

## Stage 4.A Work Completed (ADVANCED)

- Ran `check_docs_parity.py` (read-only; per handoff restart prompt) → `docs_parity_report.md` generated for range `44a8a00 → 0ea58833`.
- Built terminology glossary from `docs_rus/install/{browser_extension,dpd_app,index,chromebook}.md` + `docs_rus/abbreviations.md`.
- Wrote and got approval for `docs_translation_plan.md`.

**Approved scope — 3 files + 1 nav entry:**
1. CREATE `docs_rus/install/anki.md` (full translation of `docs/install/anki.md`, ~60 lines).
2. UPDATE `docs_rus/abbreviations.md` — insert ONE row between `DNa` and `DNt`: `|DNnt|Дигха Никая Новый подкомментарий|`.
3. REWRITE `docs_rus/install/chromebook.md` body (exact RU text given in plan TASK 3).
4. UPDATE `mkdocs_ru.yaml` — insert `    - Anki: "install/anki.md"` between Kobo and ChromeBook (only after anki.md exists).

**Scope correction (LOCKED):** `changelog.md` + `newsletters.md` are `NO_TRANSLATE` redirects per the authoritative parity script → SKIP. This supersedes the earlier handoff "Docs scope" note that called them updates. User confirmed proceeding on this basis.

**Stage 4.B commit message (USER-RUN):**
```
git commit -m "#docs: translate/update docs_rus/ for sync 44a8a00..0ea58833"
```

## Commit Messages (USER-RUN)

**Commit 1** (if not already run):
```
git commit -m "#sync: upstream pull 44a8a00..0ea58833, 159 files, 2026-06-01"
```

**Commit 2:**
```
git commit -m "#sync: manual merge resolutions 2026-06-01"
```

## Upstream Range
- From: `44a8a00556cce9bd3874a94efb5dfaceaaf20a66`
- To:   `0ea5883380f56b682cf8574043afb8e66cca3260` (upstream/main as of 2026-06-01)

---

## Stage 3 Work Completed

### Phase C
- `execute_sync.py` ran successfully — 159 files changed, 14 exclusions, `as_upstream` pinned to `0ea58833`.
- `git rm .zed/launch.json scripts/dbreader.py scripts/build/anki_updater.py` — all removed.
- C.4: `SUTTA_FIELDS` at line 243 in `gui2/dpd_fields_lists.py` ✓; `gui2/pass2_x_manager.py` exists ✓.
- `git add .` complete.

### Phase D — all items complete
- **D.1** `db/models.py` — `is_nipata`, `is_pannasaka`, AN nipāta SC link branch. ✓
- **D.2** `.gitignore` — 6 edits (`.zed/`, dpd.db-shm/wal, docs/rss.xml, scripts/suttas glob, graphify/pytest/ruff cache, removed `dpd/`). ✓
- **D.3** `family_compound_ru.py`, `family_root_ru.py`, `family_word_ru.py` — import path + `pr.green_title`. ✓
- **D.4** `exporter/webapp/main_ru.py` — CORSMiddleware. ✓
- **D.5** `exporter/webapp/ru_templates/dpd_headword.html` + `sbs_templates/dpd_headword.html` — 4 hunks each. ✓
- **D.6** `exporter/goldendict/ru_components/templates/dpd_headword_ru.jinja` + `sbs_templates/dpd_headword_sbs.jinja` — 4 hunks each. ✓
- **D.7** `shared_data/help_ru/abbreviations.tsv` — DNnt row inserted. ✓
- **D.8** `scripts/bash/generate_components.sh` — anki path updated. ✓
- **D.9** `tests/smoke_test_sync.py` — 5 import replacements. ✓
- **D.10** `gui2/pass2_add_view.py` — all 13 edits (SUTTA_FIELDS, Pass2XManager, _x_button, _click_x_button, _apply_sutta_prefill, _disable_id_field_autofocus, sutta Radio, filter logic, clear_all_fields). ✓
- **D.11** `exporter/goldendict/export_dpd_ru.py` + `export_dpd_sbs.py` — exitcode RuntimeError. ✓
- **D.13** `exporter/goldendict/data_classes_dps.py` — removed `"link"` from `_convert_newlines`. ✓
- **D.14** `exporter/webapp/data_classes_ru.py` — removed `"link"` from `convert_newlines`. ✓

### Additional unlisted fixes (discovered during Phase E)
- **Extra A** `db/tpd/tpd_to_lookup.py` + `db/rpd/rpd_to_lookup.py` — added `from tools.configger import config_read` and early-exit guard. Required to pass `test_shadow_parity` (upstream added `config_read` to `epd_to_lookup.py`; shadows needed same mirror).
- **Extra B** `exporter/goldendict/export_dpd_ru.py` + `export_dpd_sbs.py` — changed `if i.needs_sutta_info_button:` → `if i.su and i.needs_sutta_info_button:` before `i.su.sutta_codes_list`. D.11 exitcode check surfaced a pre-existing worker crash (None dereference) in the smoke test mini DB.

### Phase E Results
- `pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py` → 233 passed, 1 skipped, 0 failed ✓
- `python3 tests/check_shadow_modifications.py` → "SUCCESS: All shadow copies of modified upstream sources have been updated." ✓
- `python tests/smoke_test_sync.py` → 24 passed, 0 failed ✓
- ruff check + format: clean on all edited files (1 pre-existing F841 in family_word_ru.py not introduced by sync)
- pyright: 8 pre-existing errors (all in lines untouched by sync), 0 new
- pyrefly: pre-existing Flet pattern errors in pass2_add_view.py (follows existing idiom), 0 new

---

## Current Stage / Next Model

**Stage 4.B — FAST** in a fresh session.

Reads needed:
1. `kamma/threads/20260601_upstream_sync/handoff.md` (this file)
2. `kamma/upstream_sync/guide.md`
3. `kamma/threads/20260601_upstream_sync/docs_translation_plan.md` (the approved plan — execute literally)

Task: Execute `docs_translation_plan.md` TASK 1→4 literally, then run the `--strict` parity check. Do NOT analyze, redesign, or expand scope. Stop and request ADVANCED if any anchor is missing or terminology is unclear.

## Docs scope (FINAL — from approved docs_translation_plan.md)
Actionable (per authoritative `docs_parity_report.md`):
- `docs_rus/install/anki.md` — CREATE, full translation
- `docs_rus/abbreviations.md` — insert ONE DNnt row
- `docs_rus/install/chromebook.md` — rewrite body (exact RU text in plan)
- `mkdocs_ru.yaml` — add Anki nav entry (after anki.md exists)

SKIP (LOCKED): `changelog.md` + `newsletters.md` are NO_TRANSLATE redirects — no action. (Supersedes earlier handoff note that called them updates.)

Other skips (confirmed, not docs-parity items):
- home.html (ru + sbs) RSS → SKIP
- `tools/paths_ru.py` + `paths_dps.py` new attrs → SKIP (unused)
- `mkdocs_ru.yaml` `custom_dir` + upstream Anki nav → SKIP (Stage 4 only for local Anki nav)
- `ru_static.yml` RSS step + `uv sync` → SKIP

## Decisions (all LOCKED, do NOT re-ask)
- A1 db/models.py → PORT (DONE). A2 .gitignore → MERGE (DONE). A3 AGENTS.md → SKIP.
- Prep blocker_paths → code fix (DONE). Dirty-submodule → --ignore-submodules=dirty (DONE).
- C tools/ai_models.json → no_sync_files (DONE). pass2_add_view.py → PORT (DONE). D.11 exitcode → YES (DONE).
- SHA bump: `0ea58833` (DONE).
- D.13 + D.14 data_classes shadow port → DONE.
- Extra A/B (tpd/rpd config_read + su None guard) → applied during Stage 3.

## Errors, Issues, and Repeated Mistakes
- **Prior handoff A1 anchors were WRONG** (sc_link/dv_exists neighbors). Corrected Stage 2.
- `ruff --select E999` removed in current ruff; plan task 1.1 references `F821,E999` — drop E999.
- `resources/fdg_dpd` submodule fetch fails (remote not found) — pre-existing, not a blocker.
- Manifest `mapped_actions[].local_target_path` wrong for renamed goldendict shadows — D.6 used real paths.
- execute_sync has no discuss-acknowledge flag — manual `discuss_paths:[]` edit required.
- A.1 registry edit caused validate_registry overlap (`db_tests/` vs the specific unique_path entry); fixed.
- **Dirty submodule blocker (RESOLVED):** `--ignore-submodules=dirty` in execute_sync (B.1).
- **Upstream SHA drift:** upstream/main moved 4 commits past planned target during work. Resolved by bumping `prep_manifest.json.to_upstream_sha` to current upstream/main and adding D.13/D.14.
- **Shadow parity test failure (resolved):** upstream added `config_read` to `epd_to_lookup.py`; tpd/rpd shadows needed same mirror — fixed in Extra A.
- **Smoke test worker crash (resolved):** D.11 exitcode check surfaced pre-existing `i.su = None` dereference in export_dpd_ru/sbs — fixed with `if i.su and i.needs_sutta_info_button:` in Extra B.
- **Pre-existing F841:** `family_word_ru.py:132` unused `add_to_db = []` — pre-existing, not introduced by sync, ruff can't auto-fix without --unsafe-fixes.
- **Parity check can't pass at Stage 4.B:** `check_docs_parity.py --strict` compares git history between the two upstream SHAs; translated files remain "STALE" (git history is immutable) until `finalize_accepted_sync.py` advances `accepted_sync.json` in Stage 5. The plan's "→ must report 0 missing, 0 stale, exit 0" expectation applies post-Stage 5, not post-4.B.

## Restart Prompt
```text
Switch to FAST. Start a fresh session.

Continue upstream sync thread: kamma/threads/20260601_upstream_sync.

First read:
1. kamma/threads/20260601_upstream_sync/handoff.md
2. kamma/upstream_sync/guide.md
3. kamma/threads/20260601_upstream_sync/docs_translation_plan.md

This is Stage 4.B (FAST). Execute docs_translation_plan.md literally, TASK 1 → TASK 4:
  1. CREATE docs_rus/install/anki.md (full translation per glossary + rules).
  2. UPDATE docs_rus/abbreviations.md — insert the one DNnt row.
  3. REWRITE docs_rus/install/chromebook.md body (exact RU text in plan TASK 3).
  4. UPDATE mkdocs_ru.yaml nav (Anki entry between Kobo and ChromeBook), only after anki.md exists.
Then run: uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py kamma/threads/20260601_upstream_sync --strict
Record the result in handoff.md and prepare commit message:
  #docs: translate/update docs_rus/ for sync 44a8a00..0ea58833

Do NOT analyze, redesign, or expand scope. Do NOT touch changelog.md or newsletters.md (NO_TRANSLATE redirects). Stop and request ADVANCED if any anchor is missing or terminology is unclear.

Stage 3 and Stage 4.A are fully complete. The plan is user-approved.
```
