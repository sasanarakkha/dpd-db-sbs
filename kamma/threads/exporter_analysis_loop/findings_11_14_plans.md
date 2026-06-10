# Detailed Implementation Plans: Findings 11–14

Status: Finding 11 was implemented on 2026-06-10 as Issue 20. Findings 12-14 remain
PENDING USER APPROVAL. Do not implement any remaining finding until the user approves it
explicitly. One finding per session unless the user explicitly overrides the one-issue rule.

These plans were written on 2026-06-10 against the working tree at commit `8880da34` plus
uncommitted changes. All code anchors below were verified by reading the actual source on
that date. If the anchor code does not match when you implement, STOP and re-read the file —
do not guess.

Evidence sources (verified, do not re-derive from memory):
- `exporter/analysis/output/MN122_p2_ai_debug.json` — retry raw_response is exactly
  `Error: timed out waiting for response`, status `SUCCESS in 98.84s. antigravity_cli/Gemini 3.5 Flash (High)`.
- `exporter/analysis/output/DN2_p3_ai_debug.json` — same timeout text, status `SUCCESS in 98.92s. ...`.
- `exporter/analysis/output/TH66_ai_debug.json` — reformat raw_response starts with
  `Authentication required. Please visit the URL to log in:` followed by an
  `accounts.google.com/o/oauth2` URL; reformat status `SUCCESS in 35.96s. ...`; the report
  `exporter/analysis/reports/TH66_study.md` has empty Translation as a direct result.
- `exporter/analysis/output/AN4.43_p1_ai_debug.json` — retry raw_response is a flat
  top-level map `{"19158_1": {"score": 1}, ...}` with no `scores` wrapper; all entries were
  discarded; retry status is `SUCCESS in 73.71s. Success in 73.71s. (after 1 failed attempt(s): ...)`
  with no succeeding provider name.

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
- Modern type hints (`int | float`, `str | None`), `Path` from pathlib, no `sys.path` hacks.
- Commit messages (prepared for the user, not committed by the agent) must reference `#197`.
- Do NOT touch prompt wording, chunking, or schema design — explicitly out of scope.

---

## Finding 11 — classify agy error/auth stdout as provider failure

Status: IMPLEMENTED on 2026-06-10 as Issue 20. This plan is retained for audit history.

### Problem
`agy` prints its own failure text to stdout and exits 0. Two confirmed shapes:
1. `Error: timed out waiting for response` (MN122_p2, DN2_p3 retries).
2. A Google OAuth prompt starting `Authentication required. Please visit the URL to log in:`
   with an `accounts.google.com/o/oauth2/...` URL (TH66 reformat — caused an empty
   translation in the generated report).

`generate_content` in `tools/ai_antigravity_cli.py` only rejects non-zero exit codes and
empty output, so this text is returned as model content, `AIManager` reports `SUCCESS`, and
no fallback provider is tried.

### Files to change
- `tools/ai_antigravity_cli.py` (implementation)
- `tests/tools/test_ai_antigravity_cli.py` (tests)

### Exact current anchor (tools/ai_antigravity_cli.py, end of `generate_content`)
```python
    response = _extract_response(result.stdout)
    if response is None or not response.strip():
        raise AntigravityCliProviderError(f"{model} returned an empty response")
    return response
```

### Implementation
1. Add module-level constants near `MAX_ARGV_PROMPT_BYTES`:
```python
AUTH_PROMPT_MARKERS = ("Authentication required", "accounts.google.com")
MAX_ERROR_LINE_LENGTH = 200
```
2. Add a helper function (place after `_extract_response`):
```python
def _classify_error_text(response: str) -> str | None:
    """Detect agy failure text printed to stdout with exit code 0.

    agy reports timeouts ("Error: timed out waiting for response") and Google
    OAuth login prompts on stdout while exiting 0. Both must surface as provider
    errors so AIManager falls back, instead of being parsed as model content.
    """
    stripped = response.strip()
    if all(marker in stripped for marker in AUTH_PROMPT_MARKERS):
        return "authentication required (agy is not logged in)"
    if (
        stripped.startswith("Error:")
        and "\n" not in stripped
        and len(stripped) <= MAX_ERROR_LINE_LENGTH
    ):
        return stripped
    return None
```
3. Call it in `generate_content` after the empty-response check, before `return response`:
```python
    error_reason = _classify_error_text(response)
    if error_reason:
        raise AntigravityCliProviderError(f"{model} error response: {error_reason}")
```

