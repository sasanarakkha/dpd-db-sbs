# Spec: `/update-upstream` Skill

## Goal
Create a standalone Claude skill (`/update-upstream`) that makes upstream sync smooth, reliable, and frustration-free. This replaces the fragile Conductor-based rehearsal process.

## Root Problems Being Solved
1. **AI invents fixes** instead of mirroring upstream — invalidates the entire sync
2. **Generic instructions** ("consider localized changes") don't work — AI needs per-file, concrete rules
3. **Scattered tooling** — spec, plan, guide, registry spread across `conductor/templates/`
4. **No discussion flags** — AI charges through files that need human judgment

## Success Criteria
- AI never introduces a new solution during sync — it mirrors upstream, then re-applies local changes
- Every shadow file has a concrete SMD entry telling the AI exactly what to preserve
- Files requiring human judgment are flagged and paused before touching
- The 3-commit rule is strictly enforced with explicit user approval gates
- `tests/test_shadow_parity.py` passes after every sync

## Deliverables

### 1. `/Users/deva/.claude/commands/update-upstream.md`
The skill protocol. Phases 0–7 with Iron Rule enforcement at every step.

### 2. `kamma/upstream_sync/smd.md`
**Shadow Module Descriptions** — per-file breakdown of every local change.
The AI reads this before touching anything.

### 3. `kamma/upstream_sync/registry.json`
Moved from `conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json`.
Extended with `discuss` and `discuss_reason` fields.

### 4. `kamma/upstream_sync/guide.md`
Slimmed process reference (most protocol moves into the skill).

### 5. `kamma/upstream_sync/improvements.md`
Moved from conductor templates for reference.

## Key Design Decisions

### Iron Rule (critical)
> When a shadow file breaks after sync, the ONLY fix is:
> 1. Open the upstream source
> 2. See exactly how upstream solves it
> 3. Copy that exact solution
> 4. Re-apply ONLY the local changes from smd.md
>
> FORBIDDEN: workarounds, alternative libraries, try/except papering, restructuring differently from upstream.

### SMD Format (per file)
Each entry specifies: Local Changes (numbered, concrete), Sync Rule (PORT / MIRROR EXACTLY / PRESERVE / DISCUSS).

### Discussion Flags
Files marked `"discuss": true` in registry trigger a STOP and require explicit user decision before the AI touches them:
- `db/models.py` — schema changes
- `gui2/main.py` — UI tab structure
- `.gitignore` — must be manually merged
- `AGENTS.md` — fork identity

### File Relocation
All sync tooling moves from `conductor/templates/upstream_sync_rehearsal/` to `kamma/upstream_sync/`.
Conductor templates remain as reference during the transition period.
