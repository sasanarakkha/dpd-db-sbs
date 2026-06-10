# Handoff: exporter_analysis_loop

## Current Status
- This is an ongoing Kamma feedback-loop thread for `exporter/analysis/` under GitHub issue
  `#197`.
- This file is now a historical handoff for old sessions, not an execution queue.
- Issues 1-21 are implemented. No approved queued finding remains.
- Latest preparation-only live-run evidence was added on 2026-06-10 for
  `TH66`, `DHP77`, `AN4.43_p1`, `MN122_p2`, and `DN2_p3`; see
  "Live Debug Prep Session - 2026-06-10" below.
- For the next session, ask the user for one concrete `exporter/analysis/` issue, inspect
  current source/tests, propose a focused plan, and stop for explicit approval before edits.
- 2026-06-10: Findings 11-12 were implemented as Issues 20-21. Findings 13-14 remain in
  `kamma/threads/exporter_analysis_loop/findings_11_14_plans.md` and are PENDING USER
  APPROVAL — do not implement without it; one finding per session.
- Keep `plan.md` stable. Do not add recurring task-list checkboxes to this loop thread.

## Completed History
- Issue 1: added `UD` and `ITI` passage-code support.
  - Achieved: `UD12` and `ITI37` are accepted prefixes and extract from KN3/KN4 as
    verse-style sources.
  - Main files: `exporter/analysis/passage_by_code.py`,
    `exporter/analysis/study_passage.py`, `exporter/analysis/passage_extraction.py`,
    `tests/exporter/analysis/test_passage_by_code.py`.
  - Validation included focused passage-code tests and extraction smoke checks for `UD12`
    and `ITI37`.

- Issue 2: filtered synthetic particle-expanded headword candidates.
  - Achieved: analyzer output keeps real sandhi/direct grammar matches while dropping noisy
    particle-deconstructor base headwords such as the wrong base candidate for `yañ'ca`.
  - Main files: `exporter/analysis/analyzer.py`,
    `tests/exporter/analysis/test_analyzer.py`.
  - Validation covered `yañ'ca`, `yañcidaṃ`, `soḷasinti`, `jānāti`, and `bhavissanti`.

- Issue 3: printed explicit local JSON analysis progress.
  - Achieved: `study_passage.py` shows the local analysis stage separately from AI analysis.
  - Main files: `exporter/analysis/translate_core.py`,
    `exporter/analysis/study_passage.py`,
    `tests/exporter/analysis/test_translate_core.py`.
  - Validation covered progress events and targeted exporter-analysis tests.

- Issue 4: fixed example bolding inside compound/sandhi verse tokens.
  - Achieved: database-inflection matches such as `sukhaṃ`, `taṇhakkhaya`, `taṇha`, and
    `khaya` are bolded correctly without over-bolding compound prefixes.
  - Main files: `exporter/analysis/example_bolding.py`,
    `tests/exporter/analysis/test_example_bolding.py`.
  - Validation included focused tests plus regenerated `UD12_words.csv` inspection.

- Issue 5: fixed missing AI-score handling and fallback selection for compound components.
  - Achieved: missing AI scores are auditable as missing, retryable once, and fallback
    selection no longer chooses implausible component meanings such as `sammā | nt | cymbal`
    in `sammāsambuddhassa`.
  - Main files: `exporter/analysis/translate_core.py`,
    `exporter/analysis/analyzer.py`, `exporter/analysis/study_passage.py`,
    `tests/exporter/analysis/test_translate_core.py`,
    `tests/exporter/analysis/test_analyzer.py`.
  - Validation included targeted tests, ruff, pyright, and debug artifact generation.

- Issue 6: clipped exported word-card examples to the relevant bolded context.
  - Achieved: prose exports use the sentence containing the bolded word; gāthā exports use a
    bounded line window instead of whole passages.
  - Main files: `exporter/analysis/export_words_csv.py`,
    `tests/exporter/analysis/test_export_words_csv.py`.
  - Validation included focused CSV tests and regenerated `SN12.4_words.csv` inspection.

