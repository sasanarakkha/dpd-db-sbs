# Project Workflow

## Principles

1. **The Plan is the Source of Truth:** All work must be tracked in `plan.md`.
2. **Task Sequentiality:** Choose the next available task from `plan.md` in sequential order.
3. **Scope Hard Stop:** Implement only what the user explicitly requested and
   what the active plan/spec explicitly requires. If any unrequested edit seems
   useful, necessary, safer, or required to proceed, stop before editing and ask
   the user for explicit approval. Without approval, do not make that edit.
4. **Root Hygiene:** The repository root is never a scratch directory. Temporary
   scripts, logs, probes, transcripts, dumps, and generated artifacts must go
   under `temp/`. Tests must go under `tests/`. Treat `temp/` as disposable
   trashcan storage: delete temporary files once they have fulfilled their
   purpose.


## Task Lifecycle (TDD)

All tasks follow a strict lifecycle:

1. **Mark In Progress:** Change task status from `[ ]` to `[~]` in `plan.md`.
2. **Red Phase (Failing Tests):**
   - Create a new test file or add cases to existing ones in `tests/`.
   - Run tests and confirm failure (see **Quality Gates** for commands).
3. **Green Phase (Implementation):** Write minimum code to pass tests.
4. **Refactor Phase:** Clean up code while keeping tests green.
5. **Empirical Validation:** Run the script against a real test target and verify output. Confirm all **Quality Gates** pass.
6. **Root Hygiene Check:** Run `git status --short` and confirm no new
   root-level untracked scratch files were created. Move or remove any
   agent-created scratch files before completion. Delete temporary files in
   `temp/` once they have fulfilled their purpose; do not keep them for handoff.
7. **Completion:** Mark task as complete `[x]` in `plan.md`. Do NOT commit yet.

### Phase Completion Verification and Checkpointing Protocol

**Trigger:** This protocol is executed immediately after a task is completed that also concludes a phase in `plan.md`.

1.  **Announce Protocol Start:** Inform the user that the phase is complete and the verification protocol has begun.

2.  **Ensure Test Coverage for Phase Changes:**
    -   **Step 2.1: Determine Phase Scope:** Identify files changed since the last marked phase.
    -   **Step 2.2: Verify and Create Tests:** For each modified code file, verify a corresponding test file exists. Create missing tests as needed.

3.  **Execute Automated Tests with Proactive Debugging:**
    -   Announce the test command (e.g., `CI=true pytest`).
    -   Execute and debug if necessary (max 2 fix attempts).

4.  **Propose a Detailed, Actionable Manual Verification Plan:**
    -   Generate a step-by-step plan for the user to verify the phase's goals.

5.  **Await Explicit User Feedback:**
    -   Ask the user: "**Does this meet your expectations? Please confirm with yes or provide feedback on what needs to be changed.**"
    -   **PAUSE** and await the user's response.

6.  **Mark Phase as Complete in Plan:**
    -   Update `plan.md` to show the phase is finished.

7.  **Announce Completion:** Inform the user that the phase is complete and ready for their manual checkpoint commit.

## Quality Gates

Before marking any task complete, verify:

- [ ] **Pre-completion validation — run ALL of the following on the exact changed file(s),
      one command at a time, never batched together, never on `.` or the whole repo:**
      1. `uv run ruff check --fix <file>`
      2. `uv run ruff format <file>`
      3. `uv run pyright <file>`
      4. `uv run --with pyrefly pyrefly check --min-severity warn <file>`
      5. `uv run pytest tests/test_<thread_name>.py -v`
      **Do NOT report completion until every command passes.**
      Pyrefly warnings count as failures unless explicitly approved by the user.
      **NEVER use bare `uv run pytest` without a specific file path —
      parallel bash calls spawn concurrent processes and cause macOS memory
      explosions (91 GB+). Enforced by `~/.claude/hooks/guard_pytest.sh`.**
