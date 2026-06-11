# Finding 45 Higher-Model Evaluation Summary

This note summarizes the DeepSeek and Gemini/Low Finding 45 evaluation so a
higher model can analyze pipeline-improvement opportunities without rereading
the full execution history first.

## Purpose

Evaluate two post-improvement analyzer runs on the same five benchmark targets
for pipeline-improvement signals, not only for model-default selection.

The next higher-model session should look for:
- shared failure modes that require pipeline or prompt changes;
- model-specific strengths that suggest provider routing or fallback strategy;
- quality issues caused by dictionary-option selection versus report prose;
- recovery paths that are still too frequent or too expensive.

## Artifact Locations

- DeepSeek run artifacts:
  `temp/tier_eval/deepseek_post_improvements/`
- Gemini/Low run artifacts:
  `temp/tier_eval/low_post_improvements/`
- Detailed Finding 45 record:
  `kamma/threads/exporter_analysis_loop/findings_45_50_plans.md`
- Current handoff:
  `kamma/threads/exporter_analysis_loop/handoff.md`

Each artifact folder contains 25 files: for each of `TH215`, `DHP211`,
`AN3.33_p1`, `MN41_p2`, and `SN15.1_p2`, there is a run log, AI debug JSON,
study JSON, study markdown, and raw AI response log.

## Run Matrix

| Provider/model | Target | Result | Calls | Chunks | Reformats | Translations | Retries | Missing first | Missing after retry | Final scores | Max call |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gemini Low | TH215 | ok | 3 | 0 | 0 | 1 | 1 | 25 | 0 | 94 | 14.78s |
| Gemini Low | DHP211 | ok | 3 | 0 | 1 | 0 | 1 | 6 | 0 | 43 | 12.10s |
| Gemini Low | AN3.33 p1 | ok | 5 | 2 | 0 | 2 | 1 | 38 | 0 | 141 | 12.40s |
| Gemini Low | MN41 p2 | ok | 7 | 3 | 1 | 2 | 1 | 49 | 0 | 239 | 18.53s |
| Gemini Low | SN15.1 p2 | ok | 11 | 4 | 0 | 4 | 3 | 96 | 0 | 487 | 19.39s |
| DeepSeek | TH215 | ok | 2 | 0 | 0 | 0 | 1 | 23 | 0 | 94 | 9.22s |
| DeepSeek | DHP211 | ok | 2 | 0 | 0 | 0 | 1 | 4 | 0 | 40 | 6.03s |
| DeepSeek | AN3.33 p1 | ok | 3 | 2 | 0 | 0 | 1 | 15 | 0 | 92 | 10.66s |
| DeepSeek | MN41 p2 | ok | 4 | 3 | 0 | 0 | 1 | 27 | 0 | 169 | 24.06s |
| DeepSeek | SN15.1 p2 | ok | 5 | 4 | 0 | 0 | 1 | 38 | 0 | 335 | 31.29s |

Important metric interpretation:
- Both providers completed all five targets on attempt 1.
- Both providers ended with zero missing-score groups after retry.
- DeepSeek used fewer calls and fewer recovery paths on all five targets.
- Gemini Low needed more compact-map translation calls and retries,
  especially on `SN15.1_p2`.
- Visible markdown table row counts were identical across providers:
  `TH215` 22, `DHP211` 20, `AN3.33_p1` 100, `MN41_p2` 130, `SN15.1_p2` 160.
- DeepSeek had lower max-call latency on small targets; Gemini Low had lower
  max-call latency on the two largest targets.

## Quality Findings

### Shared Failures

- Both providers selected the wrong `MN41_p2` `upapajjantī'ti`
  deconstruction:
  `upapajjantī + iti`, not expected `upapajjanti + iti`.
- Both providers selected nominative `bhagavā` for the vocative address in
  `AN3.33_p1` `etassa, bhagavā, kālo`.
- These are strong pipeline-improvement candidates because changing only the
  model did not fix them.

