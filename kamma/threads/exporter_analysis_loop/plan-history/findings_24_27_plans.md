# Detailed Implementation Plans: Findings 24–27

Status: APPROVED by the user on 2026-06-11. Findings 24, 25, and 27 are approved for
implementation. Finding 26 is approved ONLY contingent on its stated condition firing.
Findings 24, 25, 26, and 27 are now implemented. Execute one finding per session unless
the user explicitly overrides the one-issue rule.

These plans were written on 2026-06-11 from analysis of the 2026-06-11 five-request
prep batch (`TH180`, `DHP180`, `AN3.13_p1`, `MN119_p2`, `SN22.1_p2`; model
`Gemini 3.5 Flash (High)`, 150s timeout). All code anchors were verified by reading the
actual source on 2026-06-11. If an anchor does not match when you implement, STOP and
re-read the file — do not guess.

Evidence sources (verified 2026-06-11 with direct JSON inspection and live probes):
- `exporter/analysis/output/AN3.13_p1_ai_debug.json`:
  - 3 first-pass chunks, ALL succeeded through agy (69.88s / 13.61s / 15.72s). Finding 23
    chunking worked exactly as designed.
  - 89 missing groups after first response. ONE retry request: prompt 170,445 chars,
    352 keys (302 unique). Status `SUCCESS in 30.45s. antigravity_cli/Gemini 3.5 Flash
    (High)` — valid JSON, **no parse error, no truncation** (raw response only 2,449
    chars, ends cleanly with `}`), but it contains only **77 score entries**. The model
    voluntarily under-covered a 302-key request. 64 groups remained unresolved →
    heuristic fallback.
  - This breaks the assumption behind dropping Finding 21: the binding constraint is not
    only the DeepSeek 8,192-token *output cap* — the preferred model also under-covers
    large key lists even when its response is well-formed and far below any cap.
- Retry-context composition (measured with jq on the same file): the full
  `missing_groups` dump is 169,143 chars; with `example_1`, `source_1`, `example_2`,
  `source_2` removed from each option it is 75,197 chars — a **55% reduction**. The
  retry prompt only asks for `{"score": N}` per key; examples are first-pass baggage.
- `exporter/analysis/output/MN119_p2_ai_debug.json`: chunks 1–3 succeeded through agy
  (11.42s / 85.95s / 154.55s — the third nearly at the 150s limit), then chunks 4–6 and
  the retry ALL failed with `Gemini 3.5 Flash (High) returned an empty response` in
  4.95–24.66s each and fell back to DeepSeek. `SN22.1_p2`: every agy attempt empty in
  ~5s. Pattern: success, then a long call, then immediate empty responses for the rest
  of the run — consistent with the handoff's quota-exhaustion hypothesis.
- DeepSeek fallback fully recovered both runs (0 unresolved after retry), so empty
  responses cost preferred-model quality and ~5–25s per call, not correctness.
- Live `agy` probes (2026-06-11, after the batch): `agy models` lists Gemini 3.5 Flash
  (Medium/High/Low), Gemini 3.1 Pro (Low/High), Claude Sonnet 4.6 (Thinking), Claude
  Opus 4.6 (Thinking), GPT-OSS 120B (Medium). Tiny JSON probes:
  `GPT-OSS 120B (Medium)` returned exact clean JSON in 12.1s;
  `Gemini 3.5 Flash (High)` also answered in 10.9s (quota recovered by probe time).
- `tools/ai_manager.py:21-26` (verified): `antigravity_cli_work_models` entries are
  prepended to `default_models` in order — a second agy entry is tried after Flash
  fails and before DeepSeek, with no code change.
- `tests/tools/test_ai_manager.py:140-150` (verified):
  `test_antigravity_has_per_model_timeout` asserts **exactly one** antigravity_cli
  entry with timeout 150.0 — Finding 27 must update this test.

What this run set confirmed is working (no action):
- Finding 23 first-pass chunking: `AN3.13_p1` (3 chunks) and `MN119_p2` (6 chunks) both
  stayed under the argv guard; `TH180`/`DHP180`/`SN22.1_p2` used the single path.
