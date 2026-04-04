# Improve the `implement_update_upstream` Plan Before Implementation

## Summary

The implementation thread should own only the `/update-upstream` skill itself and the
workflow encoded inside it. It should assume the prep thread has already delivered the
canonical registry, SMD coverage, and validator scripts.

Current repo facts that materially affect this thread:

- Writing `~/.claude/commands/update-upstream.md` is outside the repo and should be
  treated as a separate installation step requiring approval.
- The skill workflow must not depend on behavior the prep thread has not yet enabled.
- Per-run execution artifacts such as `dynamic_plan.md` should stay in the active thread
  folder, not in `kamma/upstream_sync/`.

## Key Changes

- Make the skill depend explicitly on prep-thread completion:
  - `kamma/upstream_sync/registry.json` exists and is validated.
  - `kamma/upstream_sync/smd.md` has full coverage.
  - validators pass before skill drafting begins.
- Keep static tooling and runtime artifacts separate:
  - `kamma/upstream_sync/` contains the reusable skill draft and sync references.
  - `dynamic_plan.md` and other per-run artifacts stay thread-local during execution.
- Treat external installation as the final step:
  - Draft the skill in-repo first.
  - Review the draft in-repo.
  - Install to `~/.claude/commands/update-upstream.md` only after approval.
- Keep command realism in the skill:
  - Do not promise dry-run or no-commit behaviors unless the prep thread actually adds
    them.
  - Match verification commands to real tool behavior.
- Keep the workflow centered on execution control:
  - Iron Rule at the top and reused in execution/audit phases.
  - Discussion-flag protocol enforced before touching flagged files.
  - Three user approval gates before presenting commit commands.
  - Explicit model switch points for deep analysis and logic audit.
- Keep the skill focused on sync execution, not infrastructure migration:
  - Registry relocation, SMD generation, and validator creation belong to the prep
    thread and should only be referenced here as prerequisites.

## Public Interface Changes

- Add the in-repo skill draft:
  - `kamma/upstream_sync/update-upstream.md`
- Add the installed external skill after approval:
  - `~/.claude/commands/update-upstream.md`
- The skill should reference these existing prep-thread interfaces rather than redefine
  them:
  - canonical `registry.json`
  - canonical `smd.md`
  - validation scripts

## Test Plan

- Draft review:
  - Verify the in-repo draft contains the full phase structure and required gates before
    installation.
- Workflow validation:
  - Iron Rule is present at the top and referenced again in execution/audit phases.
  - Discussion-flag protocol stops work before flagged files are modified.
  - Triple-shadow checks appear in dynamic analysis.
  - `dynamic_plan.md` is always thread-local, never under `kamma/upstream_sync/`.
- Install verification:
  - After approval, confirm the installed file exists and matches the reviewed draft.

## Assumptions And Defaults

- This thread does not create the sync infrastructure; it consumes it.
- Installation to `~/.claude/commands/` happens only after the repo draft is reviewed.
- Any workflow promises around no-commit, dry-run, or cleanup safety must reflect the
  actual prepared tooling rather than aspirational behavior.
