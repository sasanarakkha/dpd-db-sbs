# Implementation Plan: Gemini CLI Safety Hook (pytest guard)

## Objective
Implement a preventative safety hook in the Gemini CLI to block bare `pytest` commands, similar to the existing `guard_pytest.sh` hook used for Claude Code. This ensures that parallel full-suite test runs do not inadvertently trigger massive memory consumption on macOS.

## Key Files & Context
- `~/.gemini/hooks/guard_pytest.sh` (New File)
- `~/.gemini/settings.json` (Modified File)

## Background & Motivation
A previous issue occurred where the agent executed multiple concurrent bare `pytest` commands (`uv run pytest --tb=short -q`), leading to ~91 GB of virtual memory pressure on macOS due to aggressive mmap allocations by the test suite. A `PreToolUse` hook was implemented for Claude to block this. As a preventative measure, a similar `BeforeTool` hook should be available for the Gemini CLI to intercept the `run_shell_command` tool if this issue ever arises.

## Implementation Steps

### Phase 1: Create the Guard Hook Script
1.  **Create the script:** Create the file `~/.gemini/hooks/guard_pytest.sh`.
2.  **Write the logic:** The script must read JSON input from stdin, extract the command from the `tool_input.command` field, and check if it is a bare `pytest` invocation.
    ```bash
    #!/usr/bin/env bash
    # Blocks bare pytest Bash calls (no specific test file) to prevent memory explosions.
    
    # Read hook input (JSON) from stdin
    input=$(cat)
    command=$(echo "$input" | jq -r '.tool_input.command // ""')

    # Pass through if no pytest in command
    echo "$command" | grep -qE '\bpytest\b' || exit 0

    # Pass through if a specific tests/*.py file is given
    echo "$command" | grep -qE 'pytest\s+tests/[^ ]+\.py' && exit 0

    # Block: bare pytest without a specific file
    echo '{"decision": "deny", "reason": "Bare pytest is blocked to prevent memory explosion. Use: uv run pytest tests/<specific_file>.py -v"}'
    exit 0
    ```
3.  **Set permissions:** Make the script executable (`chmod +x ~/.gemini/hooks/guard_pytest.sh`).

### Phase 2: Wire the Hook in Settings
1.  **Update `settings.json`:** Open `~/.gemini/settings.json`.
2.  **Add `BeforeTool` hook:** Add the following configuration to the `hooks` object to trigger the guard script whenever `run_shell_command` is used:
    ```json
    {
      "hooks": {
        "BeforeTool": [
          {
            "matcher": "run_shell_command",
            "hooks": [
              {
                "name": "pytest-guard",
                "type": "command",
                "command": "bash ~/.gemini/hooks/guard_pytest.sh"
              }
            ]
          }
        ]
      }
    }
    ```
    *Note: Ensure the resulting JSON is well-formed if other hooks already exist.*

## Verification & Testing
1.  **Test Blocking:** Attempt to execute a bare `pytest` command (e.g., `uv run pytest`) via the agent. The command should be intercepted, and the agent should receive the `"deny"` decision with the provided reason.
2.  **Test Allowed Commands:** Attempt to execute a targeted `pytest` command (e.g., `uv run pytest tests/test_example.py`). The command should execute normally.
3.  **Test Irrelevant Commands:** Attempt to execute a non-pytest command (e.g., `ls -la`). The command should execute normally.

## Migration & Rollback
To disable the hook, either:
1.  Remove the `BeforeTool` entry from `~/.gemini/settings.json`.
2.  Modify `~/.gemini/hooks/guard_pytest.sh` to always return `{"decision": "allow"}`.