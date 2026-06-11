# Detailed Implementation Plans: Findings 31–39

Status: APPROVED by the user on 2026-06-11 and tightened in a follow-up planning
pass on 2026-06-11. Execute the corrected queue in this order:
**32 → 37 → 31 → 33 → 34 → 35 → 36 → 39**. Finding 38 is merged into
Finding 35 and must not be executed separately.

Execute ONE finding per session unless the user explicitly overrides the
one-issue rule. At the start of each session, pick the first finding in the
corrected order above not yet marked IMPLEMENTED. Do not rely on numeric order.

These plans were written on 2026-06-11 from post-implementation analysis of
findings 11–30, source code review of all `exporter/analysis/` modules and
`tools/ai_*.py`, test coverage audit of `tests/exporter/analysis/` and
`tests/tools/`, and inspection of live debug artifacts from two prep batches.
All code anchors below were verified by reading the actual source on 2026-06-11.
If an anchor does not match when you implement, STOP and re-read the file — do
not guess.

Shared constraints for every finding:
- For behavior fixes, use TDD: write the failing test first, run it, confirm it
  fails for the expected reason, then implement.
- For coverage-only, type-only, or refactor-only findings, use characterization
  tests or existing tests as the safety net. Do not pretend an existing-behavior
  test is a red test unless it genuinely fails before the source edit.
- Quality gates per changed Python file (all must pass before reporting
  completion):
  1. `uv run ruff check --fix <files>`
  2. `uv run ruff format <files>`
  3. `uv run pyright <files>`
  4. `uv run --with pyrefly pyrefly check --min-severity warn <files>`
  5. `uv run pytest <specific test files> -v`
- Never run bare `uv run pytest`. Always pass the specific test file path.
- Modern type hints, `Path` from pathlib, no `sys.path` hacks.
- POSIX-compatible shell commands (the agent shell is zsh); temp probes under
  `temp/` only, deleted before the final response.
- Prepare a draft commit message referencing `#197`; the user commits.
- DO NOT edit files beyond the approved scope.
- If source anchors have drifted, stop and re-read the relevant file before
  implementing. Do not guess from stale line numbers.

---

## Finding 31 — expand `analyzer.py` unit test coverage

Status: IMPLEMENTED 2026-06-11. Impact: high (data quality foundation — the module that
builds analysis groups from tokens feeds everything downstream).

### Problem
`exporter/analysis/analyzer.py` (843 lines) has three existing test files
(`test_analyzer.py` with 6 integration tests, `test_analysis_analyzer.py` with
6 unit tests, `test_analyze_sentence.py` with 4 integration tests), but several
important helper functions have **zero unit tests**:
- `get_completeness(i: DpdHeadword)` — no return type annotation, untested
- `root_combo(i: DpdHeadword)` — no return type annotation, untested
- `is_stem_compatible(grammar_string: str) -> bool` — untested
- `get_in_comp_forms(inflections_html: str) -> set[str]` — untested
- `get_grammar_from_inflections_html(form, headword) -> str | None` — untested
- `is_pos_compatible(hw_pos, grammar_pos, grammar_string)` — untested as a unit

These are pure functions (or only need a mock DpdHeadword) — they do not require
a database.

### Exact current anchors (verified 2026-06-11)
- `get_completeness`: line 639. No return annotation. Returns `(int, str)`.
- `root_combo`: line 835. No return annotation. Returns `str`.
- `is_stem_compatible`: line 271. Has return annotation `-> bool`.
- `get_in_comp_forms`: line 196. Has return annotation `-> set[str]`.
- `get_grammar_from_inflections_html`: line 206. Has return annotation
  `-> str | None`.
- `is_pos_compatible`: line 152. Has return annotation `-> bool`.
- Existing test: `tests/exporter/analysis/test_analysis_analyzer.py` tests
  `_normalize_kammadharaya_construction` and `tokenize_sentence` only.

### Files to change
- `exporter/analysis/analyzer.py` (add return type annotations to
  `get_completeness` and `root_combo` — NO other changes)
- `tests/exporter/analysis/test_analysis_analyzer.py` (add unit tests)

### Implementation

1. Add return type annotations (the only source changes):
   - `get_completeness(i: DpdHeadword) -> tuple[int, str]:` (line 639)
   - `root_combo(i: DpdHeadword) -> str:` (line 835)