Design notes (do not deviate):
- The `Error:` branch is deliberately conservative: single line, ≤200 chars, must be the
  whole response. The analysis prompts always demand JSON objects, so a legitimate answer
  cannot be one short prose line starting `Error:`.
- The auth branch requires BOTH markers so ordinary text mentioning authentication is not
  misclassified.
- `AntigravityCliManager.request` already converts `AntigravityCliProviderError` into a
  failed `_Response(content=None, ...)`, which `AIManager.request` records as a failed
  attempt and falls through to the next provider. No change needed in `tools/ai_manager.py`
  for this finding.

### Tests (tests/tools/test_ai_antigravity_cli.py)
Use the existing monkeypatch style in that file. The module imports `run_antigravity_print`
into its own namespace, so patch `antigravity_cli.run_antigravity_print`. Import `RunResult`
from `tools.antigravity_cli_models`. Patch `antigravity_cli._locate_antigravity` to return
`Path("/usr/bin/true")` so the tests do not depend on `agy` being installed.

Write these failing tests FIRST:
```python
def _patch_agy(monkeypatch: pytest.MonkeyPatch, stdout: str) -> None:
    monkeypatch.setattr(
        antigravity_cli, "_locate_antigravity", lambda: Path("/usr/bin/true")
    )
    monkeypatch.setattr(
        antigravity_cli,
        "run_antigravity_print",
        lambda *args, **kwargs: RunResult(returncode=0, stdout=stdout, stderr=""),
    )


def test_request_classifies_timeout_text_as_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_agy(monkeypatch, "Error: timed out waiting for response")

    response = antigravity_cli.AntigravityCliManager().request(prompt="p", prompt_sys="s")

    assert response.content is None
    assert "timed out waiting for response" in response.status_message


def test_request_classifies_auth_prompt_as_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_agy(
        monkeypatch,
        "Authentication required. Please visit the URL to log in:\n"
        "  https://accounts.google.com/o/oauth2/auth?access_type=offline&client_id=x",
    )

    response = antigravity_cli.AntigravityCliManager().request(prompt="p", prompt_sys="s")

    assert response.content is None
    assert "authentication required" in response.status_message


def test_request_keeps_normal_json_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_agy(monkeypatch, '{"translation": "x", "scores": {}}')

    response = antigravity_cli.AntigravityCliManager().request(prompt="p", prompt_sys="s")

    assert response.content == '{"translation": "x", "scores": {}}'


def test_request_keeps_multiline_content_mentioning_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = '{"translation": "Error: this is part of a translation",\n "scores": {}}'
    _patch_agy(monkeypatch, stdout)

    response = antigravity_cli.AntigravityCliManager().request(prompt="p", prompt_sys="s")

    assert response.content == stdout
```
Expected red-state failure: the first two tests fail because `response.content` equals the
error text instead of `None`.

### Verification commands
```
uv run pytest tests/tools/test_ai_antigravity_cli.py -v
uv run ruff check --fix tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py
uv run ruff format tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py
uv run pyright tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py
uv run --with pyrefly pyrefly check --min-severity warn tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py
```
Live smoke (optional, normal-path regression only — agy timeouts cannot be forced
deterministically):
```
printf 'DHP77\n' | UV_CACHE_DIR=/private/tmp/uv-cache uv run python exporter/analysis/study_passage.py --debug
```
Confirm the run completes and the report has a non-empty translation. Do not claim live
proof of the error classification itself; the unit tests are the evidence.

### Out of scope
- Any retry/re-login logic for auth failures.
- Changes to `tools/antigravity_cli_models.py` or `tools/ai_manager.py`.

---

## Finding 12 — accept flat retry score maps without the `scores` wrapper

### Problem
The missing-scores retry can return the flat scores map directly, e.g.
`{"19158_1": {"score": 1}, "19159_1": {"score": 1}, ...}`, with no top-level `scores` key.
`translate_core.py` does `retry_data.get("scores", {})`, gets `{}`, and silently discards
every entry (AN4.43_p1: ~1,500 valid entries lost).

