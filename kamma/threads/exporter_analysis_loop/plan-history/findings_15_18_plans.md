# Detailed Implementation Plans: Findings 15–18

Status: proposed 2026-06-10; Finding 15 IMPLEMENTED 2026-06-10 as Issue 25; Finding 16
IMPLEMENTED 2026-06-10 as Issue 26; Finding 17 DROPPED 2026-06-10 — coverage sufficient
after 15+16; Finding 18 IMPLEMENTED 2026-06-11 as Issue 28. On 2026-06-10 the user
approved the execution queue in `handoff.md`
("Approved Execution Plan") covering Findings 15, 16, and 18 plus a live MN17 p2
measurement session. Execution order, session boundaries, and closure steps live in
`handoff.md`; this file is the authoritative code-level detail (anchors, helper code,
tests, design notes).
One finding per session unless the user explicitly overrides the one-issue rule.

These plans were written on 2026-06-10 from analysis of the requested live-debug prep set
(`TH70`, `DHP120`, `AN5.43_p1`, `MN17_p2`, `SN5.1_p2`). All code anchors were verified by
reading the actual source on that date. If an anchor does not match when you implement,
STOP and re-read the file — do not guess.

Evidence sources (verified with one-shot temp scripts, since deleted; re-derive with the
same JSON inspections if needed):
- `exporter/analysis/output/MN17_p2_ai_debug.json` —
  `missing_score_groups_after_first_response` has 303 groups (only 68 unique by
  `(word, missing_keys)`, 265 unique option keys); serialized group context is 568,228
  chars, deduplicated 151,329 chars; the single retry prompt was 569,777 chars; the agy
  retry succeeded in 30.90s but returned only 46 score entries (1,557 chars); 225 of 303
  groups have no key in `final_scores` (104 entries).
- `exporter/analysis/output/MN17_p2_ai_debug.json` first response — direct
  `deepseek-v4-flash` (after the argv guard rejected agy at 921,621 bytes) returned
  truncated JSON, `parse_error` = `Expecting ',' delimiter: line 211 column 28 (char 7279)`;
  ~7.3KB of content is consistent with the 2,048-token completion cap.
- `exporter/analysis/output/AN5.43_p1_ai_debug.json` — healthy contrast: 35 missing
  groups, 66 unique keys, 82,838-char retry prompt; the deepseek retry returned all 66
  entries (1,963 chars); all 35 groups resolved.
- `exporter/analysis/output/TH70_ai_debug.json` — `status_message` embeds the entire raw
  DeepSeek response dict, including ~6KB of `reasoning_content`, inside the
  `(after 2 failed attempt(s): ...)` suffix.
- `exporter/analysis/reports/*_study.md` for all five targets have non-empty
  `**Translation:**` and `**Literal Translation:**` lines.

What this run set also confirmed is working (no action):
- Issue 20 live-proved: TH70 auth prompt and AN5.43_p1 retry timeout were both classified
  as provider ERRORs and fell back instead of polluting content.
- Issue 22 live-proved: success statuses name the actual succeeding provider/model
  (e.g. `SUCCESS in 8.40s. deepseek/deepseek-v4-flash (200) (after 1 failed attempt(s): ...)`).
- Issue 24 live-proved: post-fix direct `deepseek-v4-flash` calls return real content
  (MN17_p2 first response, AN5.43_p1 retry).
- `SN5.1_p2` was a clean single-pass run; `DHP120` recovered fully via reformat + one retry.
- Wrong-schema first responses from agy remain frequent (3 of 5 runs needed reformat) —
  stays in the handoff's "observation only / do not redesign prompts" bucket.

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

Recommended order: 15 → 16 → live re-run of MN17 p2 → 18. Finding 17 was dropped after
the live MN17 p2 rerun showed sufficient retry coverage.

---

## Finding 15 — deduplicate missing-score groups before the retry prompt

Status: IMPLEMENTED 2026-06-10 as Issue 25.

Impact: high. Quality tradeoff: none — this removes exact duplicates only, so it is NOT
the deferred "example trimming / chunking" item.

