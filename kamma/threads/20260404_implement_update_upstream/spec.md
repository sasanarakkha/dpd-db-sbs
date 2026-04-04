# Spec: Implement `/update-upstream` Skill

## Goal

Write the `/update-upstream` Claude skill file that encodes the full 7-phase upstream sync
workflow — with Iron Rule enforcement, discussion flags, and 3-commit gating. Draft the
skill in-repo first for review, then install to `~/.claude/commands/` only after explicit
approval.

## Pre-condition

Thread `prepare_update_skill` must be complete:
- `kamma/upstream_sync/registry.json` exists with `discuss` fields.
- `kamma/upstream_sync/smd.md` has a concrete entry for every registry file.
- `kamma/upstream_sync/validate_registry.py` and `verify_smd_coverage.py` pass.

## Root Problems Being Solved

1. **AI invents fixes** instead of mirroring upstream — the skill enforces the Iron Rule
   explicitly at every phase.
2. **No discussion protocol** — files requiring human judgment get auto-touched without
   pausing.
3. **No 3-commit gates** — syncs complete in one unreviewed commit, hiding errors.
4. **Model confusion** — dynamic analysis needs PRO model but skill never instructs switch.

## Success Criteria

- Iron Rule appears at the top AND is referenced in Phases 3 and 4.
- All 3 commit gates have explicit user-approval stops before the commit command is presented.
- Discussion flags are enforced: `discuss: true` → STOP before touching the file.
- Triple Shadow Checklist is referenced in Phase 2 dynamic analysis.
- `smd.md` is read in Phase 0 and referenced in Phase 3.
- Model switch instructions are clear in Phases 2 and 4.
- The draft file is reviewed in-repo before installation to `~/.claude/commands/`.

## Deliverables

| File | Description |
|---|---|
| `kamma/upstream_sync/update-upstream.md` | In-repo draft of the skill |
| `~/.claude/commands/update-upstream.md` | Installed skill (after approval only) |

## Key Design Decisions

### Iron Rule (non-negotiable)
> When a shadow file breaks after sync, the ONLY fix is:
> 1. Open the upstream source
> 2. See exactly how upstream solves it
> 3. Copy that exact solution
> 4. Re-apply ONLY the local changes from `kamma/upstream_sync/smd.md`
>
> FORBIDDEN: workarounds, alternative libraries, try/except papering, restructuring
> differently from upstream.

### 3-Commit Gates
- Commit 1: after automated sync (`sync: automated upstream pull YYYY-MM-DD`)
- Commit 2: after manual merge resolutions + user verification (`sync: manual merge resolutions YYYY-MM-DD`)
- Commit 3: after cleanup and finalization (`sync: cleanup and finalization YYYY-MM-DD`)

Each gate requires explicit "Proceed with Commit N" from the user before the commit
command is presented.

### Discussion Flag Protocol
Before touching ANY file during Phase 3 execution, check its `discuss` field in
`registry.json`. If `discuss: true`: STOP, present the diff, state the reason, wait for
explicit "Approved" from the user.

### Model Switch Points
- Phase 2 (Dynamic Analysis): switch to PRO for deep diff analysis; switch back after.
- Phase 4 (Logic Audit): switch to PRO for compliance verification; switch back after.

### In-Repo Draft First
The skill is drafted as `kamma/upstream_sync/update-upstream.md` and reviewed before
being copied to `~/.claude/commands/`. External installation requires explicit approval.
