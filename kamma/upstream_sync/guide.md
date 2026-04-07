# Upstream Sync Protocol

> This is the canonical protocol for running `/update-upstream`. For per-file merge
> guidance, see `smd.md`. For accumulated lessons, see `archive_improvements.md`.
> For lessons from the most recent run, see `new_improvements.md` (if it exists).

---

## Iron Rule

**When a shadow file breaks after sync, the ONLY permitted fix is:**
1. Open the upstream source file.
2. See exactly how upstream implements the broken functionality.
3. Copy that exact solution into the shadow.
4. Re-apply ONLY the local changes listed in `smd.md` for that file.

**FORBIDDEN:**
- Workarounds, patches, or logic not present in the upstream source.
- Alternative libraries or imports not used by upstream.
- `try/except` blocks that paper over the real issue.
- Restructuring the file differently from upstream.

**The upstream sources are correct and carefully tested.
A broken shadow always means the sync is incomplete or inaccurate — not that the source has a bug.**

---

## When the User Reports an Error After Sync

This is the most critical part of the process. Follow this exactly:

1. **DO NOT invent a new solution.**
2. Read the upstream source file for the broken functionality (`git show as_upstream:<path>`).
3. Identify the exact lines that implement the feature that is now broken.
4. Port those exact lines to the shadow — nothing more, nothing less.
5. Re-apply ONLY the SMD-listed local changes for that file.
6. Re-run automated tests and report results.
7. **Do NOT assume the error is fixed.** Wait for the user to confirm.

If you are tempted to add a try/except, change an import, or take a different approach than upstream — STOP. That is a signal the sync is incomplete, not that a workaround is needed.

---

## Discussion Flag Protocol

Before touching ANY `modified_upstream_files` entry in the registry, check its `discuss` field.

If `discuss: true`:
!TODO! double check if all modified files which need manual attention have that flag set to true
1. **STOP.** Do not modify the file.
2. Run `git diff as_upstream -- <path>` and present the full diff to the user.
3. State the `discuss_reason` from the registry entry.
4. Wait for explicit **"Approved: [decision]"** from the user.
5. Log the decision in `dynamic_plan.md` before proceeding.

---

## Registry Categories

| Category | Key | Description |
|---|---|---|
| `modified_upstream_files` | object array | Upstream files where this fork diverges. Each entry: `path`, `discuss` (bool), `discuss_reason`. When `discuss: true`, do NOT port blindly — read `smd.md` first. |
| `russian_copies` | `shadow: upstream` map | Shadow files that mirror an upstream source with Russian-specific additions. Tier 2/3 symbols use `_ru` suffix. |
| `sbs_copies` | `shadow: upstream` map | Shadow files that mirror an upstream source with SBS-specific additions. Tier 2/3 symbols use `_sbs` suffix. |
| `dps_copies` | `shadow: upstream` map | Shadow files that serve BOTH Russian and SBS locales. Shared Tier 2/3 symbols may use `_dps`, but RU-only helpers keep `_ru` and SBS-only helpers keep `_sbs`. |
| `unique_paths` | string array | Files/dirs that exist only in this fork. Never in upstream; never auto-synced. |
| `no_sync_files` | string array | Paths that must never be overwritten by an upstream sync (fork-only infrastructure). |
| `ignored_files` | string array | !TODO! (we do not use it at all, I forgot what was the purpose of that list, please analyze and suggest) Paths ignored during sync scanning (build artifacts, local-only dirs). |
| `folders_to_check` | string array | Top-level directories included in sync diff analysis. |

---

## Shadow Copy Merge Strategies

### PORT
Apply upstream changes to the shadow, then re-apply localized additions on top.
Steps:
1. `git diff <old_upstream>..<new_upstream> -- <upstream_file>` to see the upstream delta.
2. Apply that delta to the shadow file.
3. Verify localized additions (imports, columns, RU/SBS data) are still intact.
4. Run `uv run pytest tests/test_shadow_parity.py -k <shadow_basename>`.

### MIRROR_EXACTLY
Shadow must be byte-for-byte identical to upstream (e.g., template directories where
all localization is in a separate namespaced copy). Simply overwrite from upstream.
 d
### PRESERVE
Fork-specific content that has no upstream equivalent. Do not sync; only update manually.

### DISCUSS
High-risk file where blind porting would delete localized data. Stop, read the SMD entry,
and plan explicitly before touching the file.

---

## Symbol Naming Policy for Shadow Copies

To maintain namespace isolation and ensure that shadow copies do not accidentally
collide with or overshadow upstream symbols during synchronization, the following
naming policy is enforced via `tests/test_namespace_isolation.py`:

