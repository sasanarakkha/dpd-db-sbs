# Handoff: Upstream Sync 2026-06-01

## Status

**Stage 3 — Phases A + B DONE (committed). Manifest SHA bumped. Awaiting USER commit of SHA bump, then Phase C.**

- Phase A: complete, committed (all 6 steps).
- Phase B.1: `execute_sync._check_if_dirty` patched with `--ignore-submodules=dirty`. ✓
- Phase B.2: pre-sync commit `#pre-sync: clear sync blockers, ack discuss, 2026-06-01` ✓ (d3a82e75)
- Manifest SHA bump: `prep_manifest.json.to_upstream_sha` updated from `40083765` → `0ea58833`.
  Staged. USER must commit before Phase C.

## Current Stage / Next Model

**FAST** — after USER commit of SHA bump, FAST continues Phase C → D → E → F.
Do NOT re-analyze decisions; all locked.

## Upstream Range (UPDATED)
- From: `44a8a00556cce9bd3874a94efb5dfaceaaf20a66`
- To:   `0ea5883380f56b682cf8574043afb8e66cca3260` (upstream/main as of 2026-06-01)
  - Original planned target was `40083765d770...` but upstream moved to `0ea58833` (4 new commits).
  - Bumped to current upstream/main; additional shadow work is 5 single-line edits (see D.3+ and D.13/D.14 below).

## Why the SHA was bumped (do NOT re-litigate)

Upstream/main moved 4 commits past the planned target. The 4 new commits:
1. `58bdda2a` docs: update changelog — docs only, no shadow.
2. `13cf0e9c` exporter: fix multi-link href — 1 line each in `data_classes.py` x2; shadows `data_classes_dps.py` + `data_classes_ru.py` need same fix (D.13, D.14).
3. `3431ac5f` pali update — data TSV only, no shadow.
4. `0ea58833` makedict-quick — `family_root/set/word.py` `pr.green_tmr→pr.green_title` (1 line); shadows need same fix in D.3+ step.

Decision: proceed with full current range. Additional port work is entirely mechanical.

---

## Open items for next session (FAST)

1. **SHA-bump commit (first thing):** Confirm user ran:
   `git commit -m "#pre-sync: bump manifest sha to current upstream/main 0ea58833"`
   Then verify: `git status --porcelain --ignore-submodules=dirty` is EMPTY.

2. **Phase C.1:** `uv run python3 kamma/upstream_sync/scripts/execute_sync.py kamma/threads/20260601_upstream_sync`

3. **Phase C.2:** git rm 3 files:
   - `git rm .zed/launch.json`
   - `git rm scripts/dbreader.py`
   - `git rm scripts/build/anki_updater.py`
   (`.claude/commands/dpd-newsletter.md` already absent — verified.)

4. **Phase C.3:** Review git diff → `git add .` → present Commit 1 for user:
   `#sync: upstream pull 44a8a00..0ea58833, <N> files, 2026-06-01`

5. **Phase C.4 post-pull dependency checks:**
   - `rg -n "^SUTTA_FIELDS = " gui2/dpd_fields_lists.py` — must exist
   - `test -f gui2/pass2_x_manager.py` — must exist
   If either missing, STOP before D.10.

6. **Phase D — manual ports (all decisions locked):**
   - D.1: `db/models.py` — PORT (3 hunks per dynamic_plan.md)
   - D.2: `.gitignore` — MERGE (6 edits per dynamic_plan.md)
   - D.3: family imports mirror — `family_compound_ru.py`, `family_root_ru.py`, `family_word_ru.py`:
     - Replace `from scripts.build.anki_updater import family_updater` → `from exporter.anki.anki_updater import family_updater`
     - **ALSO** replace `pr.green_tmr("disabled in config.ini")` → `pr.green_title("disabled in config.ini")` (new from makedict commit 0ea58833; verify line exists first with rg)
   - D.4: `exporter/webapp/main_ru.py` — CORS middleware
   - D.5: webapp templates ru + sbs — 4 hunks each
   - D.6: goldendict jinja templates ru + sbs — 4 hunks each
   - D.7: `shared_data/help_ru/abbreviations.tsv` — DNnt row
   - D.8: `scripts/bash/generate_components.sh` — anki path update
   - D.9: `tests/smoke_test_sync.py` — 5 import replacements
   - D.10: `gui2/pass2_add_view.py` — PORT (13 edits per dynamic_plan.md)
   - D.11: `exporter/goldendict/export_dpd_ru.py` + `export_dpd_sbs.py` — exitcode check (approved YES)
   - **D.13 (NEW):** `exporter/goldendict/data_classes_dps.py` — remove `"link"` from `_convert_newlines` list (mirror of upstream `13cf0e9c`)
   - **D.14 (NEW):** `exporter/webapp/data_classes_ru.py` — remove `"link"` from `convert_newlines` list (mirror of upstream `13cf0e9c`)

