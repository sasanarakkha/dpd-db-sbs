# Plan: Simplify & De-duplicate the Upstream Sync Infrastructure

> Companion to `spec.md`. Read `spec.md` § Execution Model Policy first.
> Mark tasks `[~]` when started, `[x]` when done.
>
> **Model discipline (per spec):**
> - Default owner is **FAST (Sonnet)** — all mechanical work.
> - **ADVANCED (Opus)** runs ONLY the named analysis kernels below, as little as
>   possible.
> - **Every model switch is a hard stop.** The switching session updates
>   `handoff.md`, writes the exact restart prompt naming the next model, and
>   stops. Never switch models mid-session.
> - Do not pull a later Tier's edits into an earlier Tier's commit.

---

## Ownership map (at a glance)

| Block | Owner | Why |
|---|---|---|
| Tier 1 (all) | **FAST (Sonnet)** | Literal doc edits; no analysis needed |
| Tier 1 escalation (only if ambiguity) | ADVANCED (Opus) | De-dup judgment kernel |
| Tier 2.A design + `guide.md` rewrite | **ADVANCED (Opus)** | Deciding what is load-bearing = analysis |
| Tier 2.B template + agent reconcile | **FAST (Sonnet)** | Mechanical mirror of 2.A decisions |
| Tier 3 proposal | **ADVANCED (Opus)** | Design proposal = analysis |

Total Opus: one short Tier-2 authoring pass + one short Tier-3 pass. Tier 1 is
Sonnet-only in the happy path.

---

## Tier 1 — Consolidation — OWNER: FAST (Sonnet), no Opus

> Doc-only, low risk, independently revertable. Resolve the Tier-1 open
> questions (spec/plan bottom) in chat BEFORE this session starts; they are user
> decisions, not analysis. Given those answers, every edit below is literal.
>
> **FAST escalation rule:** if — and only if — you hit a real "which file is the
> canonical home / am I about to delete a fact that exists nowhere else"
> question you cannot resolve from the literal instructions, STOP and hand off to
> ADVANCED (Opus) with the specific ambiguity. Do not guess. In the happy path,
> Opus is never invoked in Tier 1.

### 1.1 Fix the stale skill entry point (F1)
- [x] Only after user approves editing this **global file outside the repo**:
  `~/.claude/commands/update-upstream.md`.
- [x] In frontmatter `description`, replace `7 phases` with `5 stages`
  (final: `Run upstream sync — 5 stages, 3 commits, Iron Rule enforced`).
- [x] Leave the body pointer to `guide.md` unchanged.
- Verify: `grep -n "phase" ~/.claude/commands/update-upstream.md` → no match.

### 1.2 Remove the dead legacy 7-phase workflow (F3)
- [x] In `kamma/upstream_sync/archive_improvements.md`, remove the block from
  `## Historical: Legacy 7-Phase Workflow (Pre-April 2026)` to end of file
  (was lines 149–253, incl. the `---` separator) — deleted per user's gate
  answer.
