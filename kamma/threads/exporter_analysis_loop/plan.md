# Plan: exporter_analysis_feedback_loop

## Architecture Decisions
- **Standing workflow thread, not a feature implementation**: this thread defines how future sessions handle `exporter/analysis/` feedback. It does not change analyzer code during setup.
- **No task checkboxes in the loop**: this is an ongoing feedback loop, so reusable instructions must stay as plain bullets. Do not use markdown task-list markers for recurring loop work.
- **Focused approved scope**: future agents must keep work limited to the issue(s) explicitly included in the approved plan. If the user reports several unrelated issues, group related issues where practical and state which ones are in scope before implementation.
- **Approval gate before implementation**: each issue requires analysis and a focused implementation plan first. The agent must stop before code edits until the user explicitly approves that per-issue plan.
- **Concise handoff history**: `handoff.md` should preserve only what future sessions need: issue summary, files changed, tests run, remaining risk, and errors/mistakes. It should not become a full transcript.
- **Issue history lives in handoff only**: completed issue work is recorded in `handoff.md`. Keep this plan stable and do not append per-issue history here.
- **Use existing project verification rules**: each issue should use focused tests under `tests/exporter/analysis/` where practical, plus `uv run ruff check <changed files>` and relevant smoke commands.

## Setup History
- Thread directory exists: `kamma/threads/exporter_analysis_loop/`.
- `spec.md` describes the ongoing `exporter/analysis/` feedback-loop scope, issue routing rules, approval gate, testing expectations, and handoff expectations.
- `plan.md` is this reusable loop guide, not a finite implementation task list.
- `handoff.md` exists with current status, completed issues, pending/suggested next issues, important context, and errors/issues/repeated mistakes.

## Session Startup Rules
- At the start of every future session, read:
  - `kamma/threads/exporter_analysis_loop/spec.md`
  - `kamma/threads/exporter_analysis_loop/plan.md`
  - `kamma/threads/exporter_analysis_loop/handoff.md`
  - relevant files under `exporter/analysis/`
  - relevant tests under `tests/exporter/analysis/`
- Before proposing a fix, cite the relevant current code paths and any handoff constraints.
- If no concrete issue is reported, ask the user for an `exporter/analysis/` issue or issue set and stop.
- If multiple unrelated issues are reported, state which reported issues are included in the current approved scope and which are being deferred.
- The current session plan must name the issue(s) in scope and list unrelated reported issues as deferred unless the user explicitly approves them for the same scope.

## Per-Issue Planning Gate
- Inspect the affected `exporter/analysis/` files and any related tests before stating behavior or proposing changes.
- Avoid claims about script behavior unless backed by source reading.
- Reproduce the issue where practical.
- If reproduction is not practical, explain why before planning.
- Draft a focused issue plan with:
  - issue summary
  - suspected cause
  - files to change
  - test-first strategy
  - verification commands
  - out-of-scope items
- Hard stop for explicit user approval before code edits.
- Do not modify source or test files before the user approves the issue plan.

## Per-Issue Implementation Rules
- Start implementation only after explicit approval of the focused per-issue plan.
- Add or update a focused failing test first where practical.
- Run the relevant `uv run pytest ...` command and confirm the test fails for the expected reason before implementation.
- Implement the minimal fix for the approved issue.
- Keep changed files limited to the approved issue scope, unless a newly discovered dependency is explained in the session notes.
- Run targeted checks:
  - `uv run ruff check <changed files>`
  - `uv run pytest <related test paths>`
  - any relevant smoke command, for example `uv run python exporter/analysis/<script>.py ...`
- If callback, CLI, import, or logging paths change, do a runtime sweep with a focused `rg` search or import/smoke command that would catch stale names, import errors, or missing runtime references.
- Document exact remaining blockers if a command fails after reasonable fix attempts.

## Per-Issue Closure
- Add a concise completed issue entry to `handoff.md`.
- Include in the handoff entry:
  - short issue title
  - reported symptom
  - approved approach
  - files changed
  - validation commands
  - outcome
  - handoff note
- Update `handoff.md` with only necessary next-session context:
  - what was done
  - tests run
  - remaining risks or follow-up
  - deferred issues, if any
  - errors / issues / repeated mistakes
- Keep `handoff.md` concise and preserve its dedicated errors/mistakes section.
- Do not append issue history, issue queues, task markers, or session results to this plan.
- Stop after the approved issue scope is complete unless the user explicitly approves expanding the scope.
- Do not begin another unrelated fix unless the user explicitly approves it.
- When preparing a manual commit for work from this thread, include issue `#197` in the commit message.

## Final Loop Completion
- Only use this section when the user says all `exporter/analysis/` issues are resolved.
- Run final targeted validation across the affected analysis area.
- Use relevant accumulated `uv run pytest tests/exporter/analysis/...` commands and `uv run ruff check` for touched files.
- Prepare the thread for review/finalization.
- Ensure `handoff.md` summarizes completed issues, validations, risks, and errors/mistakes clearly enough for `/kamma:3-review`.
- Tell the user to run `/kamma:3-review` for `kamma/threads/exporter_analysis_loop`.
