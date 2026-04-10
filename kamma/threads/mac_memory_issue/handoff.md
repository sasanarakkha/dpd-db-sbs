# Handoff: Memory Issue Resolution

## Status
- **Phase**: Implementation pending
- **Date**: 2026-04-10
- **Priority**: Critical

---

## Problem

- `/kamma:2-do` caused 80GB memory explosion on macOS
- System ran out of memory, process terminated
- Root cause: async pytest hook spawning 30+ concurrent processes during agentic workflow

### Root Cause Analysis
1. User has `PostToolUse` hook in `~/.claude/settings.json`
2. Hook runs `uv run pytest` on every Python file edit
3. With `async: true`, multiple hook instances run concurrently
4. `/kamma:2-do` performs 30+ rapid file edits
5. 30+ concurrent pytest processes × ~3GB each = 90GB total

### Why It Occurred
- Hook created for local development workflow
- Works fine in interactive mode (few edits)
- Agentic workflows (kamma) do 30+ rapid sequential edits
- Memory accumulation happens only in agentic mode

---

## Solution Applied

### Changes Required
1. **Disable pytest** in hook (line 22 of pytest_on_edit.sh)
   - Keep only pyright for type checking
2. **Keep async: true** (safe with lightweight pyright)

### File: ~/.claude/hooks/pytest_on_edit.sh
```bash
# BEFORE (line 22):
PYTEST_OUT=$(uv run pytest --tb=short -q 2>&1)

# AFTER (comment out):
# PYTEST_OUT=$(uv run pytest --tb=short -q 2>&1)
```

---

## Verification

After making changes, run `/kamma:2-do` and monitor:
```bash
btop
# or
top -o mem
```

Expected result: ~6GB max (pyright processes) vs 80-90GB before

---

## Open Items
- [ ] Apply fix to pytest_on_edit.sh
- [ ] Test with /kamma:2-do
- [ ] Verify no memory explosion

---

## Notes
- pyright is fast and lightweight (~200MB vs ~3GB for pytest)
- async: true is safe with pyright
- If issues persist, fall back to `async: false`