# Project Workflow

## Guiding Principles

1. **The Plan is the Source of Truth:** All work must be tracked in `plan.md`
2. **NO AGENT COMMITS WITHOUT EXPLICIT SIGNAL:** The AI agent must NEVER execute `git commit`, `git add`, or `git notes` for the final stage or mark a track complete without the user explicitly stating the exact phrase "Proceed with final commit". Do NOT assume the stage is complete just because tests pass. The user will manually review all changes.
3. **Strict Upstream Logic Parity:** For all shadow copies (localized Russian or SBS versions), you MUST maintain strict logic parity with the original upstream source files. When fixing bugs or implementing updates in shadow copies, DO NOT introduce new solutions. Instead, refer back to the original source as the absolute authority and emulate its implementation exactly, only layering localized data or UI updates on top.
4. **The Tech Stack is Deliberate:** Changes to the tech stack must be documented in `tech-stack.md` *before* implementation
5. **Data Output Verification:** Write tests to verify accurate data output. Automated tests are NOT required for UI elements, CSS, or HTML, as these are best verified and tweaked by a human. Do not test UI components - user interaction will reveal UI issues. Do not test internal function implementation details.
6. **User Experience First:** Every decision should prioritize user experience
7. **README Maintenance:** Each project folder contains a `README.md`, which MUST be updated if anything within the folder changes to ensure documentation stays in sync with code.
8. **Documentation is Mandatory:** Once a task is finished and approved by the user, the `docs/` folder MUST be updated with all relevant changes. This is not optional.
9. **Code Quality is Mandatory:** All changed files MUST pass `uv run ruff check --fix` and `uv run ruff format` before task completion. This is not optional.
10. **Non-Interactive & CI-Aware:** Prefer non-interactive commands. Use `CI=true` for watch-mode tools (tests, linters) to ensure single execution.
11. **Proactive Research:** Always perform a Google Search during the planning and task execution phases for any framework-specific (e.g., Flet), OS-specific (e.g., Linux window management), or non-trivial technical requirements to identify known quirks, limitations, or best practices.
12. **Root Directory Cleanliness:** NEVER create temporary files, scripts, or reports in the project's root directory. All temporary data should go into `temp/` (which is git-ignored), scripts into `scripts/`, and track-specific reports into their respective folder in `conductor/tracks/`. A clean root directory is mandatory for project organization.
13. **Focused Exporter Tracking:** During synchronization, only track and update exporters that contain localized data (Russian, SBS, or DPS-specific). Ignore changes to upstream exporters that have no localized counterparts or relevance to localized data. Maintain a list of relevant exporters in the sync registry.
14. **Unambiguous Approval Protocol:** To prevent premature commits or phase advancements, the AI agent MUST adhere to this strict protocol:
    - **Feedback is NOT Approval:** If the user points out an error, suggests a change, or asks a question, the agent MUST perform the requested action and then **ask for approval again**.
    - **Explicit Signal Required:** The agent MUST NOT proceed to a commit or the next phase until the user provides an explicit signal of completion, such as: *"Phase X is complete"*, *"Approved"*, or *"Proceed with commit"*.
    - **Confirm Understanding:** If the user's response is ambiguous, the agent MUST ask: *"Does this mean I have your approval to commit and proceed to the next task? Please confirm with 'Yes' or 'Phase X is complete'."*

## Task Workflow

All tasks follow a strict lifecycle:

### Standard Task Workflow

1. **Select Task:** Choose the next available task from `plan.md` in sequential order

2. **Research & Planning:** 
   - Before marking a task in progress, perform a Google Search to identify any known issues or platform-specific nuances related to the task.
   - Update the implementation approach if research reveals a more robust solution.

3. **Mark In Progress:** Before beginning work, edit `plan.md` and change the task from `[ ]` to `[~]`

3. **Write Failing Tests (Red Phase):**
   - Create a new test file for the feature or bug fix.
   - Write one or more unit tests that clearly define the expected behavior and acceptance criteria for the task.
   - **CRITICAL:** Run the tests and confirm that they fail as expected. This is the "Red" phase of TDD. Do not proceed until you have failing tests.

4. **Implement to Pass Tests (Green Phase):**
   - Write the minimum amount of application code necessary to make the failing tests pass.
   - Run the test suite again and confirm that all tests now pass. This is the "Green" phase.

5. **Refactor (Optional but Recommended):**
    - With the safety of passing tests, refactor the implementation code and the test code to improve clarity, remove duplication, and enhance performance without changing the external behavior.
    - Rerun tests to ensure they still pass after refactoring.

6. **Verify Output Accuracy:** Ensure tests verify data output accuracy. Do not enforce coverage metrics or test internal implementation details. Focus on validating that the system produces correct data outputs.

7. **Document Deviations:** If implementation differs from tech stack:
   - **STOP** implementation
   - Update `tech-stack.md` with new design
   - Add dated note explaining the change
   - Resume implementation

8. **Lint and Format Code (REQUIRED):**
   - Run `uv run ruff check --fix` on all changed files to fix linting issues automatically.
   - Run `uv run ruff format` on all changed files to ensure consistent formatting.
   - Fix any remaining linting errors that cannot be auto-fixed.

9. **Notify User for Commit:**
   - Inform the user that the task is complete and ready for manual review and commit.
   - List all created/modified files.
   - Propose a clear, concise commit message.

10. **Update Plan:**
     - Read `plan.md`, find the line for the completed task, and update its status from `[~]` to `[x]`.
     - Write the updated content back to `plan.md`.

11. **Update Documentation (REQUIRED):**
     - After user approval, the `docs/` folder MUST be updated with any relevant changes.
     - This includes: feature documentation, technical specs, API docs, installation guides, or any other docs affected by the changes.

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

### Quality Gates

Before marking any task complete, verify:

- [ ] All tests pass
- [ ] Data output accuracy verified through tests
- [ ] Code follows project's code style guidelines
- [ ] All public functions/methods are documented
- [ ] Type safety is enforced
- [ ] No linting or static analysis errors (ruff check --fix and ruff format run on all changed files)
- [ ] Works correctly on mobile (if applicable)
- [ ] `docs/` folder updated with all relevant changes (features, technical specs, API docs, etc.)

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

## Definition of Done

A task is complete when:

1. All code implemented to specification
2. Tests verify data output accuracy and are passing
3. Code passes all configured linting (`uv run ruff check --fix`) and formatting (`uv run ruff format`) on all changed files
4. Implementation notes added to `plan.md`
5. User notified to perform manual commit
6. **Documentation Updated:** The `docs/` folder has been updated with all relevant changes (features, technical specs, API changes, etc.)

## Continuous Improvement

- Review workflow weekly
- Update based on pain points