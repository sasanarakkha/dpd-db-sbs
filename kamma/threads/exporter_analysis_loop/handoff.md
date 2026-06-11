# Handoff: exporter_analysis_loop

## Current Status
- Thread: ongoing `exporter/analysis/` feedback loop for GitHub issue `#197`.
- Purpose: handle one focused analyzer issue or approved issue set per session.
- Stable workflow lives in `plan.md`; keep per-issue history out of `plan.md`.
- All approved implementation work through Finding 60 is complete.
- Finding 61 live evidence collection is complete. It is mostly clean, but
  DeepSeek `TH215` still selects nominative duration for
  `paṇṇavīsativassāni` and component `vassāni`.
- 2026-06-12: manual analysis of the Finding 61 artifacts found three
  pipeline defects (not model limitations) and produced a proposed queue,
  Findings 62-65, in
  `kamma/threads/exporter_analysis_loop/plan-history/findings_62_65_plans.md`.
  It is NOT approved and NOT implemented.
- Review is pending behind two user decisions: the Findings 62-65 queue and
  the DeepSeek `TH215` duration residual.

## Handoff Hygiene Rule
- Keep this handoff tight. It is active session memory, not a full transcript.
- Once a proposed finding or issue is implemented, replace proposal details
  with a short historical summary: problem, change, files, validation, outcome,
  remaining risk, and artifact/history pointers.
- Preserve detailed evidence in `plan-history/` files or `temp/tier_eval/`
  artifacts when useful. Do not keep long completed plans, raw metrics tables,
  or analysis chains in the active handoff unless they are needed for the next
  decision.
- Future sessions should only expand this handoff for active decisions,
  unresolved risks, or concise completed-work summaries.

## Implementation Validation Rule
Every future implementation started from this handoff must be fully validated
before it is reported complete.

For Python changes, run each command separately on the exact changed file(s):
- `uv run ruff check --fix <file>`
- `uv run ruff format <file>`
- `uv run pyright <file>`
- `uv run --with pyrefly pyrefly check --min-severity warn <file>`
- a targeted `uv run pytest <specific test path> -v`

Also required:
- Add or update focused tests first where practical and confirm the red phase.
- Run relevant smoke/live commands when behavior cannot be proven by unit tests.
- Never run bare `uv run pytest`; always pass a specific test path.
- If a validation command fails after reasonable fixes, document the exact
  failure and remaining risk in this handoff before stopping.
- For non-Python/doc-only handoff updates, verify with focused text checks and
  `git status --short`; do not claim Python validation was run.

## Next Decision
- Approve, trim, or reject the proposed Findings 62-65 queue
  (`plan-history/findings_62_65_plans.md`). Summary:
  - Finding 62: empty AI `contextual_meaning`/`selected_pos` strings overwrite
    dictionary meanings → blank Meaning cells (`merge_ai_selections` and the
    inline field copy in `_apply_deterministic_scores_to_map`).
  - Finding 63: db-example promotion flattens the AI's correct intra-headword
    grammar choice (four "dat pl" rows in both SN15.1 reports should be gen
    pl; DeepSeek had selected gen pl before being stomped).
  - Finding 64: component homonym tie-break prefers `ind`, rendering `santi`
    inside `cetosanti` ("peace of mind") as "own; personal; self-" on Low.
  - Finding 65: deferred design question (all-zero retry groups count as
    resolved); recommendation is to implement 62-64 first.
- Decide whether DeepSeek `TH215` nominative duration is acceptable:
  - Accept as a model limitation and proceed to manual confirmation/review.
  - Or queue a focused follow-up for duration-grammar selection.
- Do not make model-default changes from this thread. User decision on
  2026-06-11: keep `Gemini 3.5 Flash (Low)` as default and keep
  `deepseek/deepseek-v4-flash` as an occasional second model.

## Recent Completed Queue: Findings 56-61
User approved implementing Findings 56-61 as one issue set for `#197`.

Implemented in `exporter/analysis/translate_core.py` and
`tests/exporter/analysis/test_translate_core.py`:
- Finding 56: reformat merge now lets first-pass salvaged scores win conflicts;
  reformat scores still fill keys absent from salvage.
- Finding 57: reformat key overview now includes `key (grammar)` context, and
  the reformat prompt includes the no-grammar-parenthetical instruction.
- Finding 58: main prompt now tells models not to enumerate score-0 options;
  only the selected key and plausible 1-9 alternatives should be listed.
- Finding 59: sanitizer strips abbreviated grammar parentheticals such as
  `(abl. sg.)`, `(masc. gen. sg.)`, and interrogative-pronoun grammar notes
  while preserving useful notes such as `(lit. accumulation)`.
- Finding 60: main prompt explains same-id grammar variants, and common Pali
  rules include accusative duration for counted time-spans such as `vassāni`.
- Finding 61: live re-evaluation ran the same three targets on Low and
  DeepSeek, preserving artifacts under `temp/tier_eval/final_eval_56_61_low/`
  and `temp/tier_eval/final_eval_56_61_deepseek/`.

