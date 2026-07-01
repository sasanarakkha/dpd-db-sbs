# Handoff: improve-sync

## State: Tier 1 complete, hard stop for user commit + Tier 2 decision

All Tier 1 tasks (1.1–1.5) are done and verified. See `plan.md` for per-task
detail; summary below.

## Open questions resolved this session (user answers)
- Q1 (1.2): Delete the legacy 7-phase block — done (not relocated).
- Q2 (1.3): Canonical intake = `retrospective.md` — done.
- Q3 (1.1): Approved editing global file `~/.claude/commands/update-upstream.md` — done.
- Q4 (Tier 2) and Q5 (Tier 3): **still open** — not answered yet. Ask before
  starting Tier 2.

## Files touched
- `~/.claude/commands/update-upstream.md` (global, outside repo VCS): "7 phases" → "5 stages".
- `kamma/upstream_sync/archive_improvements.md`: removed legacy 7-phase block (was lines 149–253); top note already covered the "post-mortem log only" requirement, no further edit needed.
- `kamma/upstream_sync/guide.md`: removed the redundant `new_improvements.md` line from Stage 5 "After sync".
- `kamma/upstream_sync/README.md`: removed `new_improvements.md` row/clause; trimmed FAST/ADVANCED narrative paragraph to a single pointer line to `guide.md`.
- `kamma/upstream_sync/scripts/init_sync_thread.py`: next-steps print message now points to `retrospective.md` instead of `new_improvements.md`.
- `kamma/upstream_sync/templates/sync_thread_spec.md`: Definition-of-Done bullet now references `retrospective.md`.
- `kamma/upstream_sync/templates/sync_thread_plan.md`: Stage 5 checklist item now references `retrospective.md`.
- `.gitignore`: removed the `kamma/upstream_sync/new_improvements.md` ignore line.
- `kamma/threads/improve-sync/plan.md`: tasks 1.1–1.5 marked `[x]` with verification notes.

Archived thread records under `kamma/archive/` and `kamma/sessions/` still
mention `new_improvements.md` — left untouched intentionally (historical logs,
out of scope per plan).

## Verification run
- `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` → `registry.json is valid`.
- `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` → coverage ok; one **pre-existing** rubric warning on `.pre-commit-config.yaml` (confirmed via `git stash` A/B test — present before this session's changes too, unrelated to this thread).
- `grep -rn "7 phase\|7-phase\|new_improvements" kamma/upstream_sync` → zero matches.

## Commit scope
Proposed commit message: `docs(sync): consolidate upstream-sync docs, remove legacy 7-phase workflow`

Files to stage: `.gitignore`, `kamma/upstream_sync/README.md`,
`kamma/upstream_sync/archive_improvements.md`, `kamma/upstream_sync/guide.md`,
`kamma/upstream_sync/scripts/init_sync_thread.py`,
`kamma/upstream_sync/templates/sync_thread_plan.md`,
`kamma/upstream_sync/templates/sync_thread_spec.md`,
`kamma/threads/improve-sync/plan.md`, `kamma/threads/improve-sync/handoff.md`.

Plus separately: `~/.claude/commands/update-upstream.md` (global file, not part of this repo's git).

**Excluded from commit scope:**
- `resources/*` submodule pointer changes (dirty at session start, unrelated).
- `kamma/improve/queue.md` — was already modified before this session started (dirty in the initial git status snapshot); this thread never touched it. Flagging per project rule to not silently include another in-progress change.

## Next action
1. User reviews/commits the Tier 1 changes above.
2. User answers Q4 (start Tier 2 now or defer?) and Q5 (want the Tier 3 state-machine proposal, or drop it?).
3. If Tier 2 approved: restart prompt is
   `Switch to ADVANCED (Opus). Start a fresh session. Continue thread kamma/threads/improve-sync. Read handoff.md, spec.md, plan.md Tier 2. Execute Tier 2.A only (design + guide.md rewrite), then hard stop.`
