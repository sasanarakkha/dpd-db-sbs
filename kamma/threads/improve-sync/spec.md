# Spec: Simplify & De-duplicate the Upstream Sync Infrastructure

> Meta-thread. This does NOT run a sync. It refactors the sync *process
> documentation and orchestration* under `kamma/upstream_sync/` to remove
> accreted ceremony, kill documentation drift, and lower per-run token cost —
> without weakening the correctness machinery (registry, tests, Iron Rule).
>
> Folder name note: requested as `improve-sunc`; created as `improve-sync`
> (typo corrected). Rename the folder if a different name was intended.

## Background / Verdict

The sync system was assessed on 2026-07-01. Findings:

- **Durable core is excellent, keep untouched:** `registry.json` as the single
  machine-readable source of truth; the test suite (`test_shadow_parity`,
  `test_namespace_isolation`, `test_template_syntax`, `check_shadow_modifications`);
  `execute_sync.py` deletion-propagation + clean-gate; the Iron Rule; async docs
  decoupling (Stage 4 → queue).
- **The orchestration ceremony is disproportionate.** It is the product of ~6
  syncs where every failure added a rule and almost nothing was removed or
  consolidated (see the 20 numbered items in `archive_improvements.md`). The
  result: the same facts are restated in 3–4 documents, two "lessons intake"
  paths exist, and a heavy human-driven FAST/ADVANCED model-switch protocol
  sits layered on top of the newer `sync-fast` subagent-dispatch path that
  largely obsoletes it.

Assessment confidence: 7/10 (all prose + registry/script inventory read; script
internals not line-by-line audited).

## Goal

Reduce the sync process to its smallest correct form:

1. **One fact, one home.** Protocol lives only in `guide.md`. `README.md` becomes
   a pure index. `archive_improvements.md` becomes a pure post-mortem log.
2. **Kill the drift that already exists** (the entry-point skill advertises a
   dead "7-phase" workflow).
3. **Collapse the two lessons-intake mechanisms** into one.
4. **Express the FAST/ADVANCED split through subagent dispatch**, not through
   manual model-switch ritual + every-5-item hard stops + restart-prompt
   scaffolding.
5. Leave a clear Tier 3 note for a future state-machine-driven workflow.

## Explicit Non-Goals (do NOT touch)

- `registry.json` schema, categories, or contents.
- `smd/` merge rules.
- The test suite or any parity/namespace/template enforcement.
- `execute_sync.py`, `prep_analyzer.py`, `check_docs_parity.py`, or any script
  *logic*. (Tier 3 may later add a state-machine wrapper; that is a separate,
  approval-gated decision — not part of Tier 1/2.)
- The Iron Rule as a principle.
- Any actual upstream sync run.

## Findings → Changes (traceability)

| # | Finding | Tier | Primary file(s) |
|---|---|---|---|
| F1 | Skill description says "7 phases, 3 commits"; protocol is 5 stages | 1 | `~/.claude/commands/update-upstream.md` |
| F2 | Registry categories / Iron Rule / stage defs restated in README, guide, archive, smd/index | 1 | `README.md` (make index) |
| F3 | `archive_improvements.md` carries a dead 100-line legacy 7-phase workflow | 1 | `archive_improvements.md` |
| F4 | Two lessons-intake paths: `retrospective.md` template AND `new_improvements.md` temp file | 1 | `guide.md`, `README.md` |
| F5 | Manual FAST/ADVANCED model-switch ceremony duplicates `sync-fast` subagent dispatch; every-5-item hard stops + restart-prompt scaffolding are costly | 2 | `guide.md`, `templates/sync_thread_plan.md`, `.claude/agents/sync-fast.md`, `README.md` |
| F6 | 423-line prose `guide.md` re-parsed every sync; workflow could be state-machine-driven off `sync_status.py` | 3 | `sync_status.py` + scripts |

## Success Criteria

