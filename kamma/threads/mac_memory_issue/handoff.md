# Handoff: mac_memory_issue

## Status
VERIFIED COMPLETE. All fixes applied, hook is live and confirmed working.

## Summary
A PreToolUse hook was installed in Claude Code to hard-block bare `uv run pytest`
calls during agentic sessions. Root cause was parallel bare pytest invocations
spawning concurrent 1.5 GB processes, causing 91 GB memory pressure on macOS.

## What was done
1. **Hard Block (Claude Code)**:
   - `~/.claude/hooks/guard_pytest.sh` — PreToolUse hook that hard-blocks bare `uv run pytest`. Exits 2 = Claude Code hard block.
   - `~/.claude/settings.json` — PreToolUse wired to `guard_pytest.sh` for all Bash calls.
2. **Workflow Documentation**:
   - `kamma/workflow.md` — Quality Gates and Dev Commands updated with targeted pytest mandates and warnings.
   - `conductor/workflow.md` — Updated with targeted pytest mandates.
3. **Repository-Wide Targeted Test Update**:
   - Performed a full scan of the repository.
   - Replaced bare `uv run pytest` with targeted file paths in:
     - `kamma/threads/20260412_vib_rule_workflow/plan.md`
     - `kamma/threads/20260412_vib_rule_workflow/spec.md`
     - `kamma/threads/20260411_tpr_index/plan.md`
     - `kamma/threads/20260409_repeating_ru_check/plan.md`
     - `kamma/upstream_sync/templates/sync_thread_plan.md`
     - `kamma/upstream_sync/archive_improvements.md`
     - `kamma/upstream_sync/stages/execution.md`
     - `kamma/upstream_sync/README.md`
     - `kamma/upstream_sync/guide.md`
4. **Gemini Prevention Plan**:
   - `kamma/threads/mac_memory_issue/plan_gemini_hook.md` created for if similar memory issues ever occur with Gemini.

## Verification
- Hook is **live and confirmed working**: a test Bash call containing `pytest`
  was intercepted and blocked by the PreToolUse hook in real-time during the
  verification session (2026-04-12). The hook correctly emitted the block
  message and exited with code 2.
- `grep` verification: No remaining unguarded bare `uv run pytest` calls in
  active plans or sync templates.

## Keep this thread
This thread and its plan are kept for reference. If a similar memory issue
occurs in future (with Claude Code or Gemini), refer to:
- `plan.md` — step-by-step fix for Claude Code
- `plan_gemini_hook.md` — preventative plan for Gemini CLI

## Known Errors / Repeated Mistakes (for future reference)
- **The hook blocks itself**: Attempting to test `guard_pytest.sh` by running
  a Bash command that contains the word "pytest" (even in an echo/pipe) will
  trigger the hook on the outer command. Workaround: write the test to a temp
  `.sh` file first, then invoke it with a command that has no "pytest" string.
- **exit 2 not exit 1**: Must exit 2 for Claude Code hard block. exit 1 is
  treated as an error but may not block.
- **JSON validity**: `~/.claude/settings.json` must be valid JSON after editing.