2. Add the following test functions to
   `tests/exporter/analysis/test_analysis_analyzer.py`:

   **`test_get_completeness_complete`** — mock DpdHeadword with
   `meaning_1="test"` and `source_1="SN1.1"`. Assert returns `(2, "complete")`.

   **`test_get_completeness_semi_complete`** — mock with `meaning_1="test"` and
   `source_1=""`. Assert returns `(1, "semi-complete")`.

   **`test_get_completeness_incomplete`** — mock with `meaning_1=""`. Assert
   returns `(0, "incomplete")`.

   **`test_root_combo_with_root`** — mock DpdHeadword with `rt` attribute set
   (mock DpdRoot with `root_group="1"`, `root_meaning="to go"`), `root_clean=
   "√gam"`, `root_sign="gacchati"`. Assert returns
   `"√gam 1 gacchati (to go)"`.

   **`test_root_combo_without_root`** — mock with `rt=None`. Assert returns
   `""`.

   **`test_is_stem_compatible_in_comp`** — assert
   `is_stem_compatible("masc in comp") == True`.

   **`test_is_stem_compatible_inflected`** — assert
   `is_stem_compatible("masc nom sg") == False`.

   **`test_is_stem_compatible_no_case`** — assert
   `is_stem_compatible("adj") == True`.

   **`test_get_in_comp_forms_found`** — HTML with `in comps</th><td>...dhamma
   buddha...</td></tr>`. Assert returns `{"dhamma", "buddha"}`.

   **`test_get_in_comp_forms_not_found`** — HTML without `in comps`. Assert
   returns `set()`.

   **`test_get_grammar_from_inflections_html_found`** — HTML with a `<td
   title='masc acc sg'>` cell containing the form `dhammaṃ`. Mock headword with
   `lemma_clean="dhamma"`, `inflections_html=...`. Assert returns
   `"masc acc sg of dhamma"`.

   **`test_get_grammar_from_inflections_html_not_found`** — form not in HTML.
   Assert returns `None`.

   **`test_is_pos_compatible_exact_match`** — `is_pos_compatible("masc",
   "masc")` → `True`.

   **`test_is_pos_compatible_noun_gender`** — `is_pos_compatible("masc",
   "noun")` → `True`.

   **`test_is_pos_compatible_verb_tense`** — `is_pos_compatible("aor", "verb")`
   → `True`.

   **`test_is_pos_compatible_mismatch`** — `is_pos_compatible("masc", "verb")`
   → `False`.

### Tests — write FIRST
These are characterization tests plus an annotation check. Existing-behavior
helper tests are expected to pass before the source edit; they document behavior
and protect against regression. The annotation check should fail before the
source edit.

Add this annotation-specific test:
- **`test_helper_return_annotations_present`** — use
  `typing.get_type_hints()` on `get_completeness` and `root_combo`. Assert:
  - `get_type_hints(get_completeness)["return"] == tuple[int, str]`
  - `get_type_hints(root_combo)["return"] is str`

Then add the helper behavior tests listed above. Run
`uv run pytest tests/exporter/analysis/test_analysis_analyzer.py -v -k helper_return_annotations_present`
and confirm it fails before adding the return annotations. After adding the
annotations, run the full test file.

### Verification commands
```
uv run ruff check --fix exporter/analysis/analyzer.py tests/exporter/analysis/test_analysis_analyzer.py
uv run ruff format exporter/analysis/analyzer.py tests/exporter/analysis/test_analysis_analyzer.py
uv run pyright exporter/analysis/analyzer.py tests/exporter/analysis/test_analysis_analyzer.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/analyzer.py tests/exporter/analysis/test_analysis_analyzer.py
uv run pytest tests/exporter/analysis/test_analysis_analyzer.py -v
```

### Implementation outcome
- Added the annotation red test and helper characterization tests to
  `tests/exporter/analysis/test_analysis_analyzer.py`.
- Red check failed as expected before the source edit:
  `uv run pytest tests/exporter/analysis/test_analysis_analyzer.py -v -k helper_return_annotations_present`
  failed with `KeyError: 'return'`.
- Added only the planned return annotations in `exporter/analysis/analyzer.py`.
- Final local checks passed:
  - `uv run ruff check --fix exporter/analysis/analyzer.py tests/exporter/analysis/test_analysis_analyzer.py`
  - `uv run ruff format exporter/analysis/analyzer.py tests/exporter/analysis/test_analysis_analyzer.py`
  - `uv run pyright exporter/analysis/analyzer.py tests/exporter/analysis/test_analysis_analyzer.py`
  - `uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/analyzer.py tests/exporter/analysis/test_analysis_analyzer.py`
  - `uv run pytest tests/exporter/analysis/test_analysis_analyzer.py -v`
    (`23 passed`)

### Out of scope
- Any changes to `analyzer.py` logic, algorithm, or data flow.
- Tests that require a live DB session (those already exist in
  `test_analyzer.py` and `test_analyze_sentence.py`).
- The `search_inflections_for_form` full-table-scan concern (performance, not
  correctness — may be a future finding).
- Findings 32–38.

---

## Finding 32 — expand `ai_manager.py` test coverage for rate-limiting and edge cases

Status: IMPLEMENTED 2026-06-11. Impact: high (the central routing component has 8 tests
but the rate-limiting loop, grounding path, missing-provider skip, and
all-fail path are untested).

Execution note: run this before Finding 37. It establishes characterization
coverage for the current routing behavior and gives Finding 37 a safer base.

### Problem
`tests/tools/test_ai_manager.py` (171 lines, 8 tests) covers:
- per-model timeout passthrough
- clean success status naming
- success-after-failure status
- provider detail handling
- model ordering

But it does NOT cover:
- The rate-limiting pre-loop (lines 164-180) sleeping for each model
- The `grounding=True` path (line 153-154)
- The `provider not in self.providers` skip (line 184-185)
- The all-providers-fail path (line 238-240)
- Provider raising an exception (line 230-236)
- The `provider_preference and model` forced path with a missing provider

### Exact current anchors (verified 2026-06-11)
- Rate-limit loop: lines 164-180 (`for model_tuple in models_to_try`)
- Grounding path: lines 153-154 (`if grounding:`)
- Provider skip: lines 184-185 (`if provider_name not in self.providers`)
- All-fail: lines 238-240 (`final_failure_message`)
- Exception catch: lines 230-236
- `_make_manager` helper: lines 32-44 (existing test helper)