- [x] Keep the 20 numbered lessons above that block untouched.
- [x] Top header already carries the required note (lines 3–5: "Historical
  record only. Current canonical instructions live in `guide.md`..."); no
  further edit needed.
- Verify: `grep -rn "7-phase\|Phase 0\|Phase 7" kamma/upstream_sync` → zero.
  PASSED.

### 1.3 Collapse the two lessons-intake mechanisms (F4)
Canonical intake = `retrospective.md` (per user's gate answer; it is already
gated by `finalize_accepted_sync.py`). Remove the `new_improvements.md` path:
- [x] `guide.md` Stage 5, step "After sync": deleted the line beginning
  "Review the temporary `new_improvements.md`…". Retrospective →
  `archive_improvements.md` promotion flow kept intact.
- [x] `README.md`: deleted the `new_improvements.md` row in the File Inventory
  table AND the `new_improvements.md` clause in the `archive_improvements.md`
  bullet under Documentation & Metadata.
- [x] `grep -rn "new_improvements" kamma/ .gitignore` — also found and fixed
  dangling references in `scripts/init_sync_thread.py` (printed next-steps
  message), `templates/sync_thread_spec.md` (Definition of Done bullet),
  `templates/sync_thread_plan.md` (Stage 5 checklist item), and the
  `.gitignore` ignore line — all updated to reference `retrospective.md`
  instead, or removed. Archived thread records under `kamma/archive/` and
  `kamma/sessions/` are historical logs and were left untouched (out of scope).
- Verify: `grep -rn "new_improvements" kamma/upstream_sync .gitignore` → zero.
  PASSED.

### 1.4 Make README.md a pure index (F2)
Literal keep/remove list (no judgment required):
- [x] **Keep:** the purpose paragraph (top), the one-line stage+command cheat
  sheet (the numbered 1–5 list with its `uv run` commands), the Core Tooling
  table, the File Inventory table, the Documentation & Metadata pointer list,
  and the Registry Categories pointer.
- [x] **Remove (now duplicated in `guide.md`):** the prose paragraphs after the
  numbered stage list that restated FAST/ADVANCED responsibilities and the
  model-split narrative ("FAST performs mechanical work only…" + the old
  "For the full protocol, see guide.md." line). Replaced both with the single
  line: `For the full protocol, model responsibilities, and Iron Rule, see [guide.md](./guide.md).`
- [x] Confirmed no registry-categories table, Iron Rule body, or full stage
  description is restated in README — only pointers remain.
- Verify: read README top-to-bottom; every normative fact is a link to
  `guide.md`, not a copy. PASSED.

### 1.5 Tier 1 verification + commit prep (FAST)
- [x] `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` passes
  (`registry.json is valid`).
- [x] `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` —
  coverage ok; one pre-existing rubric warning on `.pre-commit-config.yaml`
  confirmed present before this session's changes too (via `git stash` A/B
  check) — unrelated to this thread, not touched.
- [x] `grep -rn "7 phase\|7-phase\|new_improvements" kamma/upstream_sync` →
  zero matches.
- [x] Prepare commit message only (user commits):
  `docs(sync): consolidate upstream-sync docs, remove legacy 7-phase workflow`.
- [x] Excluded dirty `resources/*` submodule pointers from commit scope.
  Also flagging `kamma/improve/queue.md` as pre-existing dirty (modified before
  this session started, per initial git status) — not touched by this thread,
  excluded from commit scope.

### ── HARD STOP after Tier 1 ──
- [ ] Update `handoff.md`: Tier 1 done, files touched, verify output, commit msg.
- [ ] STOP for user commit + Tier 2 approval. Do not begin Tier 2 in this
  session. Restart prompt (if approved):
  `Switch to ADVANCED (Opus). Start a fresh session. Continue thread kamma/threads/improve-sync. Read handoff.md, spec.md, plan.md Tier 2. Execute Tier 2.A only (design + guide.md rewrite), then hard stop.`

---

## Tier 2 — Collapse model-switch ceremony onto subagent dispatch

> **APPROVAL GATE:** do not start until the user approves Tier 2. Higher blast
> radius — shared process docs consumed by every future sync.
> Split into 2.A (Opus analysis) → hard stop → 2.B (Sonnet mechanical).

### Tier 2.A — OWNER: ADVANCED (Opus) — analysis + authoring (minimal pass)
- [ ] **2.A.1 Target-state note:** write `target_state.md` in this thread: the
  slimmed orchestration — orchestrator (Opus) holds all user gates (Stage 2
  approval, Commit 1/2/3, Stage 5 acceptance); mechanical work fans to the
  `sync-fast` subagent (Sonnet); session boundaries fall on dispatch + gate
  points, NOT on arbitrary "every 5 items". Confirm the FAST/ADVANCED
  *responsibility* split is preserved; only the human "switch models now" ritual
  and the arbitrary hard-stop counters are removed.
- [ ] **2.A.2 Author the `guide.md` rewrite** (this IS the analysis — deciding
  what is load-bearing vs. ceremony; do it directly, do not defer to FAST):
  - Remove the manual model-switch instructions superseded by subagent dispatch.
  - Remove the "hard stop after every 5 implementation items / 5 translation
    files" counters; replace with "dispatch each batch to `sync-fast`; the
    subagent's isolated context is the boundary".
  - Trim the per-stage restart-prompt scaffolding to the minimum the
    orchestrator needs when it genuinely spans sessions for context size.
  - **Keep untouched:** Iron Rule, all commit gates, Stage 2 approval gate,
    Stage 5 acceptance gate, the plan-quality handoff gates (self-contained
    plan test), and `handoff.md` contract.