Validation summary:
- Red phase confirmed for the new/updated tests.
- Exact-file gates passed for `exporter/analysis/translate_core.py` and
  `tests/exporter/analysis/test_translate_core.py`: `ruff check --fix`,
  `ruff format`, `pyright`, `pyrefly`.
- `uv run pytest tests/exporter/analysis/test_translate_core.py -v` passed:
  99 passed, with one upstream `aksharamukha` deprecation warning.

Live evaluation summary:
- All six runs completed on first attempt; no repeat was needed.
- All six had zero hard failures, zero missing-score groups after retry, and
  zero bare-number `final_scores` values.
- No generated grammar-label parentheticals were found in the six `_study.md`
  reports.
- `MN41_p2` stock phrase is clean on both models: genitive `kāyassa`,
  ablative `bhedā`, prepositional `paraṃ` = "after", ablative `maraṇā`.
- `upapajjantī'ti` selected `upapajjanti + iti` on both models.
- Low `TH215` is mostly clean: accusative `paṇṇavīsativassāni` and component
  `vassāni`, `api` = "even", finger-snap nuance preserved. Correction
  2026-06-12: its component `santi` inside `cetosanti` is the wrong homonym
  ("own; personal; self-" instead of "peace") — see Finding 64.
- DeepSeek `TH215` is not a clean pass: it keeps nominative
  `paṇṇavīsativassāni` and component `vassāni`, though `api` = "even" and the
  finger-snap nuance are preserved.

## Prior Completed Work Summary
- Passage access and analyzer output: added `UD`/`ITI` support, reduced noisy
  synthetic particle-expanded candidates, improved example bolding, clipped
  word-card examples, shortened passage previews, and added analyzer result
  typing/coverage.
- AI response recovery: hardened wrong-schema responses, compact maps, nested
  `disambiguation`, flat retry maps, score salvage, debug snapshots, and
  failed debug artifact writing.
- Provider behavior: fixed forced provider/model routing, added paired
  `study_passage.py --provider/--model`, removed `gemini_cli`, raised
  timeouts, added GPT-OSS as Antigravity fallback, isolated `agy` scratch cwd,
  classified timeout/auth stdout correctly, and moved rate limiting to the
  actual attempted provider/model.
- Prompt and retry size: compacted context JSON, added sentence-level first-pass
  chunking, deduplicated missing-score groups, bounded retry batches, trimmed
  retry context, added one supplemental retry pass, tolerated one failed
  first-pass chunk, and hardened prompts against tool-planning/idling responses.
- Quality fixes: retry-recovered score-10 selections now request contextual
  meanings, common Pali disambiguation rules were added, quote-final `'ti`
  deconstruction gets deterministic promotion when safe, bare numeric `scores`
  values are normalized, and grammar-variant/reformat handling is improved.
- Maintainability: extracted focused helpers from `translate_core.py`, added
  constants and return typing, and documented the one-selection-per-surface-word
  limitation.

## Key Findings For Future Work
- Low stayed default after manual comparison: Low won `TH215`, `DHP211`, and
  `SN15.1_p2`; DeepSeek won `MN41_p2`; `AN3.33_p1` was roughly even.
- DeepSeek's characteristic bad failures were wrong-homonym picks such as
  `agga` = "hall", `kaṭā` = "winning dice", `chavā` = "worthless",
  `apāya` = "downfall", and `api` = "just; only". Treat these as high-risk for
  a dictionary tool.
- Low's largest previous visible defect was pipeline-caused: retry-recovered
  score-10 selections lacked `contextual_meaning` and fell back to raw
  dictionary strings. Finding 51 addressed this.
- The `app'ekacce` `(singular)/(plural)` row was dictionary fallback text, not
  AI grammar-note pollution. Do not widen the grammar-note sanitizer to general
  dictionary text without a new approved plan.
- The AN3.33 `bhagavā` nominative-for-vocative issue is structurally blocked by
  one selection per surface word when the same chunk also has a real nominative
  `bhagavā`. Only per-occurrence keys could fix it.
- Hybrid provider routing was considered and rejected for now: complexity
  outweighed benefit after the 2026-06-11 evidence.

## Wrong-Schema Shapes
Already handled or partly handled:
- flat `{surface_word: option_key}` maps;
- selection lists under `disambiguation`, `sentence_analysis`, or
  `selected_meanings`;
- list items using `selected_key`, `selected_lemma_key`, `key`, or unique
  `selected_id`;
- word-to-gloss dict maps with exact unambiguous `lemma` matches.

Worth future analysis only with a new focused plan:
- `sentence_disambiguation`;
- top-level `selected_keys`;
- nested `sentence_analysis.words`;
- `words[].analysis`;
- dict-valued `disambiguation`;
- mixed payloads containing a recoverable map plus explanatory fields.

Do not widen salvage blindly. Accept only shapes whose option keys or exact
unambiguous lemma/id matches can be verified against current analyzer output.

## History Index
Detailed completed queues have been moved out of the active handoff so future
sessions can load only the level of history they need.

- Findings 11-14:
  `kamma/threads/exporter_analysis_loop/plan-history/findings_11_14_plans.md`
- Findings 15-18:
  `kamma/threads/exporter_analysis_loop/plan-history/findings_15_18_plans.md`