- Finding 19 salvage-merge and the reformat path (`DHP180`: wrong schema → reformat →
  0 unresolved).
- Finding 20 (150s timeout): `MN119_p2` chunk 3 succeeded at 154.55s — it would have
  died at the old 90s setting.
- Empty-response classification as provider failure (fallback statuses name the failed
  agy attempt and its duration).

Shared constraints for every finding:
- TDD: write the failing test first, run it, confirm it fails for the expected reason,
  then implement.
- Quality gates per changed file (all must pass before reporting completion):
  1. `uv run ruff check --fix <files>`
  2. `uv run ruff format <files>`
  3. `uv run pyright <files>`
  4. `uv run --with pyrefly pyrefly check --min-severity warn <files>`
  5. `uv run pytest <test file> -v`
- Never run bare `uv run pytest`. Always pass the specific test file path.
- Modern type hints, `Path` from pathlib, no `sys.path` hacks.
- Commit messages (prepared for the user, not committed by the agent) must reference
  `#197`.

Recommended order: 24 → live `AN3.13_p1` re-run → 25 → 27 (needs its own live smoke)
→ 26 only if the post-24/25 live evidence still shows >5 unresolved groups.

---

## Finding 24 — chunk the missing-scores retry into bounded batches (revives dropped Finding 21)

Status: IMPLEMENTED 2026-06-11. Impact: high. This
is the only finding that fixes the one concrete residual failure of the batch
(`AN3.13_p1`, 64 unresolved groups).

### Problem
The retry is a single `ai_manager.request` over ALL missing groups
(`translate_core.py:809-838`). `AN3.13_p1` live evidence: 89 groups / 302 unique keys /
170K-char prompt → Gemini Flash answered cleanly but scored only 77 keys. Finding 21
was dropped on the theory that dedupe + the DeepSeek 8,192-token cap raise had made
chunking unnecessary; `AN3.13_p1` shows a second failure mode the cap raise cannot fix:
voluntary partial coverage on large key lists. Bounded batches bound the *expected
output size* per request, which addresses both failure modes (DeepSeek truncation AND
Gemini under-coverage). All observed retry-size prompts ≤40KB completed through agy in
8–30s with full coverage.

### Files to change
- `exporter/analysis/translate_core.py` (implementation)
- `tests/exporter/analysis/test_translate_core.py` (tests)

### Exact current anchor (translate_core.py:806-838, verified 2026-06-11)
The block starts at `missing_groups = _find_missing_score_groups(analysis, scores_map)`
(line 806) and the retry request spans lines 809-838:
`missing_keys` aggregation → `_build_missing_scores_prompt(resolved_sentence,
missing_groups)` → single `ai_manager.request` → parse pipeline
(`_parse_ai_json` → `_normalize_ai_response` → `_coerce_flat_score_map` →
`scores_map.update`) → one `debug["retry_requests"].append({...})`.
`debug["retry_requests"]` is already a list (initialized at line 797) and already
supports one entry per batch.

### Implementation
1. Module-level constants next to `MAX_FIRST_CONTEXT_CHARS` (line 16):
```python
MAX_RETRY_CONTEXT_CHARS = 60_000
MAX_RETRY_BATCHES = 8
```
2. Add helper:
```python
def _batch_missing_groups(
    missing_groups: list[dict[str, Any]],
    max_chars: int,
) -> list[list[dict[str, Any]]]:
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_len = 0
    for group in missing_groups:
        group_len = len(
            json.dumps(group, ensure_ascii=False, separators=(",", ":"))
        )
        if current and current_len + group_len > max_chars:
            batches.append(current)
            current = []
            current_len = 0
        current.append(group)
        current_len += group_len
    if current:
        batches.append(current)
    return batches
```
   Greedy packing, never splits a group; a single oversized group forms its own batch.
