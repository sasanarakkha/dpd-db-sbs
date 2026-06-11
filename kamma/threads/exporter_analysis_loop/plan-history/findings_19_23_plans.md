# Detailed Implementation Plans: Findings 19–23

Status: approved 2026-06-11. Findings 19, 20, 22, and 23 were implemented on 2026-06-11.
Conditional Finding 21 was dropped on 2026-06-11 after the Finding 23 `SN15.1_p2`
live smoke left 0 unresolved groups after retry. No implementation item remains in this
approved findings set.
Execute one finding per session unless the user explicitly overrides the one-issue rule.

These plans were written on 2026-06-11 from analysis of the 2026-06-11 live-debug prep set
(`TH110`, `DHP150`, `AN7.13_p1`, `MN19_p2`, `SN15.1_p2`; see handoff.md "Live Debug Prep
Session - 2026-06-11"). All code anchors were verified by reading the actual source on
2026-06-11. If an anchor does not match when you implement, STOP and re-read the file —
do not guess.

Evidence sources (verified 2026-06-11 with direct JSON inspection):
- `exporter/analysis/output/SN15.1_p2_ai_debug.json`:
  - `system_prompt` is 853,803 chars; the argv guard rejected agy at 913,451 bytes.
  - First response (direct `deepseek-v4-flash`, status `(200)`): `raw_response` is
    26,228 chars, cut mid-token (`parse_error` at char 26227 — the final char). The
    `_extract_partial_response` salvage recovered **188 score entries** into
    `parsed_response["scores"]`.
  - Reformat (agy, 9.63s): valid JSON, but only **2 score entries** plus translations.
    Because the reformat replaces `ai_data` wholesale, the 188 salvaged entries were
    discarded — only the 2 reformat entries survived into scoring.
  - 108 missing groups after first response; retry prompt 295,030 chars; `missing_keys`
    647 total / 569 unique.
  - Retry (agy timed out at 90s → `deepseek-v4-flash`, status `(200)`): `raw_response`
    is 19,362 chars, cut mid-token (`parse_error` at char 19361). Salvage recovered 551
    entries; 18 unique keys remained unresolved. `final_scores` has 578 entries.
  - Both truncated DeepSeek responses carry success statuses showing only `(200)` —
    no `finish_reason`, so output-cap truncation is invisible outside debug JSON.
- handoff.md prep findings: first-pass agy timed out at 96.90s (`TH110`, 113,220-byte
  sys prompt), 94.84s (`AN7.13_p1`, 250,783), 96.17s (`MN19_p2`, 248,059), while
  `DHP150` (79,653) succeeded at 93.51s. All retry/reformat prompts ≤ 40KB succeeded
  through agy in 8–22s.
- `tools/ai_models.json`: antigravity entry has `"timeout": 90`; all other providers use
  the 150s fallback (`tools/ai_manager.py:17,128`).
- `agy --help` (v1.0.7, checked 2026-06-11): `--print` takes the prompt as an argv
  argument only; there is no stdin/file prompt transport. The 700,000-byte argv guard is
  therefore inherent — `SN15.1_p2`-class first prompts can never reach agy.

What this run set confirmed is working (no action):
- Issue 25 dedupe live-proved (`SN15.1_p2`: 647 → 569 unique keys; `AN7.13_p1`: 78 → 65).
- Issue 26 live-proved: 8,192-token DeepSeek completions (~19–26KB) vs the old ~7KB cap.
- Issue 28 live-proved indirectly: no oversized status dumps in any of the five runs.
- `_extract_partial_response` salvage is the workhorse for truncated responses
  (188 + 551 entries recovered in `SN15.1_p2`).
- Hallucinated salvage keys (e.g. retry `"missing_anamata"`) enter `scores_map` but
  cannot collide with real option keys (headword-id based); harmless debug noise only.

Shared constraints for every finding:
- TDD: write the failing test first, run it, confirm it fails for the expected reason, then
  implement.
- Quality gates per changed file (all must pass before reporting completion):
  1. `uv run ruff check --fix <files>`
  2. `uv run ruff format <files>`
  3. `uv run pyright <files>`
  4. `uv run --with pyrefly pyrefly check --min-severity warn <files>`
  5. `uv run pytest <test file> -v`
- Never run bare `uv run pytest`. Always pass the specific test file path.
- If `uv run` fails on `/Users/deva/.cache/uv` permissions, retry with
  `UV_CACHE_DIR=/private/tmp/uv-cache`.
- Modern type hints, `Path` from pathlib, no `sys.path` hacks.
- Commit messages (prepared for the user, not committed by the agent) must reference `#197`.

Recommended order: 19 → 20 → 23 → live `SN15.1` p2 smoke → drop 21 if unresolved
groups are <= 5 → 22. Findings 19, 20, and 23 are implemented, the `SN15.1_p2`
smoke left 0 unresolved groups, and Finding 21 is dropped. The next approved
implementation item was Finding 22, now implemented.

Finding 23 was added on 2026-06-11 from a user-proposed direction (split the passage into
parts, send them separately, unite the results). This converts the previously deferred
"first-prompt chunking" observation into a planned finding with explicit user backing.

---

## Finding 19 — merge reformat scores with salvaged first-response scores

Status: IMPLEMENTED 2026-06-11. Impact: high. This is a deterministic data-loss bug,
not a model-quality issue.

### Problem
When the first response is malformed JSON, `_parse_ai_json` falls back to
`_extract_partial_response`, which regex-salvages every complete
`"key": {"score": N}` entry from the truncated text. The reformat path then runs, and on
success does `ai_data = reformat_data` — a wholesale replacement that throws the salvage
away. `SN15.1_p2` live evidence: 188 salvaged entries were replaced by a 2-entry reformat
result. Those discarded 186 entries directly inflated the missing-group count to 108 and
the retry to 569 unique keys, which then exceeded the DeepSeek 8,192-token output cap and
left 18 keys unresolved. Keeping the salvage would have shrunk the retry below the size
that breaks.

### Files to change
- `exporter/analysis/translate_core.py` (implementation)
- `tests/exporter/analysis/test_translate_core.py` (tests)

### Exact current anchor (translate_core.py:625-631, reformat success branch)
```python
        if reformat_response.content:
            reformat_data, reformat_error = _parse_ai_json(reformat_response.content)
            reformat_ok = not reformat_error and isinstance(
                reformat_data.get("scores"), dict
            )
            if reformat_ok:
                ai_data = reformat_data
```

### Implementation
1. In the `reformat_ok` branch, before `ai_data = reformat_data`, union the salvaged
   scores into the reformat result, with reformat entries winning key conflicts (the
   reformat is the model's cleaned rendering of the same content):
```python
            if reformat_ok:
                salvaged_scores = ai_data.get("scores")
                if isinstance(salvaged_scores, dict) and salvaged_scores:
                    reformat_data["scores"] = {
                        **salvaged_scores,
                        **reformat_data["scores"],
                    }
                ai_data = reformat_data
```
2. No other change. The wrong-schema reformat trigger (valid JSON, non-dict `scores`) is
   covered by the `isinstance` guard — there is nothing to merge in that case.

Design notes (do not deviate):
- Salvaged entries are the model's own output, regex-extracted only when the full
  `"score": <digits>` value is complete; they are exactly as trustworthy as a parsed
  response, minus optional fields (`contextual_meaning`, `selected_pos`).
- Hallucinated salvage keys are already tolerated on the retry path today
  (`scores_map.update(retry_scores)` after salvage) and cannot match real option keys.
- Do NOT merge translation/literal_translation — the reformat's prose fields stay
  authoritative.

### Tests (tests/exporter/analysis/test_translate_core.py)
Write FIRST, confirm red. Mirror the existing reformat test's `FakeAIManager`
multi-call pattern (find the sibling test that exercises the reformat path; reuse its
`analyze_sentence` fixture):
- Call 1 returns truncated JSON containing two complete score entries and then a cut-off
  string, e.g.
  `'{"translation": "x", "scores": {"60847_0": {"score": 9}, "60789_0": {"score": 7}, "60790_0": {"sco'`
  → parse error, salvage recovers both keys.
- Call 2 (reformat) returns valid JSON whose `scores` has only
  `{"60790_0": {"score": 3}}`.
- Assert all three keys end up in `debug["final_scores"]` (or in option `ai_score`
  fields, matching the sibling test's assertion style).
Expected red-state failure: only `60790_0` survives.

Add a conflict-preference assertion: call 1 salvages `{"60847_0": {"score": 1}}`, call 2
returns `{"60847_0": {"score": 8}}` → final score is 8 (reformat wins).

### Verification commands
```
uv run pytest tests/exporter/analysis/test_translate_core.py -v
uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
```
Live smoke: re-run `SN15.1` paragraph 2 with `--debug`; compare
`missing_score_groups_after_first_response` count against the 2026-06-11 capture (108).

### Out of scope
- Retry path, salvage regex, reformat prompt wording.

---

## Finding 20 — raise the antigravity per-model timeout from 90s to 150s

Status: IMPLEMENTED 2026-06-11. Impact: high for provider routing on first-pass calls.

### Problem
Three of four first-pass agy launches in the 2026-06-11 set timed out at 94.84–96.90s
(prompts 113–251KB), falling back to DeepSeek; `DHP150` (80KB) succeeded at 93.51s —
right at the boundary. The pattern: agy needs slightly more than its 90s internal
`--print-timeout` window for prompts in the ~100–250KB range. The preferred provider is
effectively unusable for first-pass calls of normal paragraph size, and each run burns
~95–100s on the doomed attempt before the fallback even starts. The global/default
timeout is already 150s (Issue 9); antigravity's 90s (Issue 10) is the outlier.

### Files to change
- `tools/ai_models.json` (implementation — one value)
- `tests/tools/test_ai_manager.py` (test pins the value)

### Exact current anchors
`tools/ai_models.json:7`:
```json
      "timeout": 90
```
`tests/tools/test_ai_manager.py:140-150` (`test_antigravity_has_per_model_timeout`)
asserts `agy_entries[0][3] == 90.0` with docstring "must carry a 90s per-model timeout".

### Implementation
1. TDD on the config test: update `test_antigravity_has_per_model_timeout` to assert
   `150.0` (and fix its docstring), run it, confirm red.
2. Change `"timeout": 90` → `"timeout": 150` in `tools/ai_models.json`.
3. No code change: `run_antigravity_print` already derives `--print-timeout` from the
   passed value and hard-kills at timeout+10s (effective kill moves ~100s → ~160s).
4. `test_request_uses_per_model_timeout` uses a stub 90.0 unrelated to the JSON; leave it.

Tradeoff to state before approval: when agy genuinely cannot answer (auth loss, outage),
each first-pass attempt waits up to ~60s longer before DeepSeek fallback. Against that:
today's timed-out attempts already waste ~95–100s and deliver nothing; if agy completes
within 150s the run gets the preferred model's first-pass quality at roughly the same
wall time. Uncertainty: there is no proof agy finishes 250KB prompts within 150s —
the live re-run is the test. If it still times out, revert is one line.

### Verification commands
```
uv run pytest tests/tools/test_ai_manager.py -v
```
(`ruff`/`pyright`/`pyrefly` on the test file; the JSON has no Python gates.)
Live smoke: re-run `TH110` and `MN19` paragraph 2 with `--debug`; check whether the
first-pass status names `antigravity_cli` instead of a DeepSeek fallback, and record
actual durations in the handoff either way.

### Out of scope
- argv-guard limit, fallback ordering, other providers' timeouts.

---

## Finding 21 — chunk the missing-scores retry into bounded batches (revived Finding 17)

Status: DROPPED 2026-06-11. After Findings 19, 20, and 23 were live, the
`SN15.1_p2` re-run left 0 unresolved unique groups after retry, so the contingent
implementation condition (>5 unresolved groups) was not met.

### Problem
Finding 17 was dropped on 2026-06-10 because post-dedupe MN17_p2 left only 4 unresolved
groups. `SN15.1_p2` now exceeds the rule: 569 unique missing keys, a 295,030-char retry
prompt (agy timed out → DeepSeek), and a retry *output* truncated at the 8,192-token cap
(19,362 chars ≈ 551 entries) leaving 18 unique keys unresolved. New insight vs the
original finding: the binding constraint is the completion cap, not just the prompt —
569 compact score entries simply do not fit in one 8,192-token response. Chunking bounds
both sides: each batch's prompt stays in the size range agy answers in 8–22s, and each
batch's required output stays well under the cap.

### Files to change
- `exporter/analysis/translate_core.py` (implementation)
- `tests/exporter/analysis/test_translate_core.py` (tests)

### Current anchor (translate_core.py:653-685, verified 2026-06-11)
The retry block is a single `ai_manager.request` on the whole `missing_groups` list;
`debug["retry_requests"]` is already a list and supports one entry per batch.

### Approach (re-verify anchors at implementation time)
1. `MAX_RETRY_CONTEXT_CHARS = 60_000` (all observed ≤40KB retry prompts succeeded
   through agy quickly; `AN5.43`'s fully-successful retry context was ~80K chars).
2. `_batch_missing_groups(missing_groups, max_chars)` — greedy packing by each group's
   compact `json.dumps` length, never splitting a group.
3. Loop batches in the retry block: per-batch `_build_missing_scores_prompt` +
   `ai_manager.request`, then the existing
   `_parse_ai_json` → `_normalize_ai_response` → `_coerce_flat_score_map` →
   `scores_map.update` pipeline, and one `debug["retry_requests"]` entry per batch.
4. Cap total batches (8) to bound cost; record skipped groups in debug.

Tradeoff to state before approval: `SN15.1_p2`-class paragraphs would issue ~5 retry
requests instead of 1 — added time and cost, buying actual AI scores instead of
heuristic fallback for the unresolved tail.

### Tests
Mirror the existing retry tests' `FakeAIManager` call-counting pattern: missing groups
exceeding the budget must produce two retry calls whose prompts partition the groups and
whose responses both merge into `scores_map`. Direct unit test for
`_batch_missing_groups` boundary behavior (single oversized group still forms one batch).

### Out of scope
- Chunking the FIRST prompt, trimming examples, schema redesign (still deferred).

---

## Finding 22 (minor) — surface finish_reason on truncated non-empty DeepSeek responses

Status: IMPLEMENTED 2026-06-11. Impact: debuggability. Complements Issue 28, which covered only the
empty-content branch.

### Problem
Both truncated `SN15.1_p2` DeepSeek responses carried success statuses showing only
`(200)`. A length-capped completion is indistinguishable from a clean one anywhere
outside the debug JSON's `parse_error`; diagnosing this prep run required tail-reading
raw responses. The API already returns `finish_reason` per choice.

### Files to change
- `tools/ai_deepseek_manager.py` (implementation)
- `tests/tools/test_ai_deepseek_manager.py` (tests)

### Exact current anchor (tools/ai_deepseek_manager.py:144-153)
```python
        try:
            response_json = response.json()
            content = (
                response_json.get("choices", [{}])[0].get("message", {}).get("content")
            )
            if content:
                return AIResponse(
                    content=content,
                    status_message=str(response.status_code),
                )
```

### Implementation
1. Extract `finish_reason` defensively from `choices[0]` (same `.get` style as
   `_format_empty_content_status`).
2. In the content branch, when `finish_reason` is present and not `"stop"`, return
   `status_message=f"{response.status_code} (finish_reason={finish_reason})"`; otherwise
   keep the bare status code.
3. Touch nothing else — `AIManager` status composition (Issue 22) appends provider detail
   in parentheses already and is unit-covered.

### Tests (tests/tools/test_ai_deepseek_manager.py)
Write FIRST, confirm red, using the existing `_FakeResponse`/`_CapturingDeepseekManager`
patterns:
- Response with non-empty content and `finish_reason: "length"` →
  `"finish_reason=length" in response.status_message` and content preserved.
- Response with non-empty content and `finish_reason: "stop"` → status is the bare
  status code (no `finish_reason=` text).

### Verification commands
```
uv run pytest tests/tools/test_ai_deepseek_manager.py -v
uv run ruff check --fix tools/ai_deepseek_manager.py tests/tools/test_ai_deepseek_manager.py
uv run ruff format tools/ai_deepseek_manager.py tests/tools/test_ai_deepseek_manager.py
uv run pyright tools/ai_deepseek_manager.py tests/tools/test_ai_deepseek_manager.py
uv run --with pyrefly pyrefly check --min-severity warn tools/ai_deepseek_manager.py tests/tools/test_ai_deepseek_manager.py
```

### Out of scope
- Other providers, empty-content branch (Issue 28), retry/chunking logic.

---

## Finding 23 — chunk oversized passages into sentence batches, unite the results

Status: IMPLEMENTED 2026-06-11. Impact: high — this is the only finding
that attacks the FIRST-pass prompt size, the root cause behind the argv-guard rejection,
the agy timeouts, and the giant retries.

### Problem
`translate_sentence` issues exactly one first-pass request for the whole selected
passage. The system prompt is `json.dumps(analysis)` — dictionary options for every
word — so it grows with passage length: 854KB for the 2-sentence `SN15.1_p2`, which can
never pass the inherent 700KB argv guard, and 113–251KB for ordinary paragraphs, which
sit beyond agy's current 90s window. Multi-paragraph selections (or "analyze ALL") are
joined into one string and make this strictly worse. Chunking the passage and uniting
the results bounds every request to a size the preferred provider handles in 8–93s and
keeps every response far below the 8,192-token DeepSeek completion cap.

### Placement decision
NOT `exporter/analysis/passage_extraction.py` — that is a standalone preview CLI;
nothing in the pipeline imports it (verified 2026-06-11: only README references).
`study_passage.py` calls `translate_core.translate_sentence` directly, so the chunking
lives in `exporter/analysis/translate_core.py`, inside `translate_sentence`. Every
caller (study_passage, batch scripts, tests) gets it with no call-site changes.

### Files to change
- `exporter/analysis/translate_core.py` (implementation)
- `tests/exporter/analysis/test_translate_core.py` (tests)
- `exporter/analysis/study_passage.py` (`_build_raw_responses_log` renders per-chunk
  entries — Step 5)

### Facts verified against source on 2026-06-11 (do not re-derive from memory)
- `analyze_sentence` returns EXACTLY one `{"word": token, "status": ..., "data": [...]}`
  entry per token of `tokenize_sentence(sentence)`, in token order
  (`exporter/analysis/analyzer.py:748-832`; the only append is
  `results.append({"word": token, "status": status, "data": word_data})`).
  Therefore `len(analysis) == len(tokenize_sentence(resolved_sentence))` and slicing the
  analysis list by per-sentence token counts is a faithful partition.
- Word options are word-local: nothing in `get_word_details`/analysis depends on
  surrounding words, so a slice equals what per-chunk re-analysis would produce.
- `_normalize_ai_response` (`translate_core.py:103-121`) is idempotent — it only
  flattens a nested `{"scores": {"scores": ...}}` when no real option keys (containing
  `_`) are present. Re-normalizing merged chunk data is a no-op.
- `translate_core.py` already imports `tokenize_sentence`
  (`from exporter.analysis.analyzer import analyze_sentence, tokenize_sentence`).
  No import change needed.
- The first-pass block to extract spans `translate_core.py:508-644` in the current
  working tree: from `sys_prompt = build_system_prompt(analysis, speech_mark_options)`
  through the reformat `debug` write that ends with
  `debug["reformat_parse_error"] = reformat_error`. The shared tail continues at
  `ai_data = _normalize_ai_response(ai_data)` (line 646).
- `debug["retry_requests"] = []` is currently initialized INSIDE that block (line 513)
  but consumed by the shared retry tail; it must move to `translate_sentence`.
- Test fixtures: `tests/exporter/analysis/test_translate_core.py:359`
  (`test_translate_sentence_retries_missing_component_scores`) shows the canonical
  pattern — monkeypatch `"exporter.analysis.translate_core.analyze_sentence"` with a
  lambda returning a fixed analysis list, a local `FakeAIManager` whose `request`
  appends `kwargs["prompt"]` to `calls` and returns
  `type("FakeResponse", (), {"content": ..., "status_message": "ok"})()`, then call
  `translate_sentence("...", cast(Session, object()), ai_manager=cast(AIManager, FakeAIManager()), debug=debug)`.

### Design (threshold-gated)
Constant, module level next to the other constants:
```python
MAX_FIRST_CONTEXT_CHARS = 250_000
```
Rationale: per user decision 2026-06-11. ~250K chars ≈ ~270KB UTF-8 (observed ratio
853,803 chars → 913,451 bytes including instructions) — far under the 700KB argv guard.
This size class depends on Finding 20's 150s window (`AN7.13_p1` at 250,783 bytes timed
out at 90s). Finding 20 has landed; if the timeout is later reverted, re-discuss the
budget before implementing.

**Step 1 — pure code move (no behavior change).** Extract `translate_core.py:508-644`
into:
```python
def _request_first_pass(
    chunk_sentence: str,
    full_sentence: str,
    analysis: list[dict[str, Any]],
    ai_manager: AIManager,
    model: str | None,
    speech_mark_options: dict[str, list[str]] | None,
    progress: Callable[[str], None] | None,
    verbose: bool,
    debug: dict[str, Any] | None,
) -> dict[str, Any]:
```
- Body is the moved block verbatim, with three mechanical edits:
  1. `build_system_prompt(analysis, speech_mark_options)` stays as-is (parameters now
     local names).
  2. The user prompt becomes conditional:
     ```python
     if chunk_sentence == full_sentence:
         user_prompt = f"Return JSON for: {chunk_sentence}"
     else:
         user_prompt = (
             f"Return JSON for: {chunk_sentence}\n"
             "Full passage for context (score ONLY the words in your part): "
             f"{full_sentence}"
         )
     ```
     The single-chunk string must remain byte-identical to today's
     `f"Return JSON for: {resolved_sentence}"`.
  3. `debug["retry_requests"] = []` is REMOVED from the moved block (it moves to the
     caller); every other `debug[...]` write keeps its key name and writes into the
     `debug` parameter.
- Inside the moved block, `resolved_sentence` is renamed to `chunk_sentence` everywhere
  EXCEPT `_build_translation_prompt(resolved_sentence, ...)` and
  `_build_reformat_prompt(resolved_sentence, ...)` which also become `chunk_sentence`
  (both build per-request prompts and must describe the chunk being asked about).
- The helper returns `ai_data` exactly as the block leaves it today (NOT normalized —
  normalization stays in the callers, matching current order of operations).
- After this step, `translate_sentence` calls
  `_request_first_pass(resolved_sentence, resolved_sentence, analysis, ai_manager,
  model, speech_mark_options, progress, verbose, debug)` and sets
  `debug["retry_requests"] = []` right after the call. Run the FULL existing test file
  and confirm green before Step 2. (Cosmetic: `retry_requests` moves later in debug
  JSON key order; nothing reads key order.)

**Step 2 — splitter.** Add module-level:
```python
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _split_into_sentence_chunks(
    resolved_sentence: str,
    analysis: list[dict[str, Any]],
    max_context_chars: int,
) -> list[tuple[str, list[dict[str, Any]]]]:
```
Behavior (each rule is mandatory):
1. `whole = json.dumps(analysis, ensure_ascii=False, separators=(",", ":"))`. If
   `len(whole) <= max_context_chars` → return `[(resolved_sentence, analysis)]`.
2. `sentences = [s for s in _SENTENCE_SPLIT_RE.split(resolved_sentence) if s.strip()]`.
   If fewer than 2 sentences → return the single full chunk (cannot split).
3. `counts = [len(tokenize_sentence(s)) for s in sentences]`. If
   `sum(counts) != len(analysis)` → return the single full chunk (partition invariant
   violated; silent fallback — the run behaves exactly as today).
4. Slice `analysis` cumulatively by `counts` into per-sentence slices. Greedy-pack
   consecutive sentences: keep a running chunk; if adding the next sentence's slice
   pushes the chunk's serialized length (`json.dumps` of the combined slice, same
   compact separators) over `max_context_chars` AND the running chunk is non-empty,
   close the chunk and start a new one. A single sentence over budget forms its own
   oversized chunk (never split below sentence level; that chunk will fall back to
   DeepSeek exactly as today — not worse).
5. Chunk text = `" ".join(...)` of its sentences. Return list of
   `(chunk_text, chunk_analysis_slice)`.

**Step 3 — merge helper.** Add:
```python
def _merge_chunk_ai_data(chunk_datas: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {
        "translation": "",
        "literal_translation": "",
        "scores": {},
        "variant_choices": {},
    }
    translations: list[str] = []
    literals: list[str] = []
    for data in chunk_datas:
        translation = data.get("translation")
        if isinstance(translation, str) and translation.strip():
            translations.append(translation.strip())
        literal = data.get("literal_translation")
        if isinstance(literal, str) and literal.strip():
            literals.append(literal.strip())
        scores = data.get("scores")
        if isinstance(scores, dict):
            for key, value in scores.items():
                merged["scores"].setdefault(key, value)
        variant_choices = data.get("variant_choices")
        if isinstance(variant_choices, dict):
            for key, value in variant_choices.items():
                merged["variant_choices"].setdefault(key, value)
    merged["translation"] = " ".join(translations)
    merged["literal_translation"] = " ".join(literals)
    return merged
```
Conflict rule is `setdefault` (first chunk wins); a repeated word produces the same
option keys with equivalent meaning, so order does not matter materially.

**Step 4 — wire into `translate_sentence`.** Replace the Step-1 single call with:
```python
    chunks = _split_into_sentence_chunks(
        resolved_sentence, analysis, MAX_FIRST_CONTEXT_CHARS
    )
    if len(chunks) == 1:
        ai_data = _request_first_pass(
            resolved_sentence, resolved_sentence, analysis, ai_manager, model,
            speech_mark_options, progress, verbose, debug,
        )
    else:
        chunk_debugs: list[dict[str, Any]] = []
        chunk_datas: list[dict[str, Any]] = []
        for chunk_text, chunk_analysis in chunks:
            chunk_debug: dict[str, Any] | None = {} if debug is not None else None
            chunk_data = _request_first_pass(
                chunk_text, resolved_sentence, chunk_analysis, ai_manager, model,
                speech_mark_options, progress, verbose, chunk_debug,
            )
            chunk_datas.append(_normalize_ai_response(chunk_data))
            if chunk_debug is not None:
                chunk_debugs.append(chunk_debug)
        ai_data = _merge_chunk_ai_data(chunk_datas)
        if debug is not None:
            debug["chunk_requests"] = chunk_debugs
    if debug is not None:
        debug["retry_requests"] = []
```
- The full `speech_mark_options` dict is passed to EVERY chunk (decision: no per-chunk
  filtering — a few extra disambiguation lines cost ~nothing; `variant_choices` are
  unioned by key and `apply_variant_choices` runs on the full sentence later).
- The shared tail (`_normalize_ai_response` → `_apply_deterministic_scores_to_map` →
  missing-groups retry → `merge_ai_selections`) is NOT modified — it operates on the
  full `analysis` and the merged `ai_data`, and the retry now covers all chunks at once
  with a small prompt.
- `progress` events (`ai_start`/`ai_done`, possibly `ai_reformat_*`,
  `ai_translation_*`) fire once per chunk; `study_passage.py`'s printer simply prints
  the stage line N times. No change required there for progress.

**Step 5 — debug raw-log rendering (`exporter/analysis/study_passage.py`).** In
`_build_raw_responses_log` (study_passage.py:159-202): wrap the existing
"First response" section in `if "raw_response" in ai_debug:` and add, after it:
```python
    for i, chunk in enumerate(ai_debug.get("chunk_requests", []), start=1):
        sections.append(
            _section(
                f"Chunk {i} first response",
                chunk.get("status_message", ""),
                chunk.get("raw_response"),
            )
        )
        if "reformat_raw_response" in chunk:
            sections.append(
                _section(
                    f"Chunk {i} reformat response",
                    chunk.get("reformat_status_message", ""),
                    chunk.get("reformat_raw_response"),
                )
            )
        if "translation_raw_response" in chunk:
            sections.append(
                _section(
                    f"Chunk {i} translation response (word→key map path)",
                    chunk.get("translation_status_message", ""),
                    chunk.get("translation_raw_response"),
                )
            )
```
In chunked mode the top-level `raw_response`/`status_message`/`parsed_response`/
`parse_error` (and reformat/translation) keys are ABSENT from the debug dict — per-chunk
data lives only under `chunk_requests`. Do not duplicate chunk-1 data at top level.

Tradeoffs to state before approval:
- Oversized passages issue ~N requests instead of 1 (`SN15.1_p2` ≈ 4–5 chunks at 250K):
  more AI calls and wall time per huge passage — but today's single call is rejected by
  the argv guard, truncated by the output cap, and finishes with heuristic fallbacks, so
  the comparison is "a few small good calls vs 1 broken cascade".
- Chunk-boundary translation seams: joined prose may read slightly less fluent than a
  single-pass translation. Mitigated by the full-passage context line. Word-sense
  scoring should not degrade — each word's full dictionary options are in its own chunk.
- Most invasive change in this findings set. The Step-1 extraction MUST land green on
  the existing suite before any chunking logic is added; if the anchors at
  `translate_core.py:508-644` do not match the working tree (e.g. Finding 19 landed
  first and altered the reformat branch), re-read the file and adjust the extraction
  boundaries — do not guess.

### Tests (tests/exporter/analysis/test_translate_core.py)
Write FIRST, confirm red (except the Step-1 regression gate, which is the existing
suite). Use the exact fixture pattern of
`test_translate_sentence_retries_missing_component_scores` (line 359).
1. `test_split_into_sentence_chunks_single_chunk_under_budget` — direct call with a
   2-entry analysis and a huge budget → exactly `[(resolved_sentence, analysis)]`.
2. `test_split_into_sentence_chunks_packs_sentences` — `resolved_sentence =
   "buddho bhagavā. dhammo."`; analysis = 3 entries whose serialized length exceeds a
   tiny budget (e.g. `max_context_chars=10`); expect 2 chunks:
   `("buddho bhagavā.", first 2 entries)` and `("dhammo.", last entry)`; assert the
   slices concatenate to the original list.
3. `test_split_into_sentence_chunks_falls_back_on_token_mismatch` — analysis list whose
   length does NOT equal the sentence token count → single full chunk.
4. `test_translate_sentence_chunks_oversized_passage(monkeypatch)` — monkeypatch
   `"exporter.analysis.translate_core.analyze_sentence"` to return 3 minimal entries
   (keys `"1_0"`, `"2_0"`, `"3_0"`, fields `key`/`pali`/`pos`/`meaning_combo` as in the
   sibling fixture) for the passage `"buddho bhagavā. dhammo."`, and
   `monkeypatch.setattr(translate_core, "MAX_FIRST_CONTEXT_CHARS", 10)`. `FakeAIManager`
   returns, per call: call 1 →
   `'{"translation": "T1", "literal_translation": "L1", "scores": {"1_0": {"score": 10}, "2_0": {"score": 10}}}'`,
   call 2 →
   `'{"translation": "T2", "literal_translation": "L2", "scores": {"3_0": {"score": 10}}}'`.
   Assert: exactly 2 calls; call 1 prompt contains `"buddho bhagavā."` and the
   full-passage context line; merged `translation == "T1 T2"`; all three options carry
   `ai_score == 10` (no retry call — all keys scored); `len(debug["chunk_requests"]) == 2`
   and `debug["chunk_requests"][0]["raw_response"]` is call 1's content; top-level
   `"raw_response" not in debug`.
   Expected red-state failure before implementation: a single call containing the whole
   passage / `AttributeError` on the missing helper.
5. Step-1 regression gate: the EXISTING tests in this file (especially
   `test_translate_sentence_retries_missing_component_scores`,
   `test_translate_sentence_reformat_triggered_when_prose_returned`,
   `test_debug_parsed_response_is_snapshot_not_live_reference`) must pass unchanged
   after the extraction, before chunking is added.

### Verification commands
```
uv run pytest tests/exporter/analysis/test_translate_core.py -v
uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
```
Live smoke: re-run `SN15.1` paragraph 2 with `--debug` — expect every first-pass chunk to
go through agy (no argv-guard rejection), no output-cap truncation, and unresolved
groups ≤ 5. Also re-run `DHP150` (under budget) and confirm a single first-pass request.

### Out of scope
- Trimming example fields / dictionary-context schema redesign (still deferred).
- Chunking the retry prompt (Finding 21 — expected superseded).
- `passage_extraction.py` (preview tool stays untouched).

---

## Observations recorded, no action proposed
- The 700KB argv guard is inherent: `agy --print` accepts the prompt only as an argv
  argument (`agy --help`, v1.0.7). `SN15.1_p2`-class first prompts (854KB system prompt
  for a 2-sentence paragraph) can never reach agy. Finding 23 addresses this by keeping
  each request under the guard; example-trimming/schema redesign remains deferred.
- Wrong-schema first responses and the prompt-size correlation stay in the
  observation-only bucket per handoff caveats.
- Pali grammar accuracy (old Finding 5) remains deferred — model-quality, not code.

## Session ordering and closure rules
1. Current remaining approved implementation item: none.
2. Findings 19, 20, 22, and 23 are implemented. Finding 21 is dropped because the
   post-Finding-23 `SN15.1_p2` smoke left 0 unresolved groups after retry.
3. After each implemented finding, append a completed-issue entry to `handoff.md` in the
   existing format and mark the section here IMPLEMENTED with the date.
4. Keep `plan.md` stable — no checkboxes, no per-issue history there.
5. Prepare a draft commit message referencing `#197`; the user commits.