### Problem
`_find_missing_score_groups` walks every token occurrence in the sentence analysis. Words
that repeat in a paragraph (e.g. formula words like `ca`, repeated `bhikkhu` forms) emit
one full group per occurrence, each carrying the complete option dicts including
`example_1`/`example_2` texts. MN17_p2: 303 groups but only 68 unique `(word, keys)`
pairs; the serialized context drops from 568,228 to 151,329 chars (-73%) by deduplication
alone. Scores are keyed by option `key`, and group resolution checks
`any(key in scores_map for key in option_keys)`, so one scored occurrence already
resolves every duplicate — the duplicates add prompt bytes and model workload for zero
information.

### Files to change
- `exporter/analysis/translate_core.py` (implementation)
- `tests/exporter/analysis/test_translate_core.py` (tests)

### Exact current anchor (translate_core.py:366, `_find_missing_score_groups`)
```python
def _find_missing_score_groups(
    analysis: list[dict[str, Any]],
    scores_map: dict[str, Any],
) -> list[dict[str, Any]]:
    missing_groups: list[dict[str, Any]] = []

    def inspect_group(
        word: str,
        options: list[dict[str, Any]],
        context: str,
    ) -> None:
        if not options:
            return
        option_keys = [
            option.get("key")
            for option in options
            if isinstance(option.get("key"), str)
        ]
        if option_keys and not any(key in scores_map for key in option_keys):
            missing_groups.append(
```

### Implementation
1. Add a `seen: set[tuple[str, tuple[str, ...]]] = set()` next to `missing_groups`.
2. In `inspect_group`, before appending, compute
   `signature = (word, tuple(option_keys))`; if `signature in seen`, skip the append
   (but still recurse into components as today); otherwise add to `seen` and append.
3. Do not change the group dict shape, the recursion, or the prompt builder.

Design notes (do not deviate):
- Deduplicate by `(word, tuple(option_keys))`, not key-set alone (68 vs 59 groups —
  nearly the same size win, but keeping per-word `context` intact is safer for the model).
- The dedup changes the user-visible missing-group count (e.g. MN17 would report 68
  instead of 303). That is more truthful, not a regression.
- `debug["missing_score_groups_after_first_response"]` will contain the deduplicated
  list. Acceptable; debug `missing_keys` lists currently repeat the same key up to ~18×.

### Tests (tests/exporter/analysis/test_translate_core.py)
Write FIRST, confirm red. Direct unit test on `_find_missing_score_groups` with a
synthetic analysis where the same word + option group appears twice:
```python
def test_find_missing_score_groups_deduplicates_repeated_words() -> None:
    option = {"key": "1_0", "pali": "ca", "pos": "ind"}
    token = {"word": "ca", "data": [[option]]}  # match real nesting from sibling tests
    analysis = [token, copy.deepcopy(token)]
    groups = _find_missing_score_groups(analysis, scores_map={})
    assert len(groups) == 1
```
Check the real nesting shape against existing fixtures in the file before writing (the
`data` structure is `list` of option groups; mirror a passing sibling test such as the
`sammāsambuddhassa` fixture rather than inventing a shape). Expected red-state failure:
`len(groups) == 2`.

Also assert an existing multi-group test still passes unchanged (distinct words must not
be merged).

### Verification commands
```
uv run pytest tests/exporter/analysis/test_translate_core.py -v
uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
```
Live smoke: re-run `MN17` paragraph 2 with `--debug`; compare
`missing_score_groups_after_first_response` count and retry prompt size against the
2026-06-10 capture.

### Out of scope
- Trimming example fields, chunking, prompt wording.

---

## Finding 16 — raise the DeepSeek completion cap for JSON score responses

Status: IMPLEMENTED 2026-06-10 as Issue 26.

Impact: high for large paragraphs routed to DeepSeek (argv-guard overflow and retry
fallback paths).

### Problem
`tools/ai_deepseek_manager.py` hardcodes `"max_tokens": 2048` and no caller overrides it.
A 2,048-token completion is ~7–8KB of JSON. MN17_p2's first response (direct
`deepseek-v4-flash`) truncated at char 7,279 with a JSON parse error; only the agy
reformat rescued the run. Even the deduplicated MN17 retry (265 unique keys ≈ ~8KB of
score entries) cannot fit in 2,048 tokens, so Finding 15 alone does not fix MN17-class
retries when DeepSeek answers them.

