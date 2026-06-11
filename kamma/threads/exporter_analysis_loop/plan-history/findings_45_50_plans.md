# Approved Implementation Queue: Findings 45–50

Status: APPROVED by the user on 2026-06-11. Findings 45-50 complete;
manual model-default decision remains pending.

These findings come from the higher-model analysis of the Finding 44 tier
evaluation (artifacts in `temp/tier_eval/`, metrics table in
`findings_40_44_plans.md`). The user approved all six on 2026-06-11.

## Execution order (MANDATORY)

Original order: **46 → 47 → 48 → 49 → 50 → 45**

Remaining order after Finding 50: complete.

Finding 45 (DeepSeek evaluation) ran after all approved improvements in
Findings 46-50. By explicit user order override, DeepSeek ran first, then the
five fresh `Gemini 3.5 Flash (Low)` targets ran on the same post-improvement
pipeline. The old `temp/tier_eval/low/` baseline remains useful historical
context only; the final comparison uses `low_post_improvements/` and
`deepseek_post_improvements/`.

One finding per session (loop rule in `plan.md`). After each finding, update
`handoff.md` per the Per-Issue Closure rules.

## Shared constraints (same as Findings 40–44)

- Behavior fixes use TDD where practical: write the failing test first, run
  it, confirm it fails for the expected reason, then implement.
- Quality gates per changed Python file:
  1. `uv run ruff check --fix <files>`
  2. `uv run ruff format <files>`
  3. `uv run pyright <files>`
  4. `uv run --with pyrefly pyrefly check --min-severity warn <files>`
  5. `uv run pytest <specific test files> -v`
- Never run bare `uv run pytest`; always pass the specific test file path.
- Modern type hints, `Path` from pathlib, no `sys.path` hacks.
- POSIX-compatible shell commands under zsh; temp probes under `temp/` only.
- `temp/tier_eval/` retention exception continues: it contains the historical
  baseline and will also hold the post-improvement Low and DeepSeek
  comparison artifacts for Finding 45. Do not delete it until the user
  releases it.
- Line-number anchors below were verified on 2026-06-11. Re-read current
  source before editing; do not trust stale line numbers, especially after
  earlier findings in this queue land.

---

## Finding 46 — per-chunk failure tolerance with one retry

Status: COMPLETE 2026-06-11. Impact: high (a single failed chunk currently discards all
completed chunk work and kills the whole run).

### Problem (evidence from tier eval, 2026-06-11)
- Medium MN41 p2 attempt 1: chunks 0–1 completed (~370s of paid AI calls,
  scores in hand), then a chunk timed out and the run died with
  `ValueError: AI Request Failed ...`, discarding everything
  (`temp/tier_eval/medium/MN41_p2_run.log`).
- High SN15.1 p2: chunks 0–2 completed, chunk 3 returned empty → entire run
  discarded (`temp/tier_eval/high/SN15.1_p2_run.log`).
- Timeouts are nondeterministic: High MN41 p2 failed on attempt 1 and fully
  succeeded on attempt 2 → a single in-run retry has real rescue value.
- Retry-sized prompts demonstrably succeed (8–30s) on the same models whose
  large first-pass chunk prompts time out, so the existing missing-score
  retry machinery can recover words from a skipped chunk.

### Exact current anchors (verified 2026-06-11)
- Failure raise: `exporter/analysis/translate_core.py:1040`
  (`raise ValueError(f"AI Request Failed: {response.status_message}")`
  inside `_request_first_pass` when `response.content` is empty).
- Multi-chunk loop: `translate_sentence`, lines 1148–1166 (loop body
  1150–1163); single-chunk branch lines 1134–1146.
- Downstream recovery that covers unscored words: lines 1174+
  (`_normalize_ai_response`, `_apply_deterministic_scores_to_map`, then the
  missing-score retry passes).

### Files to change
- `exporter/analysis/translate_core.py`
- `tests/exporter/analysis/test_translate_core.py`

