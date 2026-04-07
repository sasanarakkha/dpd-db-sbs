# Project Workflow

## Principles

1. **The Plan is the Source of Truth:** All work must be tracked in `plan.md`.
2. **Task Sequentiality:** Choose the next available task from `plan.md` in sequential order.


## Task Lifecycle (TDD)

All tasks follow a strict lifecycle:

1. **Mark In Progress:** Change task status from `[ ]` to `[~]` in `plan.md`.
2. **Red Phase (Failing Tests):**
   - Create a new test file or add cases to existing ones in `tests/`.
   - Run tests and confirm failure (see **Quality Gates** for commands).
3. **Green Phase (Implementation):** Write minimum code to pass tests.
4. **Refactor Phase:** Clean up code while keeping tests green.
5. **Empirical Validation:** Run the script against a real test target and verify output. Confirm all **Quality Gates** pass.
6. **Completion:** Mark task as complete `[x]` in `plan.md`. Do NOT commit yet.

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

- [ ] All tests pass via `uv run pytest --tb=short -q`.
- [ ] **Structural Integrity**: For all renames/moves, confirmed via `grep` that 100% of references (imports, scripts, workflows, docs) are updated.
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
# Linting and Formatting
uv run ruff check .
uv run ruff format .

# Testing
uv run pytest
```

## Testing Requirements

### Unit Testing
- Every module must have corresponding tests.
- Test both success and failure cases.

## Commit Guidelines (For User)

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