### Tier 1 — Identical to Upstream
- **Rule**: Symbol MUST remain unmarked (exactly matching upstream).
- **Signal**: Safe to overwrite or update during sync if the logic remains identical.

### Tier 2 — Modified from Upstream
- **Rule**: Symbol MUST have a clear locale marker matching the registry category. An underscore suffix is preferred, but an existing clear marker already in the symbol name is also valid, such as `RuSpellChecker`, `SBSExporter`, or `DPSPaths`.
- **Signal**: Check upstream diff carefully before syncing; localized logic is present.

### Tier 3 — New (no upstream counterpart)
- **Rule**: Symbol MUST have a clear locale marker matching the registry category. Do not add a second marker when the symbol already clearly includes `RU`, `SBS`, or `DPS` in its name.
- **Signal**: Fork-only feature; no sync required, but must remain isolated.

### DPS File Rule
- `*_dps.py` means the file serves both locales, not that every helper inside it must end in `_dps`.
- Use `_dps` only for genuinely shared DPS logic.
- If a helper works only with Russian data inside a DPS file, keep `_ru` only.
- If a helper works only with SBS data inside a DPS file, keep `_sbs` only.
- Never create double markers like `_ru_dps` or `_sbs_dps`.

### Exceptions
- `main`: Script entry points.
- `GlobalVars`: whitelisted configuration containers.
- `RpdData`: keep unmarked because `RPD` already means `Russian Pali Dictionary`; the localization is semantic, not suffix-based.
- `RuSpellChecker`: keep unmarked because `Ru` already provides a clear Russian locale marker.
- `is_cyrillic`: keep unmarked because it is a unique helper in the Russian transliteration module and does not need an added locale marker.
- Webapp route handlers (e.g., `home_page_ru`) when descriptive names are required for API clarity.
- Python dunder methods (e.g., `__init__`) are NEVER renamed.

---

## Common Error Patterns

1. **Missing imports after sync** — upstream refactored a module path; shadow still uses old path.
2. **Duplicate HTML IDs in GoldenDict** — RU/SBS template lost its `ru_`/`sbs_` ID prefix.
3. **Mako syntax left in Jinja2 template** — `${var}` or `% if` leaked in after a template sync.
4. **`data_classes_dps.py` divergence** — this file is in `dps_copies` (serves both RU and SBS exporters); verify it satisfies both when syncing.

---

## Starting a New Sync Run

### Step 1 — Create the thread

Run `dpd-kamma-sync` from any terminal (it uses an absolute project path):

```bash
dpd-kamma-sync
```

This calls `scripts/cl_dps/dpd_init_sync.py`, which:
- Creates `kamma/threads/<YYYYMMDD>_upstream_sync/` with `plan.md`, `spec.md`, `handoff.md`.
- Registers the thread in `kamma/threads.md` as `[ ]` (not started).
- Prints next steps.

### Step 2 — Fill in the diff range

Open `kamma/threads/<date>_upstream_sync/spec.md` and fill in the "From" commit/tag.

### Step 3 — Execute all 7 phases

**3 commit gates** — each requires explicit **"Proceed with Commit N"** from the user.
The agent presents `git add` + `git commit` for the user to run manually. Never self-commits.

`dynamic_plan.md` is always created inside the active thread folder, NEVER in `kamma/upstream_sync/`.

---

#### Phase 0 — Pre-flight (Lower model)

1. Read `kamma/upstream_sync/smd.md` end-to-end. **STOP** if any entry is incomplete.
2. Read `kamma/upstream_sync/registry.json` end-to-end.
3. Run `uv run python3 kamma/upstream_sync/verify_smd_coverage.py` — **STOP** if any gaps.
4. Run `uv run python3 kamma/upstream_sync/validate_registry.py` — **STOP** if any errors.
5. Verify `sbs-ru` branch is clean: `git status` — **STOP** if dirty, document state.
6. Verify `as_upstream` tracking branch exists: `git branch -a | grep as_upstream`.
7. Create a backup tag: `git tag pre-sync-$(date +%Y%m%d)`.

**Phase 0 complete when:** All validators pass and SMD is confirmed complete.

---

#### Phase 1 — Automated Sync + Commit 1 gate (Lower model)

1. Run `echo 2 | bash scripts/bash/full_sync.sh` (selective sync mode — syncs tracked
   files, skips `modified_upstream_files` and `no_sync_files`).
2. Run `git submodule init && git submodule update`.
3. Spot-check: run `git diff HEAD -- db/models.py gui2/main.py .gitignore` to verify
   protected files were NOT overwritten.