- [ ] **2.A.3 Emit a literal edit list** for 2.B (exact deletions/replacements
  in `templates/sync_thread_plan.md` and `.claude/agents/sync-fast.md` that must
  mirror the guide decisions).
- [ ] **2.A.4 Present** `target_state.md` + rewritten `guide.md` for approval.

### ── HARD STOP: Opus → Sonnet ──
- [ ] Update `handoff.md`: guide.md rewritten, decisions recorded, literal edit
  list for 2.B attached. Restart prompt:
  `Switch to FAST (Sonnet). Start a fresh session. Continue thread kamma/threads/improve-sync. Read handoff.md and the 2.A edit list. Apply Tier 2.B mechanically, verify, prepare commit. Do not redesign guide.md.`
- [ ] STOP. Do not do 2.B in the Opus session.

### Tier 2.B — OWNER: FAST (Sonnet) — mechanical reconciliation
- [ ] **2.B.1** Apply the 2.A edit list to `templates/sync_thread_plan.md`
  (remove the obsolete "Switch to FAST/ADVANCED. Start a fresh session…"
  restart-prompt boilerplate; keep checklist, stop-conditions, commit gates).
- [ ] **2.B.2** Apply the 2.A edit list to `.claude/agents/sync-fast.md` (adjust
  only wording referencing the removed manual model-switch ritual).
- [ ] **2.B.3** Dry-read walkthrough: trace a hypothetical sync through the
  slimmed guide; confirm every gate (2 approval, 3 commits, 5 acceptance) still
  fires and commit structure is unchanged.
- [ ] **2.B.4** `validate_registry.py` + `verify_smd_coverage.py` still pass.
- [ ] Prepare commit message only:
  `docs(sync): drive FAST/ADVANCED split via sync-fast dispatch, drop manual model-switch ceremony`.

### ── HARD STOP after Tier 2 ──
- [ ] Update `handoff.md`. STOP for user commit + Tier 3 decision.

---

## Tier 3 — State-machine-driven workflow — OWNER: ADVANCED (Opus), NOTE ONLY

> Not implemented here. Deliverable is a written proposal. Minimal Opus pass.
> Requires its own thread + approval to implement.

### Tier 3.1 — proposal note (Opus)
- [ ] Write `state_machine_proposal.md` in this thread: extend `sync_status.py`
  from "print current stage + next command" into a small state machine owning
  workflow transitions, so the model runs "the next emitted command" instead of
  re-deriving 423 lines of prose each session.
- [ ] Identify state read (`prep_manifest.json`, `handoff.md`, commit markers,
  `stage_state.json`) and emitted output.
- [ ] Estimate token savings vs. implementation cost; flag the drift risk (a
  state machine out of sync with reality is worse than prose).
- [ ] Leave the decision open for the user. Hard stop.

---

## Open Questions for the User (resolve before Tier 1 starts)

1. **1.2** Delete the legacy 7-phase block, or relocate to `archive/dps/`?
   (Recommend delete.)
2. **1.3** Canonical intake = `retrospective.md` (recommend) or
   `new_improvements.md`?
3. **1.1** Approve editing the global file
   `~/.claude/commands/update-upstream.md`? (Outside repo VCS.)
4. **Tier 2** Approve collapsing the model-switch ceremony now, or defer?
5. **Tier 3** Want the state-machine proposal, or drop it?

## Execution Notes

- Tier 1 = one Sonnet session (doc-only), assuming Q1–Q3 answered.
- Tier 2 = one Opus session (2.A) + one Sonnet session (2.B), hard stop between.
- Tier 3 = one short Opus session.
- After any doc edit, re-run `validate_registry.py` + `verify_smd_coverage.py`
  as cheap insurance the registry/SMD were not disturbed.
- Report files touched; confirm `resources/*` submodule pointers excluded from
  every proposed commit.
