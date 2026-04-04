# Upstream Sync Process Reference

> This is a process reference only — no AI instructions here. For per-file merge
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
| `russian_copies` | `shadow: upstream` map | Shadow files that mirror an upstream source with Russian-specific additions. |
| `sbs_copies` | `shadow: upstream` map | Shadow files that mirror an upstream source with SBS-specific additions. |
| `unique_paths` | string array | Files/dirs that exist only in this fork. Never in upstream; never auto-synced. |
| `no_sync_files` | string array | Paths that must never be overwritten by an upstream sync (fork-only infrastructure). |
| `ignored_files` | string array | Paths ignored during sync scanning (build artifacts, local-only dirs). |
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

### PRESERVE
Fork-specific content that has no upstream equivalent. Do not sync; only update manually.

### DISCUSS
High-risk file where blind porting would delete localized data. Stop, read the SMD entry,
and plan explicitly before touching the file.

---

## Common Error Patterns

1. **Missing imports after sync** — upstream refactored a module path; shadow still uses old path.
2. **Duplicate HTML IDs in GoldenDict** — RU/SBS template lost its `ru_`/`sbs_` ID prefix.
3. **Mako syntax left in Jinja2 template** — `${var}` or `% if` leaked in after a template sync.
4. **`data_classes_dps.py` divergence** — this file appears in BOTH `russian_copies` AND `sbs_copies`; it must satisfy both.
5. **`unique_paths` duplication** — same path listed twice; deduplicate before relying on the list.

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

### Step 3 — Execute

Run `/kamma:2-do` (points to the new thread). The thread plan walks through 7 phases:

| Phase | Description | Model |
|---|---|---|
| 0 | Pre-flight: clean worktree, validators, SMD check | Auto |
| 1 | Automated sync (`full_sync.sh`) + Commit 1 gate | Auto |
| 2 | Dynamic analysis: diff all changed files, build `dynamic_plan.md` | **PRO** |
| 3 | Execution: port each item in `dynamic_plan.md`, Iron Rule enforced | Auto |
| 4 | Logic audit: verify Iron Rule compliance, SMD parity | **PRO** |
| 5 | Automated tests → manual verification gate → Commit 2 gate | Auto |
| 6 | Cleanup: orphan archiving, registry/SMD update | Auto |
| 7 | Final validation, `new_improvements.md`, Commit 3 gate | Auto |

**3 commit gates** — each requires explicit **"Proceed with Commit N"** from the user.
The agent presents `git add` + `git commit` for the user to run manually. Never self-commits.

`dynamic_plan.md` is always created inside the active thread folder, NEVER in `kamma/upstream_sync/`.

### Step 4 — Post-sync write-up

At the end of Phase 7, write `kamma/upstream_sync/new_improvements.md` with lessons from this run.

---

## Improvements Workflow

| File | Purpose |
|---|---|
| `archive_improvements.md` | Accumulated lessons from all past sync runs. Grows over time. |
| `new_improvements.md` | Written at the end of each sync run. Overwritten each cycle. |

**At the end of a sync run**, write `new_improvements.md` covering:
- Errors encountered that weren't in `archive_improvements.md`.
- Patterns discovered about specific files or sync strategies.
- Corrections to SMD entries (also update `smd.md` directly).

**Periodically**, review `new_improvements.md` and promote valuable entries into
`archive_improvements.md`, then clear `new_improvements.md`.

---

## Verification Sequence (Phase 5 Order — Must Not Reorder)

1. **Automated tests** — must all pass before showing anything to the user.
   - `uv run pytest tests/test_shadow_parity.py --tb=short -q`
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
- [ ] Cross-reference changed files against `modified_upstream_files`, `russian_copies`, `sbs_copies` in `registry.json`.
- [ ] Triple Shadow Checklist: `paths.py`, `goldendict/templates/`, `webapp/templates/`, `export_epd.py`.
- [ ] For each changed shadow source: read SMD entry, apply PORT strategy.
- [ ] `uv run pytest tests/test_shadow_parity.py --tb=short -q`
- [ ] `uv run python3 tests/check_shadow_modifications.py`
- [ ] `uv run python3 kamma/upstream_sync/validate_registry.py`
- [ ] `uv run python3 kamma/upstream_sync/verify_smd_coverage.py`
- [ ] `uv run python3 tests/test_shadow_cleanup.py --dry-run`
- [ ] **User manually verifies GoldenDict/webapp** — wait for confirmation.
- [ ] Write `kamma/upstream_sync/new_improvements.md`.