- Issue 7: strengthened AI response handling for wrong-format responses.
  - Achieved: prompts were tightened, non-contract JSON can go through reformat fallback,
    and `--debug` can write raw response logs.
  - Main files: `exporter/analysis/translate_core.py`,
    `exporter/analysis/study_passage.py`,
    `tests/exporter/analysis/test_translate_core.py`.
  - Validation included mocked regression tests and real `study_passage.py --debug` runs.

- Issue 8 / Finding 1: accepted compact `{surface_word: option_key}` maps.
  - Achieved: antigravity's common compact map response can be used directly, deriving score
    selections and using a lighter translation-only follow-up.
  - Main files: `exporter/analysis/translate_core.py`,
    `tests/exporter/analysis/test_translate_core.py`.
  - Validation included focused map-path tests and live passage analysis.

- Issue 9 / Finding 2: raised the global AI request cap from 60s to 150s.
  - Achieved: working CLI responses that exceed 60 seconds no longer fail prematurely.
  - Main files: `tools/ai_manager.py`, related tests.
  - Validation included focused tests and live TH52 evidence that the previous cap was too
    short.

- Issue 10: added per-model timeout support and set antigravity timeout to 90s.
  - Achieved: `antigravity_cli` gets an effective hard kill near 100s instead of inheriting
    the global 150s cap plus subprocess margin.
  - Main files: `tools/ai_manager.py`, `tools/ai_models.json`,
    `tools/ai_antigravity_cli.py`, related tests.
  - Validation included timeout tests and live provider behavior.

- Issue 11 / Finding 3B: fixed the missing-scores retry schema prompt.
  - Achieved: retry responses are instructed to return `{"score": N}` objects and to include
    `contextual_meaning` for `decon_` keys.
  - Main files: `exporter/analysis/translate_core.py`,
    `tests/exporter/analysis/test_translate_core.py`.
  - Validation included prompt-shape regression tests.

- Issue 12 / Finding 3A: handled nested `{"disambiguation": {...}}` maps.
  - Achieved: nested disambiguation maps use the same translation-only word-key path as flat
    maps.
  - Main files: `exporter/analysis/translate_core.py`,
    `tests/exporter/analysis/test_translate_core.py`.
  - Validation included unit coverage. Important caveat: one live smoke passed through a
    fallback path and did not prove this exact nested-map path live.

- Issue 13 / Finding 4: preserved AI metadata when deterministic scoring overrides score.
  - Achieved: deterministic `db_example_match` score/source overrides do not discard useful
    AI `contextual_meaning` and `selected_pos` from full-schema responses.
  - Main files: `exporter/analysis/translate_core.py`,
    `tests/exporter/analysis/test_translate_core.py`.
  - Validation included targeted regression tests.

- Issue 14 / Finding 6: added contextual meanings to the compact word-key map path.
  - Achieved: compact map responses now request and apply short contextual meanings before
    deterministic DB-example scoring, so mapped rows do not fall back to verbose DB glosses.
  - Main files: `exporter/analysis/translate_core.py`,
    `tests/exporter/analysis/test_translate_core.py`.
  - Validation included red/green tests and a live TH50 run that exercised the compact map
    path.

- Issue 15: removed the deprecated `gemini_cli` provider.
  - Achieved: deleted the dead `tools/ai_gemini_cli.py` provider, removed
    `gemini_cli_work_models`, and removed provider initialization from `AIManager`.
  - Main files: `tools/ai_gemini_cli.py` deleted, `tools/ai_models.json`,
    `tools/ai_manager.py`, `tests/tools/test_ai_manager.py`.
  - Validation passed ruff, pyright, pyrefly, focused `tests/tools/test_ai_manager.py`, and a
    source sweep. The only tolerated remaining `gemini_cli` string was a historical output
    artifact: `exporter/analysis/output/TH52_ai_debug.json`.