### Files to change
- `exporter/analysis/translate_core.py` (implementation)
- `tests/exporter/analysis/test_translate_core.py` (tests)

### Exact current anchor (translate_core.py, retry block inside `translate_sentence`)
```python
    missing_groups = _find_missing_score_groups(analysis, scores_map)
    if debug is not None:
        debug["missing_score_groups_after_first_response"] = missing_groups
    if missing_groups:
        retry_prompt = _build_missing_scores_prompt(resolved_sentence, missing_groups)
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
            retry_scores = retry_data.get("scores", {})
            if isinstance(retry_scores, dict):
                scores_map.update(retry_scores)
        if debug is not None:
            debug["retry_requests"].append(
                {
                    "prompt": retry_prompt,
                    "raw_response": retry_response.content,
                    "status_message": retry_response.status_message,
                    "parsed_response": retry_data,
                    "parse_error": retry_parse_error,
                    "missing_keys": [
                        key for group in missing_groups for key in group["missing_keys"]
                    ],
                }
            )
```

### Implementation
1. Add a helper directly after `_normalize_ai_response`:
```python
def _coerce_flat_score_map(
    ai_data: dict[str, Any],
    expected_keys: set[str],
) -> dict[str, Any]:
    """Wrap a bare ``{key: {"score": N}}`` response in the ``scores`` contract.

    The missing-scores retry can return the flat scores map directly, without
    the required top-level ``scores`` wrapper (live evidence: AN4.43_p1). When
    most top-level keys are expected option keys with score-shaped values, the
    response IS the scores map.
    """
    if not ai_data or "scores" in ai_data:
        return ai_data
    matched: dict[str, Any] = {}
    for key, value in ai_data.items():
        if key not in expected_keys:
            continue
        if isinstance(value, dict) and isinstance(value.get("score"), int | float):
            matched[key] = value
        elif isinstance(value, int | float) and not isinstance(value, bool):
            matched[key] = {"score": value}
    if not matched or len(matched) * 2 < len(ai_data):
        return ai_data
    return {"scores": matched}
```
2. In the retry block, hoist the missing-keys list (it is currently built inline only for
   debug) and apply the coercion after `_normalize_ai_response`:
   - Before `retry_prompt = ...`, add:
     ```python
     missing_keys = [
         key for group in missing_groups for key in group["missing_keys"]
     ]
     ```
   - After `retry_data = _normalize_ai_response(retry_data)`, add:
     ```python
     retry_data = _coerce_flat_score_map(retry_data, set(missing_keys))
     ```
   - In the debug append, replace the inline list comprehension for `"missing_keys"` with
     the hoisted `missing_keys` variable.

Design notes (do not deviate):
- The majority-match threshold (`len(matched) * 2 < len(ai_data)`) mirrors the proven
  `_extract_word_key_map` heuristic, so prose-shaped or unrelated JSON is never coerced.
- Only the retry path gets this coercion. Do NOT apply it to the first response — a flat map
  there is already handled by `_extract_word_key_map` (word→key maps), which is a different
  shape (values are key strings, not score dicts).
- `bool` is excluded explicitly because `isinstance(True, int)` is `True` in Python.

### Tests (tests/exporter/analysis/test_translate_core.py)
Mirror `test_translate_sentence_retries_missing_component_scores` (same `monkeypatch` of
`exporter.analysis.translate_core.analyze_sentence` with the `sammāsambuddhassa` fixture and
the same `FakeAIManager` two-call pattern). Write FIRST, confirm red:
```python
def test_translate_sentence_retry_accepts_flat_score_map(monkeypatch) -> None:
    # ... same analyze_sentence fixture as
    # test_translate_sentence_retries_missing_component_scores ...
    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs["prompt"])
            content = (
                '{"translation": "", "literal_translation": "", '
                '"scores": {"60847_0": {"score": 10}}}'
            )
            if len(calls) == 2:
                content = '{"60789_0": {"score": 10}}'  # flat, no "scores" wrapper
            return type(
                "FakeResponse", (), {"content": content, "status_message": "ok"}
            )()
    # ... call translate_sentence with debug={} as in the sibling test ...
    component_options = result["analysis"][0]["data"][0]["components"][0]
    assert component_options[1]["ai_score"] == 10
```
Expected red-state failure: `component_options[1]["ai_score"] is None` because the flat map
is discarded.