### Files to change
- `tests/tools/test_ai_manager.py` (add tests only)

### Tests — write FIRST

1. **`test_request_all_providers_fail_returns_none_content`** — build a manager
   with only `_FailingProvider`. Assert `response.content is None` and
   `"All AI providers failed"` in `response.status_message`.

2. **`test_request_provider_exception_is_caught_and_reported`** — create a
   `_RaisingProvider` stub whose `request()` raises `RuntimeError("boom")`.
   Build a manager with it as the only provider. Assert
   `response.content is None` and `"boom"` in `response.status_message`.

3. **`test_request_skips_missing_provider`** — build a manager with
   `DEFAULT_MODELS=[("nonexistent", "m", 0, 150.0), ("stub", "stub-model", 0,
   150.0)]` and only `providers={"stub": provider}`. Assert the stub provider
   receives the call and succeeds.

4. **`test_request_grounding_uses_grounded_models`** — build a manager with
   `GROUNDED_MODELS=[("stub", "grounded-model", 0, 150.0)]` and
   `DEFAULT_MODELS=[]`. Call `request(prompt="hi", grounding=True)`. Assert
   success and `"grounded-model"` in `response.status_message`.

5. **`test_request_forced_model_bypasses_default_chain`** — extend
   `_RecordingProvider` so it records each call's kwargs. Build a manager with
   `DEFAULT_MODELS` containing a failing provider first, but also
   `providers={"forced": recording_provider}`. Call `request(prompt="hi",
   provider_preference="forced", model="custom-m")`. Assert:
   - the recording provider is called once
   - the recorded `model` kwarg is `"custom-m"`
   - the failing/default provider is not called

6. **`test_request_forced_missing_provider_returns_failure`** — build a manager
   with no `"missing"` provider. Call `request(prompt="hi",
   provider_preference="missing", model="custom-m")`. Assert
   `response.content is None` and `"All AI providers failed"` appears in the
   status. This documents the current forced-missing-provider behavior before
   any later routing changes.

### Verification commands
```
uv run ruff check --fix tests/tools/test_ai_manager.py
uv run ruff format tests/tools/test_ai_manager.py
uv run pyright tests/tools/test_ai_manager.py
uv run --with pyrefly pyrefly check --min-severity warn tests/tools/test_ai_manager.py
uv run pytest tests/tools/test_ai_manager.py -v
```

### Out of scope
- Any changes to `ai_manager.py` source code.
- The rate-limit bug fix (Finding 37).
- Type hint fixes in `ai_manager.py` (Finding 37).
- Remaining queue findings.

---

## Finding 33 — expand `example_bolding.py` test coverage

Status: IMPLEMENTED 2026-06-11. Impact: medium (only 3 of 5+ strategies in
`bold_component_in_token` tested; `bold_word_in_verse`, `collect_all_ids`,
`bold_word_toplevel` all untested).

### Problem
`tests/exporter/analysis/test_example_bolding.py` (53 lines, 3 tests) only
covers the exact-match fallback path — the mock DB returns `None` for headword
lookups, so database-inflection matching is never exercised. The
sandhi/apostrophe path, stem/final-ṃ fallbacks, whole-token fallback,
`bold_word_toplevel`, `bold_word_in_verse`, `collect_all_ids`, and
`_verse_tokens` have no direct tests.

### Exact current anchors (verified 2026-06-11)
- `bold_component_in_token`: line 95, multiple ordered strategies:
  database inflections, exact match, apostrophe/sandhi fallback, final-ṃ strip,
  stem match, whole-token fallback
- `bold_word_toplevel`: not in current visible range, wraps whole token in
  `<b>` tags
- `bold_word_in_verse`: not in current visible range, finds and bolds a token
  in a verse string
- `collect_all_ids`: not in current visible range, recursively collects
  headword IDs from option trees
- `_verse_tokens`: line 33, tokenizes verse preserving apostrophes
- `_get_db_inflections`: line 13, DB lookup
- Existing mock helper: `_mock_session()` at line 8

### Files to change
- `tests/exporter/analysis/test_example_bolding.py` (add tests only)

### Tests — write FIRST

1. **`test_bold_component_strategy_0_db_inflections`** — mock session where
   headword query returns a headword with `inflections_list=["yogaṃ", "yogā",
   "yoga"]`. Call `bold_component_in_token("yogācaraṇa", "yoga", 54211,
   session, is_first_component=True)`. Assert db inflection `"yogā"` is found
   and bolded: `"<b>yogā</b>caraṇa"`.

2. **`test_bold_component_apostrophe_fallback`** — call
   `bold_component_in_token("ajj'uposatho", "uposatha", 99999,
   _mock_session(), is_first_component=False)`. Assert apostrophe handling
   yields `"ajj'<b>uposatho</b>"`.

3. **`test_bold_component_fallback_whole_token`** — call with a
   component_pali that is NOT a substring of apos_token and mock returns no
   inflections. Assert the whole token is bolded.

4. **`test_verse_tokens_basic`** — `_verse_tokens("namo tassa bhagavato")` →
   `["namo", "tassa", "bhagavato"]`.

5. **`test_verse_tokens_apostrophe`** — `_verse_tokens("ajj'uposatho aho")` →
   `["ajj'uposatho", "aho"]`.

6. **`test_bold_word_toplevel`** — `bold_word_toplevel("dhamma")` → `"<b>dhamma</b>"`.

