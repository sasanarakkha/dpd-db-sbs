# plan.md — macOS Memory Explosion Fix (Round 2)

## Context for executing agent
- Project root: `/Users/deva/Documents/dpd-db`
- Spec: `kamma/threads/mac_memory_issue/spec.md` — read it first
- Hook directory: `~/.claude/hooks/`
- Settings file: `~/.claude/settings.json`
- Workflow template: `kamma/workflow.md`
- Affected plan: `kamma/threads/20260412_vib_rule_workflow/plan.md`
- **CRITICAL CONSTRAINT**: Do NOT edit `vib_rule_workflow/plan.md` while
  another terminal tab is actively running `/kamma:2-do` on that thread.
  Ask the user to confirm that session has ended before Phase 3.
- No TDD required — this is a config/documentation chore. No test files needed.
- Files outside the repo (`~/.claude/`) cannot be committed. Only
  `kamma/workflow.md` and `kamma/threads/` files go in the commit.

---

## Phase 1: Hard Block — PreToolUse Hook

### Task 1.1 — Read current settings.json
`[ ]`
- Read `~/.claude/settings.json`
- Confirm the existing hooks structure (PostToolUse + PermissionRequest)
- Note the exact JSON structure so the new PreToolUse block matches the style

### Task 1.2 — Write guard_pytest.sh
`[ ]`
- Create `~/.claude/hooks/guard_pytest.sh` with this exact content:
  ```bash
  #!/bin/bash
  # Blocks bare pytest Bash calls (no specific test file) to prevent memory explosions.
  CMD=$(jq -r '.tool_input.command // ""')

  # Pass through if no pytest in command
  echo "$CMD" | grep -qE '\bpytest\b' || exit 0

  # Pass through if a specific tests/*.py file is given
  echo "$CMD" | grep -qE 'pytest\s+tests/[^ ]+\.py' && exit 0

  # Block: bare pytest without a specific file
  echo '{"decision":"block","reason":"Bare pytest blocked to prevent memory explosion. Use: uv run pytest tests/<specific_file>.py -v"}'
  exit 2
  ```
- Make it executable: `chmod +x ~/.claude/hooks/guard_pytest.sh`

### Task 1.3 — Wire hook into settings.json
`[ ]`
- Read `~/.claude/settings.json` again (current state)
- Add a `PreToolUse` key to the `hooks` object with this block:
  ```json
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
          "command": "bash ~/.claude/hooks/guard_pytest.sh"
        }
      ]
    }
  ]
  ```
- The final `hooks` object must contain all three keys:
  `PreToolUse`, `PostToolUse`, `PermissionRequest`
- Validate JSON is well-formed after editing

### Phase 1 Completion Verification
`[ ]`
- Re-read `~/.claude/hooks/guard_pytest.sh` and confirm content is correct
- Confirm the script is executable: `ls -la ~/.claude/hooks/guard_pytest.sh`
- Re-read `~/.claude/settings.json` and confirm `PreToolUse` block is present
- Announce: "Phase 1 complete — PreToolUse guard hook installed"

---

## Phase 2: Documentation Fix — workflow.md (Option C)

### Task 2.1 — Update Quality Gates in workflow.md
`[ ]`
- Read `kamma/workflow.md` lines 48–60
- Find the Quality Gates checklist line (around line 52):
  ```
  - [ ] All tests pass via `uv run pytest --tb=short -q`.
  ```
- Replace with:
  ```
  - [ ] All tests pass via `uv run pytest tests/test_<thread_name>.py -v`.
        **NEVER use bare `uv run pytest` without a specific file path —
        parallel bash calls will spawn concurrent processes and cause
        macOS memory explosions (91 GB+). This is enforced by the
        PreToolUse guard hook in `~/.claude/hooks/guard_pytest.sh`.**
  ```

### Task 2.2 — Update Development Commands section
`[ ]`
- In `kamma/workflow.md`, find the Testing section under Development Commands:
  ```
  # Testing
  uv run pytest
  ```
- Replace with:
  ```
  # Testing — always use targeted file paths in plans and agentic tasks
  uv run pytest tests/test_<specific>.py -v
  # WARNING: bare `uv run pytest` (no file path) is blocked by the
  # PreToolUse guard hook during agentic sessions. Manual use only.
  ```

### Phase 2 Completion Verification
`[ ]`
- Re-read updated `kamma/workflow.md` and confirm both changes are present
- Grep for bare `uv run pytest` in workflow.md — must return zero unguarded matches:
  `grep -n "uv run pytest$\|uv run pytest --" kamma/workflow.md`