3. Replace the entire `if missing_groups:` block (lines 809-838; everything from
   `missing_keys = [` through the closing `)` of the
   `debug["retry_requests"].append(...)` call) with this exact code — the per-batch
   interior is today's code verbatim except `missing_keys` → `batch_keys` and
   `missing_groups` → `batch`:
```python
    if missing_groups:
        batches = _batch_missing_groups(missing_groups, MAX_RETRY_CONTEXT_CHARS)
        skipped_batches = batches[MAX_RETRY_BATCHES:]
        if debug is not None and skipped_batches:
            debug["retry_skipped_groups"] = [
                group for batch in skipped_batches for group in batch
            ]
        for batch in batches[:MAX_RETRY_BATCHES]:
            batch_keys = [key for group in batch for key in group["missing_keys"]]
            retry_prompt = _build_missing_scores_prompt(resolved_sentence, batch)
            retry_response = ai_manager.request(
                prompt=retry_prompt,
                model=model,
                prompt_sys="Return only JSON with a flat `scores` object.",
            )
            retry_data: dict[str, Any] = {}
            retry_parse_error = ""
            if retry_response.content:
                retry_data, retry_parse_error = _parse_ai_json(retry_response.content)
                retry_data = _normalize_ai_response(retry_data)
                retry_data = _coerce_flat_score_map(retry_data, set(batch_keys))
                retry_scores = retry_data.get("scores", {})
                if isinstance(retry_scores, dict):
                    scores_map.update(retry_scores)
            if debug is not None:
                debug["retry_requests"].append(
                    {
                        "prompt": retry_prompt,
                        "raw_response": retry_response.content,
                        "status_message": retry_response.status_message,
                        "parsed_response": copy.deepcopy(retry_data),
                        "parse_error": retry_parse_error,
                        "missing_keys": batch_keys,
                    }
                )
```
4. Post-retry observability (serves this finding's own verification): immediately
   after the replaced block, before `debug["final_scores"]` (currently lines 840-841),
   add:
```python
    if debug is not None:
        debug["missing_score_groups_after_retry"] = _find_missing_score_groups(
            analysis, scores_map
        )
```
   This turns "unresolved groups after retry" — until now recomputed by hand in every
   prep session — into a first-class debug field. Note it is written even when
   `missing_groups` was empty (value `[]`), which is correct and gives every debug JSON
   the field.

Tradeoff to state before approval: `AN3.13_p1`-class paragraphs issue ~3 retry requests
instead of 1 (with Finding 25 landed: ~2) — more calls and wall time, buying actual AI
scores instead of heuristic fallback for the unresolved tail. Under-budget retries
(the common case) still produce exactly 1 request and byte-identical prompts.

### Tests (tests/exporter/analysis/test_translate_core.py)
Write FIRST, confirm red. Mirror the fixture pattern of
`test_translate_sentence_retries_missing_component_scores` (line 507) and the
constant-monkeypatch pattern of `test_translate_sentence_chunks_oversized_passage`
(line 412):
1. `test_batch_missing_groups_packs_by_size` — direct unit test: three groups whose
   serialized sizes force a split at a tiny budget → 2 batches partitioning the input
   in order; one oversized group alone → exactly 1 batch.
2. `test_translate_sentence_batches_oversized_retry(monkeypatch)` — monkeypatch
   `translate_core.MAX_RETRY_CONTEXT_CHARS` to a tiny value; first-pass FakeAIManager
   response scores nothing so all groups go to retry; assert ≥2 retry calls whose
   prompts partition the groups, all batch responses merged into final scores,
   `len(debug["retry_requests"]) >= 2`, and
   `debug["missing_score_groups_after_retry"] == []`.
   Expected red-state failure: a single retry call / missing
   `missing_score_groups_after_retry` key.
3. `test_translate_sentence_retry_batch_cap(monkeypatch)` — also monkeypatch
   `MAX_RETRY_BATCHES` to 1 with 2 batches' worth of groups → exactly 1 retry call and
   the second batch's groups present in `debug["retry_skipped_groups"]`.
4. Regression gate: the EXISTING retry tests (lines 507, 631, 696, 1393) must pass
   unchanged — single-batch behavior must remain byte-identical.

### Verification commands
```
uv run pytest tests/exporter/analysis/test_translate_core.py -v
uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
```
Live smoke: re-run `AN3.13` paragraph 1 with `--debug`; compare
`missing_score_groups_after_retry` count against the 2026-06-11 capture (64 unresolved).
Target: ≤5.

### Out of scope
- Trimming retry context fields (Finding 25).
- A second retry pass over leftovers (Finding 26).
- First-pass chunking (done, Finding 23).

---

## Finding 25 — trim example/source fields from the retry context

Status: IMPLEMENTED 2026-06-11. Impact: medium. Complements Finding 24 (fewer, faster batches);
does NOT replace it — trimming shrinks the *input*, but `AN3.13_p1` failed on voluntary
*output* under-coverage, which only batching bounds.

### Problem
`_build_missing_scores_prompt` (translate_core.py:454-481) serializes each missing
group verbatim, and `_find_missing_score_groups` (lines 398-416) copies `example_1`,
`source_1`, `example_2`, `source_2` into every option — full Pāḷi citation sentences.
Measured on `AN3.13_p1`: 169,143 chars with examples, 75,197 without (-55%). The retry
prompt instructs "Return JSON with a flat `scores` object… Do not translate again and
do not explain" — the disambiguators are `pos`/`grammar`/`meaning_1`/`meaning_combo`;
the examples were already available to the model during the first pass.

### Files to change
- `exporter/analysis/translate_core.py` (implementation)
- `tests/exporter/analysis/test_translate_core.py` (tests)

### Implementation
1. Module-level constant:
```python
_RETRY_OPTION_FIELDS = (
    "key",
    "id",
    "pali",
    "pos",
    "grammar",
    "meaning_1",
    "meaning_combo",
)
```
2. Add helper (place it directly above `_build_missing_scores_prompt`):
```python
def _trim_groups_for_retry(
    missing_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    trimmed: list[dict[str, Any]] = []
    for group in missing_groups:
        trimmed.append(
            {
                "word": group.get("word", ""),
                "context": group.get("context", ""),
                "missing_keys": group.get("missing_keys", []),
                "options": [
                    {
                        field: option.get(field, "")
                        for field in _RETRY_OPTION_FIELDS
                    }
                    for option in group.get("options", [])
                    if isinstance(option, dict)
                ],
            }
        )
    return trimmed
```
   It builds new dicts and never mutates the input —
   `debug["missing_score_groups_after_first_response"]` must keep the full groups.
   (Sharing the `missing_keys` list object with the input is acceptable; only option
   dicts are reduced.)
3. Call site depends on landing order:
   - If Finding 24 has landed: trim ONCE at the top of the retry block
     (`retry_groups = _trim_groups_for_retry(missing_groups)`) and feed `retry_groups`
     to `_batch_missing_groups` AND `_build_missing_scores_prompt`, so batch packing
     measures the trimmed size.
   - If implemented standalone: trim inside the retry block before
     `_build_missing_scores_prompt`.
4. No prompt-text change; only the serialized context shrinks.

Tradeoff to state before approval: the retry model loses example sentences as
disambiguation hints. Mitigation: grammar + meaning fields remain, the first pass
already saw the full data, and every fully-successful observed retry (≤40KB prompts)
would have been even smaller. If a live re-run shows retry quality regression
(scores present but wrong-option picks), revert is one call-site line.

### Tests (tests/exporter/analysis/test_translate_core.py)
Write FIRST, confirm red. Siblings: `test_missing_scores_prompt_specifies_score_object_format`
(line 1365) and `test_missing_scores_prompt_requires_contextual_meaning_for_decon_keys`
(line 1379):
1. `test_trim_groups_for_retry_drops_example_fields` — direct call: option with all 11
   fields → trimmed option has exactly `_RETRY_OPTION_FIELDS`; input dict unchanged.
2. `test_missing_scores_prompt_excludes_examples` — build the retry prompt via the
   production path from a group containing a distinctive `example_1` string → that
   string is absent from the prompt while `grammar` and `meaning_combo` values are
   present.

### Verification commands
Same gate set as Finding 24 (same two files).
Live smoke: re-run `AN3.13` paragraph 1 with `--debug`; check
`retry_requests[*].prompt` lengths (expect roughly half the per-batch size) and that
`missing_score_groups_after_retry` did not regress.

### Out of scope
- Trimming the FIRST-pass dictionary context (system prompt) — separate, riskier
  discussion; the first pass is where examples genuinely help scoring.
- Retry prompt wording.

---

## Finding 26 (conditional) — supplemental retry pass over post-retry leftovers

Status: IMPLEMENTED 2026-06-11 after the condition fired. CONDITION MET after Findings
24 and 25: the live `AN3.13_p1` run still showed 69 entries in
`missing_score_groups_after_retry`.

### Problem
Findings 24 and 25 bounded retry batch size and trimmed retry context, but the
post-Finding-25 live smoke still left 69 unresolved groups after retry. The retry path
currently gives each missing group one batched chance only. When the model returns a
valid but partial retry response, any missed groups immediately fall back to heuristic
selection. A single supplemental retry pass over only the leftovers preserves the
existing bounded batching while giving valid-but-partial model responses one recovery
opportunity.

### Files to change
- `exporter/analysis/translate_core.py` (implementation)
- `tests/exporter/analysis/test_translate_core.py` (tests)

### Exact current anchors (re-verified 2026-06-11)
- `translate_core.py:16-18`: `MAX_FIRST_CONTEXT_CHARS`,
  `MAX_RETRY_CONTEXT_CHARS`, and `MAX_RETRY_BATCHES` constants exist.
- `translate_core.py:444-461`: `_batch_missing_groups(...)` greedily packs retry
  groups by serialized JSON size.
- `translate_core.py:485-502`: `_trim_groups_for_retry(...)` removes example/source
  fields before retry batching and prompting.
- `translate_core.py:857-900`: retry flow computes `missing_groups`, writes
  `missing_score_groups_after_first_response`, trims and batches once, appends retry
  debug entries, then writes `missing_score_groups_after_retry`.
- `tests/exporter/analysis/test_translate_core.py:392-417`: helper fixtures
  `_analysis_with_missing_retry_keys(...)` and `_missing_keys_from_retry_prompt(...)`
  support focused retry tests.
- `tests/exporter/analysis/test_translate_core.py:420-516`: current retry-batching
  and batch-cap tests exercise the Finding 24 behavior that Finding 26 extends.

### Implementation
1. Extract the existing retry-batch request body into a private helper, placed near the
   retry prompt helpers:
```python
def _request_missing_score_retry_pass(
    *,
    resolved_sentence: str,
    missing_groups: list[dict[str, Any]],
    scores_map: dict[str, Any],
    ai_manager: AIManager,
    model: str | None,
    debug: dict[str, Any] | None,
    pass_number: int,
) -> list[dict[str, Any]]:
```
   It should:
   - trim groups with `_trim_groups_for_retry`;
   - batch with `_batch_missing_groups(..., MAX_RETRY_CONTEXT_CHARS)`;
   - request only `batches[:MAX_RETRY_BATCHES]`;
   - parse through the existing `_parse_ai_json` ->
     `_normalize_ai_response` -> `_coerce_flat_score_map` pipeline;
   - update `scores_map` from parsed retry scores;
   - append the existing retry debug fields to `debug["retry_requests"]`;
   - add `"pass": 2` only to supplemental-pass debug entries;
   - return groups skipped by the batch cap in this pass.
2. In `translate_sentence(...)`, replace the inline retry loop with:
   - pass 1 over the original `missing_groups`;
   - recompute leftovers with `_find_missing_score_groups(analysis, scores_map)`;
   - if leftovers remain, pass 2 over only those leftovers;
   - write `retry_skipped_groups` only for groups still skipped by the second/final
     pass, so the field does not list groups that were temporarily skipped by pass 1
     and then retried successfully in pass 2;
   - keep `missing_score_groups_after_retry` as the final post-pass-2 recomputation.
3. Do not add a loop beyond these two explicit passes.

Tradeoff: partial retry responses may now cost up to one extra bounded retry pass. The
common path where pass 1 resolves all groups remains a single retry pass, and the
supplemental pass only serializes the recomputed leftover groups.

### Tests
Write FIRST, confirm red.
1. `test_translate_sentence_runs_second_retry_pass_for_leftovers`:
   - use `_analysis_with_missing_retry_keys(["1_0", "2_0"])`;
   - first AI response has no scores;
   - retry pass 1 scores only `1_0`;
   - supplemental pass should prompt only for `2_0` and score it;
   - assert final scores are both 10, retry prompts are
     `[["1_0", "2_0"], ["2_0"]]`, `len(debug["retry_requests"]) == 2`,
     the second retry debug entry has `"pass": 2`, and
     `debug["missing_score_groups_after_retry"] == []`.
   Expected red-state failure: only one retry request is made and `2_0` remains
   unresolved.
2. Update `test_translate_sentence_retry_batch_cap` to reflect the new final-pass
   semantics. With `MAX_RETRY_BATCHES = 1` and three groups, pass 1 scores `1_0`, pass
   2 scores `2_0`, and only `3_0` remains in final `retry_skipped_groups` and final
   `missing_score_groups_after_retry`.
3. Existing retry tests must keep passing; especially the common single-pass retry tests
   should not get extra requests when pass 1 fully resolves the missing keys.

### Verification commands
```
uv run pytest tests/exporter/analysis/test_translate_core.py -v
uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
```
Live smoke: re-run `AN3.13` paragraph 1 with `--debug`; inspect
`retry_requests` for any `"pass": 2` entries and compare final
`missing_score_groups_after_retry` against the post-Finding-25 count of 69. Target:
<=5 unresolved groups.

Implementation outcome: the Finding 26 live smoke reached 0 unresolved groups after one
retry request, so the supplemental pass was not needed in that run. Focused unit tests
cover the second-pass behavior and final skipped-group semantics.

### Out of scope
- More than two retry passes.
- Changing retry prompt wording.
- Changing first-pass chunking, provider fallback order, or model selection.

---

## Finding 27 — add `GPT-OSS 120B (Medium)` as a second Antigravity work model

Status: IMPLEMENTED 2026-06-11. Impact: medium — keeps runs on the preferred agy provider when Gemini Flash hits its
quota wall, instead of dropping straight to DeepSeek. This answers the handoff's
"explore `agy models` and choose a suitable, non-overkill fallback" subtask.

### Problem
In `MN119_p2` chunks 4–6 and all of `SN22.1_p2`, Gemini Flash returned immediate empty
responses (~5s each; once 24.66s) — the quota-exhaustion signature noted in the
handoff. The fallback chain then leaves agy entirely. DeepSeek recovered correctness,
but every affected request lost preferred-provider quality, and during long batches the
exhaustion persists for the rest of the run.

### Model choice (from live `agy models` + probes, 2026-06-11)
- **`GPT-OSS 120B (Medium)` — chosen.** Different model family (most likely a separate
  quota pool), non-overkill, and the live probe returned exact clean JSON in 12.1s.
- Rejected: Gemini 3.5 Flash (Medium)/(Low) — same family, plausibly the same exhausted
  quota. Gemini 3.1 Pro — overkill per handoff guidance, likely tighter limits. Claude
  Sonnet/Opus (Thinking) — slow thinking models, overkill for JSON scoring.
- Rejected alternative approach: an in-process circuit breaker (skip agy after N
  consecutive empty responses). Saves only ~5–25s per call after exhaustion and adds
  state to `AIManager`; not worth it while the fallback chain works.

### Files to change
- `tools/ai_models.json` (implementation — one entry)
- `tests/tools/test_ai_manager.py` (test pins the chain)

### Exact current anchors (verified 2026-06-11)
- `tools/ai_models.json`: `antigravity_cli_work_models` is a one-entry list
  (`Gemini 3.5 Flash (High)`, delay 5, timeout 150).
- `tools/ai_manager.py:21-26`: work models are prepended to `default_models` in list
  order — no code change needed for a second entry.
- `tests/tools/test_ai_manager.py:140-150`
  (`test_antigravity_has_per_model_timeout`): asserts exactly ONE antigravity_cli entry
  with timeout 150.0. MUST be updated or it goes red.

### Implementation
1. TDD on the config test: rewrite `test_antigravity_has_per_model_timeout` to assert
   exactly two antigravity_cli entries, in order
   `["Gemini 3.5 Flash (High)", "GPT-OSS 120B (Medium)"]`, each with timeout 150.0 and
   appearing before any `deepseek` entry in `models["default"]`. Run it, confirm red.
2. Append to `antigravity_cli_work_models`:
```json
    {
      "provider": "antigravity_cli",
      "model": "GPT-OSS 120B (Medium)",
      "delay": 5,
      "timeout": 150
    }
```
3. No other change.

Tradeoffs and uncertainties to state before approval:
- If Antigravity quota is account-wide rather than per-model, the new entry also
  returns empty and each affected request waits an extra ~5–25s before DeepSeek. Revert
  is one JSON entry. The decisive evidence can only be gathered during a real
  exhaustion window: when Flash starts returning empty mid-batch, probe
  `agy --model "GPT-OSS 120B (Medium)" -p '<tiny JSON ask>'` and record whether it
  still answers.
- GPT-OSS 120B JSON reliability on real 100–250KB scoring prompts is unverified (the
  probe was tiny). The existing reformat/salvage/retry machinery is the safety net; the
  live smoke below is the test.
- When Flash fails for a NON-quota reason (transient error on one request), the run now
  gets a GPT-OSS first-pass instead of a DeepSeek one for that request — acceptable;
  both are non-preferred fallbacks.

### Verification commands
```
uv run pytest tests/tools/test_ai_manager.py -v
uv run ruff check --fix tests/tools/test_ai_manager.py
uv run ruff format tests/tools/test_ai_manager.py
uv run pyright tests/tools/test_ai_manager.py
uv run --with pyrefly pyrefly check --min-severity warn tests/tools/test_ai_manager.py
```
(The JSON file has no Python gates.)
Live smoke: run one mid-size passage with `--debug` and confirm normal Flash operation
is unchanged (statuses still name Flash). Full validation of the fallback itself
requires a quota-exhaustion window: re-run a passage when Flash returns empties and
check whether statuses show `antigravity_cli/GPT-OSS 120B (Medium)` succeeding before
any DeepSeek fallback.

### Out of scope
- Quota detection/classification inside `run_antigravity_print` (agy does not surface
  quota errors; nothing to parse).
- Circuit breaker / provider health state in `AIManager`.
- Changing `default_models` or the grounded chain.

---

## Observations recorded, no action proposed
- Heuristic-fallback quality for `AN3.13_p1`'s 64 unresolved groups was not assessed
  word-by-word — Finding 24 makes the question moot if the live re-run reaches ≤5.
- `MN119_p2` chunk 3 succeeded at 154.55s, just past the nominal 150s — the hard kill
  is timeout+10s, so this is within design, but Flash latency on ~250KB chunks sits
  close to the limit. No action unless timeouts recur.
- Pali grammar accuracy (old Finding 5) remains deferred — model-quality, not code.

## Session ordering and closure rules
1. APPROVED execution order (user approval 2026-06-11) was completed:
   **24 → live `AN3.13_p1` re-run → 25 → 27 → 26 after its condition fired.**
2. One finding per session. No remaining approved finding exists in this queue.
3. After each implemented finding, append a completed-issue entry to `handoff.md` in
   the existing format and mark the section here IMPLEMENTED with the date.
4. Keep `plan.md` stable — no checkboxes, no per-issue history there.
5. Prepare a draft commit message referencing `#197`; the user commits.