7. **`test_collect_all_ids_flat_option`** — build an option dict with
   `id=12345`, no components. Assert `collect_all_ids(option, ...)` returns a
   list containing the ID tuple.

8. **`test_collect_all_ids_nested_components`** — build an option with
   components containing sub-options. Assert IDs from all nesting levels are
   returned.

### Verification commands
```
uv run ruff check --fix tests/exporter/analysis/test_example_bolding.py
uv run ruff format tests/exporter/analysis/test_example_bolding.py
uv run pyright tests/exporter/analysis/test_example_bolding.py
uv run --with pyrefly pyrefly check --min-severity warn tests/exporter/analysis/test_example_bolding.py
uv run pytest tests/exporter/analysis/test_example_bolding.py -v
```

### Implementation outcome
- Added characterization tests only in
  `tests/exporter/analysis/test_example_bolding.py`; no
  `exporter/analysis/example_bolding.py` source changes were needed.
- Covered database-inflection matching, apostrophe fallback, final-ṃ fallback,
  stem fallback, whole-token fallback, `_verse_tokens`, `bold_word_toplevel`,
  `bold_word_in_verse`, and flat/nested `collect_all_ids`.
- Final local checks passed:
  - `uv run ruff check --fix tests/exporter/analysis/test_example_bolding.py`
  - `uv run ruff format tests/exporter/analysis/test_example_bolding.py`
  - `uv run pyright tests/exporter/analysis/test_example_bolding.py`
  - `uv run --with pyrefly pyrefly check --min-severity warn tests/exporter/analysis/test_example_bolding.py`
  - `uv run pytest tests/exporter/analysis/test_example_bolding.py -v`
    (`14 passed`)

### Out of scope
- Any changes to `example_bolding.py` source code.
- Remaining queue findings.

---

## Finding 34 — TypedDict for analysis group and option shapes

Status: IMPLEMENTED 2026-06-11. Impact: medium (type safety for the untyped `dict` objects
passed between `analyzer.py`, `translate_core.py`, `study_passage.py`, and
`export_words_csv.py`).

### Problem
Analysis groups are untyped `dict[str, Any]` objects. The shape is implicit —
you have to read the code to know what keys exist. Key typos are caught at
runtime only. `pyright` cannot verify access patterns.

### Current shapes (verified 2026-06-11)
From `analyzer.py` `get_word_details` (line 392-412 for compound path,
542-562 for grammar path):
```python
{
    "key": str,           # e.g. "12345_0", "12345_default", "decon_token_0"
    "id": int | str,      # headword ID or "" for missing/decon
    "lemma": str,         # optional: present in hw entries, absent in decon/missing
    "degree_of_completion": str,  # optional: "complete"/"semi-complete"/"incomplete"
    "score": int,         # optional: 0/1/2
    "pali": str,          # the token form
    "pos": str,           # part of speech
    "grammar": str,       # grammar description
    "meaning_1": str,     # optional: primary meaning
    "meaning_combo": str, # combined meaning
    "compound_type": str, # optional
    "compound_construction": str,  # optional
    "root_key": str,      # optional
    "construction": str,  # construction/deconstruction
    "example_1": str,     # optional
    "source_1": str,      # optional
    "example_2": str,     # optional
    "source_2": str,      # optional
    "components": list,   # recursive list[list[AnalysisOption]]
}
```
The top-level analysis result from `analyze_sentence` (line 830):
```python
{"word": str, "status": str, "data": list[AnalysisOption]}
```

### Files to change
- `exporter/analysis/types.py` (NEW file — TypedDict definitions)
- `exporter/analysis/analyzer.py` (type annotations on return values and
  function parameters — NO logic changes)

### Implementation

1. Create `exporter/analysis/types.py`:
```python
"""Type definitions for the Pāḷi analysis pipeline."""

from typing import TypedDict


class AnalysisOption(TypedDict, total=False):
    key: str
    id: int | str
    lemma: str
    degree_of_completion: str
    score: int
    pali: str
    pos: str
    grammar: str
    meaning_1: str
    meaning_combo: str
    compound_type: str
    compound_construction: str
    root_key: str
    construction: str
    example_1: str
    source_1: str
    example_2: str
    source_2: str
    components: list[list["AnalysisOption"]]


class AnalysisResult(TypedDict):
    word: str
    status: str
    data: list[AnalysisOption]
```

2. In `exporter/analysis/analyzer.py`, add the import and annotate return
   types — **NO logic changes**:
   - `get_word_details(...) -> list[AnalysisOption]:` (line 324)
   - `analyze_sentence(...) -> list[AnalysisResult]:` (line 748)
   - `get_components_from_construction(...) -> list[list[AnalysisOption]]:`
     (line 655)

### Tests
No new functional tests needed — this is a type-only change. Verify with
pyright and pyrefly that the existing code satisfies the new annotations.

### Verification commands
```
uv run ruff check --fix exporter/analysis/types.py exporter/analysis/analyzer.py
uv run ruff format exporter/analysis/types.py exporter/analysis/analyzer.py
uv run pyright exporter/analysis/types.py exporter/analysis/analyzer.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/types.py exporter/analysis/analyzer.py
uv run pytest tests/exporter/analysis/test_analysis_analyzer.py tests/exporter/analysis/test_analyzer.py -v
```

### Implementation outcome
- Added `exporter/analysis/types.py` with `AnalysisOption` and `AnalysisResult`
  TypedDict definitions.