- Issue 16 / Finding 7: compacted dictionary-context JSON.
  - Achieved: first prompts and missing-scores retry prompts use
    `json.dumps(..., separators=(",", ":"))`, reducing prompt size by roughly 24-36%.
  - Main files: `exporter/analysis/translate_core.py`,
    `tests/exporter/analysis/test_translate_core.py`.
  - Validation passed ruff, format, pyright, pyrefly, full
    `tests/exporter/analysis/test_translate_core.py`, and live TH50 plus MN12 paragraph 2
    gates. MN12_p2 system prompt size after the change was 509,171 chars.

- Issue 17 / Finding 8: added pre-flight argv-size guard for `antigravity_cli`.
  - Achieved: prompts over 700,000 UTF-8 bytes fail immediately with a provider error before
    `agy` lookup/spawn, avoiding macOS `E2BIG` crashes.
  - Main files: `tools/ai_antigravity_cli.py`,
    `tests/tools/test_ai_antigravity_cli.py`.
  - Validation passed ruff, format, pyright, pyrefly, focused tests, and a live AN4.12
    paragraph 1 gate where the guard triggered and fallback completed.

- Issue 18 / Finding 9: kept failed-provider details in fallback success statuses.
  - Achieved: when one provider fails and a later provider succeeds, the success
    `status_message` now includes the earlier failed attempt details while preserving the
    clean-success format when there were no prior failures.
  - Main files: `tools/ai_manager.py`, `tests/tools/test_ai_manager.py`.
  - Validation passed ruff, format, pyright, pyrefly, and focused
    `tests/tools/test_ai_manager.py`.

- Issue 19 / Finding 10: shortened the interactive passage-selection preview.
  - Achieved: `study_passage.py` selector prints the same header as extraction preview, then
    one counted, truncated line per unit; extraction-only full previews are unchanged.
  - Main files: `exporter/analysis/study_passage.py`,
    `tests/exporter/analysis/test_study_passage.py`.
  - Validation passed red/green truncation test, ruff, format, pyright, pyrefly, focused
    `tests/exporter/analysis/test_study_passage.py`, and a live DN14 paragraph 3 gate. The
    first live attempt hit the known uv cache permission issue; rerun with
    `UV_CACHE_DIR=/private/tmp/uv-cache` passed.

- Issue 20 / Finding 11: classified `agy` timeout/auth stdout as provider failure.
  - Achieved: short single-line `Error:` responses and Google OAuth login prompts printed
    by `agy` on stdout with exit code 0 now become `AntigravityCliProviderError`, allowing
    `AIManager` fallback instead of treating them as successful model content.
  - Main files: `tools/ai_antigravity_cli.py`,
    `tests/tools/test_ai_antigravity_cli.py`.
  - Validation passed red/green tests, ruff check --fix, ruff format, pyright, pyrefly, and
    focused `tests/tools/test_ai_antigravity_cli.py`.
  - No live smoke was run; the approved plan marked it optional and not deterministic for
    the error-classification path.

- Issue 21 / Finding 12: accepted flat retry score maps without a `scores` wrapper.
  - Achieved: missing-scores retry responses shaped like
    `{"60789_0": {"score": 10}}` are coerced into the normal `scores` contract when the
    keys match the expected missing option keys, while unrelated flat maps stay ignored.
  - Main files: `exporter/analysis/translate_core.py`,
    `tests/exporter/analysis/test_translate_core.py`.
  - Validation passed red/green tests, ruff check --fix, ruff format, pyright, pyrefly, and
    focused `tests/exporter/analysis/test_translate_core.py`.
  - No live smoke was run; the approved plan marked it optional because the flat-map retry
    shape is model-nondeterministic.

## Live Debug Prep Session - 2026-06-10
- Purpose: preparation evidence for a later advanced-model analysis, not an approved code
  change. No source or test files were edited. `plan.md` was left stable.
- Requested latest targets superseded the earlier interrupted target list:
  `TH66`, `DHP77`, `AN4.43` paragraph 1, `MN122` paragraph 2, and `DN2` paragraph 3.
- Extraction previews confirmed target units:
  - `TH66`: 1 verse.
  - `DHP77`: 1 verse.
  - `AN4.43`: 6 paragraphs; selected paragraph 1.
  - `MN122`: 25 paragraphs; selected paragraph 2.
  - `DN2`: 117 paragraphs; selected paragraph 3.
