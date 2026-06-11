# Historical Implementation Record: Findings 40–44

Status: COMPLETE. The user approved all five findings on 2026-06-11, and they
were executed in order: **40 → 41 → 42 → 43 → 44**.

Finding 44 ran last on purpose: Findings 40–41 changed the recovery pipeline,
and the model-tier decision needed to be measured against the final pipeline,
not the older one.

This file is now a historical record, not an execution queue. Keep it because
it preserves evidence, implementation rationale, tests, validation commands,
and the tier-evaluation table needed for future analyzer improvements.

These plans were written on 2026-06-11 from analysis of the live prep-batch
debug artifacts (`TH215`, `DHP211`, `AN3.33_p1`, `MN41_p2`, `SN15.1_p2` — all
forced `antigravity_cli/Gemini 3.5 Flash (Low)`) plus full source reads of
`exporter/analysis/translate_core.py`, `tools/ai_antigravity_cli.py`, and
`exporter/analysis/README.md`. All code anchors were verified by reading the
actual source on 2026-06-11. If this record is used for future implementation,
re-read current source first and do not rely on old line numbers.

Historical shared constraints used for these findings:
- Behavior fixes used TDD where practical: write the failing test first, run it,
  confirm it fails for the expected reason, then implement.
- Quality gates per changed Python file:
  1. `uv run ruff check --fix <files>`
  2. `uv run ruff format <files>`
  3. `uv run pyright <files>`
  4. `uv run --with pyrefly pyrefly check --min-severity warn <files>`
  5. `uv run pytest <specific test files> -v`
- Never run bare `uv run pytest`; always pass the specific test file path.
- Modern type hints, `Path` from pathlib, no `sys.path` hacks.
- POSIX-compatible shell commands under zsh; temp probes under `temp/` only.
- Finding 44 has an explicit exception allowing `temp/tier_eval/` to persist
  until manual quality review is complete.

---

## Finding 40 — local salvage of structured wrong-schema first responses

Status: IMPLEMENTED 2026-06-11. Impact: high (deterministic key recovery replaces the
unreliable AI reformat call for the most common wrong-schema shapes; directly
reduces missing-score groups and retry passes).

### Problem (evidence from 2026-06-11 prep batch)
7 of 9 chunked first responses came back as valid JSON in a wrong schema. The
recurring shapes, read from `exporter/analysis/output/*_ai_debug.json`:

- **Shape A — flat word→key string map** (MN41 chunk 0, SN15.1 chunk 0):
  `{"atha": "2794_default", ...}`. Already salvaged locally by
  `_extract_word_key_map()` — no reformat needed. Works today.
- **Shape B — selection lists** (AN3.33 chunks 0–1, MN41 chunk 2, SN15.1
  chunks 2–3): a dict with a single list-valued key such as `disambiguation`,
  `sentence_analysis`, or `selected_meanings`, where each item is
  `{"word": ..., "selected_key": "29188_3", "lemma": ..., "meaning": ...}`.
  Variants observed: `selected_lemma_key` (string key) and `selected_id`
  (integer headword id). The option keys are real and valid — but the code
  does not recognize the list form, so each one costs an AI reformat call.
- **Shape C — word→gloss-dict map** (MN41 chunk 1, SN15.1 chunk 1):
  `{"seyyathā'pi": {"lemma": "seyyathāpi", "pos": "sandhi", "grammar": ...,
  "meaning": ...}}`. The `lemma` values match the analysis options' `lemma`
  field exactly (`"purisa 1"`, `"ta 1.1"`), so the key is recoverable by
  local lemma matching.

The AI reformat fallback is unreliable: SN15.1 chunk 1's reformat returned
`scores` keyed by **surface words** (`"bhikkhave"`, `"puriso"`, ...), which
`merge_ai_selections()` can never match. All 6 words fell into missing groups,
feeding the 277+285-key pass-1 retries and forcing a pass-2 retry.