7. **Phase E:** Full verification suite (per dynamic_plan.md Phase E).

8. **Phase F:** `git add .` → present Commit 2 for user:
   `#sync: manual merge resolutions 2026-06-01`

## Decisions (all LOCKED, do NOT re-ask)
- A1 db/models.py → PORT (D.1). A2 .gitignore → MERGE (D.2). A3 AGENTS.md → SKIP.
- Prep blocker_paths → no_sync_files code fix (Phase A) — DONE.
- Dirty-submodule blocker → Option 2 (`--ignore-submodules=dirty`) — DONE.
- C tools/ai_models.json → no_sync_files — DONE.
- pass2_add_view.py → PORT (D.10). D.11 export_dpd exitcode → YES.
- SHA bump: proceed with `0ea58833` (current upstream/main) — DECIDED this session.
- D.13 + D.14 data_classes shadow port → YES (mechanical 1-line mirrors).
- Skips (prose only): home.html RSS, paths_ru/dps attrs, mkdocs_ru custom_dir + Anki nav, ru_static.yml RSS + uv sync.

## D.13 / D.14 Detail (new, not in dynamic_plan.md)

### D.13 `exporter/goldendict/data_classes_dps.py` — mirror exporter fix
Find the `_convert_newlines` list. Remove the entry `"link"` from it.
Upstream diff: one line deleted from `exporter/goldendict/data_classes.py` (commit 13cf0e9c).
→ verify: `rg -n '"link"' exporter/goldendict/data_classes_dps.py` returns nothing in that list.

### D.14 `exporter/webapp/data_classes_ru.py` — mirror exporter fix
Find the `convert_newlines` list. Remove the entry `"link"` from it.
Upstream diff: one line deleted from `exporter/webapp/data_classes.py` (commit 13cf0e9c).
→ verify: `rg -n '"link"' exporter/webapp/data_classes_ru.py` returns nothing in that list.

## Errors, Issues, and Repeated Mistakes
- **Prior handoff A1 anchors were WRONG** (sc_link/dv_exists neighbors). Corrected Stage 2.
- `ruff --select E999` removed in current ruff; plan task 1.1 references `F821,E999` — drop E999.
- `resources/fdg_dpd` submodule fetch fails (remote not found) — pre-existing, not a blocker.
- Manifest `mapped_actions[].local_target_path` wrong for renamed goldendict shadows — D.6 uses real paths.
- execute_sync has no discuss-acknowledge flag — manual `discuss_paths:[]` edit required.
- A.1 registry edit caused validate_registry overlap (`db_tests/` vs the specific unique_path entry); fixed.
- **Dirty submodule blocker (RESOLVED):** `--ignore-submodules=dirty` in execute_sync (B.1).
- **Upstream SHA drift:** upstream/main moved 4 commits past planned target during work. Resolved by bumping `prep_manifest.json.to_upstream_sha` to current upstream/main and adding D.13/D.14.

## Next Model
**FAST.**

## Restart Prompt
```text
Start a fresh session.

Continue upstream sync thread: kamma/threads/20260601_upstream_sync.

First read:
1. kamma/threads/20260601_upstream_sync/handoff.md
2. kamma/threads/20260601_upstream_sync/dynamic_plan.md (for D.1–D.11 literal hunks)

Confirm the user ran: git commit -m "#pre-sync: bump manifest sha to current upstream/main 0ea58833"
Then verify git status --porcelain --ignore-submodules=dirty is EMPTY.

Then execute Phase C → D (including D.13 + D.14 from handoff.md) → E → F literally.
All commits are USER-RUN. Stop only if a plan anchor is missing or a test fails unexpectedly.
```
