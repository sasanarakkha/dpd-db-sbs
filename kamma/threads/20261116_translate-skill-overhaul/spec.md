# Spec — Translate skill overhaul: model chain, off-peak guard, synonym-audit safe apply, pipeline fixes (Russian)

**Issue:** local issue #53 — https://github.com/sasanarakkha/dpd-db-sbs/issues/53
**Follow-up (execution, NOT this thread):** #56 — https://github.com/sasanarakkha/dpd-db-sbs/issues/56 (rehearsal production run)
**Source:** `kamma/drafts/20260709_synonym-prod-run/handoff.md` (backlog A–F) + user decisions 2026-11-13 and 2026-11-16.

## Overview

Improve the `/translate` skill (`kamma/translate/`) so it is safe and efficient to run. This thread does
NOT run the skill on production data: the only real AI calls are a small model benchmark and one
judge-only sample (`--limit 300`), and no DB writes happen outside unit tests (in-memory SQLite). Scope
is Russian only — Tamil is out.

## User decisions (fixed)

1. **One model chain: `tools/ai_models.json` → `default_models`.** It becomes `deepseek` / Flash (current
   official id, expected `deepseek-flash`, confirmed via DeepSeek `GET /models`), then the OpenRouter
   fallback picked by the benchmark. The OpenRouter-DeepSeek, llama and gpt-nano entries are removed.
   `grounded_models` is unchanged. The `antigravity_cli_work_models` key is removed.
2. **Synonym judge follows `default_models`** (Flash first). The benchmark includes a flash-vs-pro judge
   comparison on the same sample; the user decides from it whether the judge stays on Flash or uses a
   pro-first chain.
3. **OpenRouter fallback chosen by one combined benchmark** across roles (judge, generate, check); the user
   picks. Nothing is written to config before the pick.
4. **DeepSeek off-peak rule** (official pricing page): peak = 01:00–04:00 and 06:00–10:00 UTC, Mon–Fri,
   excluding Chinese public holidays; all other hours (weekends, holidays in full) are off-peak at half
   price. AI runs refuse to start in peak unless `--allow-peak`. Chinese public holidays are coded per year;
   when the current year has no entry, the scripts print a block and stop until it is added
   (`--allow-peak` does not bypass this).
5. **Synonym-audit apply contract = reviewed TSV** (`--apply-tsv`); `--fix-ai` is removed.
6. Bracket-only-differing variants are never auto-removed. AI trimming of `ru_meaning` is allowed via the
   reviewed TSV only.
7. Field clearing happens on `MISMATCH` only, never on `PARTIAL_MATCH`.
8. `log.md`: one line per session.
9. Approved: a `judge_model` column in the review TSV; parking a word after 2 rejections; tracked
   `kamma/translate/rejects.json`; passing the rejection reason into the regeneration prompt (editing
   `tools/ai_related.py` is allowed if needed, with a blast-radius check).
10. Do not edit `tools/ai_manager.py` (upstream copy).

## Verified facts (2026-11-16, read from code / DB / official pages)

- `synonym_audit.py`: `--fix-ai` applies cached trims and judges+applies uncached entries unreviewed;
  `normalize()` strips brackets, so bracket-only variants are "exact" dups removed by `--fix`;
  `split_meanings` splits on every `;`; `failed` cache records are served as hits; abort counter sums
  failed entries (request-failure count discarded); no `ORDER BY`; no `--model` → default chain under
  cache key `"default"`; the judge prompt is Russian-only.
- `tools/ai_models.json`: `default_models` = deepseek `deepseek-v4-flash`, openrouter
  `deepseek/deepseek-v4-flash`, openrouter `meta-llama/llama-4-scout`, openrouter `openai/gpt-4.1-nano`;
  `grounded_models` = deepseek `deepseek-v4-pro`, openrouter `deepseek/deepseek-v4-pro`. The registry entry
  (`kamma/upstream_sync/registry.json`, path `tools/ai_models.json`) describes the antigravity key.
- DeepSeek pricing page (2026-11-16): Flash is listed as `deepseek-flash`; legacy `deepseek-v4-flash` is
  still accepted and served by DeepSeek-V4.1-Flash-1017. Off-peak USD/1M: flash in-miss 0.15 / out 0.6;
  v4-pro in-miss 0.66 / out 1.98.
- `AIManager.request`: explicit pair → only that pair; none → walks `DEFAULT_MODELS`, skipping
  uninitialised providers; failure returns `content=None` (does not raise).
