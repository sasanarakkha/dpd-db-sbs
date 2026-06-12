# Spec: translate_core decomposition with a regression safety net

## GitHub issue
No issue assigned yet. Related context: the `#197` exporter/analysis feedback
loop (`kamma/threads/exporter_analysis_loop/`). Origin analysis:
`kamma/threads/exporter_analysis_loop/plan-history/meta_tooling_improvement_plan.md`.

## Overview
`exporter/analysis/translate_core.py` is 2,376 lines and ~78 functions doing
several distinct jobs (prompt building, AI-response parse/salvage, deterministic
scoring, missing-score retry orchestration, sentence chunking, option ranking,
report rendering, AI-selection merge). Its test file is 3,858 lines. The
`exporter/analysis/` directory is **local-only** — it is listed under
`no_sync_files` in `kamma/upstream_sync/registry.json` and does not exist
upstream — so restructuring it carries **no upstream-sync parity cost**.

The recurring bug family found across the `#197` loop (Findings 62, 63, 66, 71)
is not random: it is the deterministic scoring layer, the AI-merge, and the
tie-break ranking colliding because the file has no single explicit precedence
model. Splitting the file alone does **not** fix that — but it makes the
pipeline visible and is a precondition for any safe precedence cleanup.

This thread does the restructuring **behavior-preserving and safety-net first**.

## Goal
Make `exporter/analysis/translate_core.py` maintainable without changing its
output, by:
1. building an offline passage-level regression harness that freezes current
   behavior on the canonical passages (zero AI calls), then
2. splitting the monolith into themed modules behind a stable orchestrator,
   proven byte-identical by the harness.

A third, optional, separately-approved stage reduces the scoring/ranking
coupling that causes the recurring bug family.

## What it should do
1. **Phase 1 — regression harness (no behavior change).**
   - **First action:** copy the recorded AI artifacts out of `temp/tier_eval/`
     into the git-tracked fixtures dir — `temp/` is disposable by project rule
     and may be wiped between sessions.
   - Capture, as git-tracked fixtures, the recorded AI responses for the
     canonical passages (`TH215`, `MN41_p2`, `SN15.1_p2`, `AN3.33_p1`,
     `DHP211`). Post-fix sets cover only the first three; `AN3.33_p1` and
     `DHP211` exist only in pre-fix sets. If a recorded response sequence does
     not align with the current code's call pattern, run **one fresh recorded
     live evaluation** for that passage (user has approved the credit spend)
     rather than dropping it.
   - Add a `RecordedAIManager` test double that replays those responses in call
     order through the real `translate_sentence` / `study_passage` path with no
     network calls.
   - Commit **full goldens** (the complete `study.json` and `study.md` per
     passage — this is what makes the byte-identical claim real) plus distilled
     row extracts (`surface_word, occurrence, selected_key, grammar, meaning`)
     and targeted assertions encoding the facts the loop already fixed (see
     "Frozen correctness facts" below).
   - Provide a single-command golden-update mode for intentional future changes.
2. **Phase 2 — behavior-preserving module split.**
   - Extract themed modules from `translate_core.py`, leaving the public
     entrypoints and the orchestrator in place.
   - Re-point imports across the test file and all callers.
   - Prove output is unchanged via Phase 1's harness + full unit suite.
3. **Phase 3 — OPTIONAL, separate approval.**
   - Make the score → merge → rank precedence explicit and single-sourced.
   - Not started without its own approval after Phase 2 lands and is reviewed.

## Frozen correctness facts (Phase 1 must assert these)
Each cites the loop finding that established it:
- SN15.1 refrain `avijjānīvaraṇānaṃ`, `taṇhāsaṃyojanānaṃ`, `sandhāvataṃ`,
  `saṃsarataṃ` render **gen pl**, not dat pl (F71/F63).
- `tassā` and `tassa`, and `kāyassa` (dat-then-gen), keep **independent**
  per-occurrence selections — no "of her" fan-out (F66).
- No literal `[Deconstructed]` and no `*(AI analysis of deconstruction)*` in any
  Meaning cell; `etthā'ti` uses the component-join fallback (F67/F74).
- No shifted reformat meanings (`evaṃ`≠"disaster", `vo`≠"cemetery",
  `dīgharattaṃ`≠"experienced", `dukkhaṃ`≠"increased") (F69).