- Annotated `get_word_details()`, `get_components_from_construction()`, and
  `analyze_sentence()` with the new types.
- Added minimal internal helper annotations in `analyzer.py` so the new return
  types pass Pyright's invariant list checks.
- Used local casts where direct-key runtime behavior needed to stay unchanged
  while satisfying `AnalysisOption(total=False)` checks.
- Final local checks passed:
  - `uv run ruff check --fix exporter/analysis/types.py exporter/analysis/analyzer.py`
  - `uv run ruff format exporter/analysis/types.py exporter/analysis/analyzer.py`
  - `uv run pyright exporter/analysis/types.py exporter/analysis/analyzer.py`
  - `uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/types.py exporter/analysis/analyzer.py`
  - `uv run pytest tests/exporter/analysis/test_analysis_analyzer.py tests/exporter/analysis/test_analyzer.py -v`
    (`29 passed`, 1 dependency deprecation warning)

### Out of scope
- Annotating `translate_core.py`, `study_passage.py`, or `export_words_csv.py`
  consumers with the new types. That can be a follow-up.
- Changing any runtime behavior.
- Making fields required vs optional beyond what `total=False` provides.
- Remaining queue findings.

---

## Finding 35 — extract helpers to reduce `translate_core.py` function length

Status: IMPLEMENTED 2026-06-11. Impact: low-medium (maintainability — the file is 1325
lines; two functions exceed 130 lines each). Includes the low-level annotation
and docstring cleanup originally listed as Finding 38.

### Problem
- `_request_first_pass` (lines ~830-990, ~160 lines) contains inline reformat
  handling and compact-map handling that could be separate functions.
- Duplicated `trailing_punctuation` string literal at lines 36 and 71.
- `_build_reformat_prompt` uses magic number `3000` (line 481).
- `_iter_options` (line 185) has no return type annotation.
- `pre_match_db_examples` mutates its `analysis` argument in-place but the
  docstring does not say so.

### Files to change
- `exporter/analysis/translate_core.py` (refactor only — no behavior change)
- `tests/exporter/analysis/test_translate_core.py` (no changes expected; run
  to verify no regressions)

### Implementation

1. **Extract `REFORMAT_MAX_CHARS = 3000`** as a module-level constant near
   line 18. Replace `prose_response[:3000]` at line 481 with
   `prose_response[:REFORMAT_MAX_CHARS]`.

2. **Deduplicate `trailing_punctuation`**: extract as a module-level constant
   `_TRAILING_PUNCTUATION = '.,;:!?)]}”’"'` near line 18. Replace both
   occurrences at lines 36 and 71. Preserve the curly quote characters already
   present in the current source.

3. **Add return type to `_iter_options`**: change signature (line 185) to
   `def _iter_options(options: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:`
   and add `from collections.abc import Iterator` if not already imported.

4. **Document in-place mutation in `pre_match_db_examples()`**:
   ```python
   """Mark options whose curated example text overlaps the analyzed passage.

   Mutates `analysis` in-place by setting ``ai_score`` and ``db_example_match``
   on matching options. Does not return a value.
   """
   ```

5. **Extract `_handle_reformat_response()`** from `_request_first_pass`:
   identify the reformat logic block (the section that calls
   `_build_reformat_prompt` and processes the reformat response) and move it
   into a helper. Keep the exact same debug keys:
   `reformat_raw_response`, `reformat_status_message`,
   `reformat_parsed_response`, and `reformat_parse_error`.

   Suggested signature:
   ```python
   def _handle_reformat_response(
       *,
       chunk_sentence: str,
       raw_response: str,
       ai_data: dict[str, Any],
       parse_error: str,
       ai_manager: AIManager,
       model: str | None,
       provider: str | None,
       progress: Callable[[str], None] | None,
       verbose: bool,
       debug: dict[str, Any] | None,
   ) -> dict[str, Any]:
   ```

6. **Extract `_handle_compact_map_response()`** from `_request_first_pass`:
   move the compact word-key map path (the section that handles
   `_extract_word_key_map`) into a helper. Keep the exact same debug keys:
   `translation_raw_response`, `translation_status_message`,
   `translation_parsed_response`, and `translation_parse_error`.

   Suggested signature:
   ```python
   def _handle_compact_map_response(
       *,
       chunk_sentence: str,
       word_key_map: dict[str, str],
       ai_manager: AIManager,
       model: str | None,
       provider: str | None,
       progress: Callable[[str], None] | None,
       verbose: bool,
       debug: dict[str, Any] | None,
   ) -> dict[str, Any]:
   ```

7. In `_request_first_pass`, replace the inline branches with calls to the new
   helpers. Do not change response parsing, score merging, debug key names,
   progress events, provider/model forwarding, or exception behavior.

### Tests — existing tests as safety net
No new tests. Run the full existing test suite to verify no regressions:
```
uv run pytest tests/exporter/analysis/test_translate_core.py -v
```

### Verification commands
```
uv run ruff check --fix exporter/analysis/translate_core.py
uv run ruff format exporter/analysis/translate_core.py
uv run pyright exporter/analysis/translate_core.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py
uv run pytest tests/exporter/analysis/test_translate_core.py -v
```

### Implementation outcome
- Extracted `_handle_compact_map_response()` and `_handle_reformat_response()`
  from `_request_first_pass()` without changing debug keys, progress events,
  provider/model forwarding, score merging, or exception behavior.