- Default-chain callers (`AIManager()` constructed; each still to be checked for pinning):
  `tools/proofreader.py`, `db/families/family_set_ru_update.py`,
  `exporter/analysis/{translate_core,study_passage,ai_pali_translate,ai_batch_translate}.py`,
  `gui2/ai_search_window.py`, `tools/ai_batch_processor.py`,
  `kamma/translate/scripts/{ai_generate_translation,synonym_audit}.py`,
  `kamma/improve/scripts/second_opinion.py`. `grounded_models` is read by `gui2/ai_search_window.py` and
  `second_opinion.py` (grounding=True).
- `batch_runner.py`: always pins `default_models[0]` (`load_default_provider_model`,
  `_resolve_provider_model`) → no fallback. Check op: `ok = attempted if returncode == 0 else 0`,
  `attempted` from "Found N words to analyze" → an all-failing checker that exits 0 loops on the same
  words (that failed words stay unmarked is not yet traced). One `log.md` line per chunk; `state.json`
  written every chunk and holds a leftover `window_start`. `--status` spawns a generate
  `--dry-run -limit 1` subprocess per pool, each loading the full pool. Generated ids are merged from
  `temp/last_translated.json` into `processed_ids.json` (bare list).
- Workhorses `ai_generate_translation.py` / `ai_check_russian_meanings.py` pass `provider=None, model=None`
  to `AIManager` when no flags are given.
- `tools/ai_batch_processor.py` (fork-local, in `unique_paths`): `parse_ai_response` non-JSON fallback is
  keyword-based ("mismatch/wrong/incorrect/opposite" → MISMATCH; no keyword → MATCH 0.5), individual mode
  only. Imported only by `ai_meaning_checker.py` and `tests/tools/test_ai_batch_processor.py` (16 tests).
- `ai_meaning_checker.py`: raw modes clear on `MISMATCH` or `PARTIAL_MATCH`; individual mode (CLI default)
  clears twice (per chunk + `generate_report`); the mismatch report omits English and the rejected Russian
  text; no reject counter; `DpdHeadword.id.in_(list(list_ids))` unchunked; full `.all()` then slice.
- `ai_generate_translation.py`: RU `remove_irrelevant` repeats one condition twice and ignores `ru_notes`,
  `ru_meaning_lit`, `ru_cognate`, NULLs; full `.all()` then slice; writes `temp/last_translated.json`.
- `ai_translation_check.py`: default `-lang ta`; reads `last_translated.json`, falls back to a full-table
  scan when `lang` differs; no `--ids-file`; RU `-delete` clears only `ru_meaning_raw`; uses `print()`;
  no tests.
- Antigravity mentions: `kamma/translate/pipeline.md:8,59`, `batch_runner.py:65,66,138,183,329`,
  `.claude/commands/translate.md:3`, `.agents/skills/translate/SKILL.md:3`, `tools/ai_models.json:2,4`,
  `registry.json:161,162,167`. No Python file reads `antigravity_cli_work_models`.
- `log.md` 1,072 lines, header format stale. `pipeline.md:88` cites a nonexistent "Phase 2".
  `improvments.md` (typo) holds a 1,100-line 2026-07-06 dump; referenced only from the draft handoff.
- Tamil has no literal-gloss convention (`வரி.` in 13 of 62,400 rows, incidental) — irrelevant now that
  Tamil is out of scope.