### Implementation
1. Add a module-level constant `CHUNK_FIRST_PASS_ATTEMPTS = 2` near the
   other constants (lines 16–20).
2. In the multi-chunk loop only, wrap the `_request_first_pass` call:
   - attempt up to `CHUNK_FIRST_PASS_ATTEMPTS` times, catching `ValueError`;
   - on a retry attempt, reuse a fresh `chunk_debug` dict or record both
     attempts under the same chunk entry — keep it simple: record the final
     attempt's debug plus `debug["chunk_error_attempt_1"] = str(error)` for
     the failed first attempt;
   - if all attempts fail, append a chunk debug entry containing at least
     `chunk_sentence` and `chunk_error` (string), skip
     `chunk_datas.append(...)` for that chunk, and continue the loop;
   - count failed chunks; if EVERY chunk failed, re-raise the last
     `ValueError` (preserves current all-failed behavior).
3. Do NOT change the single-chunk branch: a single-chunk run that fails must
   still raise, exactly as today.
4. `_merge_chunk_ai_data` already merges whatever chunk_datas exist; words
   from skipped chunks become missing-score groups handled by the existing
   deterministic + retry passes. Do not change retry logic.
5. If `verbose`, print an amber warning per skipped chunk
   (`pr.amber(...)`) naming the chunk and the error.

### Tests — write FIRST, confirm red
Model stubs on the existing chunked-flow tests in
`tests/exporter/analysis/test_translate_core.py` (stub AIManager returning
empty `content` to trigger the line-1040 raise):
1. `test_translate_sentence_tolerates_single_chunk_failure` — 1 of 2+ chunks
   fails on both attempts → no exception; surviving chunk's scores present;
   chunk debug entry has `chunk_error`; failed chunk's words flow into the
   missing-score retry path.
2. `test_translate_sentence_retries_failed_chunk_once` — chunk fails on the
   first attempt, succeeds on the second → no `chunk_error`, scores merged,
   first-pass request count for that chunk is exactly 2.
3. `test_translate_sentence_raises_when_all_chunks_fail` — every chunk fails
   → `ValueError` raised.
4. `test_single_chunk_failure_still_raises` — single-chunk path with empty
   responses → `ValueError` raised (current behavior preserved).

### Verification commands
```
uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pytest tests/exporter/analysis/test_translate_core.py -v
```

### Out of scope
- Cross-provider/model fallback changes (`tools/ai_manager.py`).
- Chunk sizing changes.
- Live AI probes.

### Implementation outcome - 2026-06-11
- Added `CHUNK_FIRST_PASS_ATTEMPTS = 2` and changed only the multi-chunk
  first-pass loop in `translate_sentence`.
- A failed chunk is retried once. If the retry also fails, its debug entry
  records `chunk_sentence`, `chunk_error_attempt_1`, and `chunk_error`; the
  chunk is skipped and downstream missing-score retry can fill its words.
- If all chunks fail, the last `ValueError` is re-raised. The single-chunk
  branch still raises immediately on an empty first-pass response.
- Added tests for skipped chunk recovery, one retry success, all chunks
  failing, and preserved single-chunk failure behavior.
- Validation passed:
  `uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pytest tests/exporter/analysis/test_translate_core.py -v`
  (70 passed, 1 third-party deprecation warning).

---

## Finding 47 — anti-agentic prompt hardening

Status: COMPLETE 2026-06-11. Impact: medium (directly targets the observed higher-tier
failure mode; harmless for Low).

