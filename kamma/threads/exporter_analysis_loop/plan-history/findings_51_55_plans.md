# Approved Implementation Queue: Findings 51–55

Status: APPROVED by the user on 2026-06-11 (full queue, including the final
live evaluation). Source analysis: the 2026-06-11 higher-model reading of
`temp/tier_eval/low_post_improvements/` and
`temp/tier_eval/deepseek_post_improvements/` (Finding 45 artifacts), recorded
in `finding_45_higher_model_summary.md` and `handoff.md`.

Model strategy decided by the user: keep `Gemini 3.5 Flash (Low)` as the
analyzer default AND keep `deepseek/deepseek-v4-flash` as an occasionally
used second model. Therefore both models must pass the final live
evaluation (Finding 55) equally — improvements must not regress either one.

## Execution order (MANDATORY)

**51 → 52 → 53 → 54 → 55**

- One finding per session (loop rule in `plan.md`). After each finding,
  update `handoff.md` per the Per-Issue Closure rules.
- Finding 53 was activated by the user's 2026-06-11 next-step update before
  Finding 54 and Finding 55. The earlier conditional ordering is superseded
  for the remaining queue.
- Findings 51, 52, 53, 54 are code/prompt changes with TDD. Finding 55 is
  evidence-only (no source changes).

## Shared constraints (same as Findings 45–50)

- TDD where practical: write the failing test first, run it, confirm it
  fails for the expected reason, then implement.
- Quality gates per changed Python file:
  1. `uv run ruff check --fix <files>`
  2. `uv run ruff format <files>`
  3. `uv run pyright <files>`
  4. `uv run --with pyrefly pyrefly check --min-severity warn <files>`
  5. `uv run pytest <specific test files> -v`
- Never run bare `uv run pytest`; always pass the specific test file path.
- Modern type hints, `Path` from pathlib, no `sys.path` hacks.
- POSIX-compatible shell commands under zsh; temp probes under `temp/` only.
  In zsh never use `path` as a loop variable (shadows `$PATH`); use `src`.
- `temp/tier_eval/` retention exception continues until Finding 55 is
  complete and the user releases it. Finding 55 artifacts go into
  `temp/tier_eval/final_eval_low/` and `temp/tier_eval/final_eval_deepseek/`.
- Line-number anchors below were verified on 2026-06-11. Re-read current
  source before editing; earlier findings in this queue shift lines.

## Evidence summary driving this queue (read once, do not re-derive)

- Per-target quality verdict on the Finding 45 artifacts: Low won TH215,
  DHP211, SN15.1 p2; DeepSeek won MN41 p2; AN3.33 p1 roughly even.
  Low stays default; DeepSeek stays the occasional second model.
- The dominant Low defect is PIPELINE-caused, not model-caused: selections
  recovered through the missing-score retry path carry no
  `contextual_meaning`, so the report falls back to the full raw dictionary
  meaning string. Counted score-10 selections with no meaning
  (Low vs DeepSeek): TH215 12/18 vs 19/27; AN3.33 40/58 vs 23/63;
  MN41 43/77 vs 19/70; SN15.1 **87/105 vs 14/102**.
  Verified mechanism: `_build_missing_scores_prompt` orders
  `{"score": N}`-only values and says "Do not translate again"
  (`translate_core.py:774–775`), and only `decon_` keys are exempt.