- 2027 Chinese public holidays (国办发明电〔2026〕10号, published 2026-11-05, Xinhua):
  Jan 1–3, Feb 5–13, Apr 3–5, May 1–5, Jun 9, Sep 15, Oct 1–7. Make-up workdays: Jan 31, Feb 14, May 8,
  Sep 26, Oct 9 (all weekends → stay off-peak under DeepSeek's "Monday through Friday" wording).
  No Chinese public holidays remain in 2026 after today.
- Archived validation (`kamma/archive/20260709_synonym-rerun-pro/plan.md`): with the v1 prompt and the
  older Flash model, Flash trimmed 0/30, pro 7/30 (5 of pro's drops hit `досл.` variants — now guarded in
  code).

## What it should do

### A. Model chain + off-peak guard
- **A.1 Off-peak guard** — `kamma/translate/scripts/offpeak.py`: `CN_HOLIDAYS` (per year),
  `is_deepseek_peak(now_utc)`, `require_offpeak(allow_peak)`. Missing year → printed block + exit 1,
  not bypassed by `--allow-peak`. Used by `batch_runner.py` (before every chunk; mid-session peak → clean
  stop), `synonym_audit.py --ai`, `model_benchmark.py`. Rule documented in `pipeline.md`.
- **A.2 Flash id** — confirm the current id from DeepSeek `GET /models`; update `default_models[0]`.
- **A.3 Runner stops pinning** — no `--provider/--model` → no flags passed → workhorses walk
  `default_models`. Explicit pair still pins.
- **A.4 Judge chain** — `synonym_audit.py` iterates `default_models` pairs itself (explicit pair per call)
  so it knows which model answered. It moves to the next pair only on transport failure
  (`content is None` / exception); an unparseable reply retries on the same pair.
- **A.5 Combined benchmark** — `kamma/translate/scripts/model_benchmark.py`, zero DB writes. Roles:
  - judge: first 30 flagged `ru_meaning_raw` entries; models: DeepSeek pro (yardstick), DeepSeek Flash,
    each OpenRouter candidate. Metrics: entries trimmed, agreement with pro, `досл.`-guard hits, invalid
    replies, median latency, est. cost / 100 requests; side-by-side TSV of dropped variants.
  - generate: 20 ids with human `ru_meaning`; candidate output beside the human value (user judges).
  - check: 10 true (English, `ru_meaning`) pairs + 10 shuffled pairs; accuracy vs ground truth.
  Results go to `benchmark.md` in the thread. User decides (a) judge primary: Flash or pro, (b) the
  OpenRouter fallback.

### B. Synonym audit (`synonym_audit.py`)
- **B.1 Modes:** default report; `--ai` judge, no writes; `--fix` strict dups only; `--apply-tsv PATH`
  (no AI, no cache; error if combined with `--ai`/`--fix`/`--limit`); `--fix-ai` removed; `--allow-peak`;
  `--ai` with `--field ta_meaning` → error "Tamil judge not supported".
- **B.2 Review TSV:** `id, field, lemma, english, current_value, proposed_value, dropped, max_ratio,
  verdict, judge_model, decision`; `dropped` = removed variants joined by ` | `; `decision` empty; sorted by
  `max_ratio` desc.
- **B.3 Strict vs bracket-only:** `find_exact_dups` compares lower-case, `ё→е`, collapsed whitespace,
  trailing dot stripped, **brackets kept**. `find_near_dups` keeps bracket-stripped `normalize()`, so
  bracket-only pairs score 1.0 and go to judge + TSV.
- **B.4 `--apply-tsv`:** any row with wrong `field` → abort before writes. Per row: rejected
  (`decision` ∈ n/no/skip, any case) / unchanged (`proposed_value` empty or == `current_value`) / stale
  (DB value ≠ `current_value`) / else write, commit, append `id, field, old, new` to
  `temp/synonym_audit/<ts>_applied.tsv`. Print totals.
- **B.5** Bracket-aware `split_meanings` (depth counter, never below 0).
- **B.6** Cache = judge resume only: `failed` records re-judged; lookup accepts any chain model, latest wins.
- **B.7** Abort counts failed requests (reset on any success); strip markdown fences before `json.loads`;
  `ORDER BY id`.
- **B.8** Each run appends one `log.md` line and records `last_audit` in `state.json`.

### C. Checker / runner correctness
- **C.1** Checker prints `checked N` (words with a parsed verdict); runner uses it as `ok`; missing → 0;
  `ok == 0 and attempted > 0` → exit 2. Failing test first.
- **C.2** `BatchProcessor(strict_parse=True)` in clearing modes (`meaning_raw`, `meaning_raw_list`,
  `notes_raw`): non-JSON reply → no verdict (not checked, not cleared). Other modes unchanged.
- **C.3** `processed_ids.json` → `{lang, mode, ids}`, reset at generate-session start, readers accept the
  old bare list; `IN` chunked at 500; `ai_translation_check.py --ids-file`; Op 2 uses it.
- **C.4** `kamma/translate/rejects.json` `{id: {count, reason, last}}`; incremented when the checker clears
  a `ru_meaning_raw` draft; Op 1 pool excludes count ≥ 2; regeneration prompt gets
  "A previous draft was rejected because: …" when a reason exists; mismatch report adds English and the
  rejected Russian text. Un-park = delete the entry.
- **C.5** Clear on `MISMATCH` only; separate `PARTIAL_MATCH` report section; single clearing call.
- **C.6** RU `remove_irrelevant` deletes only when `ru_meaning`, `ru_meaning_raw`, `ru_meaning_lit`,
  `ru_notes`, `ru_cognate` are all empty or NULL.
- **C.7** `ai_translation_check.py`: default `-lang ru`; RU `-delete` clears every flagged RU column;
  `print` → `pr`; first tests (incl. Hangul in RU flagged).

### D. Efficiency
- Generate/check pools via SQL `.limit()` + `count()`.
- `--status` fully in-process (no subprocesses).
- Checker clear path commits once per chunk. Apply keeps per-row commits on purpose (exact undo record).

### E. Docs and hygiene
- Remove all antigravity mentions (`pipeline.md`, both skill descriptions, `batch_runner.py`).
- `state.json`: drop `window_start`. `log.md`: one line per session (written in `try/finally`), header
  corrected, history kept.
- `pipeline.md`: model chain + off-peak rule + holiday block; Op 2 `--ids-file`; fix "see Phase 2"; Op 4 =
  judge → review → `--apply-tsv`; `rejects.json`; safety rules name `--apply-tsv`.
- `--status` / menu: Op 4 lexical flagged rows (`ru_meaning_raw`, `ru_meaning`), Op 5 dry-run count, Op 6
  re-ground count, parked rejects, `last_audit`.
- `git mv improvments.md improvements.md`; reduce to findings; dump removed (regenerable).

## Assumptions & uncertainties
- Judge fallback is a different model family; `judge_model` makes this visible in review.
- Rewriting `default_models` changes behaviour for every default-chain caller listed above (they lose
  llama/gpt-nano fallbacks) — accepted by the user; each caller is listed in the plan.
- Whether the RU generation prompt is built in `tools/ai_related.py` is not yet checked (C.4).
- C.1 root cause partly confirmed; the failing test settles it.
- Benchmark cost is estimated (chars/4 × listed price); `AIResponse` has no token usage.
- `current_value` cells are `_tsv_safe`d; a DB value with tab/newline always counts as stale (fails safe).
- After B.3/B.5 more entries are judged than the 151 counted on 2026-11-13 — expected.
- Holiday table holds 2027 plus an empty `2026` entry (added during implementation: without it every 2026 run — incl. the Phase 7 benchmark — would be blocked; no Chinese holidays remain in 2026 after 2026-11-16); from 2028-01-01 AI runs block until 2028 dates are added.

## Constraints
- Files: `kamma/translate/**` (scripts, `pipeline.md`, `state.json`, `log.md`, `improvments.md` rename,
  new `rejects.json`, new `offpeak.py`, new `model_benchmark.py`), `tools/ai_models.json`,
  `tools/ai_batch_processor.py`, `tools/ai_related.py` (only if C.4 needs it),
  `kamma/upstream_sync/registry.json` (`ai_models.json` entry), `.claude/commands/translate.md`,
  `.agents/skills/translate/SKILL.md`, tests under `tests/kamma_tests/translate/` and
  `tests/tools/test_ai_batch_processor.py`.
- Never edit `tools/ai_manager.py`, `grounded_models`, Tamil logic.
- Tests zero-network; DB tests on in-memory SQLite; targeted file paths only.
- Lint gate per touched `.py`: `ruff check --fix`, `ruff format`, `pyright` (tests:
  `--project /dev/null`), `pyrefly check --min-severity warn`.
- No `dpd.db` writes. Real AI calls only in the benchmark and the 300-row judge sample, off-peak.
- No commits; draft message references #53. Scratch under `temp/`, deleted at the end.

## How we'll know it's done
- Every new/changed behaviour has a test that fails for its own reason; all targeted test files pass.
- Linters clean on every touched `.py`; `validate_registry.py` passes.
- `benchmark.md` holds per-role tables incl. flash-vs-pro judge results; the user's picks are applied.
- Live judge-only sample (`--ai --limit 300`) writes a TSV with the new columns (`judge_model` filled);
  a DB count + hash of `ru_meaning_raw` is unchanged before/after.
- `grep -rni antigravity kamma/translate .claude/commands/translate.md .agents/skills/translate` empty;
  `grep -rn "fix-ai" kamma/translate .claude .agents` hits only the history line in `improvements.md`;
  `improvments` referenced only in drafts/archive.
- `batch_runner.py --status` runs without subprocesses and shows the new counts.

## What's not included
- Production runs (#56).
- Anything Tamil.
- Changes to `tools/ai_manager.py` or `grounded_models`.