### DeepSeek Strengths

- DeepSeek used fewer calls and no compact-map translation calls.
- DeepSeek was better on the known `MN41_p2` closing-question case cluster:
  it selected ablative `bhedā`, ablative `maraṇā`, idiomatic `paraṃ`, and
  acceptable `sugatiṃ` / `saggaṃ` rows.
- DeepSeek had no grammar-keyword parenthetical matches in generated
  markdown.

### DeepSeek Weaknesses

- `TH215`: the translation omitted the finger-snap duration nuance that
  Gemini Low retained.
- `DHP211`: translation was more literal and rougher, e.g. "make a dear one"
  and "loss ... is evil".
- `SN15.1_p2`: prose was more literal and stilted. The study output included
  awkward selections or meanings around `agga`, `kaṭā`, and `chavā`.
- DeepSeek final score counts were lower than Gemini Low on larger targets,
  though visible markdown row counts were identical. A higher-model review
  should inspect whether the lower score count reflects harmless internal map
  shape differences or lost scoring detail.

### Gemini Low Strengths

- Better prose on `TH215`, `DHP211`, and `SN15.1_p2`.
- Preserved the `TH215` finger-snap duration nuance.
- More polished English register in the longer `SN15.1_p2` report.
- Lower max-call latency on the two largest targets in this run:
  `MN41_p2` and `SN15.1_p2`.

### Gemini Low Weaknesses

- Needed more recovery calls than DeepSeek on every target.
- `MN41_p2` regressed on the closing-question case cluster:
  nominative `bhedā`, nominative `maraṇā`, nominative `paraṃ`, and noun-row
  `saggaṃ`.
- `MN41_p2` had visible `(singular)` / `(plural)` parentheticals for
  `app'ekacce`. This may be dictionary meaning text rather than AI-added
  grammar notes, but it still appears in the report and should be reviewed.

## Pipeline-Improvement Questions For Higher Model

1. Can the analyzer rank deconstruction candidates better for sandhi forms
   like `upapajjantī'ti`, where the correct option is present but not chosen?
2. Can the prompt or scoring rubric detect vocative address contexts after a
   comma, e.g. `etassa, bhagavā, kālo`, without causing false positives in
   narrative nominative uses?
3. Should the pipeline add deterministic grammar-context hints for common
   formulas such as `kāyassa bhedā paraṃ maraṇā` so models do not select
   nominative rows?
4. Should report generation or contextual-meaning cleanup strip dictionary
   parentheticals such as `(singular)` / `(plural)` when they are not helpful
   to end users?
5. Is DeepSeek's lower final-score count a real output-quality issue, or just
   a benign difference after visible rows are generated?
6. Should provider strategy be hybrid, e.g. DeepSeek for first-pass selection
   and Gemini Low for prose translation, rather than a single default model?
7. Can compact-map translation calls be reduced for Gemini Low by improving
   first-pass prompt compliance or structured-response salvage?

## Suggested Review Procedure

1. Read the paired markdown reports for each target:
   - `temp/tier_eval/low_post_improvements/<target>_study.md`
   - `temp/tier_eval/deepseek_post_improvements/<target>_study.md`
2. Inspect debug JSON for the shared failures:
   - `MN41_p2_ai_debug.json`
   - `AN3.33_p1_ai_debug.json`
3. Classify each issue as one of:
   - prompt/rubric issue;
   - deterministic pre-scoring issue;
   - dictionary-option ranking issue;
   - post-processing/report cleanup issue;
   - provider-routing issue.
4. Propose focused follow-up findings only. Do not change
   `tools/ai_models.json` or pipeline code without a new approved plan.

## Current Recommendation

Do not change the default model automatically. DeepSeek is promising because
it used fewer calls and fixed the `MN41_p2` closing-case cluster, but Gemini
Low still produced better prose on several targets. The stronger next move is
to identify targeted pipeline fixes for the shared failures, then rerun a
smaller confirmation matrix.