4. Present full `git diff --stat` to user.
5. **USER APPROVAL GATE**: Wait for explicit "Proceed with Commit 1".
6. Prepare commit: `sync: automated upstream pull YYYY-MM-DD`
7. Present `git add` + `git commit -m "..."` to user. NEVER run commit yourself.

**Phase 1 complete when:** Commit 1 staged and user has run it manually.

---

#### Phase 2 — Dynamic Analysis (Higher model)

**MODEL SWITCH**: Instruct user to switch to Higher model before starting this phase.

1. Run `git diff HEAD^` to see what changed in the automated sync.
2. For each file in `modified_upstream_files` registry entries: run
   `git diff as_upstream -- <path>` to see what upstream has changed.
3. Cross-reference every changed upstream file against `russian_copies`,
   `sbs_copies`, and `dps_copies` in registry — list ALL shadow destinations.
4. **Triple Shadow Checklist**: Explicitly check `tools/paths.py`,
   `exporter/goldendict/templates/`, `exporter/webapp/templates/`,
   `exporter/goldendict/export_epd.py`. For each, list both shadow destinations.
5. Check `discuss` flags: for every `discuss: true` file, **STOP** and present
   `git diff as_upstream -- <path>` to user, state the `discuss_reason`, wait for
   decision before including in plan.
6. Output: Create `dynamic_plan.md` in the active thread folder (NOT in
   `kamma/upstream_sync/`) with:
   - Manual Merges: which `modified_upstream_files` changed, what code blocks to port
   - Shadow Updates: each shadow file + exactly what to update + SMD sync rule
   - Documentation: new/updated upstream docs to port to `docs_rus/`

**MODEL SWITCH BACK**: Instruct user to switch back to Lower model.

**Phase 2 complete when:** `dynamic_plan.md` written, all discuss flags resolved.

---

#### Phase 3 — Execution (Lower model)

**Print the Iron Rule at the start of this phase.**

1. Read `dynamic_plan.md` — execute item by item.
2. For each shadow update:
   1. Read the SMD entry for this file from `kamma/upstream_sync/smd.md`.
   2. Read the upstream source file (`git show as_upstream:<path>`).
   3. Read the current shadow copy.
   4. Apply upstream changes while preserving ONLY the local changes listed in SMD.
   5. Verify namespace isolation (`ru_`, `sbs_`, `dps_` prefixes intact).
3. For each modified upstream file:
   1. Run `git diff as_upstream -- <path>` to see upstream delta.
   2. Manually integrate new upstream features while preserving local elements per SMD.
   3. If `discuss: true`, confirm user already approved in Phase 2.
4. **Dual-Shadow Parity Rule**: When updating one shadow, immediately check if a
   sibling shadow exists (e.g., updating `paths_ru.py` → also check `paths_dps.py`).
   Both must be updated in the same step.
5. Run `uv run pytest tests/test_shadow_parity.py --tb=short -q` after every batch of
   shadow updates.

**Phase 3 complete when:** All items in `dynamic_plan.md` executed and parity tests pass.

---

#### Phase 4 — Logic Audit (Higher model)

**MODEL SWITCH**: Instruct user to switch to Higher model.

1. For each `modified_upstream_files` entry: compare final state against `as_upstream`
   — verify local changes match SMD exactly, nothing extra introduced.
2. For each updated shadow copy: compare against upstream source — verify structural parity.
3. Check all `discuss: true` files received explicit user approval in Phase 2.
4. Verify Iron Rule compliance: no workarounds, no novel solutions, no alternative
   libraries not in upstream.

**MODEL SWITCH BACK**: Instruct user to switch back to Lower model.

**Phase 4 complete when:** Audit passes, Iron Rule compliance confirmed.

---

#### Phase 5 — Testing + Commit 2 gate (Lower model)

1. Run: `uv run pytest --tb=short -q` (full suite — includes shadow parity).
2. Run: `uv run python3 tests/check_shadow_modifications.py`.
3. Run: `uv run ruff check . && uv run ruff format .`
4. Present test results summary to user.
5. **USER MANUAL VERIFICATION**: Ask user to open GoldenDict/webapp and verify
   dictionaries load correctly. Do NOT assume pass. Wait for explicit confirmation.
6. **USER APPROVAL GATE**: Wait for explicit "Proceed with Commit 2".
7. Prepare commit: `sync: manual merge resolutions YYYY-MM-DD`
8. Present `git add` + `git commit -m "..."` to user.

**Phase 5 complete when:** All tests pass, user confirmed manual verification, Commit 2 staged.

---