- Commands run, each as a separate `study_passage.py --debug` invocation:
  - `printf 'TH66\n' | UV_CACHE_DIR=/private/tmp/uv-cache uv run python exporter/analysis/study_passage.py --debug`
  - `printf 'DHP77\n' | UV_CACHE_DIR=/private/tmp/uv-cache uv run python exporter/analysis/study_passage.py --debug`
  - `printf 'AN4.43\n1\n' | UV_CACHE_DIR=/private/tmp/uv-cache uv run python exporter/analysis/study_passage.py --debug`
  - `printf 'MN122\n2\n' | UV_CACHE_DIR=/private/tmp/uv-cache uv run python exporter/analysis/study_passage.py --debug`
  - `printf 'DN2\n3\n' | UV_CACHE_DIR=/private/tmp/uv-cache uv run python exporter/analysis/study_passage.py --debug`
- Artifact references:
  - Markdown reports: `exporter/analysis/reports/TH66_study.md`,
    `exporter/analysis/reports/DHP77_study.md`,
    `exporter/analysis/reports/AN4.43_p1_study.md`,
    `exporter/analysis/reports/MN122_p2_study.md`,
    `exporter/analysis/reports/DN2_p3_study.md`.
  - Raw AI logs: `exporter/analysis/reports/TH66_ai_raw.txt`,
    `exporter/analysis/reports/DHP77_ai_raw.txt`,
    `exporter/analysis/reports/AN4.43_p1_ai_raw.txt`,
    `exporter/analysis/reports/MN122_p2_ai_raw.txt`,
    `exporter/analysis/reports/DN2_p3_ai_raw.txt`.
  - Debug JSON: `exporter/analysis/output/TH66_ai_debug.json`,
    `exporter/analysis/output/DHP77_ai_debug.json`,
    `exporter/analysis/output/AN4.43_p1_ai_debug.json`,
    `exporter/analysis/output/MN122_p2_ai_debug.json`,
    `exporter/analysis/output/DN2_p3_ai_debug.json`.
  - Study JSON: `exporter/analysis/output/TH66_study.json`,
    `exporter/analysis/output/DHP77_study.json`,
    `exporter/analysis/output/AN4.43_p1_study.json`,
    `exporter/analysis/output/MN122_p2_study.json`,
    `exporter/analysis/output/DN2_p3_study.json`.

### Prep Findings
- `TH66`:
  - First, reformat, and retry requests all went through
    `antigravity_cli/Gemini 3.5 Flash (High)`.
  - Prompt sizes from debug JSON: system prompt 244,652 bytes; user prompt 177 bytes;
    retry prompt 181,821 bytes.
  - First response status: `SUCCESS in 87.83s`; raw response used an ad-hoc
    `sentence` + `disambiguation` shape and covered only the opening phrase, not the full
    six-line verse.
  - Reformat status: `SUCCESS in 35.96s`, but debug recorded parse error
    `Expecting value: line 1 column 1 (char 0)`.
  - Pre-retry missing scores: 56 groups / 362 keys. Retry status:
    `SUCCESS in 27.82s`; retry returned a usable `scores` object with 54 entries.
  - Generated report has empty `Translation` and `Literal Translation`.

- `DHP77`:
  - First, reformat, and retry requests all went through
    `antigravity_cli/Gemini 3.5 Flash (High)`.
  - Prompt sizes: system prompt 75,585 bytes; user prompt 108 bytes; retry prompt
    16,129 bytes.
  - First response status: `SUCCESS in 19.25s`; raw response used an ad-hoc
    `sentence` + nested `disambiguation` shape.
  - Reformat status: `SUCCESS in 38.71s`; reformat succeeded with
    `translation`, `literal_translation`, and `scores`.
  - Pre-retry missing scores: 7 groups / 35 keys. Retry status:
    `SUCCESS in 15.03s`; retry returned a usable `scores` object with 32 entries.
  - Generated report includes non-empty translation and literal translation.

