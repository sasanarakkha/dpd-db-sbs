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

<!-- LOCAL-START: Task Workflow -->
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
<!-- LOCAL-END: Task Workflow -->

## Quality Gates

Before marking any task complete, verify:

- [ ] All tests pass via `uv run pytest --tb=short -q`.
- [ ] Code follows project style guides (see `conductor/code_styleguides/`).
- [ ] No security vulnerabilities introduced.
- [ ] Documentation updated if needed.
- [ ] Data integrity preserved (no data removed from `docs/`).
- [ ] All public functions/methods are documented.
- [ ] Type safety is enforced.
- [ ] Works correctly on mobile (if applicable).
- [ ] `docs/` folder updated with all relevant changes (features, technical specs, API docs, etc.).

## Review Protocol

When reviewing a track's implementation:

1. Read `spec.md` and `plan.md` — does code match intent?
2. Check against `conductor/code_styleguides/` files.
3. Verify all **Quality Gates** pass.
4. Run external review tool if available: `coderabbit --prompt-only`.
5. Output findings with severity levels (Critical/High/Medium/Low).

## Revert Protocol

Since `conductor/` is version-controlled, revert via git:

1. Identify scope (whole track, single phase, or single task).
2. Use `git revert` or `git checkout` for the relevant changes.
3. Update `plan.md` to reflect reverted state.
4. Document reason in `handoff.md`.

## Track File Set (Canonical)

Every track folder must contain:

- **metadata.json** — track ID, type, status, timestamps, description.
- **index.md** — links to other track files.
- **spec.md** — specification / requirements.
- **plan.md** — implementation plan with status markers.
  - **Plan Mode Target Enforcement:** The generated plan MUST be written directly to `conductor/tracks/<track_id>/plan.md`.
- **handoff.md** — cross-session state.

## Definition of Done

A track is complete when:

1. All tasks marked `[x]` in `plan.md`.
2. All **Quality Gates** pass.
3. User has approved all changes.
4. Single atomic commit prepared by AI and manually committed by user.
5. Track archived to `conductor/archive/` (this folder is never committed).

## Skills

| Skill | Description |
|---|---|
| `/conductor-new-track` | Create a new track for planning a feature or task |
| `/conductor-continue` | Resume work on an in-progress track |
| `/conductor-review` | Review implementation against spec and quality gates |
| `/conductor-complete` | Finish, archive, and close a track (coderabbit → fix → test → archive) |
| `/conductor-goodnight` | End-of-session protocol — write session log, optionally update handoff |
| `/conductor-sync` | Sync Conductor workflow across all registered projects |
| `/conductor-fix` | Run ruff and pyright on a script, then fix all reported errors |

<!-- LOCAL-START: Development Commands -->
## Development Commands

### Daily Development
```bash
# Linting and Formatting
uv run ruff check .
uv run ruff format .

# Testing
uv run pytest
```
<!-- LOCAL-END: Development Commands -->

<!-- LOCAL-START: Testing Requirements -->
## Testing Requirements

### Unit Testing
- Every module must have corresponding tests.
- Test both success and failure cases.
<!-- LOCAL-END: Testing Requirements -->

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

- Review workflow weekly
- Update based on pain points
