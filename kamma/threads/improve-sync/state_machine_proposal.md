# Proposal: State-Machine-Driven Sync Workflow

> Tier 3 deliverable for the `improve-sync` thread. **Note only — no
> implementation.** Requires its own thread + approval to implement.

---

## 1. Problem Statement

Every sync session begins by parsing `guide.md` (404 lines) and the generated
plan template (~260 lines) to derive "what stage am I in, what do I do next."
The model re-reads and re-interprets this prose each session, even though the
workflow is deterministic — the next action is fully determined by which
artifacts exist in the thread directory.

`sync_status.py` already proves this: its 90-line `derive_stage()` function
produces the correct `(stage_label, next_command)` from four file-existence
checks plus one content check. But today it only *reports* — the orchestrator
still reads guide.md to know the dispatch target, the gate to hold, and the
pre/post-conditions.

## 2. Current State Derivation

### 2.1 Inputs read by `derive_stage()`

| Artifact | Check type | What it tells us |
|---|---|---|
| `prep_manifest.json` | existence | Stage 1 completed |
| `dynamic_plan.md` | existence | Stage 2 completed (plan approved) |
| `docs_translation_plan.md` | existence | Stage 4.A completed |
| `retrospective.md` | existence | Stage 5 ready to finalize |
| `prep_manifest.json` → `mapped_actions` | content (`is_localized_noop`) | Fast-path eligible |
| `prep_manifest.json` → `changed_upstream_paths` | content (any `docs/` prefix) | Docs stage needed |

### 2.2 Decision tree (current)

```
retrospective.md exists?
  → yes: Stage 5 (finalize)
prep_manifest.json missing?
  → yes: Stage 1 (prep)
docs_translation_plan.md exists?
  → yes: Stage 4.B (docs translation)
dynamic_plan.md exists?
  → docs pending? → yes: Stage 4.A (docs analysis)
  → no docs:     → Stage 3 (execution)
is_localized_noop(manifest)?
  → yes: Fast-path (Stage 1 → Commit 1 → Stage 5)
fallback:
  → Stage 2 (analysis)
```

### 2.3 Output (current)

A 2-tuple: `(stage_label: str, next_command: str)`.

That's it. No dispatch target, no gate info, no pre-conditions.

### 2.4 Artifacts NOT read but mentioned in plan.md

