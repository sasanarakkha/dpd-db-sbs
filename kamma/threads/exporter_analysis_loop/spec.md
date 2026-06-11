# Spec: exporter_analysis_feedback_loop

## GitHub issue
#197

## Overview
Create an ongoing Kamma feedback-loop thread for fixing issues in the Pāḷi analyzer scripts under `exporter/analysis/`.

This thread is not for one predefined bug. It is a standing workflow: in each new session, the user reports one or more issues related to `exporter/analysis/`; the model analyzes the reported issue scope, proposes a focused plan, stops for explicit approval, then implements only after approval.

The loop continues across sessions until the user says all issues are resolved.

## What it should do
1. Treat each approved issue or issue set as a focused, explicitly scoped unit of work.
2. At the start of a new session, read:
   - `kamma/threads/exporter_analysis_loop/spec.md`
   - `kamma/threads/exporter_analysis_loop/plan.md`
   - `kamma/threads/exporter_analysis_loop/handoff.md` if it exists
   - relevant files under `exporter/analysis/`
   - relevant tests under `tests/exporter/analysis/`
3. When the user reports an issue:
   - reproduce or inspect the issue where practical
   - identify affected files
   - write or describe a focused implementation plan
   - hard stop before implementation
   - wait for explicit user approval
4. If the user reports multiple unrelated issues:
   - group related issues where practical
   - state which issue(s) are in scope for the current approved plan
   - defer only issues that are ambiguous, unapproved, or too broad for the approved scope
5. After approval:
   - follow strict TDD where practical: failing test first, then implementation, then refactor
   - keep the change scoped to the reported issue
   - run targeted lint and tests
   - run any relevant script-level smoke checks
6. After the issue is solved:
   - update `plan.md` with the issue summary, affected files, validation, and outcome
   - update `handoff.md` with only necessary history:
     - what was done
     - tests run
     - remaining risks or follow-up
     - errors, mistakes, or repeated mistakes
   - summarize any remaining reported issues or follow-up choices
7. Do not continue into unapproved issues or broaden the approved scope without explicit user approval.

## Affected area
Primary scope:
- `exporter/analysis/README.md`
- `exporter/analysis/ai_batch_translate.py`
- `exporter/analysis/ai_pali_translate.py`
- `exporter/analysis/analyzer.py`
- `exporter/analysis/book_to_verses.py`
- `exporter/analysis/column_options.py`
- `exporter/analysis/example_bolding.py`
- `exporter/analysis/examples.md`
- `exporter/analysis/export_words_csv.py`
- `exporter/analysis/passage_by_code.py`
- `exporter/analysis/passage_extraction.py`
- `exporter/analysis/paths.py`
- `exporter/analysis/study_passage.py`
- `exporter/analysis/translate_core.py`

Likely related tests:
- `tests/exporter/analysis/`

Related helper files may be touched only when required by the issue:
- `tools/passage_by_code.py`
- `scripts/change_in_db/preview_dhp_changes.py`
- `scripts/change_in_db/fill_dhp_examples.py`
- MCP wrapper files if the issue crosses into MCP integration

## Assumptions & uncertainties
- The user wants a new active Kamma thread, not to reopen the archived `20260527_universal_passage_analysis` thread.
- "Pali analyzer scripts" means the standalone analysis pipeline now living in `exporter/analysis/`, not the older MCP folder.
- "Hard start before approval" is assumed to mean "hard stop before implementation until the plan is approved."
- Each approved issue or issue set should be solved completely before expanding scope.
- When several unrelated issues arrive together, the scoped plan should make clear which issues are included now and which are deferred.
- The handoff should be concise, not a full chronological transcript.
- The model should not append speculative future issues unless the user reports them.

## Constraints
- Do not implement before explicit approval of the per-issue plan.
- Use `uv run pytest ...` for related tests.
- After edits, run `uv run ruff check <changed files>` and related tests before reporting completion.
- Follow project conventions:
  - modern type hints
  - `Path` from `pathlib`
  - no `sys.path` hacks
  - no `.env` or `.ini` edits
  - no commits unless explicitly requested
- Any commit prepared for this thread must reference issue `#197` in the commit message.
- Keep Kamma history useful but concise.
- `handoff.md` must include a dedicated section for errors, issues, and repeated mistakes.

## How we'll know it's done
The loop thread is ready when:
- `spec.md` clearly defines the ongoing feedback workflow.
- `plan.md` gives future agents exact startup behavior, approval gates, issue workflow, testing requirements, and handoff rules.
- The plan prevents implementation before approval.
- The plan instructs future agents to keep each approved issue or issue set scoped and to avoid unapproved follow-on work.
- The thread directory exists under `kamma/threads/exporter_analysis_loop/`.
- Future sessions can continue the loop using only `spec.md`, `plan.md`, and `handoff.md`.

## What's not included
- No immediate code changes to `exporter/analysis/`.
- No predefined list of bugs to solve.
- No bulk refactor.
- No migration outside `exporter/analysis/` unless a reported issue requires it.
- No commits.