- The `(singular)/(plural)` parentheticals in Low's MN41 `app'ekacce` row are
  dictionary fallback text shown because `7117_0` had `{"score": 10}` with no
  meaning — NOT AI pollution. Do not widen the Finding 48 sanitizer to
  dictionary text.
- The AN3.33 `bhagavā` nominative-for-vocative failure is structurally
  blocked by the one-selection-per-surface-word limitation (the same chunk
  contains a genuine nominative `bhagavā`). It is NOT a prompt/model bug.
  Do not chase it; it is documented in `exporter/analysis/README.md`
  (Finding 50). It is excluded from Finding 55 acceptance criteria.
- DeepSeek's lower final-score counts (169 vs 239 on MN41 etc.) are benign:
  keys are `{id}_{variant}` per option; both providers had zero missing
  groups after retry and identical visible rows; Low's extra calls simply
  scored more alternative options.
- The system prompt (`build_system_prompt`, `translate_core.py:1400–1452`)
  contains only mechanical instructions and zero Pāḷi-specific
  disambiguation guidance — Finding 52 adds it.

---

## Finding 51 — retry-recovered selections must carry contextual meanings

Status: COMPLETE (2026-06-11). Impact: HIGH — removes the dominant visible quality gap on
the Low/Gemini path (87/105 meaning-less selections on SN15.1 p2) with ZERO
extra AI calls. Also benefits DeepSeek (its retry-recovered words have the
same gap, just fewer of them).

### Problem (evidence)
- `_build_missing_scores_prompt` (`translate_core.py:752–780`) instructs:
  values are `{"score": N}` and "Do not translate again and do not
  explain." Only `decon_` keys get a `contextual_meaning` requirement.
- Result: every word recovered via the retry pass renders with the full raw
  dictionary `meaning_combo` string in the report (e.g. the
  `(singular) a certain; (plural) some...` row for `app'ekacce`, the
  five-epithet `bhagavā` rows, wrong-tense "is; is being; becomes" for
  `bhavissan'ti`).
- Verified in `temp/tier_eval/low_post_improvements/MN41_p2_ai_debug.json`:
  `7117_0` is `{"score": 10}` (no meaning) for Low, while DeepSeek's
  first-pass entry is `{"score":10,"contextual_meaning":"some",...}`.

### Exact current anchors (verified 2026-06-11)
- Retry prompt builder: `_build_missing_scores_prompt`,
  `translate_core.py:752` (score-only instruction at lines 774–775,
  `decon_instruction` at 763–769).
- Retry pass: `_request_missing_score_retry_pass`,
  `translate_core.py:783`; response handling at 814–822
  (`_parse_ai_json` → `_normalize_ai_response` → `_coerce_flat_score_map`
  → `scores_map.update`).
- IMPORTANT ordering bug to avoid: `_normalize_ai_response` (which strips
  grammar annotations from `contextual_meaning`) runs at line 818 BEFORE
  `_coerce_flat_score_map` at line 819. For a flat `{key: N}` response the
  normalize call is a no-op, and meanings inside a `{"scores": {...}}`
  retry response are normalized fine — but meanings arriving inside a flat
  `{key: {"score": N, "contextual_meaning": ...}}` shape are coerced AFTER
  normalization and would skip grammar stripping. The implementation must
  guarantee stripping for retry meanings regardless of shape.

### Files to change
- `exporter/analysis/translate_core.py`
- `tests/exporter/analysis/test_translate_core.py`

### Implementation
1. In `_build_missing_scores_prompt`, change the value-shape instruction:
   for the option you score **10** in each group, include a short
   `"contextual_meaning"` (fitted to the sentence, core meaning only); for
   lower-scored alternatives, `{"score": N}` alone remains correct. Keep
   "Do not translate again" for the prose translation (we still do not want
   `translation`/`literal_translation` from retries). Keep the existing
   `decon_instruction` and `NO_GRAMMAR_NOTES_INSTRUCTION` lines.
   Suggested wording to add after line 775:
   `For the single best option per word (score 10), also include
   "contextual_meaning": a short English meaning fitted to this sentence.`
2. In `_request_missing_score_retry_pass`, after
   `_coerce_flat_score_map(...)` (line 819), apply grammar-annotation
   stripping to any `contextual_meaning` values in the coerced scores
   before `scores_map.update(...)` — simplest: run the coerced dict
   through `_normalize_ai_response` again, or call
   `_strip_grammar_annotations` on each meaning. Pick whichever keeps
   pyright/pyrefly clean; do not duplicate stripping logic.
3. Do NOT touch the compact-map flow (`_handle_compact_map_response`) —
   it already requests and merges meanings for all mapped surface words
   (lines 953–987). Do NOT add a separate meaning-fill AI call.
4. Deterministic `db_example_match` selections legitimately have no
   AI meaning (the dictionary meaning is editor-validated for that exact
   verse); leave them alone.

### Tests — write FIRST, confirm red
In `tests/exporter/analysis/test_translate_core.py`:
1. `test_missing_scores_prompt_requests_contextual_meaning_for_best_option`
   — `_build_missing_scores_prompt(...)` output contains the new
   instruction text.