- **`handoff.md`** — read by the model, not by `sync_status.py`.
- **`stage_state.json`** — mentioned in guide.md as optional ("only when a
  script or later session needs machine-readable state"). Not actually consumed
  by any script today.
- **Commit markers** — no machine-readable signal that Commit 1/2/3 happened.
  The model infers this from `handoff.md` prose and git log.

## 3. Proposed Extension

Extend `derive_stage()` to emit a **stage descriptor** — a structured dict
that gives the orchestrator everything it needs without parsing guide.md.

### 3.1 Stage descriptor schema

```python
@dataclass
class StageDescriptor:
    stage: str              # e.g., "Stage 3: Execution & Verification"
    next_command: str       # e.g., "Execute dynamic_plan.md item-by-item"
    owner: str              # "FAST" | "ADVANCED"
    dispatch: str           # "sync-fast" | "self" | "user"
    gate_before: str | None # e.g., "Stage 2 approval" — must fire BEFORE work
    gate_after: str | None  # e.g., "Commit 2" — must fire AFTER work
    reads: list[str]        # artifacts this stage consumes
    produces: list[str]     # artifacts this stage creates
    stop_condition: str     # when the stage's work is done
```

### 3.2 Enriched decision tree

Each branch in the current `derive_stage()` would return a `StageDescriptor`
instead of a 2-tuple. Example for Stage 3:

```python
StageDescriptor(
    stage="Stage 3: Execution & Verification",
    next_command="Execute dynamic_plan.md item-by-item (sync-fast subagent).",
    owner="FAST",
    dispatch="sync-fast",
    gate_before=None,  # Stage 2 approval already fired (dynamic_plan.md exists)
    gate_after="Commit 2 (manual merge)",
    reads=["dynamic_plan.md", "prep_manifest.json"],
    produces=["handoff.md (updated)"],
    stop_condition="All items in dynamic_plan.md marked [x]",
)
```

### 3.3 Output format options

| Option | Pros | Cons |
|---|---|---|
| **A. JSON to stdout** | Parseable by model or script; composable | Model must parse JSON |
| **B. Structured print** (current style, more fields) | Human-readable; consistent with `pr.summary()` | Harder to compose programmatically |
| **C. Both** (JSON flag `--json`, human default) | Best of both | Slight code complexity |

**Recommendation:** Option C. The `--json` flag costs ~10 lines. The human
default keeps the current `pr.summary()` UX for manual runs.

## 4. What This Does NOT Do

This proposal is deliberately conservative. The state machine **does not**:

- **Own transitions.** It reports; it does not execute. The orchestrator (or
  user) still runs the emitted command. There is no daemon, no event loop.
- **Write `stage_state.json`.** State remains derived from artifact presence.
  Adding a writable state file introduces a new consistency obligation.
- **Replace guide.md.** The guide remains the canonical human-readable protocol.
  The state machine is a **machine-readable projection** of the same logic.
- **Manage commits.** Commit gates remain user-driven. The descriptor tells the
  model *which* gate fires, not *how* to fire it.

## 5. Token Savings Estimate

### 5.1 Per-session cost today

| Read | Tokens (est.) | When |
|---|---|---|
| `guide.md` (404 lines) | ~3,200 | Every session |
| `sync_thread_plan.md` template (260 lines) | ~2,100 | Every session |
| `handoff.md` (variable) | ~400 | Every session |
| **Total context load** | **~5,700** | |

### 5.2 Per-session cost with state machine

| Read | Tokens (est.) | When |
|---|---|---|
| `sync_status.py --json` output (~20 lines) | ~150 | Every session |
| `handoff.md` (variable) | ~400 | Every session |
| `guide.md` sections (only on gate/error) | ~500 | Some sessions |
| **Total context load** | **~1,050** | |

### 5.3 Savings

- **Per session:** ~4,650 tokens input (~82% reduction in workflow context).
- **Per full sync (5+ sessions):** ~23,000 tokens saved.
- **Qualitative:** Less re-derivation means fewer "the model misread the
  protocol" errors — the dominant failure mode in the 20-lesson archive.

### 5.4 Implementation cost

| Work | Estimate |
|---|---|
| `StageDescriptor` dataclass + enriched `derive_stage()` | ~120 lines |
| `--json` flag + JSON serialization | ~15 lines |
| Test coverage (one test per branch) | ~80 lines |
| Drift guard test (see §6) | ~40 lines |
| **Total** | **~255 lines** |

Single Sonnet session. No guide.md edits required (it remains canonical).

## 6. Drift Risk Assessment

> *"A state machine out of sync with reality is worse than prose."*

This is the central risk. If guide.md adds a new stage or gate and
`sync_status.py` isn't updated, the machine emits wrong instructions —
confidently and silently.

### 6.1 Current drift exposure

Today there is **zero** drift risk from `sync_status.py` because it only
reports a label and command. The model still reads guide.md for everything
else. If the status script is wrong, the model self-corrects from the prose.

### 6.2 Drift exposure with the enriched descriptor

The descriptor becomes the model's *primary* source for dispatch target, gates,
and pre/post-conditions. If it's wrong, the model won't self-correct because
it may skip reading guide.md.

### 6.3 Mitigations

| Mitigation | Mechanism | Confidence |
|---|---|---|
| **Drift-guard test** | A test that extracts stage names and gate names from guide.md (regex on `### Stage` headers and `gate`/`commit`/`approval` keywords) and asserts they match the `StageDescriptor` inventory. Fails CI if guide.md evolves without a matching descriptor update. | High — catches structural drift |
| **Version stamp** | `sync_status.py` prints the guide.md SHA256 it was validated against. If guide.md changes, the orchestrator sees a mismatch and falls back to reading guide.md directly. | Medium — requires orchestrator cooperation |
| **Conservative scope** | Don't put *everything* in the descriptor. Keep the Iron Rule, gotchas, and registry-category semantics in guide.md. The descriptor handles only the stage→dispatch→gate mapping — the part that is truly mechanical. | High — limits blast radius |

**Recommendation:** Drift-guard test + conservative scope. The version stamp
is clever but adds a manual step (re-stamp after every guide edit).

## 7. Alternatives Considered

### 7.1 Do nothing

**Status quo cost:** ~5,700 tokens/session × 5+ sessions/sync = ~28,500 tokens
of workflow context per sync. Not catastrophic, but the re-derivation also
causes errors (the 20-lesson archive is evidence).

**Verdict:** Viable. The system works. But each sync carries a tax that scales
with guide.md length.

### 7.2 Shrink guide.md further

Tier 2 already cut it from ~550 to ~404 lines. Further cuts risk losing
information that's genuinely needed for edge cases. The remaining prose is
largely load-bearing (Iron Rule, gotchas, registry semantics).

**Verdict:** Diminishing returns. The low-hanging fruit was harvested in Tier 2.

### 7.3 Full workflow engine (e.g., state chart, transition table)

A proper state machine with `transition(current_state, event) → next_state`
and explicit event types (artifact_created, user_approved, commit_done).

**Verdict:** Over-engineered for a 7-state workflow that runs ~monthly. The
drift-guard cost outweighs the benefit. The "enriched reporter" (§3) captures
90% of the value at 10% of the complexity.

## 8. Recommendation

**Implement the enriched `StageDescriptor` reporter (§3) with drift-guard
test (§6.3) and `--json` flag (§3.3 Option C).**

Scope it as a single Sonnet session in its own thread. No guide.md edits.
The drift-guard test is the key safety mechanism — without it, do not implement.

## 9. Decision Required

This is a note, not an implementation. Options:

1. **Approve** — create a new thread to implement §3 + §6.3.
2. **Defer** — the current system works; revisit after the next sync if
   re-derivation errors recur.
3. **Reject** — the drift risk isn't worth the savings.

No action is taken until the user decides.
