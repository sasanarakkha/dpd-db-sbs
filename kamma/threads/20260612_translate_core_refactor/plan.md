# Plan: translate_core decomposition with a regression safety net

Status: **PROPOSED — NOT APPROVED. Do not implement any phase without explicit
user approval.** This thread is behavior-preserving; the harness (Phase 1) is a
hard gate before the split (Phase 2). Phase 3 needs its own separate approval.

Source analysis: `kamma/threads/exporter_analysis_loop/plan-history/meta_tooling_improvement_plan.md`.

## Architecture decisions
- `exporter/analysis/` is local-only (`no_sync_files` in
  `kamma/upstream_sync/registry.json`); restructuring has no upstream-sync cost.
- Safety net first: freeze current output deterministically before moving any
  code. The split is only "safe" if a byte-level regression check exists.
- Phase 2 is a pure move + re-import. Zero logic edits. If a logic change looks
  necessary, STOP and record it as a Phase 3 item or a new `#197` finding.
- Final module names are the implementer's choice; the clusters below are the
  intended seams, verified against the current function layout.

## Model Strategy
Pro tier is scarce — it is used for exactly one short analysis window in
Phase 1; everything else is Fast. The user performs the switch manually at the
⚠️ markers; the agent must HARD STOP at each marker and wait.

| Stage | Tier | Reason |
| --- | --- | --- |
| 1.1a copy-out | Fast | mechanical file copying |
| 1.1b analysis window | **Pro** | sequence-alignment diagnosis + `RecordedAIManager` keying design — judgment only, no code, written deliverable |
| 1.1c re-records | Fast | run documented commands per the Pro re-record list |
| 1.2–1.7 harness build | Fast | implementation strictly following the Pro design note |
| Phase 2 split | Fast | pure move + re-import with explicit symbol map |
| Phase 3 (optional) | Pro analysis, Fast implementation | own approval gate |

The Pro window's deliverable is a written analysis in `handoff.md` (section
"Pro analysis — replay design"). It must contain everything Fast needs so no
later task requires judgment: per-passage alignment verdicts, the re-record
list, and the replay-double keying scheme.

## Pre-flight (every session)
- Read this `plan.md`, `spec.md`, and `handoff.md` (if present).
- Re-read current source before editing; do not trust line numbers from the
  source analysis doc — they will drift.
- Confirm `exporter/analysis` is still under `no_sync_files` before adding files.
- **Commit prerequisite for Phase 1:** the uncommitted `#197` working-tree
  changes (`translate_core.py`, `analyzer.py`, `example_bolding.py`, test
  files) must be committed by the user before goldens are frozen. Record the
  commit hash in `handoff.md` next to the goldens. If the tree is still dirty,
  stop and ask the user to commit first.
- **`temp/` is disposable** (project rule): the source artifacts under
  `temp/tier_eval/` may vanish between sessions. Task 1.1a (copy-out) must run
  before anything else in Phase 1.

---

## Phase 1 — Passage regression harness (no behavior change) [GATE]

### Replay seam (exact — do not invent another path)
The harness reproduces `study.json`/`study.md` byte-identically by mirroring
`study_passage.main()` (`exporter/analysis/study_passage.py:273`) without stdin:

```python
result = get_passage_by_code("SN15.1")          # passage_by_code.py
passage = result.paragraphs[1]                   # paragraph 2 → source "SN15.1_p2"
merged = translate_sentence(
    passage, db_session, recorded_ai_manager,    # RecordedAIManager test double
    model=<from fixture>, provider=<from fixture>,
    verse_source="SN15.1_p2", debug={},
)
study_json = json.dumps(merged, ensure_ascii=False, indent=2)
study_md = generate_markdown_report(merged, passage, verse_id="SN15.1_p2")
```

Notes for the executor:
- "Zero network" does NOT mean zero DB: `translate_sentence` needs a real
  `db_session` on the local `dpd.db` (same as existing analysis tests).