**Tier 1 (mechanical, low risk):**
- Skill entry point states the current workflow ("5 stages, 3 commits"), no
  reference to "7 phases".
- `archive_improvements.md` contains only post-mortem lessons; the legacy
  7-phase workflow block is removed (or moved to a clearly-dead
  `archive/`-style note, per user choice at the gate).
- Exactly one lessons-intake mechanism remains, referenced consistently across
  `guide.md` and `README.md`.
- `README.md` is a pointer index: it does not restate the registry categories
  table, the Iron Rule body, or full stage definitions — it links to `guide.md`.
- `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` passes.
- `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` passes.
- `grep -rn "7 phase\|7-phase\|new_improvements" kamma/upstream_sync` returns
  only intended, consistent references (ideally zero for the removed items).

**Tier 2 (reduce per-run cost) — requires explicit approval before starting:**
- FAST/ADVANCED remains as a *responsibility* split, expressed through
  `sync-fast` dispatch boundaries — not through "tell the user to switch models".
- Redundant every-5-item hard-stop rules and restart-prompt scaffolding are
  removed from `guide.md` and `templates/sync_thread_plan.md`; session
  boundaries collapse onto subagent-dispatch + user gates (Stage 2 approval,
  commits, Stage 5 acceptance).
- `sync-fast.md` and the guide agree on one handoff mechanism (no contradictory
  duplicate instructions).
- A dry-read walkthrough confirms the slimmed guide still yields the same gates
  and the same commit structure.

**Tier 3 (structural) — note only, no implementation this thread:**
- A written proposal exists for driving the workflow from a `sync_status.py`
  state machine that emits "the exact next command", so the model stops
  re-deriving the workflow from 423 lines of prose each run.

## Execution Model Policy

Mirror the sync system's own FAST/ADVANCED split to minimize cost:

- **Default owner is FAST (Sonnet).** All mechanical edits, deletions, greps,
  verification commands, and commit-message prep run on Sonnet.
- **ADVANCED (Opus) is used as little as possible — only for genuine analysis
  kernels** where "is this line load-bearing or redundant?" is a judgment call
  that a mechanical executor cannot safely make. Those kernels are named
  explicitly in `plan.md`. Opus authors, then hands a literal edit list to FAST.
- **Every model switch is a hard stop.** The switching session updates
  `handoff.md`, writes an exact restart prompt naming the next model, and stops.
  Never switch models mid-session.
- **Minimize the number of switches**, not just Opus time — each switch has
  handoff overhead. Order work so each model runs in one contiguous block.
- Tier 1 is designed to need **zero Opus** in the happy path (literal edits);
  Opus is an escalation target only if a real de-dup ambiguity surfaces.

## Constraints

- No autonomous git commit/pull/push. Prepare messages; user commits.
- `~/.claude/commands/update-upstream.md` is a **global user file outside the
  repo** — editing it is out of the repo's version control. Flag it at the gate;
  do not silently edit user-global config (see global rule: don't modify machine
  config without request — here the user requested the plan, so confirm the edit
  explicitly).
- Docs sanctity: process docs stay under `kamma/upstream_sync/`; nothing moves
  into upstream-owned `docs/`.
- Each Tier is independently approvable and independently revertable.

## Key References

| File | Purpose |
|---|---|
| `kamma/upstream_sync/guide.md` | Canonical protocol (the main de-dup target) |
| `kamma/upstream_sync/README.md` | Folder index (to be slimmed to pointers) |
| `kamma/upstream_sync/archive_improvements.md` | Lessons log (legacy block to remove) |
| `kamma/upstream_sync/templates/sync_thread_plan.md` | Per-run plan template (ceremony source) |
| `.claude/agents/sync-fast.md` | FAST subagent contract |
| `~/.claude/commands/update-upstream.md` | Skill entry point (stale description) |
| `kamma/upstream_sync/scripts/sync_status.py` | Tier 3 state-machine seed |
| `kamma/threads/improve-sync/plan.md` | Executable task list for this thread |