- No empty Meaning cells where a dictionary fallback exists (F62).
- No grammar-note parentheticals (`(accusative)`, `(nominative plural)`) in AI
  contextual meanings (F48).

## Affected area
- `exporter/analysis/translate_core.py` (split source — Phase 2)
- New `exporter/analysis/` modules (e.g. `prompts.py`, `ai_response.py`,
  `scoring.py`, `retry.py`, `ranking.py`, `rendering.py` — final names are the
  implementer's choice)
- Callers that import from `translate_core`: `exporter/analysis/study_passage.py`,
  `exporter/analysis/ai_pali_translate.py`, and any others found by grep
- `tests/exporter/analysis/test_translate_core.py` (import re-pointing)
- New `tests/exporter/analysis/test_passage_regression.py` and
  `tests/exporter/analysis/fixtures/passages/`
- `exporter/analysis/README.md` (document fixtures + module map)

## Assumptions & uncertainties
- The recorded `*_ai_debug.json` / `*_ai_raw.txt` artifacts under
  `temp/tier_eval/live_test_20260612/`, `live_test_post_fix/`, and the
  `final_eval_66_68_*` / `69_70` sets reflect current post-fix code for
  `TH215`, `MN41_p2`, `SN15.1_p2`. `AN3.33_p1` and `DHP211` artifacts exist
  only in pre-fix sets (`high`, `low`, `medium`, `deepseek_post_improvements`)
  and may not replay cleanly; remediation is a fresh recorded live run
  (approved).
- Phase 1 task 1 must verify each fixture's recorded response sequence aligns
  with the current code's call pattern (replay produces a complete report with
  no sequence desync) before freezing its golden.
- **Goldens must be frozen against a known commit.** The working tree currently
  carries uncommitted `#197` changes (`translate_core.py` +544 lines, plus
  test files, `analyzer.py`, `example_bolding.py`). Those changes must be
  committed (by the user) before goldens are generated, and the plan's
  `handoff.md` must record the commit hash the goldens correspond to.
- `exporter/analysis` being under `no_sync_files` means new modules inside it
  inherit the no-sync exclusion and do **not** each need a `dps_copies` registry
  entry. The executor must confirm this with the validation scripts, not assume.
- The split is purely a move + re-import in Phase 2; no logic edits. Any logic
  change discovered as "needed" is out of scope and becomes a Phase 3 item or a
  separate finding.

## Constraints
- **Behavior-preserving:** Phases 1-2 must not change generated `study.json` /
  `study.md` output. The harness is the proof.
- **Harness before refactor:** do not begin Phase 2 until Phase 1 is green.
- New `.py` files start with a one-sentence purpose description (project rule).
- Modern type hints, `Path` from pathlib, no `sys.path` hacks, no `.env`/`.ini`
  edits, no commits unless explicitly requested.
- Per changed Python file, run separately:
  `uv run ruff check --fix <file>`, `uv run ruff format <file>`,
  `uv run pyright <file>`,
  `uv run --with pyrefly pyrefly check --min-severity warn <file>`,
  `uv run pytest <specific test path> -v`.
- Never run bare `uv run pytest`; always pass specific test paths.
- Respect the Atomic Rename Protocol for any function/module moves: grep the old
  import paths repo-wide, update every caller, and prove zero stale references.

## How we'll know it's done
- Phase 1: `tests/exporter/analysis/test_passage_regression.py` runs with zero
  network calls, asserts the full `study.json`/`study.md` goldens and every
  frozen correctness fact, and passes; goldens are committed with their source
  commit hash recorded; refresh procedure is documented.
- Phase 2: `translate_core.py` is reduced to an orchestrator plus stable public
  API; logic lives in themed modules; the full analysis unit suite and the
  passage-regression harness pass unchanged; grep proves no stale imports.
- Phase 3 is explicitly out of scope for completion of this thread unless the
  user approves it.

## What's not included
- No change to AI prompts' wording, scoring heuristics, ranking order, or report
  formatting in Phases 1-2.
- No model/provider-routing change (that is the deferred Finding 45 decision).
- No new analyzer features.
- No edits to upstream-synced files.