- Added `REFORMAT_MAX_CHARS`, `_TRAILING_PUNCTUATION`, and the `_iter_options()`
  return annotation; documented `pre_match_db_examples()` in-place mutation.
- Added a type-only `cast()` at the `analyze_sentence()` boundary so
  `translate_core.py` passes Pyright after the earlier `AnalysisResult`
  annotation work. Runtime behavior is unchanged.
- Final local checks passed:
  - `uv run ruff check --fix exporter/analysis/translate_core.py`
  - `uv run ruff format exporter/analysis/translate_core.py`
  - `uv run pyright exporter/analysis/translate_core.py`
  - `uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py`
  - `uv run pytest tests/exporter/analysis/test_translate_core.py -v`
    (`49 passed`, 1 dependency deprecation warning)

### Out of scope
- Any behavior change.
- Splitting `translate_core.py` into multiple files.
- Finding 36 or Finding 39.

---

## Finding 36 — remove markdown fencing from the first-response schema prompt

Status: IMPLEMENTED 2026-06-11. Impact: low-medium (cheap prompt hardening; possible
reduction in wrong-schema first responses, but live effect is nondeterministic).

### Problem
In the latest prep batch, multiple first responses came back with wrong schema
(wrong top-level key, truncated JSON, or tool-call payloads). The recovery
pipeline handles them, but each reformat costs time. `build_system_prompt()`
already includes a JSON skeleton, so do **not** add a duplicate schema example.
The safer deterministic cleanup is to remove the markdown code fence around the
schema and end the prompt with a plain-text schema reminder. This avoids telling
the model "no markdown fences" while showing a fenced example.

### Files to change
- `exporter/analysis/translate_core.py` — modify `build_system_prompt()` only
- `tests/exporter/analysis/test_translate_core.py` — add prompt text tests

### Implementation

1. In `build_system_prompt()`, remove the literal ```json / ``` fence lines
   around the output schema example. Keep the schema content and all existing
   fields, including `variant_choices` behavior.

2. Add one final line immediately before the closing triple quote:
   `Your response MUST be exactly one JSON object with translation, literal_translation, and scores.`

3. Do not alter retry prompt text, reformat prompt text, response parsing,
   compact-map parsing, scoring, or provider behavior.

4. Live measurement is optional and cost-bearing. Do not run the five live AI
   probes unless the user explicitly asks during the execution session. If the
   user asks, use the existing baseline in `handoff.md` and record:
   - correct first-response schema yes/no
   - reformat needed yes/no
   - total wall time

### Tests — write FIRST, confirm red
Add these tests to `tests/exporter/analysis/test_translate_core.py`:

1. **`test_build_system_prompt_schema_example_is_not_markdown_fenced`** —
   call `build_system_prompt([])`. Assert `"```" not in prompt` and
   `"\"scores\""` remains in the prompt.

2. **`test_build_system_prompt_ends_with_schema_reminder`** — assert the final
   non-empty line contains
   `"Your response MUST be exactly one JSON object"`.