- `model` / `provider` passed to `translate_sentence` must be the recorded
  values stored in the fixture (they can affect chunking/prompt branches).
- Compare goldens against these in-memory strings; do not write into
  `exporter/analysis/output/` or `reports/` from tests.

### Re-record command (for misaligned passages, task 1.1b)
The recorded sets were produced with (see any `*_run.log`):

```
printf 'AN3.33\n1\n' | uv run python exporter/analysis/study_passage.py \
  --debug --provider <provider> --model "<model>"
```

(stdin = sutta code, newline, paragraph number; single-paragraph passages like
`DHP211` need only the code + newline). Artifacts land in
`exporter/analysis/output/` (`*_ai_debug.json`, `*_study.json`) and
`exporter/analysis/reports/` (`*_study.md`). Use the same provider/model tier
as the aligned passages' fixtures.

- [x] 1.1a Copy-out (FIRST action — `temp/` is disposable). Copy the candidate
  artifact sets for all five passages out of `temp/tier_eval/` into
  `tests/exporter/analysis/fixtures/passages/_raw/` (or directly into their
  final fixture layout). Newest post-fix sets (`live_test_20260612/`,
  `live_test_post_fix/`, `final_eval_66_68_*/`, `final_eval_69_70_low/`) cover
  only `TH215`, `MN41_p2`, `SN15.1_p2`; take `AN3.33_p1` and `DHP211` from the
  pre-fix sets (`high`, `low`, `medium`, `deepseek_post_improvements`) as
  provisional candidates.
  → verify: all five passages have `*_ai_debug.json` + `*_study.json` copies
  under `tests/`; `git status --short` shows them.
⚠️ **MODEL SWITCH REQUIRED (Pro tier): sequence-alignment diagnosis and
replay-double design — analysis only. HARD STOP: report that 1.1a is done and
wait for the user to switch models before starting 1.1b.**

- [x] 1.1b [PRO — analysis only, no code edits, no live runs] Inventory and
  alignment analysis. Per passage, identify the ordered AI responses the
  pipeline received (first-pass per chunk, plus reformat / retry / translation
  responses) from the `*_ai_debug.json` request/response records, and check the
  sequence against the **current** code's call pattern (would replay complete
  with no desync — no missing or surplus responses?). Pre-fix artifacts for
  `AN3.33_p1` / `DHP211` are expected to misalign. Then design the
  `RecordedAIManager` keying scheme for task 1.3: how each incoming request is
  classified (first-pass / reformat / retry / translation) and matched to the
  recorded response (e.g. by chunk index + prompt markers), citing the actual
  prompt-distinguishing features in the current code. Write the deliverable to
  `handoff.md` under "Pro analysis — replay design": per-passage alignment
  verdict, the re-record list, and the keying scheme — complete enough that
  Fast implements 1.2–1.7 without further judgment. Do not silently drop a
  passage.
  → verify: `handoff.md` section exists listing every passage with source
  artifact path, recorded response count, alignment verdict
  (aligned / re-record), and the keying design.

⚠️ **MODEL SWITCH REQUIRED (Fast tier): mechanical execution resumes. HARD
STOP: report that the Pro analysis is written and wait for the user to switch
back before starting 1.1c.**

- [x] 1.1c [FAST] Re-record misaligned passages. For each passage on the Pro
  re-record list, run one fresh recorded live evaluation using the documented
  re-record command (user-approved credit spend) and copy the new artifacts
  into the fixtures dir, replacing the pre-fix candidates.
  → verify: every passage on the re-record list has fresh `*_ai_debug.json` +
  `*_study.json` + `*_study.md` in the fixtures dir; run.log/command recorded
  in `handoff.md`.
- [x] 1.2 Finalize `tests/exporter/analysis/fixtures/passages/` (git-tracked):
  per passage, the ordered recorded responses, the exact stdin
  (e.g. `SN15.1\n2\n`), and the provider/model the responses came from.
  → verify: `git status --short` shows the fixture files under `tests/`; no
  passage is left on misaligned pre-fix artifacts.