Add a guard test in the same style where the second call returns
`'{"unrelated_key": {"score": 5}}'` and assert that `"unrelated_key"` does not appear in
`debug["final_scores"]` and `component_options[1]["ai_score"] is None`.

Add a direct unit test for the helper:
```python
def test_coerce_flat_score_map_shapes() -> None:
    expected = {"a_0", "b_0"}
    assert _coerce_flat_score_map({"a_0": {"score": 3}}, expected) == {
        "scores": {"a_0": {"score": 3}}
    }
    assert _coerce_flat_score_map({"a_0": 7}, expected) == {
        "scores": {"a_0": {"score": 7}}
    }
    untouched = {"scores": {"a_0": {"score": 1}}}
    assert _coerce_flat_score_map(untouched, expected) is untouched
    prose_like = {"x": "y", "z": "w", "a_0": {"score": 1}}
    assert _coerce_flat_score_map(prose_like, expected) is prose_like
```

### Verification commands
```
uv run pytest tests/exporter/analysis/test_translate_core.py -v
uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
```
Live smoke (optional): rerun `AN4.43` paragraph 1 with `--debug` and inspect
`retry_requests[0]` in the new debug JSON. The flat-map shape is model-nondeterministic, so
do not treat a non-reproduction as failure; the unit tests are the primary evidence.

### Out of scope
- First-response handling, reformat handling, prompt text changes.

---

## Finding 13 — name the succeeding provider/model in AIManager success statuses

### Problem
`AIManager.request` composes `f"SUCCESS in {duration:.2f}s. {ai_response.status_message}"`.
Only the antigravity provider self-identifies (`antigravity_cli/{model}`); all other
providers return bare `"Success"` / `"Success in Xs"`. After a fallback, the status reads
`SUCCESS in 73.71s. Success in 73.71s. (after 1 failed attempt(s): ...)` — no way to tell
which provider actually answered (AN4.43_p1 live evidence).

### Files to change
- `tools/ai_manager.py` (implementation)
- `tests/tools/test_ai_manager.py` (tests)

### Exact current anchor (tools/ai_manager.py, inside `request`)
```python
                if ai_response.content is not None:
                    status_message = (
                        f"SUCCESS in {duration:.2f}s. {ai_response.status_message}"
                    )
```

### Implementation
Replace the anchor with:
```python
                if ai_response.content is not None:
                    status_message = (
                        f"SUCCESS in {duration:.2f}s. {provider_name}/{model_name}"
                    )
                    provider_detail = ai_response.status_message
                    if (
                        provider_detail
                        and provider_detail not in status_message
                        and not provider_detail.startswith("Success")
                    ):
                        status_message = f"{status_message} ({provider_detail})"
```
Design notes (do not deviate):
- `provider_name`/`model_name` are already in scope in that loop body.
- The `not in` check drops the antigravity provider's redundant
  `antigravity_cli/{model}` self-identification; the `startswith("Success")` check drops the
  bland `"Success"` / `"Success in Xs"` strings from the other providers. Any genuinely
  informative provider detail is preserved in parentheses.
- Do NOT change the error path or the `(after N failed attempt(s): ...)` suffix — Issue 18
  already covers failed-attempt details and has passing tests.
- Do NOT edit the individual provider managers.

### Tests (tests/tools/test_ai_manager.py)
The file already has `_RecordingProvider` (status `"stub"`), `_FailingProvider`,
`_make_manager`, and `_make_fallback_manager`. Write FIRST, confirm red:
```python
def test_request_success_status_names_provider_and_model() -> None:
    provider = _RecordingProvider()
    manager = _make_manager(provider)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert "stub/stub-model" in response.status_message


def test_request_fallback_success_names_succeeding_provider() -> None:
    manager = _make_fallback_manager(_FailingProvider(), _RecordingProvider())

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert "stub/stub-model" in response.status_message
    assert "after 1 failed attempt(s):" in response.status_message
```
Also add a stub provider returning `status_message="Success in 1.00s"` and assert the
composed status does NOT contain `"(Success"` (bland detail dropped), plus one returning
`status_message="model: special-variant"` and assert `"(model: special-variant)"` IS
appended.