Expected red-state failure: the current prompt contains a ```json fence and
does not end with the new exact reminder.

### Verification commands
```
uv run ruff check --fix exporter/analysis/translate_core.py
uv run ruff format exporter/analysis/translate_core.py
uv run pyright exporter/analysis/translate_core.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py
uv run pytest tests/exporter/analysis/test_translate_core.py -v
```

### Implementation outcome
- Added prompt text tests for the first-response schema example and final schema
  reminder in `tests/exporter/analysis/test_translate_core.py`.
- Red check failed as expected before the source edit:
  `uv run pytest tests/exporter/analysis/test_translate_core.py -v -k 'schema_example_is_not_markdown_fenced or ends_with_schema_reminder'`
  failed because the prompt still contained a markdown fence and ended with the
  older "Only output the JSON object" line.
- Removed only the markdown fence lines around the schema example in
  `build_system_prompt()` and added the exact final schema reminder. Retry prompt,
  reformat prompt, response parsing, compact-map parsing, scoring, and provider
  behavior were not changed.
- Final local checks passed:
  - `uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`
  - `uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`
  - `uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`
  - `uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`
  - `uv run pytest tests/exporter/analysis/test_translate_core.py -v`
    (`51 passed`, 1 dependency deprecation warning)
- Live AI probes were not run; they are optional and cost-bearing for this finding.

### Out of scope
- Changing the retry prompt or reformat prompt.
- Changing the AI response parsing logic.
- Running live AI probes unless the user explicitly asks during execution.
- Finding 39.

---

## Finding 37 — fix rate-limiting pre-sleep bug and type hint in `ai_manager.py`

Status: IMPLEMENTED 2026-06-11. Impact: low (wastes time sleeping for models that may
never be reached; minor type hint rule violation).

Execution note: run after Finding 32 so the routing edge cases are already
covered.

### Problem
1. The rate-limiting loop (lines 164-180) iterates over ALL models in
   `models_to_try` and sleeps for each model's delay BEFORE any request is
   attempted. It should only rate-limit the model about to be tried, inside
   the main request loop.
2. Line 44 uses `Optional[str]` instead of `str | None` — violates project
   type hint rules.

### Exact current anchors (verified 2026-06-11)
- Rate-limit pre-loop: lines 164-180 (complete `for model_tuple in
  models_to_try` block with `time.sleep`)
- Main request loop: lines 182-236 (`for model_tuple in models_to_try`)
- `Optional[str]` import: line 5 (`from typing import Any, NamedTuple,
  Optional`)
- `content: Optional[str]` usage: line 44

### Files to change
- `tools/ai_manager.py` (implementation)
- `tests/tools/test_ai_manager.py` (add tests)

### Implementation

1. **Move rate-limiting inside the main request loop**: Delete the pre-loop
   (lines 164-180). In the main request loop (after line 183), add the
   per-model rate-limit check before the `try` block:
   ```python
   for model_tuple in models_to_try:
       provider_name, model_name = model_tuple[0], model_tuple[1]
       if provider_name not in self.providers:
           continue

       # Rate-limit this specific model
       model_key = f"{provider_name}:{model_name}"
       model_delay = self._get_model_delay(provider_name, model_name)
       current_time = time.monotonic()
       last_request = self.model_last_request.get(model_key, 0)
       elapsed_since_last = current_time - last_request
       wait_time = model_delay - elapsed_since_last
       if wait_time > 0:
           pr.green(f"RATE LIMITING for {model_key} - {wait_time:.2f}s")
           time.sleep(wait_time)
       self.model_last_request[model_key] = time.monotonic()

       provider = self.providers[provider_name]
       # ... rest of existing try/except ...
   ```

2. **Fix type hint**: Change line 5 from `from typing import Any, NamedTuple,
   Optional` to `from typing import Any, NamedTuple`. Change line 44 from
   `content: Optional[str]` to `content: str | None`.

### Tests — write FIRST

1. **`test_request_does_not_sleep_for_unused_fallback_models`** — create a
   manager with 3 models where the first one succeeds and all three models have
   a non-zero delay. Pre-populate `manager.model_last_request` for all three
   model keys with `time.monotonic()` (or monkeypatch `time.monotonic` to a
   stable value) so the current pre-loop computes positive waits for every
   model. Monkeypatch `time.sleep` to record calls without sleeping. Assert
   exactly one sleep occurs for the first/successful model, not for the unused
   fallback models.

   Expected red-state failure before implementation: current code sleeps for
   all three models before it knows the first one will succeed.

2. **`test_rate_limit_sleep_applies_to_tried_model`** — create a manager with
   a non-zero delay model. Make two rapid requests. Assert that `time.sleep`
   was called on the second request with a positive wait time for that model.

### Verification commands
```
uv run ruff check --fix tools/ai_manager.py tests/tools/test_ai_manager.py
uv run ruff format tools/ai_manager.py tests/tools/test_ai_manager.py
uv run pyright tools/ai_manager.py tests/tools/test_ai_manager.py
uv run --with pyrefly pyrefly check --min-severity warn tools/ai_manager.py tests/tools/test_ai_manager.py
uv run pytest tests/tools/test_ai_manager.py -v
```

### Out of scope
- Changing the delay values or timeout configuration.
- Changing the fallback chain logic.
- Finding 38 is merged into Finding 35; do not treat it as follow-up work here.

---

## Finding 38 — MERGED into Finding 35; do not execute separately

Status: MERGED 2026-06-11 during plan-tightening. Impact: none as a separate
task.

The `_iter_options` return annotation and `pre_match_db_examples` docstring
cleanup are now part of Finding 35. Future agents must skip this section and
continue to Finding 36 or Finding 39 depending on the corrected queue order.

---

## Finding 39 — write debug/raw artifacts when `study_passage.py --debug` fails

Status: IMPLEMENTED 2026-06-11. Impact: medium-high (auditability — failed AI runs should
still leave the raw/debug evidence needed for diagnosis).

### Problem
The handoff records a forced `MN4_p2` run that exited before the final
report-writing stage, leaving no report/debug artifacts for that failed run.
Current `study_passage.py` writes `*_ai_debug.json` and `*_ai_raw.txt` only
after `translate_sentence()` returns successfully. If `translate_sentence()`
raises after partial AI debug data has been collected, `db_session.close()`
runs, but no debug/raw artifact is written.

### Exact current anchors (verified 2026-06-11)
- `study_passage.py:293`: initializes `ai_debug: dict = {}`.
- `study_passage.py:295-309`: calls `translate_sentence(...)` in a `try` with
  only `db_session.close()` in `finally`.
- `study_passage.py:319-328`: writes `*_ai_debug.json` and, when `--debug` is
  enabled, `*_ai_raw.txt` only after successful `translate_sentence()`.
- `tests/exporter/analysis/test_study_passage.py` already tests
  `_build_raw_responses_log()` and argument parsing.

### Files to change
- `exporter/analysis/study_passage.py`
- `tests/exporter/analysis/test_study_passage.py`

### Implementation

1. Add a helper near `_build_raw_responses_log()`:
   ```python
   def _write_ai_debug_artifacts(
       source: str,
       ai_debug: dict[str, Any],
       include_raw: bool,
   ) -> None:
       debug_path = _OUTPUT_DIR / f"{source}_ai_debug.json"
       debug_path.write_text(
           json.dumps(ai_debug, ensure_ascii=False, indent=2),
           encoding="utf-8",
       )
       if include_raw:
           raw_path = _REPORTS_DIR / f"{source}_ai_raw.txt"
           raw_path.write_text(
               _build_raw_responses_log(source, ai_debug),
               encoding="utf-8",
           )
           pr.green(f"Raw AI responses: {raw_path}")
   ```
   Add `from typing import Any` if needed for the annotation.

2. Replace the existing successful debug/raw writing block with a call to
   `_write_ai_debug_artifacts(source, ai_debug, args.debug)`.

3. Around the `translate_sentence(...)` call, add an `except Exception:` branch
   before `finally`:
   - if `args.debug` is true or `ai_debug` is non-empty, call
     `_write_ai_debug_artifacts(source, ai_debug, args.debug)`
   - re-raise the original exception unchanged
   - keep `db_session.close()` in `finally`

4. Do not write `*_study.md` or `*_study.json` on failure; there is no complete
   merged result. Do not swallow the exception or convert it to success.

### Tests — write FIRST, confirm red

1. **`test_write_ai_debug_artifacts_writes_json_and_raw`** — monkeypatch
   `study_passage._OUTPUT_DIR` and `study_passage._REPORTS_DIR` to `tmp_path`
   subdirectories, call the helper with a debug dict containing `raw_response`,
   and assert both files are written with the expected content.

2. **`test_main_writes_debug_artifacts_when_translate_sentence_fails`** —
   monkeypatch:
   - `_parse_args()` to return an object with `debug=True`, `provider=None`,
     `model=None`
   - `ProjectPaths` so `dpd_db_path.exists()` returns true
   - `get_passage_by_code()` to return a one-paragraph `PassageResult`
   - `input()` to return a code such as `"TH1"`
   - `get_db_session()` to return a mock session with `close()`
   - `AIManager` to a lightweight stub
   - `translate_sentence()` to mutate the passed `debug` dict with
     `{"raw_response": "partial", "status_message": "failed status"}` and then
     raise `ValueError("boom")`
   - `_OUTPUT_DIR` and `_REPORTS_DIR` to `tmp_path` subdirectories

   Assert `main()` re-raises `ValueError`, the mock session is closed, and
   `TH1_ai_debug.json` plus `TH1_ai_raw.txt` exist. Expected red-state failure:
   current code re-raises before writing those files.

### Verification commands
```
uv run ruff check --fix exporter/analysis/study_passage.py tests/exporter/analysis/test_study_passage.py
uv run ruff format exporter/analysis/study_passage.py tests/exporter/analysis/test_study_passage.py
uv run pyright exporter/analysis/study_passage.py tests/exporter/analysis/test_study_passage.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/study_passage.py tests/exporter/analysis/test_study_passage.py
uv run pytest tests/exporter/analysis/test_study_passage.py -v
```

### Implementation outcome
- Added `_write_ai_debug_artifacts()` in `exporter/analysis/study_passage.py`
  and reused it for successful debug artifact writes.
- Added an exception path around `translate_sentence()` that writes debug JSON
  and, when `--debug` is enabled, the raw-response log before re-raising the
  original exception. The DB session still closes in `finally`.
- No failure-path study report or study JSON is written.
- Red check failed as expected before the source edit:
  `uv run pytest tests/exporter/analysis/test_study_passage.py -v -k 'write_ai_debug_artifacts or main_writes_debug_artifacts'`
  failed because `_write_ai_debug_artifacts()` did not exist and failed runs did
  not write `*_ai_debug.json` / `*_ai_raw.txt`.
- Final local checks passed:
  - `uv run ruff check --fix exporter/analysis/study_passage.py tests/exporter/analysis/test_study_passage.py`
  - `uv run ruff format exporter/analysis/study_passage.py tests/exporter/analysis/test_study_passage.py`
  - `uv run pyright exporter/analysis/study_passage.py tests/exporter/analysis/test_study_passage.py`
  - `uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/study_passage.py tests/exporter/analysis/test_study_passage.py`
  - `uv run pytest tests/exporter/analysis/test_study_passage.py -v`
    (`11 passed`, 1 dependency deprecation warning)

### Out of scope
- Writing success reports for failed runs.
- Swallowing or transforming `translate_sentence()` exceptions.
- Changing AI provider behavior, retry behavior, or debug schema keys.

---

## Observations recorded, no action proposed

- **Retry score inflation in large option sets** (AN3.23_p1): retry scores
  show many `"score": 1` values for non-winning options. Model tendency with
  large option sets, not a code bug. Re-evaluate only if score precision
  matters for downstream consumers.
- **`search_inflections_for_form` full-table scan**: O(N) fallback query in
  compound breakdown. Performance concern, not correctness. Consider indexing
  or caching if compound analysis becomes slow on larger databases.
- **GPT-OSS fallback under real Flash quota exhaustion**: still unproven.
  Use Finding 28's `--provider`/`--model` flags to capture live evidence
  when a quota window occurs.
- **Pali grammar accuracy (old Finding 5)**: deferred — model quality, not
  code.

## Session ordering and closure rules
1. APPROVED corrected execution order (user approval 2026-06-11; tightened
   2026-06-11): **32 → 37 → 31 → 33 → 34 → 35 → 36 → 39**.
2. Finding 38 is merged into Finding 35 and must not be executed separately.
3. One finding per session. At session start, implement the first finding in
   the corrected order above not marked IMPLEMENTED. Do not use numeric order.
4. After each implemented finding, append a completed-issue entry to
   `handoff.md` in the existing format and mark the section here IMPLEMENTED
   with the date.
5. Keep `plan.md` stable — no checkboxes, no per-issue history there.
6. Prepare a draft commit message referencing `#197`; the user commits.