### Files to change
- `tools/ai_deepseek_manager.py` (implementation)
- `tests/tools/test_ai_deepseek_manager.py` (tests)

### Exact current anchor (tools/ai_deepseek_manager.py:92)
```python
        payload = {
            "model": current_model,  # Use the potentially defaulted model
            "max_tokens": 2048,
            "thinking": DISABLED_THINKING_MODE,
```

### Implementation
1. Add a module-level constant near `DISABLED_THINKING_MODE`:
   `DEFAULT_MAX_TOKENS = 8192`.
2. Use it in the payload: `"max_tokens": DEFAULT_MAX_TOKENS,`.
3. `payload.update(kwargs)` already lets explicit callers override; keep that behavior.

Design notes:
- VERIFY at implementation time the current `deepseek-v4-flash` maximum output tokens in
  the official DeepSeek API docs (historically `deepseek-chat` allowed up to 8,192 with a
  4,096 default; the v4 limit may differ). If the documented max is lower, use that max.
- Cost note: `max_tokens` is a cap, not a target; short responses cost the same as before.
- Follow the existing test pattern (`_CapturingDeepseekManager` captures the payload; see
  `test_request_disables_thinking_mode_by_default`).

### Tests (tests/tools/test_ai_deepseek_manager.py)
Write FIRST, confirm red:
```python
def test_request_uses_raised_max_tokens_default() -> None:
    manager = _CapturingDeepseekManager()
    manager.request(prompt="p", model="deepseek-v4-flash")
    assert manager.captured_payload["max_tokens"] == DEFAULT_MAX_TOKENS


def test_request_allows_explicit_max_tokens_override() -> None:
    manager = _CapturingDeepseekManager()
    manager.request(prompt="p", model="deepseek-v4-flash", max_tokens=512)
    assert manager.captured_payload["max_tokens"] == 512
```
(Adapt attribute names to the actual `_CapturingDeepseekManager` implementation.)
Expected red-state failure: captured `max_tokens` is 2048.

### Verification commands
```
uv run pytest tests/tools/test_ai_deepseek_manager.py -v
uv run ruff check --fix tools/ai_deepseek_manager.py tests/tools/test_ai_deepseek_manager.py
uv run ruff format tools/ai_deepseek_manager.py tests/tools/test_ai_deepseek_manager.py
uv run pyright tools/ai_deepseek_manager.py tests/tools/test_ai_deepseek_manager.py
uv run --with pyrefly pyrefly check --min-severity warn tools/ai_deepseek_manager.py tests/tools/test_ai_deepseek_manager.py
```
Live smoke (optional): small `deepseek-v4-flash` request returning valid JSON, as done for
Issue 24.

### Out of scope
- Per-model token budgets in `tools/ai_models.json`, streaming, other providers.

---

## Finding 17 — chunk the missing-scores retry into bounded batches

Status: DROPPED 2026-06-10 — coverage sufficient after 15+16.

Drop evidence: Session C reran `MN17` paragraph 2 after Findings 15+16 and measured
31 missing groups, one 54,498-character retry prompt, 88 parsed retry score entries, and
4 unresolved groups. This meets the approved drop rule (`<= 5` unresolved groups
absolute).

Impact: high for MN17-class paragraphs, but CONTINGENT — implement only if a live MN17 p2
re-run after Findings 15+16 still leaves substantial unresolved groups. This touches the
handoff's deferred "chunking" area and needs explicit, separate user approval.

### Problem
The retry is a single request regardless of size (`translate_core.py:649`,
`missing_groups` serialized whole into one `_build_missing_scores_prompt`). MN17_p2:
569,777-char retry prompt → agy answered with only 46 of 265 unique keys; 225 of 303
groups were never scored, so deterministic fallback selection (Issue 5 heuristics) chose
the displayed meaning for ~74% of flagged words. The handoff already notes MN17's "word
choices still need advanced-model review" — this is the mechanism.

### Files to change
- `exporter/analysis/translate_core.py` (implementation)
- `tests/exporter/analysis/test_translate_core.py` (tests)