- Findings 19-23:
  `kamma/threads/exporter_analysis_loop/plan-history/findings_19_23_plans.md`
- Findings 24-27:
  `kamma/threads/exporter_analysis_loop/plan-history/findings_24_27_plans.md`
- Findings 28-30:
  `kamma/threads/exporter_analysis_loop/plan-history/findings_28_30_plans.md`
- Findings 31-38:
  `kamma/threads/exporter_analysis_loop/plan-history/findings_31_38.md`
- Findings 40-44:
  `kamma/threads/exporter_analysis_loop/plan-history/findings_40_44_plans.md`
- Finding 45 higher-model summary:
  `kamma/threads/exporter_analysis_loop/plan-history/finding_45_higher_model_summary.md`
- Findings 45-50:
  `kamma/threads/exporter_analysis_loop/plan-history/findings_45_50_plans.md`
- Findings 51-55:
  `kamma/threads/exporter_analysis_loop/plan-history/findings_51_55_plans.md`
- Findings 62-65 (PROPOSED, awaiting approval):
  `kamma/threads/exporter_analysis_loop/plan-history/findings_62_65_plans.md`

Important historical note: Finding 38 was merged into Finding 35 and must not
be executed separately.

## Artifact Locations
- Finding 55 artifacts:
  `temp/tier_eval/final_eval_low/` and
  `temp/tier_eval/final_eval_deepseek/`.
- Finding 61 artifacts:
  `temp/tier_eval/final_eval_56_61_low/` and
  `temp/tier_eval/final_eval_56_61_deepseek/`.
- Current report outputs: `exporter/analysis/reports/*_study.md`.
- Raw AI logs: `exporter/analysis/reports/*_ai_raw.txt`.
- Debug JSON: `exporter/analysis/output/*_ai_debug.json`.
- Study JSON: `exporter/analysis/output/*_study.json`.
- Current README context: `exporter/analysis/README.md`.

`temp/tier_eval/` is intentionally preserved until the user releases it.

## Future Session Guardrails
- At startup, read `spec.md`, `plan.md`, this handoff, relevant
  `exporter/analysis/` source, and related `tests/exporter/analysis/` files.
- If no concrete issue is reported, ask the user for one `exporter/analysis/`
  issue or approved issue set and stop.
- Before code edits, inspect/reproduce where practical, propose a focused plan,
  and hard stop for explicit user approval.
- Use TDD where practical: failing test first, minimal implementation, focused
  validation.
- Keep changed files limited to the approved issue scope.
- After implementing, update this handoff as a concise completed summary, not a
  full transcript or repeated proposal text.
- If callback, CLI, import, or logging paths change, do a runtime sweep with a
  focused `rg` search or import/smoke command.
- For live AI checks, use `study_passage.py --debug` and inspect both raw logs
  and debug JSON before claiming live proof.
- Do not describe a live run as a pure Antigravity success unless raw/debug
  statuses show that provider/model path actually ran.
- If `uv run ...` hits `/Users/deva/.cache/uv` permission problems, retry with
  `UV_CACHE_DIR=/private/tmp/uv-cache`.
- When preparing a commit message for this thread, include `#197`.
- Do not commit autonomously unless the user explicitly asks.

## Errors, Issues, And Repeated Mistakes
- Use POSIX-compatible shell under zsh; do not use Fish-style `and` / `or`.
- Do not use root-level scratch files. Temporary probes/logs belong under
  `temp/` and should be deleted when no longer needed. `temp/tier_eval/` is the
  explicit exception until manual review is complete.
- Do not use plain `python` or inline `python -c`; use project-approved
  `uv run python` commands or a temporary script under `temp/`.
- Current analyzer token shape is top-level `[option]`; component groups are
  nested. Do not copy old synthetic `analysis` nesting blindly.
- When narrowing option keys, use explicit type checks so `pyright` sees `str`.
- Preserve clean retry prompt formatting; accidental tabs before retry context
  were introduced and fixed in prior sessions.
- `exporter/analysis/README.md` previously said to use `agy --list-models`;
  local `agy` 1.0.7 reports that flag as unsupported and uses `agy models`
  instead.
- Pyright may require internal helper annotations after adding TypedDict return
  types.
- Pyrefly may reject unnecessary casts or `str()` calls that Pyright tolerates.
- `translate_core.py` may need local type-only `cast()` boundaries where
  `analyze_sentence()` returns `list[AnalysisResult]` but helper APIs accept
  `list[dict[str, Any]]`.
- In zsh, do not use `path` as a loop variable; it shadows the tied `$PATH`
  array. Use names like `src` instead.

## Review Readiness
- Implementation queues through Finding 60 are complete.
- Finding 61 evidence collection is complete, but DeepSeek `TH215` remains a
  not-clean pass on duration grammar.
- Remaining before review: user decision on the proposed Findings 62-65
  queue; user decision on accepting the DeepSeek `TH215` residual or queuing a
  focused follow-up; manual confirmation/testing; release `temp/tier_eval/`
  when no longer needed.
- After user confirmation, run:
  `/kamma:3-review kamma/threads/exporter_analysis_loop`
