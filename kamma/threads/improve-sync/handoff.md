# Handoff: improve-sync

## State: All tiers complete. Ready for user review.

Tier 1 committed as `50ee07bb1`. Tier 2 committed by user (check git log).
Tier 3 (this session, Opus) wrote the state-machine proposal note.

## What Tier 3 did

1. **`state_machine_proposal.md`** — written in this thread directory.
   - Analyzed `sync_status.py` (90 lines): already a de facto state machine
     deriving stage from 4 artifact-existence checks + 1 content check.
   - Proposed extending it to emit a `StageDescriptor` (stage, owner, dispatch
     target, gates, reads, produces) so the orchestrator can skip parsing
     guide.md (~4,650 tokens/session saved, ~82% reduction).
   - Identified drift risk as the central concern; recommended a drift-guard
     test that validates the descriptor inventory against guide.md headers.
   - Estimated implementation at ~255 lines (one Sonnet session).
   - Left three options open: approve (new thread), defer, or reject.
   - `stage_state.json` is not consumed by any script today; the proposal
     deliberately avoids introducing it (keeps artifact-presence as ground truth).

2. **No code changed.** Tier 3 is note-only per spec.

## Files touched (Tier 3)

- `kamma/threads/improve-sync/state_machine_proposal.md` — created.
- `kamma/threads/improve-sync/plan.md` — markers updated.
- `kamma/threads/improve-sync/handoff.md` — this file.

## All tiers summary

| Tier | Status | Commit |
|---|---|---|
| 1 — Consolidation | ✅ Done | `50ee07bb1` |
| 2 — Collapse model-switch ceremony | ✅ Done | User committed |
| 3 — State-machine proposal | ✅ Done (note only) | Not committed yet |

## Next action

1. **User:** Review `state_machine_proposal.md` and decide (approve / defer / reject).
2. **User:** Commit Tier 3 files if desired, or bundle with the decision.
3. **Thread:** All plan tasks are `[x]`. Ready for `/kamma:3-review`.