### Approach (sketch — write exact anchors at implementation time)
1. Add a constant, e.g. `MAX_RETRY_CONTEXT_CHARS = 60_000` (AN5.43's fully-successful
   retry context was ~80K chars; stay under it with margin).
2. Add a helper `_batch_missing_groups(missing_groups, max_chars)` that greedily packs
   groups by their individual `json.dumps(..., separators=(",", ":"))` length, never
   splitting a group.
3. In the retry block, loop over batches: one `ai_manager.request` per batch with a
   per-batch `_build_missing_scores_prompt`, applying the existing
   `_parse_ai_json` → `_normalize_ai_response` → `_coerce_flat_score_map` →
   `scores_map.update` pipeline, and appending one `debug["retry_requests"]` entry per
   batch (the debug list already supports multiple entries).
4. Cap total batches (e.g. 8) to bound cost; report skipped groups in debug.

Tradeoff to state to the user before approval: large paragraphs will issue several retry
requests instead of one (MN17 deduplicated ≈ 151KB → ~3 batches). That is added time and
cost per run; it buys actual AI scores instead of heuristic fallback for most words.

### Tests
Mirror the existing retry tests' `FakeAIManager` call-counting pattern: a fixture whose
missing groups exceed the batch budget must produce two retry calls whose prompts
partition the groups, and `scores_map` must merge both responses. Direct unit test for
`_batch_missing_groups` boundary behavior.

### Out of scope
- Chunking the FIRST prompt, trimming examples, schema redesign (still deferred).

---

## Finding 18 (minor) — bound provider error payloads in status messages

Status: IMPLEMENTED 2026-06-11 as Issue 28.

Impact: cosmetic/debuggability. The TH70 first status message is ~7KB long because it
embeds an entire raw DeepSeek response dict (including all 2,048 reasoning tokens) inside
the failed-attempts suffix; this propagates into every later status line and debug JSON.

### Problem
`tools/ai_deepseek_manager.py` empty-content branch:
```python
            else:
                return AIResponse(
                    content=None,
                    status_message=f"{response_json}",
                )
```
`AIManager` then concatenates that status into its `(after N failed attempt(s): ...)`
suffix verbatim.

### Files to change
- `tools/ai_deepseek_manager.py` (implementation)
- `tests/tools/test_ai_deepseek_manager.py` (tests)

### Implementation
Replace the f-string dump with a compact composer, e.g.:
```python
MAX_ERROR_DETAIL_CHARS = 300
```
and in the empty-content branch build
`f"empty content (finish_reason={finish_reason}, usage={usage})"` plus a
`reasoning_content`/`content` excerpt truncated to `MAX_ERROR_DETAIL_CHARS` with an
ellipsis. Extract `finish_reason` from `choices[0]` defensively (`.get` chains). Keep the
full dict out of the status; `--debug` raw captures remain the place for full payloads.

Design notes:
- Do NOT touch `tools/ai_manager.py` — Issue 18/22 status composition is unit-covered and
  correct; the oversized detail originates in the provider manager.
- The truncated message must still contain `finish_reason` so a `length` exhaustion stays
  diagnosable from the status line alone (the Issue 24 trigger evidence relied on it).

### Tests (tests/tools/test_ai_deepseek_manager.py)
Write FIRST, confirm red: feed `_FakeResponse` JSON with empty `content`, a long
`reasoning_content`, and `finish_reason: "length"`; assert `response.content is None`,
`"finish_reason=length" in response.status_message`, and
`len(response.status_message) < 500`.

### Verification commands
Same file set and gates as Finding 16.

### Out of scope
- `tools/ai_manager.py`, other provider managers, debug capture contents.

---

## Session ordering and closure rules
1. Recommended order: 15 → 16 → live MN17 p2 re-run → 18. Finding 17 is dropped after
   Session C because the rerun left only 4 unresolved groups.
2. One finding per session by default; 15 and 16 touch disjoint files and may be batched
   ONLY if the user explicitly approves both.
3. After each implemented finding, append a completed-issue entry to `handoff.md` in the
   existing format and mark the section here IMPLEMENTED with the date.
4. Keep `plan.md` stable — no checkboxes, no per-issue history there.
5. Prepare a draft commit message referencing `#197`; the user commits.