#### Phase 6 — Cleanup + Orphan Archiving (Lower model)

1. Run `uv run python3 tests/test_shadow_cleanup.py` for each path in
   `folders_to_check` from registry.
2. Identify orphans: files present locally but missing upstream source in `as_upstream`.
3. For each orphan:
   - Still referenced in codebase? → Promote to `unique_paths` in registry.
   - Unused? → Archive: scripts → `scripts/dps_archive/`, other → `archive/dps/`.
4. Update `kamma/upstream_sync/registry.json` with any changes.
5. Root directory audit: `ls -F` on project root — remove any temp artifacts.
6. Update `kamma/upstream_sync/smd.md` if files were added or removed.

**Phase 6 complete when:** No orphans remain, registry updated, root clean.

---

#### Phase 7 — Final Verification + Commit 3 gate (Lower model)

1. Re-run: `uv run pytest --tb=short -q`.
2. Re-run: `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py --tb=short -q`.
3. Run: `uv run python3 kamma/upstream_sync/verify_smd_coverage.py` — must pass.
4. Run: `uv run python3 kamma/upstream_sync/validate_registry.py` — must pass.
5. Run: `uv run ruff check . && uv run ruff format .`
6. Write `kamma/upstream_sync/new_improvements.md` with lessons from this run.
7. Delete `dynamic_plan.md` from the active thread folder (temp artifact).
8. **USER APPROVAL GATE**: Wait for explicit "Proceed with Commit 3".
9. Prepare commit: `sync: cleanup and finalization YYYY-MM-DD`
10. Present `git add` + `git commit -m "..."` to user.

**Phase 7 complete when:** All validators pass, `new_improvements.md` written, Commit 3 staged.

---

## Improvements Workflow (TODO need top rewrite)

| File | Purpose |
|---|---|
| `archive_improvements.md` | Accumulated lessons from all past sync runs. Which has been already implemented, at least attempted to. |
| `new_improvements.md` | Written at the end of each sync run. Overwritten each cycle. |

!TODO! we analyze current session and add them to a new improvement maybe we call it new suggestions and then we wait. We suggest something for the guide and for the whole process itself and only after that suggestions been saved. We moved those to the Archie So the suggestions file just a temporary file after analysis of the history of this exact process before adapting some implementation into the guide and then clean the file move everything what has been adopted into Archie.

**At the end of a sync run**, write `new_improvements.md` covering:
- Errors encountered that weren't in `archive_improvements.md`.
- Patterns discovered about specific files or sync strategies.
- Corrections to SMD entries (also update `smd/` directly).

**Periodically**, review `new_improvements.md` and promote valuable entries into
`archive_improvements.md`, then clear `new_improvements.md`.

---

## Verification Sequence (Phase 5 Order — Must Not Reorder)

1. **Automated tests** — must all pass before showing anything to the user.
   - `uv run pytest --tb=short -q` (full suite — includes shadow parity)
   - `uv run python3 tests/check_shadow_modifications.py`
   - `uv run ruff check . && uv run ruff format .`
2. **Present results** — summarize pass/fail to user.
3. **Manual verification gate** — STOP. Ask user to test GoldenDict/webapp.
   - Do NOT assume pass. Wait for explicit user confirmation.
   - If user reports any error: apply Iron Rule fix protocol (see above). Then re-run all automated tests before asking for manual verification again.
4. **Commit 2 gate** — only after user confirms manual verification passed.

---

## Manual Sync Checklist

- [ ] `git status` — clean before starting.
- [ ] `git branch -a | grep as_upstream` — tracking branch exists.
- [ ] `git diff as_upstream..upstream/main` — review all upstream changes.
- [ ] Cross-reference changed files against `modified_upstream_files`, `russian_copies`, `sbs_copies`, `dps_copies` in `registry.json`.
- [ ] Triple Shadow Checklist: `paths.py`, `goldendict/templates/`, `webapp/templates/`, `export_epd.py`.
- [ ] For each changed shadow source: read SMD entry, apply PORT strategy.
- [ ] `uv run pytest tests/test_shadow_parity.py --tb=short -q`
- [ ] `uv run python3 tests/check_shadow_modifications.py`
- [ ] `uv run python3 kamma/upstream_sync/validate_registry.py`
- [ ] `uv run python3 kamma/upstream_sync/verify_smd_coverage.py`
- [ ] `uv run python3 tests/test_shadow_cleanup.py --dry-run`
- [ ] **User manually verifies GoldenDict/webapp** — wait for confirmation.
- [ ] Write `kamma/upstream_sync/new_improvements.md`.
vements.md`.