- [x] 1.3 Add a `RecordedAIManager` test double in
  `tests/exporter/analysis/` implementing **exactly the keying scheme from the
  Pro analysis in `handoff.md`** (request classification + response matching).
  Reuse the existing `AIManager` stub seam used by current tests (see the
  `FakeAIManager` patterns in `test_translate_core.py`); add no network layer.
  If the design proves unimplementable as written, HARD STOP and report —
  do not improvise an alternative scheme.
  → verify: a throwaway test drives `translate_sentence` for one passage with
  zero network calls and produces a non-empty `study.json`.
- [x] 1.4 Generate, per passage, the goldens. **Full golden:** the complete
  replay-produced `study.json` and `study.md` — these carry the byte-identical
  guarantee for Phase 2. **Distilled golden:** a stable list of
  `(surface_word, occurrence, selected_key, grammar, meaning)` rows extracted
  from `study.json`, for readable diffs. Commit both under the fixtures dir.
  Add an `UPDATE_GOLDENS=1` (env or pytest flag) regeneration mode. Record in
  `handoff.md` the commit hash the goldens were generated against (see
  pre-flight commit prerequisite).
  → verify: running the harness twice is byte-stable; toggling update mode
  regenerates identical goldens.
- [x] 1.5 Write `tests/exporter/analysis/test_passage_regression.py`: replay each
  passage and assert (a) byte-equality of `study.json` and `study.md` against
  the full goldens, (b) the distilled golden rows, and (c) explicit assertions
  for every "Frozen correctness fact" in `spec.md` (F71/F63 refrain gen pl;
  F66 no fan-out; F67/F74 no placeholder; F69 no shifted meanings; F62 no
  empty meanings; F48 no grammar parentheticals).
  → verify: `uv run pytest tests/exporter/analysis/test_passage_regression.py -v`
  passes with zero network calls.
- [x] 1.6 Confirm new test files need no registry shadow entry (directory-level
  `no_sync_files` / `tests/` skip pattern covers them).
  → verify:
  `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` and
  `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` pass.
- [x] 1.7 Phase gate. All Phase 1 files pass the five per-file validation gates.
  → verify: ruff check --fix, ruff format, pyright, pyrefly (min-severity warn),
  and the regression pytest all pass on each changed file.

**⚠️ STOP after Phase 1.** Phase 1 has standalone value (it protects the current
code regardless of any refactor). Report to the user and get explicit approval
before starting Phase 2.

---

## Phase 2 — Behavior-preserving module split

- [ ] 2.1 Map every top-level `def`/`class` and module constant in
  `translate_core.py` to a target module. Intended seams (adjust names freely):
  - `prompts.py` — `build_system_prompt`, `_build_translation_prompt`,
    `_build_reformat_prompt`, `_build_missing_scores_prompt`,
    `_previous_translation_block`, `_word_keys_overview`, prompt constants
    (`COMMON_PALI_RULES`, `NO_TOOLS_INSTRUCTION`, `NO_GRAMMAR_NOTES_INSTRUCTION`).
  - `ai_response.py` — `_parse_ai_json`, `_extract_partial_response`,
    `_normalize_ai_response`, `_coerce_flat_score_map`, `_extract_word_key_map`,
    `_extract_selected_keys_map`, `_extract_structured_selection_map`,
    `_collect_option_keys`, `_matching_key_by_*`, related helpers.
  - `scoring.py` — `pre_match_db_examples`,
    `_apply_deterministic_scores_to_map`, quotative-ti helpers,
    `_db_example_group_key`, score-value helpers, `_copy_score_context_fields`,
    `merge_ai_selections`.
  - `retry.py` — `_find_missing_score_groups`, `_narrow_db_example_tied_groups`,
    `_batch_missing_groups`, `_trim_groups_for_retry`, `_retry_prompt_groups`,
    `_fan_out_retry_scores`, `_request_missing_score_retry_pass`.
  - `ranking.py` — `_option_rank` and all `_*_rank`, `_select_best_option`,
    `_meaning_tokens`, fallback-meaning helpers
    (`_component_join_fallback_meaning`, `_deconstruction_fallback_meaning`,
    `_first_meaning_sense`).
  - `rendering.py` — `format_markdown_table`, `generate_markdown_report`,
    `_clean_meaning`, `_strip_grammar_annotations`.
  - `translate_core.py` keeps the orchestrator + public API:
    `translate_sentence`, `_request_first_pass`, `_handle_compact_map_response`,
    `_handle_reformat_response`, chunking glue, variant helpers.
  → verify: every current symbol appears in exactly one target; no symbol
  dropped. Record the mapping in `handoff.md`.
