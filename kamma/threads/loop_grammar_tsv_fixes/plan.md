> **Thread type:** Loop (standing thread)

# Plan: Grammar TSV fixes (protocol)

## Architecture Decisions
- Find-and-replace only, never hand edits. The dry-run list guards against false positives; the diff check proves nothing extra changed.
- One explicit user request per cycle, so approvals and diffs stay small and reversible.
- The replace tool is a throwaway script in `temp/`, deleted after the cycle; pattern and scope are kept in the cycle record.
- Baseline captured once in `baseline.md`; cycles compare against it and do no other preliminary work.

## Per-Cycle Protocol
1. **Report:** Take the correction the user explicitly asked for. Do not search for other issues.
2. **Analyze:** Exact pattern, file/column scope, dry-run match list with context, false-positive risks.
3. **Approval (HARD STOP):** Wait for explicit approval of the match list before any edit.
4. **Implement:** Apply the approved matches only.
5. **Validate:** Per spec Validation Standards.
6. **Record:** Write `cycles/NNNN_slug.md` (pattern, scope, match count, validation results).
7. **Handoff:** Update `handoff.md`.
8. **Learn:** Curate `learnings.md`.

## Read Contract
A cycle reads only `spec.md`, `plan.md`, `handoff.md`, `learnings.md` (and `baseline.md` for validation numbers). Cycle records are read only on demand.

## Pre-Commit Cross-Check (final step, before the commit)
When the user says all corrections are done and the thread is ready for the final commit, do NOT go straight to commit. First remind the user:
> "Before committing: switch to a different model in a NEW session and have it double-check all uncommitted changes for anything overlooked."

Brief to give the reviewing model (read-only; no edits without approval):
- Scope: `git diff` of `shared_data/pali_class/grammar/*.tsv` (all cycles 0001-0004+; skip `samasa.tsv` unless this thread touched it), plus `cycles/*.md` and `learnings.md` for the conventions applied.
- Check for: remaining sg/pl, case, person and gender mismatches between `gramma` / `eng` / `native`; part-count mismatches; inconsistent conventions (вещь/предмет, ты/вы, case prepositions); typos, Latin letters in Russian text, stray whitespace; meaning errors against `dpd.db`; accidental changes outside approved cells (row/column counts vs `baseline.md`).
- Output: a findings list with file:line, current value, proposed fix, confidence. The user decides; approved items go into the next cycle here.
After the cross-check findings are resolved (or declined), draft the commit message(s) and hand off to the user to commit.