- [ ] **Structural Integrity**: For all renames/moves, confirmed via `grep` that 100% of references (imports, scripts, workflows, docs) are updated.
- [ ] **Blast-Radius (Shared Code)**: When the behavior, signature, return
      shape, or contract of a shared symbol changed (anything under `tools/`, or
      any module imported in more than one place), `grep`ed for every
      importer/caller, read each call site, and ran the tests/entrypoints that
      exercise them — not just the edited file. Dependents checked are listed in
      the completion report; any caller that cannot be verified is called out.
      A clean static check on the edited file says nothing about its callers;
      this applies even when the symbol name is unchanged.
- [ ] **Root Hygiene**: No new temporary scripts, logs, probes, transcripts,
      dumps, generated reports, fixtures, or test output files exist in the
      repository root. Scratch artifacts are in `temp/`; tests are in `tests/`.
      Temporary files in `temp/` that have fulfilled their purpose are deleted,
      not kept as hidden handoff state.
- [ ] Code follows project style guides (see `conductor/code_styleguides/`).
- [ ] No security vulnerabilities introduced.
- [ ] Documentation updated if needed.
- [ ] Data integrity preserved (no data removed from `docs/`).
- [ ] All public functions/methods are documented.
- [ ] Type safety is enforced.
- [ ] Works correctly on mobile (if applicable).
- [ ] `docs/` folder updated with all relevant changes (features, technical specs, API docs, etc.).

## Review Protocol

When reviewing a thread's implementation:

1. Read `spec.md` and `plan.md` — does code match intent?
2. Check against `conductor/code_styleguides/` files.
3. Verify all **Quality Gates** pass.
4. Run external review tool if available: `coderabbit --prompt-only`.
5. Output findings with severity levels (Critical/High/Medium/Low).

## Revert Protocol

Since `kamma/` is version-controlled, revert via git:

1. Identify scope (whole thread, single phase, or single task).
2. Use `git revert` or `git checkout` for the relevant changes.
3. Update `plan.md` to reflect reverted state.
4. Document reason in `handoff.md`.

## Thread File Set (Canonical)

Every thread folder must contain:

- **spec.md** — specification / requirements.
- **plan.md** — implementation plan with status markers.
  - **Plan Mode Target Enforcement:** The generated plan MUST be written directly to `kamma/threads/<thread_id>/plan.md`.
- **handoff.md** — cross-session state (created when needed).

## Definition of Done

A thread is complete when:

1. All tasks marked `[x]` in `plan.md`.
2. All **Quality Gates** pass.
3. User has approved all changes.
4. Single atomic commit prepared by AI and manually committed by user.
5. Thread archived to `kamma/archive/` (this folder is never committed).

## Skills

| Skill | Description |
|---|---|
| `/kamma:1-plan` | Create a new thread for planning a feature or task |
| `/kamma:2-do` | Resume work on an in-progress thread |
| `/kamma:3-review` | Review implementation against spec and quality gates |
| `/kamma:4-finalize` | Finish, archive, and close a thread |
| `/kamma:5-status` | Show current progress across all threads |

## Development Commands

### Daily Development
```bash
# Run each command separately on the exact file — never batch, never use `.` (whole repo)
uv run ruff check --fix <file>
uv run ruff format <file>
uv run pyright <file>
uv run --with pyrefly pyrefly check --min-severity warn <file>

# Testing — always use targeted file paths in plans and agentic tasks
uv run pytest tests/test_<specific>.py -v
# WARNING: bare `uv run pytest` (no file path) is blocked by the
# PreToolUse guard hook during agentic sessions. Manual use only.
```

## Testing Requirements

### Unit Testing
- Every module must have corresponding tests.
- Test both success and failure cases.

## Commit Guidelines (For User)

### Submodule Scope
When preparing commit plans, checkpoint commits, draft commit messages, or any
discussion of what to commit, exclude `resources/` submodule pointer changes by
default. Mention dirty `resources/*` submodules separately and never suggest
staging or committing them unless the user explicitly asks for submodule
updates.

### Message Format
```
<type>(<scope>): <description>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests
- `chore`: Maintenance tasks

## Continuous Improvement

- Review workflow periodically.
- Update based on pain points.