- [ ] 2.2 Move one cluster at a time, leaf-most first as determined by
  inspecting the actual intra-module call graph during 2.1 (the expected order
  is roughly `prompts.py` → `rendering.py` → `ranking.py` → `ai_response.py` →
  `retry.py` → `scoring.py`, but the verified dependency order wins). Each new
  file starts with a one-sentence purpose docstring. Keep moved code
  identical — no edits beyond imports.
  → verify after each move: `uv run pytest tests/exporter/analysis/test_passage_regression.py tests/exporter/analysis/test_translate_core.py -q` stays green.
- [ ] 2.3 Re-point imports. Update `tests/exporter/analysis/test_translate_core.py`
  and all callers found by grep
  (`exporter/analysis/study_passage.py`, `exporter/analysis/ai_pali_translate.py`,
  and any others). Apply the Atomic Rename Protocol: grep old import paths
  repo-wide, update every reference.
  → verify: `rg "from .*translate_core import|translate_core\." ` shows only the
  intended public symbols; no test or caller imports a moved private helper from
  the old location.
- [ ] 2.4 Prove output unchanged.
  → verify: `uv run pytest tests/exporter/analysis/test_passage_regression.py -v`
  passes with the **unmodified** goldens (no `UPDATE_GOLDENS`); full analysis
  unit suite green:
  `uv run pytest tests/exporter/analysis/ -q`.
- [ ] 2.5 Per-file validation gates on every new/changed Python file.
  → verify: ruff check --fix, ruff format, pyright, pyrefly (min-severity warn)
  pass on each.
- [ ] 2.6 Registry/SMD check for the new source modules.
  → verify: `validate_registry.py` and `verify_smd_coverage.py` pass; confirm
  `no_sync_files` directory coverage is sufficient or add entries if the scripts
  demand them.
- [ ] 2.7 Update `exporter/analysis/README.md` with the new module map and the
  fixture-refresh procedure from Phase 1.
  → verify: README lists each module's responsibility and the
  `UPDATE_GOLDENS` workflow.

**⚠️ STOP after Phase 2.** Hand to the user for testing, then `/kamma:3-review`.

---

## Phase 3 — OPTIONAL coupling reduction (separate approval required)

Do not start without a fresh, explicit user decision after Phase 2 is reviewed.

- [ ] 3.1 Trace the score → merge → rank data flow at line level and document the
  current implicit precedence (deterministic db-example scores vs AI scores vs
  tie-break ranks) — the F62/63/66/71 collision surface.
- [ ] 3.2 Propose a single explicit precedence model (design doc in this thread)
  for user approval before any code change.
- [ ] 3.3 Implement behind the Phase 1 harness; any intended output change must
  be a reviewed golden update with the diff shown to the user, justified
  per-row, and cross-checked against the frozen correctness facts.

## Closure
- Update `handoff.md` after each phase with: phase outcome, the symbol→module
  map, validations run, and any discovered-but-deferred logic issues (as new
  `#197` findings, not silent fixes).
- When Phases 1-2 are complete and reviewed, run `/kamma:4-finalize` for this
  thread.