2. `test_retry_scores_merge_contextual_meanings` — stub a retry response
   `{"scores": {"123_0": {"score": 10, "contextual_meaning": "some"}}}`
   through the retry pass → `scores_map["123_0"]["contextual_meaning"]`
   == "some".
3. `test_retry_flat_shape_meanings_are_grammar_stripped` — stub a flat
   retry response `{"123_0": {"score": 10, "contextual_meaning":
   "the Blessed One (accusative)"}}` → merged meaning has the
   parenthetical removed (covers the coercion-after-normalize ordering).
4. Existing retry tests still pass unchanged.

### Verification commands
```
uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pytest tests/exporter/analysis/test_translate_core.py -v
```

### Implementation outcome - 2026-06-11
- `_build_missing_scores_prompt` now asks retries to include a short
  `contextual_meaning` for the single score-10 best option per word while
  preserving the no-translation retry constraint.
- `_request_missing_score_retry_pass` normalizes retry data again after flat
  score-map coercion, so contextual meanings from flat retry shapes also get
  grammar annotations stripped before merging.
- Added focused tests for the retry prompt instruction, normal retry
  contextual-meaning merge, and flat retry grammar stripping.
- Validation passed:
  `uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pytest tests/exporter/analysis/test_translate_core.py -v` (84 passed, one third-party `aksharamukha` deprecation warning).

### Out of scope
- Extra meaning-fill AI calls; compact-map flow changes; report-rendering
  fallback changes in `analyzer.py`/`study_passage.py`.

---

## Finding 52 — Common Pāḷi Disambiguation Rules block in the system prompt

Status: COMPLETE (2026-06-11). Impact: MEDIUM-HIGH — directly targets the observed
repeated selection mistakes, including Low's MN41 closing-question case
cluster regression and the shared `upapajjantī'ti` failure.

### Problem (evidence)
- Fresh Low on MN41 p2 selected nominative `bhedā`, nominative `maraṇā`,
  nominative `paraṃ`, dative `kāyassa`, noun-row `saggaṃ` in the stock
  formula `kāyassa bhedā paraṃ maraṇā ...` (DeepSeek got these right).
- BOTH models picked `upapajjantī + iti` (fem nom sg participle) instead of
  the offered correct `upapajjanti + iti` (pr 3rd pl) for `upapajjantī'ti`.
- Low picked plain-instrumental `yena`/`tena` in MN41 instead of the
  `yena ... tena` "where ... there" idiom rows it correctly used in AN3.33;
  Low picked nominative `bho` ("Master") where DeepSeek's vocative "sir"
  is correct.
- The system prompt has no Pāḷi-specific guidance at all.

### Exact current anchors (verified 2026-06-11)
- `build_system_prompt`: `translate_core.py:1400–1452`. Insert the new
  block after instruction 6 ("Use Existing Examples for Disambiguation",
  lines 1424–1427) and before `{disambiguation_block}` (line 1428).

### Files to change
- `exporter/analysis/translate_core.py`
- `tests/exporter/analysis/test_translate_core.py`