Honest cost accounting: this does NOT reduce per-chunk AI call counts (the
compact path's translation-only follow-up replaces the reformat call). The
wins are deterministic key recovery, a much smaller follow-up prompt, and
fewer/smaller retry passes.

### Exact current anchors (verified 2026-06-11)
- `_extract_word_key_map`: `exporter/analysis/translate_core.py:291`
- `_collect_option_keys`: line 280
- `_handle_compact_map_response`: line 675
- `_request_first_pass`: line 807; the salvage decision point is line 856:
  `word_key_map = _extract_word_key_map(ai_data, analysis) if not parse_error else None`
- Analysis option fields available for matching: `key`, `id`, `lemma` (see
  `exporter/analysis/types.py` `AnalysisOption`).

### Files to change
- `exporter/analysis/translate_core.py`
- `tests/exporter/analysis/test_translate_core.py`

### Implementation

1. Add `_extract_structured_selection_map()` near `_extract_word_key_map`:
   ```python
   _SELECTION_LIST_KEYS = ("disambiguation", "sentence_analysis", "selected_meanings")
   _SELECTION_KEY_FIELDS = ("selected_key", "selected_lemma_key", "key")

   def _extract_structured_selection_map(
       ai_data: dict[str, Any],
       analysis: list[dict[str, Any]],
   ) -> tuple[dict[str, str], dict[str, str]] | None:
   ```
   Returns `(word_key_map, word_meaning_map)` or `None`. Rules:
   - Return `None` if `ai_data` is not a non-empty dict, or contains `scores`
     or `translation` (proper schema — leave alone).
   - **Shape B**: if `ai_data` has exactly one key from `_SELECTION_LIST_KEYS`
     whose value is a non-empty list of dicts, iterate items. For each item
     with a string `word`:
     - take the first present string field from `_SELECTION_KEY_FIELDS`; accept
       it only if it is in `_collect_option_keys(analysis)`;
     - else, if `selected_id` (or `id`) is an int, map it to a key only when
       exactly ONE top-level option for that token has that `id`; if zero or
       multiple match, skip the word (the retry pass still covers it);
     - capture `item.get("meaning")` into `word_meaning_map` when it is a
       non-empty string.
   - **Shape C**: if all (or most) values of `ai_data` are dicts containing a
     `lemma` string, treat keys as surface words. For each word, find the
     token in `analysis` whose `word` matches, then select the top-level
     option whose `lemma` equals the gloss `lemma`; only map on an unambiguous
     (exactly one) match. Capture `meaning` the same way.
   - Apply the same ≥50% guard `_extract_word_key_map` uses: return `None`
     when `len(matched) * 2 < len(candidate_items)` or nothing matched.

2. Wire into `_request_first_pass()` at line 856. Keep `_extract_word_key_map`
   first (Shape A), then try the new function:
   ```python
   word_key_map = _extract_word_key_map(ai_data, analysis) if not parse_error else None
   word_meanings: dict[str, str] = {}
   if word_key_map is None and not parse_error:
       structured = _extract_structured_selection_map(ai_data, analysis)
       if structured is not None:
           word_key_map, word_meanings = structured
   ```
   On success, route into the existing `_handle_compact_map_response()` flow.
   The reformat path remains the fallback for prose/truncated responses.

3. Extend `_handle_compact_map_response()` with a keyword-only parameter
   `word_meanings: dict[str, str] | None = None`. Before the translation-only
   request, pre-fill `word_key_scores[key]["contextual_meaning"]` from
   `word_meanings` (keyed by surface word, mapped through `word_key_map`).
   Meanings returned by the translation response keep overriding pre-filled
   values (existing assignment order already does this — verify, do not
   reorder). Existing callers pass nothing, so behavior is unchanged for
   Shape A.

4. Do not change `_extract_word_key_map`, retry logic, scoring, debug key
   names, or provider behavior.

### Tests — write FIRST, confirm red
Add to `tests/exporter/analysis/test_translate_core.py`, modeling fake
analysis data on the real debug shapes quoted above:

1. `test_structured_selection_disambiguation_list_with_selected_key` — Shape B
   with valid `selected_key` values → map returned with those keys.
2. `test_structured_selection_sentence_analysis_selected_lemma_key` — the
   `sentence_analysis` + `selected_lemma_key` variant is accepted.
3. `test_structured_selection_selected_id_unique_match` — integer
   `selected_id` maps to the only option with that id.
4. `test_structured_selection_selected_id_ambiguous_skipped` — two options
   share the id → that word is skipped, others still map.
5. `test_structured_selection_gloss_map_lemma_match` — Shape C maps via exact
   lemma match and captures `meaning`.
6. `test_structured_selection_gloss_map_ambiguous_lemma_skipped` — two options
   with the same lemma → word skipped.
7. `test_structured_selection_rejects_proper_schema` — input with
   `translation`/`scores` → `None`.
8. `test_structured_selection_low_match_ratio_returns_none` — under the ≥50%
   guard → `None`.
9. `test_first_pass_routes_structured_selection_to_compact_path` — stub
   AIManager whose first response is a Shape B payload; assert the second
   request is the translation-only prompt, no `reformat_*` debug keys are
   written, and the final scores contain the selected keys with score 10.
10. `test_compact_map_prefills_contextual_meaning_from_word_meanings` —
    pre-filled meaning appears when the translation response omits that word,
    and is overridden when the translation response provides it.

Run the specific new tests first and confirm they fail (missing function /
missing parameter) before implementing.

### Verification commands
```
uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pytest tests/exporter/analysis/test_translate_core.py -v
```

### Out of scope
- Top-level JSON *list* responses (json.loads returning a list). All observed
  evidence was dict-shaped; do not widen `_parse_ai_json` typing here.
- Changing the reformat prompt (Finding 41).
- Live AI probes (cost-bearing; Finding 44 covers live measurement).

---

## Finding 41 — include expected option keys in the reformat prompt

Status: IMPLEMENTED 2026-06-11. Impact: medium (hardens the residual reformat path that
Finding 40 does not cover — prose or truncated responses).

### Problem
`_build_reformat_prompt()` (translate_core.py:468) never tells the model which
keys are valid. That is exactly why the SN15.1 chunk-1 reformat invented
surface-word score keys that `merge_ai_selections()` cannot match.

### Exact current anchors (verified 2026-06-11)
- `_build_reformat_prompt`: line 468 (signature: `(sentence, prose_response)`)
- `_handle_reformat_response`: line 741 — does NOT currently receive
  `analysis`; its caller `_request_first_pass` (line 875) has it.

### Files to change
- `exporter/analysis/translate_core.py`
- `tests/exporter/analysis/test_translate_core.py`

### Implementation

1. Add a module-level constant `REFORMAT_KEYS_MAX_CHARS = 6000` next to
   `REFORMAT_MAX_CHARS`.
2. Add a helper `_word_keys_overview(analysis) -> str` that builds a compact
   JSON map of `{token word: [top-level option keys]}` (top-level only, no
   component keys), serialized with `separators=(",", ":")`. If the serialized
   string exceeds `REFORMAT_KEYS_MAX_CHARS`, return `""` (fall back to the
   current prompt without a keys list).
3. Change `_build_reformat_prompt(sentence, prose_response, word_keys_json: str = "")`:
   when `word_keys_json` is non-empty, append a block:
   `Valid option keys per word (keys in "scores" MUST come from these lists):`
   followed by the JSON. Keep all existing prompt text unchanged otherwise.
4. Pass `analysis` into `_handle_reformat_response()` (new keyword-only
   parameter) from `_request_first_pass`, compute the overview there, and
   forward it to `_build_reformat_prompt`. Keep all debug key names unchanged.

### Tests — write FIRST, confirm red
1. `test_build_reformat_prompt_includes_valid_keys_block` — with a small
   word-keys JSON, the prompt contains the MUST instruction and the keys.
2. `test_build_reformat_prompt_without_keys_unchanged` — empty string →
   no keys block (current text preserved).
3. `test_word_keys_overview_top_level_only` — component keys are excluded.
4. `test_word_keys_overview_oversize_returns_empty` — oversized analysis →
   `""`.

### Verification commands
Same five gates as Finding 40, same two files.

### Out of scope
- Changing retry prompts or the first-pass system prompt.
- Any salvage logic (Finding 40).

---

## Finding 42 — record `chunk_sentence` in chunk debug entries

Status: IMPLEMENTED 2026-06-11. Impact: low (auditability — debug `chunk_requests` entries
currently have no field identifying which sentence the chunk covered; this
analysis had to reverse-engineer it from `user_prompt`).

### Exact current anchors (verified 2026-06-11)
- `_request_first_pass` debug assignment block: translate_core.py:828-830
  (`debug["system_prompt"] = ...` / `debug["user_prompt"] = ...`).

### Files to change
- `exporter/analysis/translate_core.py` (one line)
- `tests/exporter/analysis/test_translate_core.py` (one test)

### Implementation
In the `if debug is not None:` block at lines 828-830, add
`debug["chunk_sentence"] = chunk_sentence`. Non-chunked runs will record the
full resolved sentence — harmless and consistent.

### Tests — write FIRST, confirm red
`test_first_pass_debug_records_chunk_sentence` — call `_request_first_pass`
with a stub AIManager and a debug dict; assert
`debug["chunk_sentence"] == chunk_sentence`.

### Verification commands
Same five gates, same two files.

### Out of scope
Any other debug schema changes.

---

## Finding 43 — fix `agy --list-models` in the analysis README

Status: IMPLEMENTED 2026-06-11. Impact: trivial (documentation correctness; previously
logged as NOTICED in handoff).

### Anchor (verified 2026-06-11)
`exporter/analysis/README.md:107`: "To check what models are currently
available, run `agy --list-models` or see". Local `agy` 1.0.7 reports
`--list-models` as unsupported; the working command is `agy models`.

### Files to change
- `exporter/analysis/README.md` (one line)

### Implementation
Replace `agy --list-models` with `agy models` on line 107. No Python gates
needed. Verify with:
```
grep -n "list-models" exporter/analysis/README.md
```
(expect no matches afterwards).

### Out of scope
Any other README content.

---

## Finding 44 — model-tier evaluation: minimum sufficient Gemini 3.5 Flash tier

Status: IMPLEMENTED 2026-06-11 (user explicitly accepted the live AI cost for this finding).
Impact: cost/quality decision — determine the minimum Antigravity tier
(`Low` / `Medium` / `High`) that reliably handles this task, so the default is
neither overpaying nor under-powered.

RUN LAST — after Findings 40–43 — so the measurements reflect the improved
recovery pipeline.

### Goal
Decide which of these is the necessary minimum default:
- `antigravity_cli/Gemini 3.5 Flash (Low)`
- `antigravity_cli/Gemini 3.5 Flash (Medium)`
- `antigravity_cli/Gemini 3.5 Flash (High)`

The user is willing to pay for a higher tier if Low systematically fails, but
wants the cheapest tier that meets the bar.

### Method (evidence-only; NO source code changes in this finding)
1. Benchmark targets — the same five used for the 2026-06-11 baseline, for
   comparability:
   | Target | stdin input |
   |---|---|
   | TH215 | `TH215\n` |
   | DHP211 | `DHP211\n` |
   | AN3.33 p1 | `AN3.33\n1\n` |
   | MN41 p2 | `MN41\n2\n` |
   | SN15.1 p2 | `SN15.1\n2\n` |
2. Matrix: 5 targets × 3 tiers = 15 runs (one run each initially). Command
   template per run:
   ```
   printf '<input>' | uv run python exporter/analysis/study_passage.py --debug --provider antigravity_cli --model "Gemini 3.5 Flash (<Tier>)"
   ```
3. After EACH run, copy the artifacts before the next run overwrites them:
   ```
   mkdir -p temp/tier_eval/<tier>
   cp exporter/analysis/output/<source>_ai_debug.json temp/tier_eval/<tier>/
   cp exporter/analysis/output/<source>_study.json temp/tier_eval/<tier>/
   cp exporter/analysis/reports/<source>_study.md temp/tier_eval/<tier>/
   cp exporter/analysis/reports/<source>_ai_raw.txt temp/tier_eval/<tier>/
   ```
4. Extract metrics per run from the debug JSON (jq), for example:
   ```
   jq '{chunks: (.chunk_requests | length // 0), reformats: ([.chunk_requests[]? | select(has("reformat_raw_response"))] | length), retries: (.retry_requests | length // 0), missing_first: (.missing_score_groups_after_first_response | length // 0), missing_after_retry: (.missing_score_groups_after_retry | length // 0), final_scores: (.final_scores | length // 0)}' <debug.json>
   ```
   Also record per-call wall times from the `SUCCESS in Xs` status messages
   and any hard failures (non-zero exit, timeouts, empty responses, missing
   artifacts). Note: with Finding 39 in place, failed runs still write debug
   JSON — collect it.
5. Record the full metrics table in this section (Implementation outcome) and
   a summary in `handoff.md`. The durable record is the table — raw artifacts
   in `temp/tier_eval/` are for the user's manual quality review.
6. Repeat policy: if a tier fails a target once, repeat that single run once
   to distinguish nondeterminism from systematic failure. Do not repeat whole
   tiers without user approval.

### Decision rule
The minimum sufficient tier is the lowest tier with:
1. zero hard failures across all five targets;
2. zero missing-score groups after retry on all five targets;
3. recovery overhead (reformat + retry call counts) not materially worse than
   the next tier up;
4. user-acceptable translation/grammar quality in the markdown reports —
   this part is subjective and is the USER's manual judgment, comparing
   `temp/tier_eval/<tier>/<source>_study.md` across tiers. Do not claim
   quality verdicts on the user's behalf.

### Guardrails
- Do not describe a run as a pure Antigravity success unless raw/debug
  statuses show the actual provider/model path (existing handoff rule).
- Antigravity may return immediate empty responses on quota exhaustion; treat
  repeated immediate empties as a possible quota window, pause, and report
  rather than burning the matrix.
- `temp/tier_eval/` is explicitly allowed to persist past the session end
  until the user finishes the manual quality review; tell the user it exists
  and ask before deleting. This is an approved exception to the temp-cleanup
  rule for this finding only.

### Implementation outcome - 2026-06-11

All runs were forced through `--provider antigravity_cli` with the named
`Gemini 3.5 Flash` tier. Raw logs and copied artifacts are in
`temp/tier_eval/`.

| Tier | Target | Attempt | Result | Calls | Chunks | Reformats | Retries | Missing first | Missing after retry | Final scores | Max call | Notes |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Low | TH215 | 1 | ok | 3 | 0 | 0 | 1 | 25 | 0 | 94 | 13.60s | compact map + translation, then retry |
| Low | DHP211 | 1 | ok | 3 | 0 | 0 | 1 | 6 | 0 | 43 | 14.81s | compact map + translation, then retry |
| Low | AN3.33 p1 | 1 | ok | 5 | 2 | 0 | 1 | 38 | 0 | 142 | 13.96s | two compact-map chunks |
| Low | MN41 p2 | 1 | ok | 9 | 3 | 3 | 3 | 63 | 0 | 408 | 16.89s | three reformat recoveries, all resolved |
| Low | SN15.1 p2 | 1 | ok | 11 | 4 | 1 | 3 | 96 | 0 | 487 | 29.79s | one reformat recovery, all resolved |
| Medium | TH215 | 1 | ok | 3 | 0 | 0 | 1 | 25 | 0 | 94 | 18.72s | compact map + translation, then retry |
| Medium | DHP211 | 1 | ok | 3 | 0 | 0 | 1 | 6 | 0 | 43 | 21.05s | compact map + translation, then retry |
| Medium | AN3.33 p1 | 1 | ok | 5 | 2 | 0 | 1 | 35 | 0 | 128 | 55.88s | second chunk slow but completed |
| Medium | MN41 p2 | 1 | failed | 5 | 3 attempted | 2 | 0 | n/a | n/a | n/a | 158.33s | partial timeout on chunk 1, hard timeout on chunk 3 |
| Medium | MN41 p2 | 2 | failed | 3 | 2 attempted | 0 | 0 | n/a | n/a | n/a | 160.07s | hard timeout on chunk 2 |
| Medium | SN15.1 p2 | 1 | failed | 3 | 2 attempted | 1 | 0 | n/a | n/a | n/a | 158.06s | hard timeout on chunk 2 |
| Medium | SN15.1 p2 | 2 | failed | 3 | 2 attempted | 1 | 0 | n/a | n/a | n/a | 153.37s | hard timeout on chunk 2 |
| High | TH215 | 1 | ok | 3 | 0 | 1 | 1 | 24 | 0 | 94 | 21.35s | first response needed reformat |
| High | DHP211 | 1 | ok | 3 | 0 | 0 | 1 | 6 | 0 | 43 | 30.08s | compact map + translation, then retry |
| High | AN3.33 p1 | 1 | ok | 5 | 2 | 0 | 1 | 35 | 0 | 128 | 112.48s | second chunk very slow but completed |
| High | MN41 p2 | 1 | failed | 5 | 3 attempted | 1 | 0 | n/a | n/a | n/a | 157.87s | hard timeout on chunk 3 |
| High | MN41 p2 | 2 | ok | 6 | 3 | 1 | 1 | 15 | 0 | 242 | 145.80s | succeeded on allowed repeat, but very slow |
| High | SN15.1 p2 | 1 | failed | 7 | 4 attempted | 1 | 0 | n/a | n/a | n/a | 82.56s | empty response on chunk 4 |
| High | SN15.1 p2 | 2 | failed | 1 | 1 attempted | 0 | 0 | n/a | n/a | n/a | 7.89s | repeated immediate empty response; live calls stopped |

Automated reliability outcome before manual markdown quality review:
- Low is the only tier with zero hard failures across all five targets.
- Low also had lower worst-call latency than Medium or High in this run.
- Medium is disqualified by repeated hard timeouts on both large targets.
- High is disqualified by repeated empty-response failure on `SN15.1 p2`, even
  though `MN41 p2` succeeded on its allowed repeat.

Recommendation from automated evidence: keep `Gemini 3.5 Flash (Low)` as the
minimum sufficient default unless manual review of the markdown reports shows
unacceptable quality. Do not change `tools/ai_models.json` in this finding.

### Out of scope
- Changing `tools/ai_models.json` defaults — that is a follow-up decision the
  user makes after seeing the table.
- Evaluating non-Antigravity providers or GPT-OSS (quota-window evidence for
  GPT-OSS remains a separate standing note in handoff).

---

## Historical closure
- Findings 40-44 are complete and no longer form an active queue.
- `handoff.md` should keep only the useful historical summary and future
  improvement evidence.
- Keep `plan.md` stable — no checkboxes, no per-issue history there.
- If future work is derived from this record, create a new focused plan and get
  explicit user approval before implementation.