- `AN4.43_p1`:
  - The script attempted antigravity first, but the preflight argv guard blocked the first
    call before launching `agy`: 1,365,996 bytes > 700,000.
  - The first request then completed through fallback provider chain in 121.72s. The
    debug status preserved the failed antigravity attempt but the success portion reads
    only `Success in 121.72s`, without a clear provider name.
  - Prompt sizes from debug JSON: system prompt 1,365,423 bytes; user prompt 292 bytes;
    retry prompt 723,139 bytes. The retry antigravity wrapper size was 723,466 bytes, so
    it also hit the argv guard before launching `agy`.
  - First fallback response used the expected top-level contract
    `translation`, `literal_translation`, and `scores`; no reformat section was written.
  - Pre-retry missing scores: 168 groups / 1,506 keys. Retry fallback status:
    `SUCCESS in 73.71s`, but the raw retry response was a flat key-score map without the
    required top-level `scores` wrapper, so it contributed 0 usable retry scores.
  - Generated report includes non-empty translation and literal translation.
  - Important distinction: this run is evidence for the antigravity prompt-size guard and
    fallback behavior, not live `agy` subprocess quality for this passage.

- `MN122_p2`:
  - First, reformat, and retry requests all went through
    `antigravity_cli/Gemini 3.5 Flash (High)`.
  - Prompt sizes: system prompt 469,499 bytes; user prompt 666 bytes; retry prompt
    201,208 bytes.
  - First response status: `SUCCESS in 23.96s`; raw response used
    `sentence`, `disambiguation`, and `translation`, and covered only the opening sentence
    up through `cīvarakammaṃ`, not the whole selected paragraph.
  - Reformat status: `SUCCESS in 13.91s`; reformat succeeded with the expected top-level
    keys.
  - Pre-retry missing scores: 88 groups / 399 keys. Retry status:
    `SUCCESS in 98.84s`, but raw retry content was `Error: timed out waiting for response`;
    it contributed 0 usable retry scores.
  - Generated report translation covers only the opening sentence, while the analyzed
    passage has 64 tokens.

- `DN2_p3`:
  - First, reformat, and retry requests all went through
    `antigravity_cli/Gemini 3.5 Flash (High)`.
  - Prompt sizes: system prompt 689,777 bytes; user prompt 495 bytes; retry prompt
    492,995 bytes. This first prompt is close to the 700,000-byte antigravity guard but
    still launched.
  - First response status: `SUCCESS in 24.74s`; raw response used an ad-hoc
    `sentence_analysis` shape with `selected_key` fields and partial coverage of the
    passage.
  - Reformat status: `SUCCESS in 14.50s`; reformat succeeded with the expected top-level
    keys.
  - Pre-retry missing scores: 109 groups / 955 keys. Retry status:
    `SUCCESS in 98.92s`, but raw retry content was `Error: timed out waiting for response`;
    it contributed 0 usable retry scores.
  - Generated report includes non-empty full-paragraph translation and literal
    translation, but final score coverage remained very sparse.

### Candidate Issues For Advanced Analysis
- Antigravity wrong-contract first responses remain frequent. Fresh evidence includes
  `disambiguation` lists/maps, `sentence_analysis`, and first responses that cover only an
  opening clause/sentence.
- Some retry calls are classified as `SUCCESS` even when raw antigravity content is
  `Error: timed out waiting for response`. This looks like provider-output classification,
  not model-quality analysis.
- Missing-score retry handling may silently waste successful-looking responses:
  `AN4.43_p1` returned a flat key-score map without `scores`, and `MN122_p2`/`DN2_p3`
  returned timeout text; all three contributed 0 usable retry scores.
- `AN4.43_p1` shows that selected prose paragraphs can exceed the argv guard even after
  compact JSON. It completed by fallback, not by actual `agy` subprocess.
- Debug JSON caveat: original raw response shape should be read from `*_ai_raw.txt`.
  `debug["parsed_response"]` and related parsed dicts are mutable objects in the current
  code path and can be misleading after later normalization or fallback mutation.