### Problem (evidence)
Medium MN41 p2 chunk timeout returned:
`"No tools are being called. I will wait for the background search task to
finish and report its results."`
(`temp/tier_eval/medium/MN41_p2_run.log`). The Antigravity agent plans tool
use and idles out the 150s window instead of answering. The wrapper-level
instruction in `tools/ai_antigravity_cli.py::_build_prompt` ("Do not inspect
local files or use tools unless the user content explicitly requires it") is
demonstrably insufficient at higher reasoning tiers.

### Exact current anchors (verified 2026-06-11)
- `build_system_prompt` preamble: `exporter/analysis/translate_core.py:1299`
  (the `IMPORTANT: Your response MUST be a valid JSON object only...` line).
- Reformat call `prompt_sys`: line 966
  (`"Return only a valid JSON object. No prose. No markdown."`).
- Retry call `prompt_sys`: line 750
  (`"Return only JSON with a flat `scores` object."`).
- Translation-only follow-up call: inside `_handle_compact_map_response`
  (def at line 859) — locate its `ai_manager.request(...)` and its
  `prompt_sys` argument by reading the function.

### Files to change
- `exporter/analysis/translate_core.py`
- `tests/exporter/analysis/test_translate_core.py`

### Implementation
1. Add a module-level constant:
   ```python
   NO_TOOLS_INSTRUCTION = (
       "Do not use tools, do not plan tasks, and do not wait for anything. "
       "Produce the complete JSON directly in this single response."
   )
   ```
2. Append it to:
   - the `build_system_prompt` preamble line (after the existing
     "Start your response with { and end with }." sentence);
   - the reformat `prompt_sys` (line 966);
   - the retry `prompt_sys` (line 750);
   - the translation-only follow-up `prompt_sys` in
     `_handle_compact_map_response`.
3. No other prompt text changes. Keep all debug key names unchanged.

### Tests — write FIRST, confirm red
1. `test_system_prompt_contains_no_tools_instruction` —
   `build_system_prompt(...)` output contains `NO_TOOLS_INSTRUCTION`.
2. `test_reformat_request_sys_prompt_contains_no_tools_instruction` — stub
   AIManager capturing `prompt_sys` kwargs through a reformat flow.
3. `test_retry_request_sys_prompt_contains_no_tools_instruction` — same via
   a missing-score retry flow.
4. `test_translation_request_sys_prompt_contains_no_tools_instruction` —
   same via a compact-map flow.

### Verification commands
Same five gates as Finding 46, same two files.

### Out of scope
- `tools/ai_antigravity_cli.py::_build_prompt` wrapper text (provider-level;
  touching it affects all callers, not just the analyzer).
- Any schema or recovery-logic changes.

### Implementation outcome - 2026-06-11
- Added `NO_TOOLS_INSTRUCTION` in `exporter/analysis/translate_core.py`.
- Appended it only to the main `build_system_prompt` preamble, reformat
  `prompt_sys`, retry `prompt_sys`, and compact-map translation-only
  `prompt_sys`.
- Added tests covering all four prompt paths and confirmed the red failure
  before implementation.
- Validation passed:
  `uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pytest tests/exporter/analysis/test_translate_core.py -v`
  (74 passed, 1 third-party deprecation warning).

---

## Finding 48 — strip grammar-note parentheticals from contextual meanings

Status: COMPLETE 2026-06-11. Impact: medium (visible report quality; removes
"(accusative)" / "(nominative plural masculine)"-style pollution).

### Problem (evidence)
- `temp/tier_eval/low/MN41_p2_study.md`: meanings include
  "(nominative plural masculine)", "(enclitic emphasizing the transition)".
- `temp/tier_eval/low/AN3.33_p1_study.md`: nominative `bhagavā` rows show
  "the Blessed One, the Exalted One (accusative)".
- Root causes:
  1. The main system prompt forbids grammar parentheticals (line 1318), but
     the translation-only prompt (`_build_translation_prompt`, lines
     497–524) and the retry prompt (`_build_missing_scores_prompt`, lines
     693–720) do not carry the rule.
  2. The Finding 40 salvage captures `meaning` strings verbatim from
     wrong-schema responses into `word_meanings`, and those meanings often
     embed grammar notes.
  3. Reformat/retry responses can also return polluted
     `contextual_meaning` values; nothing sanitizes them.

### Exact current anchors (verified 2026-06-11)
- Main-prompt rule (reference text): line 1318.
- `_build_translation_prompt`: line 497.
- `_build_missing_scores_prompt`: line 693.
- Central normalization choke point: `_normalize_ai_response` — all paths
  flow through it (single-chunk at line 1174, per-chunk at line 1164, retry
  data at line 756), so sanitizing there covers first-pass, compact-map,
  reformat, and retry outputs in one place.

### Files to change
- `exporter/analysis/translate_core.py`
- `tests/exporter/analysis/test_translate_core.py`

### Implementation
1. Add `_strip_grammar_annotations(text: str) -> str`:
   - remove parenthetical groups ONLY when they contain grammar vocabulary
     (case-insensitive keyword gate), e.g.:
     `nominative|accusative|genitive|dative|instrumental|locative|ablative|`
     `vocative|singular|plural|masculine|feminine|neuter|enclitic|particle|`
     `indeclinable|optative|aorist|participle|component of|grammatical`;
   - preserve legitimate parentheticals such as "(of conversation)",
     "(as a token of respect)", "(25)";
   - collapse doubled spaces and trim trailing separators left behind.
2. In `_normalize_ai_response`, after existing normalization, iterate the
   `scores` dict; for each value dict whose `contextual_meaning` is a
   non-empty `str`, replace it with the stripped version.
3. Apply the same stripping when salvage meanings are captured into
   `word_meaning_map` (Shape B and Shape C sites inside
   `_extract_structured_selection_map`, around lines 430–495), so prefilled
   meanings are clean even before normalization.
4. Add the no-grammar-notes sentence to `_build_translation_prompt` and
   `_build_missing_scores_prompt` (reuse the wording of line 1318:
   "Provide ONLY the core meaning. Do NOT append grammatical case notes in
   parentheses.").

### Tests — write FIRST, confirm red
1. `test_strip_grammar_annotations_removes_case_notes` — "(accusative)",
   "(nominative plural masculine)", "(enclitic emphasizing the transition)"
   are removed; surrounding text intact.
2. `test_strip_grammar_annotations_preserves_legitimate_parentheticals` —
   "(of conversation)", "(as a token of respect)", "(25)" survive.
3. `test_strip_grammar_annotations_cleans_whitespace` — no doubled spaces
   or dangling separators after removal.
4. `test_normalize_ai_response_strips_grammar_annotations` — a scores dict
   with polluted `contextual_meaning` comes out clean.
5. `test_structured_selection_meanings_are_stripped` — Shape B salvage with
   `meaning: "the Blessed One (accusative)"` → captured meaning is clean.
6. `test_translation_prompt_contains_no_grammar_notes_rule` and
   `test_missing_scores_prompt_contains_no_grammar_notes_rule`.

### Verification commands
Same five gates as Finding 46, same two files.

### Out of scope
- Report-rendering changes in `study_passage.py` / `analyzer.py`.
- Touching dictionary `meaning_combo` data (only AI-produced
  `contextual_meaning` values are sanitized).

### Implementation outcome - 2026-06-11
- Added `NO_GRAMMAR_NOTES_INSTRUCTION`, a grammar-keyword gated
  `_strip_grammar_annotations()` helper, and normalization of
  `contextual_meaning` values in `_normalize_ai_response`.
- Structured wrong-schema salvage now strips grammar parentheticals from
  captured `meaning` strings before they prefill compact-map contextual
  meanings.
- `_build_translation_prompt()` and `_build_missing_scores_prompt()` now carry
  the no-grammar-notes rule already present in the main system prompt.
- Added tests for grammar-note stripping, legitimate parenthetical
  preservation, whitespace/separator cleanup, normalization, structured
  selection salvage, and the two prompt builders.
- Red phase confirmed: the seven Finding 48 tests failed before
  implementation for the expected missing helper/prompt/sanitization behavior.
- Validation passed:
  `uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pytest tests/exporter/analysis/test_translate_core.py -v`
  (81 passed, 1 third-party deprecation warning).

---

## Finding 49 — classify immediate empty Antigravity responses as possible quota exhaustion

Status: COMPLETE 2026-06-11. Impact: low (clearer diagnostics; supports the standing
handoff guidance to stop instead of burning calls in a quota window).

### Problem (evidence)
High SN15.1 p2: chunk call returned empty after 38.29s; the immediate rerun
returned empty in 7.89s (`temp/tier_eval/high/SN15.1_p2_run.log`,
`SN15.1_p2_attempt2_run.log`). `agy` does not surface quota exhaustion;
near-instant empties are the only signal. Currently both cases raise the
same message: `"{model} returned an empty response"`.

### Exact current anchors (verified 2026-06-11)
- `tools/ai_antigravity_cli.py:126`:
  `raise AntigravityCliProviderError(f"{model} returned an empty response")`
  inside the call wrapper after `run_antigravity_print(...)` (call at lines
  ~106–112).

### Files to change
- `tools/ai_antigravity_cli.py`
- `tests/tools/test_ai_antigravity_cli.py`

### Implementation
1. Add a module-level constant `IMMEDIATE_EMPTY_SECONDS = 10.0`.
2. Measure elapsed time around the `run_antigravity_print` call with
   `time.monotonic()`.
3. When the response is empty AND elapsed < `IMMEDIATE_EMPTY_SECONDS`,
   raise:
   `f"{model} returned an immediate empty response (possible quota exhaustion)"`.
   Otherwise keep the current message unchanged.
4. No retry/stop behavior changes in this finding — message classification
   only. (`tools/ai_manager.py` surfaces the message via `status_message`,
   which run logs and debug JSON already record.)

### Tests — write FIRST, confirm red
In `tests/tools/test_ai_antigravity_cli.py`, monkeypatch
`run_antigravity_print` and `time.monotonic` (or patch the constant):
1. `test_immediate_empty_response_flags_possible_quota_exhaustion` — fast
   empty → message contains "possible quota exhaustion".
2. `test_slow_empty_response_keeps_plain_message` — elapsed above threshold
   → original message, no quota wording.

### Verification commands
```
uv run ruff check --fix tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py
uv run ruff format tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py
uv run pyright tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py
uv run --with pyrefly pyrefly check --min-severity warn tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py
uv run pytest tests/tools/test_ai_antigravity_cli.py -v
```

### Out of scope
- Automatic stop/backoff logic in `tools/ai_manager.py`.
- GPT-OSS fallback behavior.

### Implementation outcome - 2026-06-11
- Added `IMMEDIATE_EMPTY_SECONDS = 10.0` in
  `tools/ai_antigravity_cli.py`.
- `generate_content()` now measures the `run_antigravity_print(...)` elapsed
  time with `time.monotonic()`.
- Empty responses under the threshold now raise
  `"{model} returned an immediate empty response (possible quota exhaustion)"`.
  Slower empty responses keep the existing
  `"{model} returned an empty response"` message.
- No retry, stop/backoff, or fallback behavior was changed.
- Added tests for fast empty-response quota classification and slow empty
  response message preservation.
- Red phase confirmed: the two Finding 49 tests failed before implementation
  because the provider did not yet import/use `time.monotonic()`.
- Validation passed:
  `uv run ruff check --fix tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py`;
  `uv run ruff format tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py`;
  `uv run pyright tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py`;
  `uv run --with pyrefly pyrefly check --min-severity warn tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py`;
  `uv run pytest tests/tools/test_ai_antigravity_cli.py -v`
  (12 passed).

---

## Finding 50 — document the one-selection-per-surface-word limitation

Status: COMPLETE 2026-06-11. Impact: trivial (documentation only; the structural fix was
explicitly deferred as poor cost/benefit).

### Problem (evidence)
The pipeline applies a single disambiguation choice and a single contextual
meaning to every occurrence of the same surface word in a sentence/chunk.
AN3.33 p1 contains `bhagavā` as both nominative (narrative) and vocative
("etassa, bhagavā, kālo"); all occurrences render with one shared selection.
A real fix requires per-occurrence keys — a structural change deliberately
NOT approved.

### Files to change
- `exporter/analysis/README.md`

### Implementation
Add a short "Known limitations" entry (create the section if it does not
exist) stating: scores are keyed by dictionary option key, so a surface word
appearing multiple times with different grammatical functions in one
sentence/chunk receives a single shared selection and contextual meaning;
cite the `bhagavā` nominative/vocative example from AN3.33 p1.

### Verification
- `grep -n "Known limitations" exporter/analysis/README.md` returns the new
  section. No Python gates needed (markdown-only change).

### Out of scope
- Any code change toward per-occurrence disambiguation.
- The `upapajjantī'ti` deconstruction prompt-hint experiment (NOT approved;
  remains a recorded idea in `handoff.md` only).

### Implementation outcome - 2026-06-11
- Added a `Known Limitations` section to `exporter/analysis/README.md`.
- Documented that repeated occurrences of the same surface word in one
  sentence/chunk share one dictionary-option selection and contextual meaning.
- Included the AN3.33 paragraph 1 `bhagavā` nominative/vocative example.
- Validation passed:
  `grep -n "Known Limitations" exporter/analysis/README.md`.

---

## Finding 45 — DeepSeek vs Gemini Flash Low model evaluation (RUN LAST)

Status: COMPLETE 2026-06-11. Impact: cost/quality decision — compare
`deepseek/deepseek-v4-flash` against a fresh post-improvement
`antigravity_cli/Gemini 3.5 Flash (Low)` run on identical targets and
identical pipeline code. User-directed order override on 2026-06-11:
DeepSeek was run first, then hard stop. Fresh Low/Gemini rerun and
side-by-side quality comparison were completed afterward.

### Evidence base
- Historical Low baseline: `temp/tier_eval/low/` (5 targets, all artifacts)
  plus the Finding 44 metrics table in `findings_40_44_plans.md`. Use this
  only as pre-improvement context.
- Required fresh Low baseline: rerun the same five targets after Findings
  46-50 are complete and store artifacts under
  `temp/tier_eval/low_post_improvements/`.
- Required DeepSeek comparison: run the same five targets and store artifacts
  under `temp/tier_eval/deepseek_post_improvements/`. This was completed
  first by user-directed order override on 2026-06-11; do not rerun it unless
  artifacts are missing or the user explicitly approves a repeat.
- `tools/ai_models.json` confirms the provider/model pair exists:
  `default_models[0]` is `{"provider": "deepseek", "model":
  "deepseek-v4-flash", "delay": 5}`.

### Method (evidence-only; NO source code changes in this finding)
1. Confirm Findings 46-50 have been completed and validated; check
   `handoff.md`, this plan, and `git status --short` before starting.
2. Use the same five benchmark targets as Finding 44, same stdin inputs:
   | Target | stdin input |
   |---|---|
   | TH215 | `TH215\n` |
   | DHP211 | `DHP211\n` |
   | AN3.33 p1 | `AN3.33\n1\n` |
   | MN41 p2 | `MN41\n2\n` |
   | SN15.1 p2 | `SN15.1\n2\n` |
3. Next rerun `Gemini 3.5 Flash (Low)` on all five targets:
   ```
   printf '<input>' | uv run python exporter/analysis/study_passage.py --debug --provider antigravity_cli --model "Gemini 3.5 Flash (Low)"
   ```
4. DeepSeek was already run first on 2026-06-11 by explicit user request:
   ```
   printf '<input>' | uv run python exporter/analysis/study_passage.py --debug --provider deepseek --model deepseek-v4-flash
   ```
5. After EACH run, copy artifacts before the next run overwrites them
   (use loop variable names like `src`, never `path`, in zsh):
   ```
   mkdir -p temp/tier_eval/<comparison_folder>
   cp exporter/analysis/output/<source>_ai_debug.json temp/tier_eval/<comparison_folder>/
   cp exporter/analysis/output/<source>_study.json temp/tier_eval/<comparison_folder>/
   cp exporter/analysis/reports/<source>_study.md temp/tier_eval/<comparison_folder>/
   cp exporter/analysis/reports/<source>_ai_raw.txt temp/tier_eval/<comparison_folder>/
   ```
   Also save terminal output as
   `temp/tier_eval/<comparison_folder>/<source>_run.log`.
   Use `<comparison_folder> = low_post_improvements` for the Low rerun and
   `<comparison_folder> = deepseek_post_improvements` for DeepSeek.
6. Extract per-run metrics from the debug JSON with the same jq shape as
   Finding 44 (chunks, reformats, retries, missing first, missing after
   retry, final scores) plus per-call wall times and any hard failures.
7. Repeat policy: if a target fails once, repeat that single run once to
   distinguish nondeterminism from systematic failure. Do not repeat the
   whole matrix without user approval. Stop on repeated quota-like failures.
8. Complete the full metrics table in this section with fresh Low and the
   existing DeepSeek rows side by side; include the Finding 44 Low rows only
   as historical context. Add a concise summary to `handoff.md`.
9. Quality comparison: read each DeepSeek `_study.md` against the fresh Low
   rerun in `temp/tier_eval/low_post_improvements/<source>_study.md` and
   report concrete disambiguation differences (case selections,
   deconstruction choices, contextual-meaning quality, translation register).
   Check specifically the known shared failure points:
   - `upapajjantī'ti` in MN41 p2: does either model pick the correct
     `upapajjanti + iti` (pr 3rd pl) deconstruction variant?
   - the MN41 p2 closing question cases (`bhedā`, `maraṇā`, `paraṃ`,
     `sugatiṃ`, `saggaṃ`, `nāma` in `nāmagottaṃ`);
   - grammar-note pollution in contextual meanings after Finding 48.
   State an opinion with evidence, but the final quality verdict is the
   USER's manual judgment.

### Decision rule
DeepSeek replaces/joins Low as default only if it has (1) zero hard
failures, (2) zero missing-score groups after retry, (3) comparable or
lower recovery overhead and latency, and (4) user-judged equal-or-better
markdown quality against the fresh post-improvement Low rerun. Otherwise
record the result and keep Low. Do not change `tools/ai_models.json` in this
finding — that is a follow-up user decision.

### Out of scope
- Any source/code/prompt changes.
- Other DeepSeek tiers or providers.

### Implementation outcome - 2026-06-11

User requested running DeepSeek first and hard-stopping before the fresh
Gemini/Low rerun. DeepSeek was completed first; fresh Low/Gemini was completed
afterward. No source or test files were intentionally changed.

Artifacts:
- DeepSeek: `temp/tier_eval/deepseek_post_improvements/`
- Fresh Low/Gemini: `temp/tier_eval/low_post_improvements/`

| Provider/model | Target | Attempt | Result | Calls | Chunks | Reformats | Retries | Missing first | Missing after retry | Final scores | Max call | Notes |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Low `Gemini 3.5 Flash (Low)` | TH215 | 1 | ok | 3 | 0 | 0 | 1 | 25 | 0 | 94 | 14.78s | compact map + translation, then retry |
| Low `Gemini 3.5 Flash (Low)` | DHP211 | 1 | ok | 3 | 0 | 1 | 1 | 6 | 0 | 43 | 12.10s | reformat, then retry |
| Low `Gemini 3.5 Flash (Low)` | AN3.33 p1 | 1 | ok | 5 | 2 | 0 | 1 | 38 | 0 | 141 | 12.40s | two compact-map translation calls, then retry |
| Low `Gemini 3.5 Flash (Low)` | MN41 p2 | 1 | ok | 7 | 3 | 1 | 1 | 49 | 0 | 239 | 18.53s | one reformat, two translation calls, then retry |
| Low `Gemini 3.5 Flash (Low)` | SN15.1 p2 | 1 | ok | 11 | 4 | 0 | 3 | 96 | 0 | 487 | 19.39s | four compact-map translation calls, three retries |
| DeepSeek `deepseek-v4-flash` | TH215 | 1 | ok | 2 | 0 | 0 | 1 | 23 | 0 | 94 | 9.22s | first response plus missing-score retry |
| DeepSeek `deepseek-v4-flash` | DHP211 | 1 | ok | 2 | 0 | 0 | 1 | 4 | 0 | 40 | 6.03s | first response plus missing-score retry |
| DeepSeek `deepseek-v4-flash` | AN3.33 p1 | 1 | ok | 3 | 2 | 0 | 1 | 15 | 0 | 92 | 10.66s | two chunks plus missing-score retry |
| DeepSeek `deepseek-v4-flash` | MN41 p2 | 1 | ok | 4 | 3 | 0 | 1 | 27 | 0 | 169 | 9.29s | three chunks plus missing-score retry |
| DeepSeek `deepseek-v4-flash` | SN15.1 p2 | 1 | ok | 5 | 4 | 0 | 1 | 38 | 0 | 335 | 31.29s | four chunks plus missing-score retry |

Metric notes:
- Both providers completed all five targets on attempt 1 with zero hard
  failures and zero missing-score groups after retry.
- DeepSeek used fewer calls and fewer recovery paths on all five targets.
- Fresh Low had lower max-call latency on the two largest targets
  (`MN41_p2`, `SN15.1_p2`), while DeepSeek had lower max-call latency on the
  three smaller targets.
- Visible markdown table row counts were identical across providers:
  TH215 22, DHP211 20, AN3.33 p1 100, MN41 p2 130, SN15.1 p2 160.

Quality comparison:
- `TH215`: Low produced a more complete translation by retaining the
  finger-snap duration detail; DeepSeek's translation omitted that nuance.
- `DHP211`: Low's translation was smoother and closer to idiomatic English;
  DeepSeek's "make a dear one" / "loss ... is evil" was more literal and
  rougher.
- `AN3.33_p1`: Both selected nominative `bhagavā` for the vocative address
  in `etassa, bhagavā, kālo`; both got `sugata` as vocative. DeepSeek's
  translation was serviceable but its literal translation was rougher.
- `MN41_p2`: DeepSeek was better on the known closing-question case
  selections: it selected ablative `bhedā`, ablative `maraṇā`, idiomatic
  `paraṃ`, and acceptable `sugatiṃ`/`saggaṃ` rows. Fresh Low regressed to
  nominative `bhedā`, nominative `maraṇā`, nominative `paraṃ`, and the
  `saggaṃ` noun row. Both still selected the wrong `upapajjantī'ti`
  deconstruction (`upapajjantī + iti`, not expected `upapajjanti + iti`).
- `SN15.1_p2`: Low's prose was more polished and less stilted; DeepSeek was
  more literal and made some awkward selections/wording around `agga`,
  `kaṭā`, and `chavā`.
- Grammar-note check: DeepSeek had no grammar-keyword parenthetical matches
  in generated markdown. Fresh Low had visible `(singular)` / `(plural)`
  parentheticals for `app'ekacce` in `MN41_p2`; this appears in the meaning
  column and should be manually judged, since it may derive from dictionary
  wording rather than AI-added grammar notes.

Recommendation: do not change `tools/ai_models.json` automatically. DeepSeek
is promising because it is cheaper/fewer-call and fixed the MN41 closing-case
cluster that fresh Low got wrong, but Low still produced better prose on some
small and large passages. The default-model decision should be a separate
user judgment after manual review of the two artifact folders.
