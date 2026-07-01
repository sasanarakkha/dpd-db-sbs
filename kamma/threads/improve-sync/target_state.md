# Target State: Sync Orchestration After Tier 2

> Describes the slimmed orchestration model that Tier 2 implements.
> Companion to `spec.md` § F5 and `plan.md` Tier 2.

## Core Principle

The FAST/ADVANCED **responsibility split is preserved**. What changes is the
**mechanism**: manual "tell the user to switch models" → subagent dispatch.

## Before (current state)

```
User types /update-upstream
  → ADVANCED session starts
  → ADVANCED tells user: "Switch to FAST. Copy this restart prompt."
  → User manually starts new FAST session, pastes prompt
  → FAST runs Stage 1
  → FAST tells user: "Switch to ADVANCED. Copy this restart prompt."
  → User manually starts new ADVANCED session, pastes prompt
  → ... repeat for each stage and every-5-item boundary
```

**Problems:**
- Every model switch requires user action (copy prompt, start session, paste).
- Arbitrary "every 5 items" counters force switches even when context is fine.
- Restart-prompt scaffolding in `guide.md` is 17+ lines of ceremony per switch.
- The same handoff contract is stated in 3 places (`guide.md`, `sync_thread_plan.md`, `sync-fast.md`).

## After (target state)

```
User types /update-upstream
  → ADVANCED orchestrator starts
  → Orchestrator dispatches Stage 1 to sync-fast subagent
  → Subagent returns results via handoff.md
  → Orchestrator reads handoff.md, runs Stage 2 analysis
  → Orchestrator dispatches Stage 3 batches to sync-fast
  → ... continues until all stages complete
  → User gates fire at: Stage 2 approval, each commit, Stage 5 acceptance
```

**What changes:**
- No more "Switch to FAST/ADVANCED" instructions to the user.
- No more "every 5 items" arbitrary hard stops — the subagent's context window
  is the natural boundary; the orchestrator dispatches batches as needed.
- No more restart-prompt templates in `guide.md` — the orchestrator writes
  dispatch prompts programmatically (or uses `sync-fast` agent definition).
- Session boundaries collapse onto three natural points:
  1. **Subagent dispatch/return** (automatic, no user action).
  2. **User gates** (Stage 2 approval, commits, Stage 5 acceptance).
  3. **Orchestrator context overflow** (rare — most work is dispatched).

**What does NOT change:**
- The FAST/ADVANCED **responsibility** split (what each model owns).
- The **Iron Rule**.
- All **user-facing gates** (Stage 2 approval, Commit 1/2/3, Stage 5 acceptance).
- The **handoff.md contract** (still written at every boundary, but now by the
  subagent returning to the orchestrator rather than by a human copy-pasting).
- The **handoff quality gates** (Stage 2→3 self-contained plan test, Stage 4.A→4.B
  translation plan completeness).
- The **commit structure** (3 commits: upstream pull, manual merge, docs).
- The **Stage 4 async docs queue** decoupling.

## Session Boundary Rules (after Tier 2)

| Boundary | Type | Who acts |
|---|---|---|
| Subagent dispatch → return | Automatic | Orchestrator dispatches, reads result |
| Stage 2 approval | User gate | Orchestrator presents plan, waits |
| Commit 1 (upstream pull) | User gate | Orchestrator prepares message, user commits |
| Commit 2 (manual merge) | User gate | Same |
| Commit 3 (docs) | User gate | Same |
| Stage 5 acceptance | User gate | User verifies, says "all good" |
| Orchestrator context overflow | Context split | Orchestrator writes handoff.md, suggests `/kamma:2-do` restart |

The "every 5 items" and "every 5 translation files" counters are gone. The
subagent decides its own session boundaries based on context health.

## Dispatch Targets (unchanged from current)

| Work | Dispatched to | Gate held by |
|---|---|---|
| Stage 1 (entire) | `sync-fast` | Orchestrator |
| Stage 3 (batches) | `sync-fast` | Orchestrator |
| Stage 4.B (docs translation) | `sync-fast` | Orchestrator |
| Stage 2 (analysis) | Orchestrator itself | User |
| Stage 4.A (docs analysis) | Orchestrator itself | User |
| Stage 5 (acceptance) | Orchestrator itself | User |

## Residual Context-Overflow Handoff

When the orchestrator itself must span sessions (rare — it does analysis, not
bulk work), it writes `handoff.md` with its usual contract and suggests the
user restart with `/kamma:2-do <thread>`. This is a one-line note, not the
17-line restart-prompt template currently in `guide.md`.

## Dry-Read Verification Checklist

After Tier 2 is applied, a hypothetical sync traced through the slimmed guide
must still hit every one of these gates:

- [ ] Stage 2 approval gate fires.
- [ ] Commit 1 gate fires (upstream pull).
- [ ] Commit 2 gate fires (manual merge).
- [ ] Commit 3 gate fires (docs translation).
- [ ] Stage 5 acceptance gate fires.
- [ ] Iron Rule is referenced and intact.
- [ ] Handoff quality gate (Stage 2→3) is intact.
- [ ] Handoff quality gate (Stage 4.A→4.B) is intact.
- [ ] FAST stop-conditions are intact (as subagent return conditions).
- [ ] ADVANCED stop-conditions are intact.