- Announce: "Phase 2 complete — workflow.md updated"

---

## Phase 3: Retroactive Fix — vib_rule_workflow plan

### Task 3.1 — Confirm the other tab's session has ended
`[ ]`
- Ask the user: "Has the kamma:2-do session for vib_rule_workflow finished
  in the other tab? Reply yes to proceed."
- PAUSE and wait for explicit user confirmation before continuing

### Task 3.2 — Read vib_rule_workflow/plan.md
`[ ]`
- Read `kamma/threads/20260412_vib_rule_workflow/plan.md` in full
- Locate every occurrence of `uv run pytest` (with any flags)
- Expected locations: Task 1.4, Phase 1 Completion, Phase 3 Completion, Task 4.2

### Task 3.3 — Replace full-suite pytest calls
`[ ]`
- For each bare pytest occurrence, replace with:
  ```
  uv run pytest tests/test_vib_rule_workflow.py -v
  ```
- Strip any extra flags (`--tb=short`, `-q`, `--ignore=...`) — they are
  unnecessary when targeting a single file
- Verify with Grep that no bare pytest remains:
  `grep -n "uv run pytest$\|uv run pytest --" kamma/threads/20260412_vib_rule_workflow/plan.md`
  Must return zero results

### Phase 3 Completion Verification
`[ ]`
- Re-read the updated plan and confirm all pytest calls are targeted
- Announce: "Phase 3 complete — vib_rule_workflow plan patched"

---

## Phase 4: Hook Verification

### Task 4.1 — Confirm pytest_on_edit.sh still has pytest disabled
`[ ]`
- Read `~/.claude/hooks/pytest_on_edit.sh`
- Confirm this line is still commented out:
  `# PYTEST_OUT=$(uv run pytest --tb=short -q 2>&1)`
- If it is NOT commented out, comment it out now and note the discrepancy
- Announce: "Hook verified — pytest disabled" or "Hook fixed"

### Phase 4 Completion Verification
`[ ]`
- Confirm all four fixes are in place:
  1. `~/.claude/hooks/guard_pytest.sh` exists, is executable, blocks bare pytest
  2. `~/.claude/settings.json` has `PreToolUse` wired to the guard hook
  3. `kamma/workflow.md` Quality Gates use targeted pytest + prohibition note
  4. `vib_rule_workflow/plan.md` has no bare full-suite pytest calls
  5. `pytest_on_edit.sh` has pytest commented out
- Ask user: "Does this meet your expectations? Please confirm with yes or provide feedback."
- **PAUSE and await user response**

---

## Phase 5: Commit Preparation

### Task 5.1 — Stage repo files only
`[ ]`
- Stage only files inside the repo (files under `~/.claude/` cannot be committed):
  ```bash
  git add kamma/workflow.md
  git add kamma/threads/20260412_vib_rule_workflow/plan.md
  git add kamma/threads/mac_memory_issue/spec.md
  git add kamma/threads/mac_memory_issue/plan.md
  git add kamma/threads/mac_memory_issue/handoff.md
  ```

### Task 5.2 — Prepare commit message (do NOT run git commit)
`[ ]`
- Present for manual execution:
  ```
  fix(kamma): block bare pytest in agentic plans + workflow.md guard

  Add PreToolUse hook (guard_pytest.sh) that hard-blocks bare `uv run pytest`
  calls at the Claude Code harness level. Update workflow.md Quality Gates to
  require targeted test file paths. Patch vib_rule_workflow plan retroactively.
  Root cause: parallel bash calls spawned concurrent 1.5 GB pytest processes,
  causing 91 GB memory pressure on macOS.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  ```
- Stop. Do not run `git commit`. User commits manually.

---

## Known Errors / Repeated Mistakes to Avoid
- **Never edit vib_rule_workflow/plan.md** while a kamma:2-do session is
  active on that thread. Always confirm the session has ended first (Task 3.1).
- **JSON validity**: `~/.claude/settings.json` must be valid JSON after editing.
  A malformed settings.json will break all Claude Code hook processing. Read
  the file before and after editing to verify structure.
- **exit 2 not exit 1**: The guard hook must exit with code 2 for Claude Code
  to treat it as a hard block. exit 1 is treated as an error but may not block.
- **No test files to write**: This is a config/documentation chore. Do not
  create test files.
- **Files outside the repo**: `~/.claude/` changes are not committed. Only
  `kamma/` files go into git.
- **Do not commit**: Prepare `git add` + draft message only. User commits manually.