Check the three existing success-path tests still pass unchanged
(`test_request_clean_success_omits_failed_attempt_suffix`,
`test_request_success_after_failure_includes_failed_attempt_details`,
`test_request_passes_150s_timeout_to_provider`). They assert on prefixes/substrings that
this change preserves.

### Verification commands
```
uv run pytest tests/tools/test_ai_manager.py -v
uv run ruff check --fix tools/ai_manager.py tests/tools/test_ai_manager.py
uv run ruff format tools/ai_manager.py tests/tools/test_ai_manager.py
uv run pyright tools/ai_manager.py tests/tools/test_ai_manager.py
uv run --with pyrefly pyrefly check --min-severity warn tools/ai_manager.py tests/tools/test_ai_manager.py
```
Also run `uv run pytest tests/tools/test_ai_antigravity_cli.py -v` (same subsystem, cheap).

### Out of scope
- Provider manager files, model JSON, retry/fallback ordering.

---

## Finding 14 (minor) — snapshot debug captures with deepcopy

### Problem
`translate_sentence` stores live references into the `debug` dict
(`debug["parsed_response"] = ai_data` etc.). Later normalization and
`scores_map.update(retry_scores)` mutate those objects, so the written
`*_ai_debug.json` misrepresents what the model originally returned. The handoff already
flags this as a known trap.

### Files to change
- `exporter/analysis/translate_core.py` (implementation)
- `tests/exporter/analysis/test_translate_core.py` (tests)

### Implementation
1. Add `import copy` to the module imports (stdlib group).
2. Wrap exactly these five debug captures inside `translate_sentence` in
   `copy.deepcopy(...)`:
   - `debug["parsed_response"] = ai_data` → `copy.deepcopy(ai_data)`
   - `debug["translation_parsed_response"] = translation_data` → deepcopy
   - `debug["reformat_parsed_response"] = reformat_data` → deepcopy
   - `"parsed_response": retry_data` in the `debug["retry_requests"].append({...})` dict →
     `copy.deepcopy(retry_data)`
   - `debug["final_scores"] = scores_map` → `copy.deepcopy(scores_map)`
     (`merge_ai_selections` runs afterward and hands these dicts into the analysis where
     they can be mutated further).
3. Do NOT deepcopy raw strings (`raw_response`, prompts, status messages) — they are
   immutable.

Cost note: deepcopy only runs when `debug is not None` (i.e. `--debug` runs); negligible
next to AI round-trips.

### Test (tests/exporter/analysis/test_translate_core.py)
Extend `test_translate_sentence_retries_missing_component_scores` or add a sibling test with
the same fixture. Write FIRST, confirm red:
```python
def test_debug_parsed_response_is_snapshot_not_live_reference(monkeypatch) -> None:
    # same analyze_sentence fixture + FakeAIManager as
    # test_translate_sentence_retries_missing_component_scores
    debug: dict = {}
    translate_sentence(..., debug=debug)

    # First response only scored 60847_0; the retry added 60789_0 to the live
    # scores map. The debug snapshot of the FIRST response must not show it.
    assert "60789_0" not in debug["parsed_response"]["scores"]
```
Expected red-state failure: `debug["parsed_response"]["scores"]` contains `60789_0` because
it is the same dict object as the final scores map.

### Verification commands
Same file set as Finding 12:
```
uv run pytest tests/exporter/analysis/test_translate_core.py -v
uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
```

### Out of scope
- Changing what is captured, debug file naming, or report generation.
- May be batched with Finding 12 (same files) ONLY if the user explicitly approves both.

---

## Session ordering and closure rules
1. Recommended order: 11 → 12 → 13 → 14 (impact-ranked). One per session by default.
2. After each finding is implemented and verified, append a completed-issue entry to
   `kamma/threads/exporter_analysis_loop/handoff.md` following the existing entry format,
   and mark that finding's section here as IMPLEMENTED with the date.
3. Keep `plan.md` stable — no checkboxes, no per-issue history there.
4. Prepare a draft commit message referencing `#197`; the user commits.