### Implementation
1. Add a module-level constant `COMMON_PALI_RULES` (keeps the f-string
   prompt readable and lets tests assert on the constant):
   ```python
   COMMON_PALI_RULES = """### Common Pāḷi Disambiguation Rules:
   - In the stock phrase `kāyassa bhedā paraṃ maraṇā`, `kāyassa` is genitive, `bhedā` and `maraṇā` are ablative singular ("after the breakup of the body, after death"), and `paraṃ` is the indeclinable preposition "after" — never nominative plurals.
   - Final-vowel lengthening before quotative `'ti` is sandhi: for words ending in -ī'ti / -ā'ti / -ū'ti at the end of a quotation, prefer the deconstruction that restores the short final vowel (e.g. `upapajjanti + iti`, a finite verb), not a long-vowel feminine/participle reading, unless the context clearly requires one.
   - In the formula `yena <person/place> tena upasaṅkami`, `yena` and `tena` are the adverbial "where ... there" rows, not plain instrumental pronouns.
   - Inside direct speech, a word set off by commas that addresses the listener (e.g. `bho`, a teacher's name) is usually vocative.
   """
   ```
   (Exact wording may be tightened during implementation; keep it ≤ ~6
   lines so prompt size stays bounded. Do NOT add passage-specific words
   beyond the canonical formulas above.)
2. Insert `{COMMON_PALI_RULES}` into the `build_system_prompt` f-string
   between instruction 6 and `{disambiguation_block}`.
3. Main prompt only. Do NOT add this block to reformat/retry/translation
   prompts (they are size-bounded recovery paths; the first-pass selection
   is where these mistakes happen).
4. Caution agreed in analysis: the vocative rule must stay scoped to
   "inside direct speech, addressing the listener" to avoid false
   vocatives in narrative. The AN3.33 `bhagavā` case is NOT expected to
   change (structurally blocked) and is not a success criterion.

### Tests — write FIRST, confirm red
1. `test_system_prompt_contains_common_pali_rules` —
   `build_system_prompt(...)` output contains `COMMON_PALI_RULES`.
2. `test_common_pali_rules_cover_known_failures` — the constant mentions
   `kāyassa bhedā`, `'ti`, `yena`, and "vocative" (guards against the
   block being accidentally emptied later).

### Verification commands
Same five gates as Finding 51, same two files.

### Implementation outcome - 2026-06-11
- Added `COMMON_PALI_RULES` to the main analyzer system prompt only, covering
  the `kāyassa bhedā paraṃ maraṇā` case cluster, final-vowel lengthening
  before quotative `'ti`, the `yena ... tena upasaṅkami` idiom, and scoped
  direct-speech vocatives.
- Inserted the rules between the existing example-disambiguation guidance and
  the optional passage-text disambiguation block.
- Added focused tests proving the prompt includes the constant and the constant
  still covers the known failure classes.
- Validation passed:
  `uv run pytest tests/exporter/analysis/test_translate_core.py -v -k 'system_prompt_contains_common_pali_rules or common_pali_rules_cover_known_failures'` failed before implementation for the expected missing `COMMON_PALI_RULES` constant;
  `uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pytest tests/exporter/analysis/test_translate_core.py -v` (86 passed, one third-party `aksharamukha` deprecation warning).

### Out of scope
- Further deterministic pre-scoring changes beyond completed Finding 53.
- Recovery-prompt changes.

---

## Finding 54 — normalize bare-number score values in `scores` dicts

Status: COMPLETE (2026-06-11). Impact: LOW (debug-artifact consistency + enables meanings
on salvaged entries) — small, do it before the live evaluation so Finding 55
artifacts are uniformly shaped.

### Problem (evidence)
- `temp/tier_eval/low_post_improvements/DHP211_ai_debug.json` contains bare
  numeric values inside `final_scores` (jq dict-indexing over the artifacts
  fails on them: `Cannot index number with string "score"`).
- Mechanism: `_coerce_flat_score_map` (`translate_core.py:184–205`) returns
  early at line 189–190 when the response already has a `scores` key, so a
  response shaped `{"scores": {"123_0": 7}}` keeps bare numbers all the way
  into `final_scores`. Bare numbers can never carry `contextual_meaning`
  or `selection_source`.

### Files to change
- `exporter/analysis/translate_core.py`
- `tests/exporter/analysis/test_translate_core.py`

### Implementation
1. In `_normalize_ai_response` (`translate_core.py:153`), after the
   existing normalization, iterate the `scores` dict and replace any bare
   numeric value (`int | float`, excluding `bool`) with
   `{"score": value}`. Leave dict values untouched; drop nothing.
2. No prompt changes; no behavior change for already-dict values.

### Tests — write FIRST, confirm red
1. `test_normalize_ai_response_coerces_bare_number_scores` —
   `{"scores": {"123_0": 7, "124_0": {"score": 10}}}` →
   `{"123_0": {"score": 7}, "124_0": {"score": 10}}`.
2. `test_normalize_ai_response_ignores_bool_score_values` — `True` is not
   coerced into a score dict.

### Verification commands
Same five gates as Finding 51, same two files.

### Implementation outcome - 2026-06-11
- `_normalize_ai_response` now wraps bare numeric values inside `scores` as
  `{"score": value}`, while leaving dict-valued scores untouched and not
  coercing bools.
- Added focused tests for numeric score coercion and bool-value preservation.
- Validation passed:
  `uv run pytest tests/exporter/analysis/test_translate_core.py -v -k 'normalize_ai_response_coerces_bare_number_scores or normalize_ai_response_ignores_bool_score_values'` failed before implementation for the expected bare-number score;
  `uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pytest tests/exporter/analysis/test_translate_core.py -v` (90 passed, one third-party `aksharamukha` deprecation warning).

### Out of scope
- Re-writing historical debug artifacts; they stay as-is.

---

## Finding 55 — final live evaluation of BOTH models (RUN AFTER 51, 52, 53, 54)

Status: COMPLETE - EVIDENCE COLLECTED (2026-06-11; acceptance concerns remain).
Impact: confirmation — proves Findings 51/52/54 worked on
the live pipeline and that BOTH kept models (default Low/Gemini and the
occasional DeepSeek) succeed equally. Evidence-only; NO source changes.

### Scope decision (user-approved rationale)
Three passages per model — six runs total — instead of the full five:
- `MN41_p2` (`printf 'MN41\n2\n'`): measures the Finding 52 case-cluster
  rule, the `'ti` vowel rule, and the former `(singular)/(plural)` fallback
  row (`app'ekacce`).
- `SN15.1_p2` (`printf 'SN15.1\n2\n'`): the meaning-coverage stress test
  for Finding 51 (was 87/105 meaning-less on Low) and the largest/chunked
  target.
- `TH215` (`printf 'TH215\n'`): small-target sanity; quick check that the
  prompt additions did not disturb small passages (duration accusative,
  `api` = "even").
Excluded with reasons: `AN3.33_p1` — its known failure (`bhagavā`
vocative) is structurally blocked and cannot measure these findings;
`DHP211` — its residual issues are model lexical choices with no pipeline
fix in this queue. Do not run them unless the user asks.

### Method
1. Confirm Findings 51, 52, 53, 54 are complete (check this file and
   `handoff.md`) and `git status --short` shows no unexpected changes.
2. Run each target with each model:
   ```
   printf '<input>' | uv run python exporter/analysis/study_passage.py --debug --provider antigravity_cli --model "Gemini 3.5 Flash (Low)"
   printf '<input>' | uv run python exporter/analysis/study_passage.py --debug --provider deepseek --model deepseek-v4-flash
   ```
3. After EACH run, copy artifacts before the next run overwrites them
   (zsh: loop variable `src`, never `path`):
   ```
   mkdir -p temp/tier_eval/final_eval_low temp/tier_eval/final_eval_deepseek
   cp exporter/analysis/output/<source>_ai_debug.json temp/tier_eval/<folder>/
   cp exporter/analysis/output/<source>_study.json temp/tier_eval/<folder>/
   cp exporter/analysis/reports/<source>_study.md temp/tier_eval/<folder>/
   cp exporter/analysis/reports/<source>_ai_raw.txt temp/tier_eval/<folder>/
   ```
   plus the terminal log as `<source>_run.log`.
4. Repeat policy: if a target fails once, repeat that single run once.
   Stop on repeated quota-like failures (immediate empty responses).
5. Metrics per run (same jq shape as Finding 45): calls, chunks,
   reformats, translations, retries, missing first, missing after retry,
   final scores, max call time, PLUS the new meaning-coverage metric:
   ```
   jq '[.final_scores | to_entries[] | select((.value | type) == "object" and .value.score == 10)] as $sel | {selected: ($sel|length), no_meaning: ([$sel[] | select((.value.contextual_meaning // "") == "")] | length)}' <debug.json>
   ```

### Acceptance criteria (PER MODEL — both must pass)
1. Zero hard failures; zero missing-score groups after retry (attempt 1 or
   the single allowed repeat).
2. Meaning coverage: `no_meaning / selected` ≤ ~15% per target
   (deterministic `db_example_match` selections legitimately count toward
   the residue). SN15.1 p2 on Low is the headline number — it must drop
   from 83% to this band.
3. `MN41_p2` closing question on BOTH models: ablative `bhedā`, ablative
   `maraṇā`, `paraṃ` = "after" (prepositional/indeclinable row), genitive
   `kāyassa` — read the `_study.md` table directly.
4. `upapajjantī'ti` deconstruction: `upapajjanti + iti` selected. If still
   wrong on either model → record it as follow-up evidence; this does not
   fail the rest of the evaluation.
5. `TH215`: no regression (accusative `paṇṇavīsativassāni` on Low; `api`
   "even" preferred; translation keeps the finger-snap nuance).
6. No new `(accusative)`-style grammar parentheticals in any `_study.md`.
7. Debug JSON `final_scores` contains no bare-number values (Finding 54).
- NOT a criterion: AN3.33 `bhagavā` vocative (structurally blocked);
  prose-register differences between the two models (Low is known to write
  smoother prose; DeepSeek is kept for its compliance/cost profile).

### Reporting
Complete a metrics + acceptance table in this section, add a concise
summary to `handoff.md`, and state per model PASS/FAIL per criterion.
The final equal-success judgment is the USER's; present the evidence and
hard-stop. If both models pass, recommend releasing `temp/tier_eval/`
(user decision) and proceeding to `/kamma:3-review`.

### Live evaluation outcome - 2026-06-11

All six approved runs completed on first attempt; no repeat run was needed.
Artifacts are preserved in:
- `temp/tier_eval/final_eval_low/`
- `temp/tier_eval/final_eval_deepseek/`

Metrics:

| Model | Target | Calls | Chunks | Reformat | Translation | Retries | Missing first | Missing after | Final scores | Max call | Selected / no meaning |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Low | `MN41_p2` | 8 | 3 | 2 | 1 | 2 | 54 | 0 | 236 | 20.43s | 69 / 1 |
| Low | `SN15.1_p2` | 11 | 4 | 0 | 4 | 3 | 94 | 0 | 502 | 24.66s | 113 / 25 |
| Low | `TH215` | 3 | 0 | 0 | 1 | 1 | 25 | 0 | 94 | 14.73s | 15 / 0 |
| DeepSeek | `MN41_p2` | 5 | 3 | 1 | 0 | 1 | 11 | 0 | 308 | 47.47s | 77 / 6 |
| DeepSeek | `SN15.1_p2` | 5 | 4 | 0 | 0 | 1 | 38 | 0 | 356 | 31.88s | 118 / 1 |
| DeepSeek | `TH215` | 2 | 0 | 0 | 0 | 1 | 11 | 0 | 107 | 14.90s | 30 / 0 |

Meaning coverage notes:
- Low `SN15.1_p2` raw no-meaning ratio is 25/113 (22.1%), above the
  approximate 15% band. All 25 are `selection_source:
  db_example_text_overlap`, which the criterion allowed as legitimate
  deterministic residue; adjusted AI-selected residue is 0/88.
- Low `MN41_p2` has 1/69 no-meaning, also `db_example_text_overlap`.
- DeepSeek `MN41_p2` has 6/77 no-meaning without a deterministic source label
  but remains under the 15% band.
- DeepSeek `SN15.1_p2` has 1/118 no-meaning, `db_example_text_overlap`.

Acceptance table:

| Criterion | Low | DeepSeek |
|---|---|---|
| 1. Zero hard failures; zero missing after retry | PASS | PASS |
| 2. Meaning coverage | PASS with deterministic-residue caveat on `SN15.1_p2` | PASS |
| 3. `MN41_p2` closing question stock phrase | NOT CLEAN PASS: `paraṃ` = "after" and `upapajjantī'ti` selects `upapajjanti + iti`; `kāyassa` / `bhedā` / `maraṇā` show genitive/ablative only inside contextual-meaning parentheticals while the grammar column remains dat/nom/nom. | NOT CLEAN PASS: `paraṃ` = "after" and `upapajjantī'ti` selects `upapajjanti + iti`; `kāyassa` / `bhedā` / `maraṇā` grammar column remains dat/nom/nom and meanings do not explicitly show genitive/ablative. |
| 4. `upapajjantī'ti` deconstruction | PASS: `upapajjanti + iti` selected. | PASS: `upapajjanti + iti` selected. |
| 5. `TH215` no regression | NOT CLEAN PASS: `api` = "even" and finger-snap nuance are good; top compound `paṇṇavīsativassāni` remains `nt nom pl` though component `vassāni` is `nt acc pl`. | NOT CLEAN PASS: `api` = "even" and finger-snap nuance are good; top compound `paṇṇavīsativassāni` and component `vassāni` remain nominative plural. |
| 6. No generated grammar parentheticals | FAIL: Low `MN41_p2` has 10 selected contextual meanings with grammar parentheticals, e.g. `(masc. gen. sg.)`, `(abl. sg.)`, `(fem. acc. sg.)`. | PASS: refined scan found 0 selected contextual meanings with grammar-label parentheticals. |
| 7. No bare-number `final_scores` values | PASS | PASS |

Outcome: evidence collection is complete, but the result is not a clean equal
success. The user should review the preserved artifacts and decide whether to
approve the evaluation as sufficient, request a new focused follow-up issue, or
adjust the acceptance criteria.

### Out of scope
- Any source/prompt/code change (including Finding 53 work).
- `tools/ai_models.json` changes.

---

## Finding 53 — deterministic boost for quotative `'ti` deconstructions

Status: COMPLETE (2026-06-11). Activated by the user's 2026-06-11 next-step
update, before Findings 54 and 55.

### Problem (evidence)
- In the Finding 45 artifacts, both models selected
  `decon_upapajjantīti_0` (`upapajjantī + iti`) instead of
  `decon_upapajjantīti_1` (`upapajjanti + iti`) in `MN41_p2`.
- The correct option is structurally visible in the analyzer output: its
  first component group contains a finite verb option
  (`pos: "verb"`, `grammar: "pr 3rd pl of upapajjati"`), while the wrong
  long-vowel option's first component is participial/feminine
  (`pos: "prp"`, `grammar: "fem nom sg/pl/acc/voc ..."`).

### Files to change
- `exporter/analysis/translate_core.py`
- `tests/exporter/analysis/test_translate_core.py`

### Implementation
1. Add a narrow deterministic helper used by
   `_apply_deterministic_scores_to_map`.
2. Activate the helper only for analysis tokens whose surface word ends in
   quotative `'ti`/`’ti`.
3. For that token, inspect top-level deconstruction options whose
   construction ends with `+ iti`.
4. If exactly one such deconstruction has a first component group containing
   a finite verb option, score that deconstruction `10` with a deterministic
   `selection_source`, and score competing same-token `+ iti`
   deconstructions `0`.
5. Preserve any existing AI contextual meaning/selected POS for the winning
   deconstruction; if no contextual meaning exists, derive a short meaning
   from the finite verb component's `meaning_combo`/`meaning_1`.
6. Do not modify analyzer option construction, prompt text, model defaults,
   or non-deconstruction score handling.

### Tests — write FIRST, confirm red
1. A direct `_apply_deterministic_scores_to_map` test proving a quoted
   `upapajjantī'ti` token promotes the `upapajjanti + iti` finite-verb
   deconstruction and demotes the `upapajjantī + iti` participle
   deconstruction.
2. A direct negative test proving a genuine feminine `-ī + iti`
   deconstruction with no finite verb component is not boosted.

### Verification commands
```
uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py
uv run pytest tests/exporter/analysis/test_translate_core.py -v
```

### Implementation outcome - 2026-06-11
- Added a deterministic `upapajjantī'ti` guard in
  `_apply_deterministic_scores_to_map`: for quote-final `'ti` tokens, it
  promotes the unique `+ iti` deconstruction whose first component is a
  finite verb, demotes competing same-token `+ iti` deconstructions, and
  records `selection_source: deterministic_quotative_ti_deconstruction`.
- The winning deconstruction preserves existing AI context fields when
  present; otherwise it derives a short `contextual_meaning` from the
  finite verb component.
- Added focused tests proving `upapajjanti + iti` is promoted over
  `upapajjantī + iti`, and a genuine feminine `-ī + iti` deconstruction is
  not boosted.
- Validation passed:
  `uv run pytest tests/exporter/analysis/test_translate_core.py -v -k 'quotative_ti_deconstruction'` failed before implementation for the expected missing deterministic promotion;
  `uv run ruff check --fix exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run ruff format exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pyright exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run --with pyrefly pyrefly check --min-severity warn exporter/analysis/translate_core.py tests/exporter/analysis/test_translate_core.py`;
  `uv run pytest tests/exporter/analysis/test_translate_core.py -v` (88 passed, one third-party `aksharamukha` deprecation warning).

### Handoff note
- Finding 54 was completed later. Next active item: Finding 55.
