# Detailed Implementation Plans: Findings 28–30

Status: APPROVED by the user on 2026-06-11. All three findings are approved for
implementation in the order **28 → 29 → 30**. Execute ONE finding per session unless
the user explicitly overrides the one-issue rule. At the start of each session, pick
the first finding below not yet marked IMPLEMENTED.

These plans were written on 2026-06-11 from analysis of the 2026-06-11 live debug prep
batch (`TH145`, `DHP141`, `AN3.23_p1`, `MN8_p2`, `SN36.1_p2`, plus the `DHP23` GPT-OSS
check). All code anchors below were verified by reading the actual source on
2026-06-11. If an anchor does not match when you implement, STOP and re-read the
file — do not guess.

Evidence sources (verified 2026-06-11 by direct file inspection):
- `exporter/analysis/reports/AN3.23_p1_ai_raw.txt`: chunk 1 first response has status
  `SUCCESS in 158.36s. antigravity_cli/Gemini 3.5 Flash (High)` but the body is
  truncated JSON ending with the literal line `Error: timed out waiting for response`
  (raw file line 137). Reformat + retry recovered to 0 missing groups.
- `exporter/analysis/reports/MN8_p2_ai_raw.txt`: first response has status
  `SUCCESS in 158.15s` but the body starts with a tool-call payload
  `include:default_api:write_to_file{...TargetFile:/Users/deva/Documents/dpd-db/temp/disambiguate/query_keys_0_14.py...}`
  (raw file line 6) and ends with `Error: timed out waiting for response` (line 34).
  During this run `agy` actually WROTE nine scratch scripts into the repo's
  `temp/disambiguate/` directory (cleaned up afterwards; see handoff "Live Debug Prep
  Session - 2026-06-11").
- `tools/ai_manager.py:157` (verified): `elif provider_preference and model:` — a
  forced model is honored ONLY when the provider is also given. `translate_core.py`
  never passes `provider_preference`, so the `model` parameter of
  `translate_sentence()` is currently dead: it silently falls through to the default
  fallback chain. This is why the `DHP23` GPT-OSS check needed a temp wrapper script.
- `agy --help` (live, 2026-06-11): there is NO tool-disabling flag. Relevant flags:
  `--sandbox` ("Run in a sandbox with terminal restrictions enabled", semantics
  unverified), `--add-dir` (workspace dirs, default empty → workspace is cwd).
- `tools/antigravity_cli_models.py:48-55` (verified): `subprocess.run` is called
  without `cwd`, so `agy` inherits the repo as its working directory — that is how the
  MN8_p2 tool-calls landed inside the repo.

What the prep batch confirmed is working (no action):
- The salvage → reformat → bounded-retry pipeline recovered ALL six runs to
  `missing_score_groups_after_retry == 0`, including the truncated and tool-call
  first responses. Findings 28–30 change reporting, containment, and debuggability —
  NOT the recovery pipeline.
- First-response schema unevenness (clean / wrong schema / truncated / tool-call) is
  model nondeterminism; no deterministic code fix is justified.
- GPT-OSS fallback under a real Flash quota-exhaustion window remains unproven and
  untestable on demand; Finding 28 makes it trivially testable when a window occurs.

Shared constraints for every finding:
- TDD: write the failing test first, run it, confirm it fails for the expected reason,
  then implement.
- Quality gates per changed Python file (all must pass before reporting completion):
  1. `uv run ruff check --fix <files>`
  2. `uv run ruff format <files>`
  3. `uv run pyright <files>`
  4. `uv run --with pyrefly pyrefly check --min-severity warn <files>`
  5. `uv run pytest <specific test files> -v`
- Never run bare `uv run pytest`. Always pass the specific test file path.
- Modern type hints, `Path` from pathlib, no `sys.path` hacks.
- POSIX-compatible shell commands (the agent shell is zsh); temp probes under `temp/`
  only, deleted before the final response.
- Prepare a draft commit message referencing `#197`; the user commits.

---

## Finding 28 — fix the dead `model` parameter; add `--provider`/`--model` CLI flags to `study_passage.py`

Status: IMPLEMENTED 2026-06-11. Impact: high (latent bug fix + removes the
temp-wrapper workaround for targeted live debugging).

### Problem
`AIManager.request()` honors a forced model only when BOTH `provider_preference` and
`model` are passed (`tools/ai_manager.py:157`). `translate_core.py` passes only
`model=` at its request call sites and never `provider_preference`, so
`translate_sentence(..., model="GPT-OSS 120B (Medium)")` silently uses the default
fallback chain. Targeted live debugging (e.g., the `DHP23` GPT-OSS check) currently
requires a temporary wrapper that monkey-forces every request.

### Files to change
- `exporter/analysis/translate_core.py` (thread `provider` through)
- `exporter/analysis/study_passage.py` (CLI flags + validation)
- `tests/exporter/analysis/test_translate_core.py` (tests)
- `tests/exporter/analysis/test_study_passage.py` (tests)

### Exact current anchors (translate_core.py, verified 2026-06-11)
- `_request_missing_score_retry_pass` signature: lines 535-544 (keyword-only, has
  `*`); its `ai_manager.request(...)` call: lines 557-561
  (`prompt=retry_prompt, model=model, prompt_sys=...`).
- `_request_first_pass` signature: lines 669-679 (positional params:
  `chunk_sentence, full_sentence, analysis, ai_manager, model, speech_mark_options,
  progress, verbose, debug`); its first-pass `ai_manager.request(...)`: lines 695-699;
  translation follow-up `ai_manager.request(...)`: lines 734-738; reformat
  `ai_manager.request(...)`: lines 790-793 — NOTE the reformat call currently passes
  NEITHER `model` nor `provider_preference`.
- `translate_sentence` signature: lines 828-838 (`model: str | None = None` is the
  4th parameter).
- Internal `_request_first_pass` call sites (positional): lines 865-875 (single-chunk)
  and 881-891 (multi-chunk loop).
- Internal `_request_missing_score_retry_pass` call sites (keyword): lines 914-922
  (pass 1) and 925-933 (pass 2).

### Exact current anchors (study_passage.py, verified 2026-06-11)
- `main()` builds its `argparse.ArgumentParser` inline at lines 232-238 (only
  `--debug` exists).
- `translate_sentence(...)` call: lines 281-290 (keyword args; no `model`/`provider`
  currently passed).

### Implementation
1. `translate_core.py` — thread a `provider` parameter:
   - `translate_sentence`: add `provider: str | None = None` immediately after the
     `model: str | None = None` parameter.
   - `_request_first_pass`: add `provider: str | None` immediately after the `model`
     parameter. Update BOTH internal call sites (lines 865-875 and 881-891): they are
     positional — insert `provider,` immediately after `model,` in each.
   - `_request_missing_score_retry_pass`: add `provider: str | None,` to the
     keyword-only parameters (place after `model`). Update both call sites (914-922,
     925-933) adding `provider=provider,`.
   - Add `provider_preference=provider,` to ALL FOUR `ai_manager.request(...)` call
     sites: retry (557), first pass (695), translation follow-up (734), and reformat
     (790). At the reformat site also add `model=model,` (it currently omits it; since
     `model` alone was dead, adding both is a no-op for default runs and required for
     forced runs).
   - Behavior guarantee: when `provider` is None (every existing caller), every
     request gets `provider_preference=None`, the `elif provider_preference and model`
     branch stays False, and the default chain is byte-identical to today.
2. `study_passage.py` — extract an arg parser helper so it is testable, then add
   flags:
```python
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pāḷi passage analyzer — Stage 1")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print raw AI responses and parse errors to the terminal",
    )
    parser.add_argument(
        "--provider",
        help="Force one AI provider for every request (requires --model), e.g. antigravity_cli",
    )
    parser.add_argument(
        "--model",
        help='Force one model for every request (requires --provider), e.g. "GPT-OSS 120B (Medium)"',
    )
    args = parser.parse_args(argv)
    if bool(args.provider) != bool(args.model):
        parser.error("--provider and --model must be used together")
    return args
```
   In `main()`, replace the inline parser block (lines 232-238) with
   `args = _parse_args()` and pass `model=args.model, provider=args.provider` to the
   `translate_sentence(...)` call (lines 281-290).

### Tests
Write FIRST, confirm red. All existing `FakeAIManager` fakes in
`test_translate_core.py` use `def request(self, **kwargs)` (verified at lines 225,
365, 433, 481, 534, 755, 849, 932, 965), so recording `provider_preference` is safe.
1. `test_translate_sentence_passes_provider_and_model_to_every_request`
   (tests/exporter/analysis/test_translate_core.py): mirror the fixture pattern of
   the existing retry tests around `_analysis_with_missing_retry_keys` (line 392).
   FakeAIManager records every `kwargs` dict into a list. First response: non-JSON
   prose (forces the reformat path); reformat response: valid
   `{"translation": "...", "literal_translation": "...", "scores": {}}` with no
   scores (forces the retry path); retry responses: valid flat scores. Call
   `translate_sentence(..., model="m-x", provider="prov-x")`. Assert EVERY recorded
   request has `kwargs["provider_preference"] == "prov-x"` and
   `kwargs["model"] == "m-x"`, and that ≥3 requests were made (first, reformat,
   retry). Expected red-state failure: `provider_preference` missing from kwargs
   (TypeError is acceptable red too if the param does not exist yet) or reformat
   request missing `model`.
2. `test_translate_sentence_default_provider_is_none` — same fixture, call without
   `provider`; assert every recorded request has
   `kwargs.get("provider_preference") is None` (proves default-path parity).
3. `test_parse_args_requires_provider_and_model_together`
   (tests/exporter/analysis/test_study_passage.py): import `_parse_args`;
   `_parse_args([])` works with both None; `_parse_args(["--provider", "p"])` and
   `_parse_args(["--model", "m"])` each raise `SystemExit`;
   `_parse_args(["--provider", "p", "--model", "m"])` returns both values.

### Verification commands
```
uv run pytest tests/exporter/analysis/test_translate_core.py tests/exporter/analysis/test_study_passage.py -v
uv run ruff check --fix exporter/analysis/translate_core.py exporter/analysis/study_passage.py tests/exporter/analysis/test_translate_core.py tests/exporter/analysis/test_study_passage.py
uv run ruff format exporter/analysis/translate_core.py exporter/analysis/study_passage.py tests/exporter/analysis/test_translate_core.py tests/exporter/analysis/test_study_passage.py
uv run pyright exporter/analysis/translate_core.py exporter/analysis/study_passage.py tests/exporter/analysis/test_translate_core.py tests/exporter/analysis/test_study_passage.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py exporter/analysis/study_passage.py tests/exporter/analysis/test_translate_core.py tests/exporter/analysis/test_study_passage.py
```
Live smoke:
`printf 'DHP23\n' | uv run python exporter/analysis/study_passage.py --debug --provider antigravity_cli --model "GPT-OSS 120B (Medium)"`
— then confirm in `exporter/analysis/reports/DHP23_ai_raw.txt` that EVERY section
status names `antigravity_cli/GPT-OSS 120B (Medium)` (first, reformat if any,
translation if any, retries). Also one default-path smoke
(`printf 'TH145\n' | ... --debug`) confirming statuses still show the normal
Flash-first chain.

### Out of scope
- Other `translate_sentence` callers (`ai_batch_translate.py`,
  `ai_pali_translate.py`): the new parameter defaults to None; do not modify them.
- Any change to `AIManager.request` selection logic.
- Findings 29 and 30.

---

## Finding 29 — stop reporting partial agy timeouts as clean SUCCESS

Status: IMPLEMENTED 2026-06-11. Impact: medium (status honesty/auditability +
cleaner JSON input to the parser).

### Problem
`_classify_error_text` (`tools/ai_antigravity_cli.py:174-190`) only detects the case
where the ENTIRE stripped response is a single-line `Error: ...` message. When agy
streams partial content and THEN times out, the response is partial content plus a
trailing `Error: timed out waiting for response` line — it passes through as model
content and the run is reported `SUCCESS in 158s` (live evidence: `AN3.23_p1` chunk 1,
`MN8_p2` first response). The handoff guardrail "do not describe a run as a pure
success unless logs show it" currently has no code support, and the trailing error
line contaminates `_parse_ai_json` input.

### Decision already made (do not re-litigate)
Keep the partial content and continue the normal salvage → reformat → retry pipeline
(it demonstrably recovered both live cases to full coverage); hard-failing would
discard salvageable scores and burn another ~150s call. Only the STATUS becomes
honest and the error line is stripped from the content.

### Files to change
- `tools/ai_antigravity_cli.py` (implementation)
- `tests/tools/test_ai_antigravity_cli.py` (tests)

### Exact current anchors (verified 2026-06-11)
- `_Response` NamedTuple: lines 25-27.
- `AntigravityCliManager.request`: lines 30-48; on success returns
  `_Response(content=content, status_message=f"antigravity_cli/{model}")`.
- `generate_content`: lines 74-120; calls `_extract_response` (114), empty check
  (115-116), `_classify_error_text` (117-119). Leave `generate_content` and
  `get_working_key` untouched — the split happens in `request()`.
- `_classify_error_text`: lines 174-190; `MAX_ERROR_LINE_LENGTH = 200` at line 23.
- `tools/ai_manager.py:205-215` (verified): on success AIManager appends the
  provider's `status_message` in parentheses when it is not already a substring of
  `SUCCESS in Xs. {provider}/{model}` and does not start with `"Success"`. So a
  provider status of `partial: ...` propagates automatically into the final status,
  raw logs, and debug JSON with NO changes to AIManager or translate_core.
- Existing tests that MUST keep passing unchanged
  (tests/tools/test_ai_antigravity_cli.py): `_patch_agy` helper (line 11),
  `test_request_classifies_timeout_text_as_provider_error` (line 54: whole-response
  error stays a provider failure), `test_request_keeps_normal_json_response`
  (line 84), `test_request_keeps_multiline_content_mentioning_error` (line 94: its
  last line is `' "scores": {}}'`, which does not start with `Error:` — safe).

### Implementation
1. Add a helper to `tools/ai_antigravity_cli.py` (place near `_classify_error_text`):
```python
def _split_trailing_error(response: str) -> tuple[str, str | None]:
    """Split a trailing single-line agy error off partial streamed content.

    agy can stream partial model output and then print
    "Error: timed out waiting for response" as the final line while exiting 0.
    The whole-response error case is handled by _classify_error_text; this helper
    handles the partial-content case so the status can be marked partial.
    """
    lines = response.rstrip().splitlines()
    if len(lines) < 2:
        return response, None
    last = lines[-1].strip()
    if last.startswith("Error:") and len(last) <= MAX_ERROR_LINE_LENGTH:
        content = "\n".join(lines[:-1]).rstrip()
        if content:
            return content, last
    return response, None
```
2. In `AntigravityCliManager.request` (lines 39-48), after `generate_content`
   succeeds:
```python
content = generate_content(...)
content, trailing_error = _split_trailing_error(content)
status_message = f"antigravity_cli/{model}"
if trailing_error:
    status_message = f"partial: {trailing_error}"
return _Response(content=content, status_message=status_message)
```
   Final composed status for a partial run becomes
   `SUCCESS in 158.36s. antigravity_cli/Gemini 3.5 Flash (High) (partial: Error: timed out waiting for response)`.
3. Tradeoffs to record in the handoff entry (already accepted by approval):
   - The stripped error line no longer appears inside `raw_response` debug fields;
     the information moves to the status string. The full unstripped stdout is not
     preserved anywhere — acceptable; the status carries the error text verbatim.
   - Theoretical false positive: legitimate model content whose final line starts
     with `Error:` and is ≤200 chars would be stripped and flagged. For JSON-oriented
     prompts (responses end with `}`), this is negligible.

### Tests (tests/tools/test_ai_antigravity_cli.py)
Write FIRST, confirm red. Use the existing `_patch_agy(monkeypatch, stdout)` helper.
1. `test_request_strips_trailing_timeout_line_and_marks_partial` — stdout =
   `'{"translation": "x",\n "scores": {\nError: timed out waiting for response'`
   (truncated JSON + trailing error, mirroring AN3.23_p1). Assert
   `response.content == '{"translation": "x",\n "scores": {'` and
   `"partial: Error: timed out waiting for response" in response.status_message`.
   Expected red-state failure: content keeps the error line and status is the plain
   `antigravity_cli/...` string.
2. `test_split_trailing_error_cases` — direct unit test: (a) whole-response
   single-line error → returned unchanged with `None` (that path belongs to
   `_classify_error_text`); (b) clean JSON → unchanged, `None`; (c) content +
   trailing error → split; (d) trailing line over `MAX_ERROR_LINE_LENGTH` starting
   with `Error:` → unchanged, `None`.
3. Regression gate: tests at lines 54, 84, and 94 must pass unchanged.

### Verification commands
```
uv run pytest tests/tools/test_ai_antigravity_cli.py -v
uv run ruff check --fix tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py
uv run ruff format tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py
uv run pyright tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py
uv run --with pyrefly pyrefly check --min-severity warn tools/ai_antigravity_cli.py tests/tools/test_ai_antigravity_cli.py
```
Live smoke: one normal `--debug` run (e.g. `TH145`) confirming a clean response still
reports the plain SUCCESS status with no `partial:` marker. A live partial-timeout
cannot be triggered on demand; the unit tests cover it.

### Out of scope
- Hard-failing partial responses or changing fallback behavior.
- Preserving full unstripped stdout in debug JSON.
- The tool-call-text marker (Finding 30 step 4).

---

## Finding 30 — keep agy tool-call side effects out of the repo (cwd isolation)

Status: IMPLEMENTED 2026-06-11. Impact: medium (containment: the analyzer must
never mutate the working tree mid-run). Implemented AFTER Finding 29. Probe A and
Probe B both passed, so cwd isolation and `--sandbox` were both adopted.

### Problem
During `MN8_p2`, agy executed `write_to_file` tool actions and created nine scratch
scripts inside the repo (`temp/disambiguate/*.py`). The prompt wrapper's "do not use
tools" instruction (`ai_antigravity_cli.py:130-144`) is advisory only. The subprocess
in `run_antigravity_print` (`tools/antigravity_cli_models.py:48-55`) inherits the repo
cwd, so agy's workspace IS the repo: it can read and write repo files. `agy --help`
shows no tool-disabling flag, but `--sandbox` exists with unverified semantics.

### Files to change
- `tools/antigravity_cli_models.py` (implementation)
- `tests/tools/test_antigravity_cli_models.py` (NEW test file)
- `tools/ai_antigravity_cli.py` + `tests/tools/test_ai_antigravity_cli.py`
  (step 4 marker only)

### Step 1 — live probes (run BEFORE any code change; record results in handoff)
- Probe A (cwd isolation): from a scratch directory OUTSIDE the repo, run:
  `cd "$(mktemp -d)" && agy --model "Gemini 3.5 Flash (Low)" --print "Return OK only." --print-timeout 60s`
  - PASS = returncode 0 and a normal short response. → proceed to step 2.
  - FAIL (auth/config error that does not occur from the repo cwd) → STOP. Do not
    implement cwd isolation. Record the failure output in the handoff and report the
    blocker to the user; steps 2-3 are cancelled, step 4 may still proceed.
- Probe B (`--sandbox`): from the repo cwd, run:
  `agy --sandbox --model "Gemini 3.5 Flash (Low)" --print "Return OK only." --print-timeout 60s`
  - PASS = returncode 0 and a normal short response. → include `--sandbox` in step 2.
  - FAIL or odd output → skip the flag, record the observed behavior in the handoff.

### Step 2 — implementation (gated on Probe A PASS)
In `tools/antigravity_cli_models.py`:
1. Add `import tempfile` to the imports.
2. In `run_antigravity_print` (lines 32-60), run the subprocess from a disposable
   scratch directory so any agy tool writes land outside the repo:
```python
    with tempfile.TemporaryDirectory(prefix="agy_print_") as scratch_dir:
        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
            cwd=scratch_dir,
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=timeout + 10,
        )
```
3. If Probe B passed: insert `"--sandbox",` into the `command` list (after
   `str(agy_path)`).

### Step 3 — tests (gated on Probe A PASS)
NEW file `tests/tools/test_antigravity_cli_models.py` (no test file exists for this
module yet — verified 2026-06-11). Write FIRST, confirm red. Monkeypatch
`subprocess.run` inside `tools.antigravity_cli_models`, capture the call kwargs,
return a stub `CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")`.
1. `test_run_antigravity_print_uses_isolated_cwd` — call
   `run_antigravity_print(Path("/usr/bin/false"), "m", "p")`; assert the captured
   `cwd` kwarg is not None, existed at call time (capture
   `Path(cwd).is_dir()` inside the fake), and is NOT inside `Path.cwd()`
   (`Path.cwd() not in Path(cwd).parents and Path(cwd) != Path.cwd()`).
   Expected red-state failure: `cwd` kwarg absent.
2. If Probe B passed: `test_run_antigravity_print_passes_sandbox_flag` — assert
   `"--sandbox"` is in the captured command list. (Skip this test if `--sandbox` was
   not adopted.)
3. Existing behavior pins: command still contains `--model`, the model name,
   `--print`, the prompt, `--print-timeout`, `f"{timeout}s"`; `timeout` kwarg is
   `timeout + 10`.

### Step 4 — tool-call-text status marker (not gated; always implement)
In `tools/ai_antigravity_cli.py`, extend the Finding 29 warning logic in
`AntigravityCliManager.request`:
1. Module constant: `TOOL_CALL_MARKER = "include:default_api:"`.
2. Build warnings as a list:
```python
warnings: list[str] = []
content, trailing_error = _split_trailing_error(content)
if trailing_error:
    warnings.append(f"partial: {trailing_error}")
if TOOL_CALL_MARKER in content:
    warnings.append("tool-call text in response")
status_message = "; ".join(warnings) if warnings else f"antigravity_cli/{model}"
```
3. Test (tests/tools/test_ai_antigravity_cli.py), write first:
   `test_request_marks_tool_call_text_in_status` — stdout containing
   `include:default_api:write_to_file{...}` plus a trailing timeout line (mirroring
   MN8_p2); assert content is kept (minus the trailing error line) and
   `status_message` contains BOTH `partial:` and `tool-call text in response`.

### Verification commands
```
uv run pytest tests/tools/test_antigravity_cli_models.py tests/tools/test_ai_antigravity_cli.py -v
uv run ruff check --fix tools/antigravity_cli_models.py tools/ai_antigravity_cli.py tests/tools/test_antigravity_cli_models.py tests/tools/test_ai_antigravity_cli.py
uv run ruff format tools/antigravity_cli_models.py tools/ai_antigravity_cli.py tests/tools/test_antigravity_cli_models.py tests/tools/test_ai_antigravity_cli.py
uv run pyright tools/antigravity_cli_models.py tools/ai_antigravity_cli.py tests/tools/test_antigravity_cli_models.py tests/tools/test_ai_antigravity_cli.py
uv run --with pyrefly pyrefly check --min-severity warn tools/antigravity_cli_models.py tools/ai_antigravity_cli.py tests/tools/test_antigravity_cli_models.py tests/tools/test_ai_antigravity_cli.py
```
Live smoke: one full normal run
(`printf 'TH145\n' | uv run python exporter/analysis/study_passage.py --debug`) —
confirm a clean SUCCESS status and that `git status --short` shows no new files
created inside the repo by the run (beyond the expected
`exporter/analysis/reports|output` artifacts).

Tradeoffs and uncertainties (accepted by approval):
- cwd isolation also stops agy from READING repo files — desirable for a pure-prompt
  API, but if a future prompt intentionally references local files it will break;
  none do today.
- `--sandbox` semantics are agy-internal; the probe gate is the only safety. Revert is
  one list element.
- agy may still write into its OWN config/log locations (e.g. `~/.agy`); out of scope.

### Out of scope
- Disabling agy tools entirely (no such flag exists).
- Changing the prompt wrapper text in `_build_prompt`.
- A repo-level guard/watcher for unexpected file writes.

---

## Observations recorded, no action proposed
- First-response schema unevenness is model nondeterminism; the recovery pipeline
  achieved 0 missing groups in all six prep runs. Re-evaluate only if a live run ends
  with unresolved groups.
- GPT-OSS fallback under real Flash quota exhaustion: watch item. When a window
  occurs, use the Finding 28 flags to capture live evidence.
- Pali grammar accuracy (old Finding 5) remains deferred — model quality, not code.

## Session ordering and closure rules
1. APPROVED execution order (user approval 2026-06-11): **28 → 29 → 30**.
2. One finding per session. At session start, implement the first finding above not
   marked IMPLEMENTED.
3. After each implemented finding, append a completed-issue entry to `handoff.md` in
   the existing format and mark the section here IMPLEMENTED with the date.
4. Keep `plan.md` stable — no checkboxes, no per-issue history there.
5. Prepare a draft commit message referencing `#197`; the user commits.