## Inactive / Not Approved / Do Not Execute Automatically
- Finding 5, Pāḷi grammar accuracy:
  - Status: deferred indefinitely unless the user explicitly asks to revisit it.
  - Reason: observed grammar mistakes and non-determinism look like model-quality behavior,
    not a straightforward deterministic code bug.
  - Examples seen: near-identical TH51/TH52 verses parsed the same words differently; `me`
    was tagged instr/acc instead of gen/dat; TH52 `kāye` was tagged masc acc pl instead of
    loc sg; `sukhā` varied between correct fem nom sg and wrong masc nom pl.

- Wrong-schema first responses correlate with prompt size:
  - Status: observation only, not a queued fix.
  - Evidence: DHP30 around 30 KB returned the expected contract schema; larger prompts such
    as TH40, DN14_p3, and MN12_p2 returned valid but ad-hoc JSON schemas covering only the
    opening clause.
  - Existing reformat plus missing-scores retry recovered those runs. Do not add chunking,
    example trimming, or prompt-shape redesign without a new issue and explicit approval.

- Example/context trimming and chunking:
  - Status: out of scope for completed findings.
  - Reason: examples are large, but they support disambiguation quality. Any trimming is a
    quality tradeoff and needs a separate plan.

## Future-Session Guardrails
- One issue per session by default. If the user reports several unrelated issues, choose one
  and explicitly defer the rest.
- Do not implement before a focused per-issue plan is approved.
- Read current source and tests before describing behavior. Do not trust this handoff for
  line numbers or exact current code shape.
- For Python changes, run exact-file quality gates: `ruff check --fix`, `ruff format`,
  `pyright`, `pyrefly`, and targeted pytest.
- Never run bare `uv run pytest`; always pass a specific test path.
- If `uv run ...` fails on `/Users/deva/.cache/uv` permissions, retry with
  `UV_CACHE_DIR=/private/tmp/uv-cache`.
- Use `study_passage.py --debug` for live AI checks. It writes
  `reports/<source>_ai_raw.txt` and `output/<source>_ai_debug.json`.
- Do not claim live proof when the live run only exercised fallback behavior. Record which
  provider path actually ran.
- For original AI response shape, prefer `reports/<source>_ai_raw.txt` over
  `output/<source>_ai_debug.json` parsed-response fields.
- Watch for `Error: timed out waiting for response` in antigravity stdout; current live
  evidence shows it can be logged under a success status and then parse as zero usable
  scores.
- `AIManager.request(provider_preference=...)` only constrains provider when a model is also
  supplied; provider preference alone can fall through to the default model list.
- Effective antigravity hard kill is model timeout plus 10 seconds. With a 90s model timeout,
  expect termination near 100s.
- For user-visible output bugs, regenerate and inspect the relevant artifact before claiming
  completion.
- For this loop thread, keep `plan.md` stable and keep issue history in `handoff.md`.

## Useful Historical Artifacts
- Debug JSON and raw logs from analysis runs may exist under:
  - `exporter/analysis/output/*_ai_debug.json`
  - `exporter/analysis/reports/*_ai_raw.txt`
  - `exporter/analysis/reports/*_study.md`
- Particularly useful old evidence:
  - `TH50`: compact map path and contextual-meaning validation.
  - `TH52`: old `gemini_cli` historical artifact and timeout evidence.
  - `AN4.12_p1`: oversized prompt / argv guard / fallback status evidence.
  - `MN12_p2`: compact prompt size and wrong-schema recovery evidence.
  - `DN14_p3`: interactive selector preview and wrong-schema recovery evidence.
  - `TH66`: fresh wrong-schema + failed reformat + empty translation evidence.
  - `DHP77`: fresh wrong-schema + successful reformat/retry evidence.
  - `AN4.43_p1`: fresh argv-guard + fallback + flat retry-map evidence.
  - `MN122_p2`: fresh partial first response + retry timeout-content evidence.
  - `DN2_p3`: fresh near-guard antigravity launch + `sentence_analysis` + retry
    timeout-content evidence.

## Review Readiness
- No approved implementation task remains in this handoff.
- If the user says all `exporter/analysis/` issues are resolved, the next process step is
  `/kamma:3-review` for `kamma/threads/exporter_analysis_loop`.
