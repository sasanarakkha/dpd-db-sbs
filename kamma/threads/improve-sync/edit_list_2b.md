# Tier 2.B Edit List

> Literal edits for `templates/sync_thread_plan.md` and `.claude/agents/sync-fast.md`.
> Written by Opus (Tier 2.A). Apply mechanically — do not redesign `guide.md`.

---

## File 1: `kamma/upstream_sync/templates/sync_thread_plan.md`

### Edit 1.1 — Stage 1 handoff: remove restart-prompt boilerplate (lines 38–41)

**Replace** these 4 lines:
```
**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md` with commands run, outputs/failures, files changed, open issues, and repeated mistakes.
- [ ] Restart prompt: `Switch to ADVANCED. Start a fresh session. Continue upstream sync thread: <thread_dir>. First read <thread_dir>/handoff.md, kamma/upstream_sync/guide.md, prep_report.md, and prep_manifest.json. Analyze Stage 1 results and write dynamic_plan.md. Do not perform mechanical edits.`
- [ ] Stop. Do not continue in this session.
```

**With:**
```
**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md` with commands run, outputs/failures, files changed, open issues, and next action.
- [ ] Stop. Do not continue in this session.
```

### Edit 1.2 — Stage 2 handoff: remove restart-prompt boilerplate (lines 66–69)

**Replace** these 4 lines:
```
**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md` with decisions, open questions, and exact next steps.
- [ ] Restart prompt: `Switch to FAST. Start a fresh session. Continue upstream sync thread: <thread_dir>. First read <thread_dir>/handoff.md, kamma/upstream_sync/guide.md, and <thread_dir>/dynamic_plan.md. Execute dynamic_plan.md literally item by item. Do not analyze or redesign. Stop if any plan item is incomplete or fails unexpectedly.`
- [ ] Stop. Do not continue in this session.
```

**With:**
```
**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md` with decisions, open questions, and exact next steps.
- [ ] Stop. Do not continue in this session.
```

### Edit 1.3 — Stage 3: remove "every 5 items" counter (line 80)

**Delete** this line:
```
  - [ ] Split after every 5 implementation items.
```

### Edit 1.4 — Stage 3 handoff: remove restart-prompt boilerplate (lines 94–97)

**Replace** these 4 lines:
```
**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md` with completed items, failed items, files changed, commands run, test evidence, and repeated mistakes.
- [ ] Restart prompt: `Switch to ADVANCED. Start a fresh session. Continue upstream sync thread: <thread_dir>. First read <thread_dir>/handoff.md, kamma/upstream_sync/guide.md, and <thread_dir>/dynamic_plan.md. Analyze Stage 3 evidence and decide whether to proceed to docs parity or write a corrective plan. Do not perform mechanical edits.`
- [ ] Stop. Do not continue in this session.
```

**With:**
```
**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md` with completed items, failed items, files changed, commands run, test evidence, and next action.
- [ ] Stop. Do not continue in this session.
```

### Edit 1.5 — Stage 4.A handoff: remove restart-prompt boilerplate (lines 118–121)

**Replace** these 4 lines:
```
**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md`.
- [ ] Restart prompt: `Switch to FAST. Start a fresh session. Continue upstream sync thread: <thread_dir>. First read <thread_dir>/handoff.md, kamma/upstream_sync/guide.md, and <thread_dir>/docs_translation_plan.md. Execute the docs translation plan literally. Stop if terminology or scope is unclear.`
- [ ] Stop. Do not continue in this session.
```

**With:**
```
**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md` with translation plan decisions and next action.
- [ ] Stop. Do not continue in this session.
```

### Edit 1.6 — Stage 4.B: remove "every 5 files" counter (line 130)

**Delete** this line:
```
- [ ] Split after every 5 translation files.
```

### Edit 1.7 — Stage 4.B handoff: remove restart-prompt boilerplate (lines 137–140)

**Replace** these 4 lines:
```
**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md` with files changed, remaining files, and issues.
- [ ] Restart prompt: `Switch to ADVANCED. Start a fresh session. Continue upstream sync thread: <thread_dir>. First read <thread_dir>/handoff.md, kamma/upstream_sync/guide.md, and docs translation evidence. Decide whether Stage 5 verification can begin. Do not perform mechanical edits.`
- [ ] Stop. Do not continue in this session.
```

**With:**
```
**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md` with files changed, remaining files, issues, and next action.
- [ ] Stop. Do not continue in this session.
```

---

## File 2: `.claude/agents/sync-fast.md`

### Edit 2.1 — Description: remove fixed batch size mention (line 3)

**Replace:**
```
description: Mechanical FAST executor for upstream sync stages (Stage 1, Stage 3 batches, Stage 4.B). Use for factual data collection, literal plan execution, file copying, formatting, testing, and bulk translation. Do NOT use for analysis, planning, judgment, or conflict resolution.
```

**With:**
```
description: Mechanical FAST executor for upstream sync stages (Stage 1, Stage 3, Stage 4.B). Dispatched by the ADVANCED orchestrator for factual data collection, literal plan execution, file copying, formatting, testing, and bulk translation. Do NOT use for analysis, planning, judgment, or conflict resolution.
```

No other changes needed — the agent file already reads as a subagent contract.
The "hand off to ADVANCED" wording in § Stop Conditions and § handoff.md Duty
is correct (a subagent returning to its orchestrator).

---

## Verification commands for 2.B (run after all edits)

```bash
# Stale ceremony check — all should return zero matches
grep -rn "restart prompt\|Switch to FAST\|Switch to ADVANCED\|every 5" kamma/upstream_sync/templates/sync_thread_plan.md
grep -rn "restart prompt\|Switch to FAST\|Switch to ADVANCED\|every 5" .claude/agents/sync-fast.md

# Registry + SMD integrity (no files were created/moved/deleted, but run as insurance)
uv run python3 kamma/upstream_sync/scripts/validate_registry.py
uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py

# Dry-read walkthrough: trace a hypothetical sync through the slimmed template
# and confirm every gate still fires (manual review — see target_state.md checklist)
```
