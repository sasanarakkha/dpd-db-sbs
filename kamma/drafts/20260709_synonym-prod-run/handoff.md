# handoff.md — Translate Skill: Improvement Backlog + Synonym Audit Production Run

- **Origin:** `kamma/archive/20260709_synonym-rerun-pro/` (mechanism-validated thread) + a full read-through analysis of `kamma/translate/` on 2026-11-13.
- **Status:** draft backlog. Nothing below is implemented. No code, DB or skill file was changed by the analysis session; only this file was rewritten.
- **Next session:** turn this into a proper thread (or threads — see "Suggested thread split").
- **Issue:** local issue #53 (https://github.com/sasanarakkha/dpd-db-sbs/issues/53). Reference it in the thread's spec/plan and in its commit messages.

## Decisions (user, 2026-11-13)

1. **Apply contract:** reviewed TSV. Implement `--apply-tsv` (A1 option 2); apply makes no AI calls and no longer depends on the `temp/` cache (resolves A2).
2. **Verified `ru_meaning`:** AI trimming is allowed, through the same judge → review TSV → apply flow.
3. **`PARTIAL_MATCH`:** clear on `MISMATCH` only. Change the code (C5), not the doc.
4. **Providers:** antigravity is no longer an option anywhere in this pipeline. DeepSeek direct is first, OpenRouter-DeepSeek is second (C7).
5. **`log.md`:** one line per session.
6. **Bracket-only-differing variants (A3):** never auto-remove; always send to review.
7. **Antigravity cleanup scope:** `tools/ai_models.json` may be freed of antigravity. `tools/ai_manager.py` is copied from upstream — do not change it.

## Read this first (instructions for the planning agent)

- This file is a backlog plus one ready-to-plan spec. **Plan Thread 1 only** ("Thread 1 — pinned spec" below). Threads 2–4 are listed for later sessions; do not fold them in.
- Where a section in A–F offers alternatives ("X or Y"), the choice is already made in "Decisions" or in the Thread 1 spec. Those two sections win over any wording elsewhere in this file.
- Items marked **(user)** are user decisions and are fixed. Items marked **(proposed)** are the analysis session's recommendation; show them to the user in the plan summary for approval, do not treat them as approved.
- Line numbers were correct on 2026-11-13. Re-locate by the quoted code/function name, not by number.
- Flags named `--apply-tsv`, `--ids-file`, `--retry-failed` **do not exist yet**. Existing flags of `synonym_audit.py`: `--field`, `--limit`, `--fix`, `--ai`, `--fix-ai`, `--threshold`, `--provider`, `--model`, `--batch-size`, `--max-judgments`.

### Guardrails (from project rules — they apply to every task)

- No DB write before a fresh `uv run python3 db/backup_tsv/backup_dps.py` and the user's explicit go-ahead. Judge-only and report-only runs are fine.
- Do not edit `tools/ai_manager.py` (upstream copy). Do not commit; prepare a draft commit message.
- Tests: targeted files only, never bare `uv run pytest`. Tests are zero-network (fake the AI manager, as the existing tests in `tests/kamma_tests/translate/test_synonym_audit.py` do).
- Every touched `.py` must pass: `uv run ruff check --fix <file>`, `uv run ruff format <file>`, `uv run pyright <file>` (for files under `tests/`: `uv run pyright --project /dev/null <file>`), `uv run --with pyrefly pyrefly check --min-severity warn <file>`.
- Scratch files only under `temp/<task>/`, deleted before the final report. Fish shell: no heredocs in commands given to the user.
- Never re-run AI generation to fix formatting; use local text manipulation.

## Thread 1 — pinned spec: synonym audit safe apply + `ru_meaning_raw` production run

**Files:** `kamma/translate/scripts/synonym_audit.py`, `tests/kamma_tests/translate/test_synonym_audit.py`, `kamma/translate/pipeline.md` (Op 4 section and the safety-rules line that names `--fix-ai`). Nothing else.

**Goal:** nothing reaches the DB from the AI judge unless the user left it in a reviewed TSV.

### Behaviour to build

1. **Three modes.**
   - default: lexical report only (unchanged).
   - `--ai`: judge flagged entries, write report + review TSV, **no DB writes** (unchanged).
   - `--apply-tsv <path>` (new, **user**): apply a reviewed TSV. No AI calls, no cache reads.
   - Remove `--fix-ai` (**proposed**; `--apply-tsv` replaces it). Keep `--fix`, but only for strict duplicates (point 3).
2. **Review TSV format** (**proposed**). Columns, in order: `id`, `field`, `lemma`, `english`, `current_value`, `proposed_value`, `dropped`, `max_ratio`, `verdict`, `decision`.
   - `dropped` = the removed variants joined with ` | `. `decision` is written empty.
   - Review protocol for the user: delete a row, or put `n` in `decision`, to reject it; `proposed_value` may be hand-edited.
3. **Strict vs bracket-only duplicates** (**user**: never auto-remove bracket-only).
   - Strict duplicate = equal after lower-casing, `ё→е`, whitespace collapse and trailing-dot strip, **with brackets kept**. Only these are removed by `--fix`.
   - Variants equal only after bracket stripping (today's `normalize`) are no longer "exact". Flag them as near-duplicate candidates so they are judged and appear in the review TSV.
4. **`--apply-tsv` rules.** For each row:
   - skip if `decision` is `n`/`no`/`skip` (case-insensitive), or `proposed_value == current_value`, or `proposed_value` is empty;
   - error out before any write if a row's `field` differs from `--field`;
   - read the DB value; if it differs from `current_value`, skip and count it as "stale" (the row changed since judging);
   - otherwise write `proposed_value`, commit, and append `id, field, old, new` to `temp/synonym_audit/<timestamp>_applied.tsv` immediately (this is the undo record);
   - print totals: applied / rejected / unchanged / stale.
5. **Bracket-aware split.** `split_meanings` must not split on a `;` that is inside `(...)`.
6. **Cache is for judge resume only.** Do not serve `failed` records from the cache — re-judge them (A4).
7. **Judge model** (**user**: DeepSeek first, OpenRouter-DeepSeek second). With no `--provider/--model`, try the entries of `grounded_models` in `tools/ai_models.json` in order (currently `deepseek / deepseek-v4-pro`, then `openrouter / deepseek/deepseek-v4-pro`): the second is tried only when the first request fails. Implement inside `synonym_audit.py`; do not change `AIManager`. Cache model key (**proposed**): the model name with a leading `deepseek/` stripped, so both routes share verdicts.
8. **Small fixes:** count failed *requests* (not entries) for the 5-in-a-row abort; strip markdown code fences before `json.loads`; `ORDER BY id` when `--limit` is used.

### Tests to add (each must fail for its own reason)

- bracket-only pair (`"идет; идет (в)"`) is not a strict duplicate, is flagged as a near-duplicate candidate, and `--fix` leaves it untouched;
- strict duplicate (`"наступающий; Наступающий."`) is still removed by `--fix`;
- `split_meanings("a (b; c); d")` returns two parts;
- TSV round-trip: written header and column order; `dropped` content;
- apply: approved row written; `decision=n` row skipped; stale row skipped; wrong-`field` row aborts with no writes; hand-edited `proposed_value` written as edited;
- cache: a `failed` record is re-judged, a `keep`/`trim` record is served;
- fallback: first pair fails → second pair is called; first succeeds → second is never called;
- fenced JSON reply parses; abort triggers on 5 failed requests, not on 5 failed entries inside successful requests.

### Production run (after the code passes and the user approves)

1. `uv run python3 db/backup_tsv/backup_dps.py`
2. `uv run python3 kamma/translate/scripts/synonym_audit.py --field ru_meaning_raw --ai` (≈151 entries, ≈16 requests)
3. Hand the user the path of `temp/synonym_audit/<timestamp>_review.tsv`. **Stop and wait** for their review.
4. `uv run python3 kamma/translate/scripts/synonym_audit.py --field ru_meaning_raw --apply-tsv <reviewed path>` — only after explicit go-ahead.
5. Verify from the DB, not from script output: for 10 ids from the applied file, `sqlite3 dpd.db "select id, ru_meaning_raw from russian where id in (...)"` matches the `new` column; re-run the report-only scan and record the new flagged counts.
6. `uv run python3 db/backup_tsv/backup_dps.py` again; the user commits.

### Done when

- all listed tests pass with `uv run pytest tests/kamma_tests/translate/test_synonym_audit.py -v`, plus the four linters on both files;
- `--help` shows `--apply-tsv` and no `--fix-ai`; `grep -rn "fix-ai" kamma/translate .claude .agents` returns only archived/draft text;
- `pipeline.md` Op 4 describes judge → review → apply with the real commands;
- the production run is either completed and verified, or explicitly left for the user with the exact commands.

### Out of scope for Thread 1

`ru_meaning` and `ta_meaning` runs (the `ru_meaning` run reuses this code and can follow in the same way once the user asks; Tamil needs A6 first), everything in C–F, the antigravity cleanup.

---

# Analysis and backlog

## How this was produced

Read in full: `pipeline.md`, `state.json`, `batch_runner.py`, `synonym_audit.py`, `ai_generate_translation.py`, `ai_meaning_checker.py`, `ai_check_russian_meanings.py`, the archived thread's `review.md` and plan Drift Log, `.claude/commands/translate.md`, `.agents/skills/translate/SKILL.md`.
Read in part: `ai_translation_check.py` (id selection, delete path, CLI), `tools/ai_manager.py` (`request`), `tools/ai_batch_processor.py` (individual mode + response parsing), `improvments.md` (head only), `log.md` (head/tail).
Queried live `dpd.db` read-only. Ran `synonym_audit.py`'s own lexical functions over all three fields read-only (no AI calls, no writes).

Not run: any AI request, any `--fix`, any test. Every "bug" below is from reading the code path, not from reproducing it — reproduce before fixing.

## Live numbers (2026-11-13, read-only)

| Fact | Value |
|---|---|
| `russian` rows | 89,050 |
| pending drafts (`ru_meaning_raw` set, `ru_meaning` empty) | 64,921 |
| rows with both `ru_meaning_raw` and `ru_meaning` | 3,370 |
| RU rows matching the Op 5 empty-row filter | 77 (2 of them carry `ru_notes`, 1 carries `ru_meaning_lit`) |
| `tamil` rows | 62,400 |
| `temp/ai_from_batch_api/processed_ids.json` | 4,589 ids |
| `temp/synonym_audit/judgments.jsonl` | **missing** (the cache from the validation thread is gone) |

Lexical scan at the default threshold 0.85 (same functions the script uses):

| Field | Rows | Multi-part rows | Exact-dup rows | Near-dup entries / pairs |
|---|---|---|---|---|
| `ru_meaning_raw` | 68,291 | 42,448 | 28 | **151 / 155** |
| `ru_meaning` | 24,052 | 15,858 | 20 | 231 / 245 |
| `ta_meaning` | 62,400 | 37,614 | 379 | 798 / 826 |

Consequences:

- The production judge run on `ru_meaning_raw` is small: 151 entries ≈ 16 requests at `--batch-size 10`. Cost is not a concern; correctness of the apply step is.
- The "362-entry / 646-pair baseline" in `improvments.md` is **not comparable** any more. It counted pairs the old pairwise judge called distinct on 2026-07-06; the whole field now flags only 155 pairs. Why the pool shrank was not investigated (regeneration and promotions are the likely causes). Drop the baseline comparison from the acceptance criteria, or redefine it.

---

## A. Blockers for the production `--fix-ai` run

Fix or consciously accept these before item "Production run" below.

### A1. The human review step has no effect on what gets applied

`--ai` writes `<timestamp>_review.tsv`, but `--fix-ai` never reads it. It applies every cached `trim` verdict, and also judges any uncached entry and applies that verdict immediately, unreviewed (`synonym_audit.py:565-567`, `:598-603`). The user cannot reject a single row. The archived Drift Log already called this "a real data-quality risk".

Options, simplest first:

1. `--exclude-ids 1 2 3` on `--fix-ai`, plus a `--cached-only` switch so apply never makes new judgments.
2. **Recommended:** `--apply-tsv <reviewed.tsv>`. The reviewed TSV becomes the contract. Apply only rows the user left in the file (or marked in a new `decision` column), write `proposed_value`, and skip any row whose DB value no longer equals `current_value`. No AI calls at apply time, no dependence on the cache or the model key.
3. Interactive per-row confirm in the terminal. Slow for Tamil (798 entries).

### A2. The cache that links judge and apply lives in `temp/`

`CACHE_PATH = temp/synonym_audit/judgments.jsonl`. Project rules call `temp/` a disposable trashcan, and the file is in fact already gone. If it is cleaned between review and apply, `--fix-ai` silently re-judges and applies fresh, unreviewed verdicts. Option A1.2 removes this dependency. Otherwise move the cache somewhere not covered by the "delete temp files" rule.

### A3. `--fix` is documented as safe but is lossy

`normalize()` strips all bracketed text (`synonym_audit.py:69-74`), so variants that differ only in a bracketed qualifier count as exact duplicates and the later one is deleted. `--fix-ai` applies these too (`apply_drop` starts from `exact_dups`). Real rows that would lose content today:

- `ru_meaning` 13514: `от этого (человека); от этого (предмета)` (human-verified field)
- `ru_meaning` 21726: `что я (говорю) тебе?; что я (называю) тебе?`
- `ru_meaning_raw` 5975: `стекается; стекается (к)`
- `ru_meaning_raw` 49754: `говорит (за); выступает (от имени); (комм) говорит (с)`

Rough count of exact-dup rows where the strings differ beyond case/`ё`/trailing dot: 16 of 28 (`ru_meaning_raw`), 6 of 20 (`ru_meaning`), 69 of 379 (`ta_meaning`). The count heuristic is approximate; the examples are real.

Decided: never auto-remove these. Treat as "exact" only when the strings match with brackets kept; bracket-only differences always go to the review TSV (judged like near-duplicates, applied only via the reviewed TSV).

### A4. A failed judgment is cached forever

A `failed` verdict is written to the cache and later served as a cache hit (`synonym_audit.py:485-493`), so a transient provider error is never retried unless the variants change. Fix: do not serve `failed` records from cache.

### A5. Splitting on `;` ignores brackets

`split_meanings` splits on every `;`. Rows with a `;` inside parentheses: 25 (`ru_meaning_raw`), 8 (`ru_meaning`), 8 (`ta_meaning`). On those rows the variant list is wrong and a trim would rebuild a mangled field. Fix: bracket-aware split.

### A6. The judge is Russian-only; `ta_meaning` is not actually supported

`JUDGE_SYSTEM_PROMPT` says "Russian lexicographer", "Russian variants", and hard-codes `досл.` / `(комм)`; `_is_literal_gloss` checks only `досл.`. The old handoff's claim that the machinery "supports any field" holds for `ru_meaning` only. Tamil needs its own prompt and its own literal-prefix guard (id 2750 shows `வரி.` used as the literal marker — confirm the convention with the Tamil prompt in `tools/ai_related.py` before coding).

### A7. Smaller judge-loop issues

- Abort counter counts failed *entries*, not failed *requests* (`:515-518`); `_request_failures` is computed and discarded. One batch where the `досл.` guard turns five entries into FAILED aborts the run with a "provider may be down" message.
- Without `--provider/--model` the judge uses the whole default chain and caches under model key `"default"`, mixing verdicts from different models. The validation thread found flash trims 0/30, so the `--ai` example in `pipeline.md` (no model given) produces no signal. Resolved in the Thread 1 spec, point 7.
- A reply wrapped in markdown fences fails `json.loads` and costs a retry plus per-entry fallback. Strip fences before parsing.
- `--limit` is applied with no `ORDER BY`, so sample runs are not reproducible.
- The report and TSV are written only at the end; a crash mid-apply leaves DB changes with no record. Write an applied-changes TSV (id, old, new) incrementally — it doubles as an undo file.
- The review TSV does not say which variants were dropped; add a `dropped` column.
- `ru_meaning` is human-verified data. Decided: AI trimming is allowed there, via the reviewed-TSV apply only.

---

## B. Production run (original item 1, corrected)

Only after section A is settled.

1. Backup: `uv run python3 db/backup_tsv/backup_dps.py`
2. Judge only: `uv run python3 kamma/translate/scripts/synonym_audit.py --field ru_meaning_raw --ai --provider deepseek --model deepseek-v4-pro`
3. Review `temp/synonym_audit/<timestamp>_review.tsv` (already sorted by `max_ratio` descending).
4. Apply — use the Thread 1 flow (`--apply-tsv`), not the command that exists today. For reference, today's command is `... --fix-ai --provider deepseek --model deepseek-v4-pro` with the same pair so the cache key matches — but see A1/A2/A3: as written it ignores the review, depends on a `temp/` file, and also applies the lossy exact-dup fix.
5. Verify by re-running the report-only scan and reading a sample of changed rows from the DB.
6. Backup again and let the user commit the TSVs.

Then `ru_meaning` (231 entries; trimming approved) and `ta_meaning` (798 entries; blocked on A6).

---

## C. Pipeline bugs outside the synonym audit

### C1. Check op can loop forever on a provider outage

In `batch_runner.py:363-365`, `ok = attempted if returncode == 0 else 0`. The checker exits 0 even when every AI request failed, and failed words are not marked checked, so the next chunk selects the same 50 words. Result: endless loop, and `totals.checked` inflates by 50 per pass. The "will not loop forever" guard only works for generate. Fix: have the checker print a parseable "checked N" line (or compare snapshot size before/after) and use that as `ok`.

The same mechanism lets words that never parse sit at the head of the queue and be retried every chunk.

### C2. A non-JSON checker reply can clear a draft on a keyword match

`BatchProcessor.parse_ai_response` falls back to substring heuristics: any of "mismatch / wrong / incorrect / opposite" in the text → `MISMATCH`; no keyword → `MATCH` at 0.5 and the word is marked checked. In `meaning_raw` / `notes_raw` modes a `MISMATCH` clears the field. "No mismatch found" would clear a good draft. Fix: in clearing modes treat an unparseable reply as "no verdict" (not checked, not cleared).

Blast radius: `tools/ai_batch_processor.py` is shared — grep importers first.

### C3. Mechanical check covers only the last chunk

`ai_translation_check.py` reads `temp/last_translated.json`, which each generate subprocess overwrites. After a multi-chunk Op 1 session, Op 2 step 1 checks at most the last chunk (the 2026-07-08 session: 24 of ~5,000 rows). If the file's `lang` differs, it silently falls back to scanning the entire table. Fix: accept `--ids-file` and point Op 2 at the session-merged id list.

Related: `processed_ids.json` is a bare id list with no lang/mode, is never pruned, and feeds `DpdHeadword.id.in_(list(list_ids))` in one statement (`ai_meaning_checker.py:237`). At 4,589 ids this works; a full Op 6 re-ground (~26k rows) would push it toward SQLite's bound-variable limit. Chunk the `IN`, and store `{lang, mode, ids}` per session with a reset at session start.

### C4. Reject → regenerate has no memory

A cleared draft re-enters the Op 1 pool and is regenerated with the same prompt. Nothing counts attempts or feeds the checker's `reasoning` / `suggested_fix` back, so a word the checker dislikes can ping-pong indefinitely. The mismatch report also omits the English and the rejected Russian text, so the cleared draft is unrecoverable from the report. Suggested: a per-id reject counter (park for human review after 2), include both texts in the report, optionally pass the rejection reason into the regeneration prompt.

### C5. `PARTIAL_MATCH` also clears in raw modes

`ai_meaning_checker.py:519-522` clears on `MISMATCH` or `PARTIAL_MATCH`; `pipeline.md`'s table says MISMATCH only. The final "Found N problematic entries" line counts MISMATCH only, so it under-reports what was cleared. Decided: MISMATCH only — remove `PARTIAL_MATCH` from the clearing filter and from the report's mismatch filter; `PARTIAL_MATCH` rows stay in place (report them separately so they are still visible). In individual mode the clearing also runs twice (per chunk at `:677-680`, again in `generate_report` at `:609-612`) — harmless, redundant.

### C6. Op 5 deletes rows that still hold data

`remove_irrelevant` (RU) checks only `ru_meaning` and `ru_meaning_raw` (the two `or_` branches at `ai_generate_translation.py:113-131` are the same condition twice). Of the 77 matching rows, 2 have `ru_notes` and 1 has `ru_meaning_lit`. Add those columns (and `ru_cognate`) to the filter; then the "do not run Op 5 after Op 6" warning in `pipeline.md` becomes mostly unnecessary. It also ignores NULLs.

### C7. Explicit provider means no fallback

`batch_runner.py` always passes `--provider` and `--model`; `AIManager.request` then tries exactly that one pair. The OpenRouter entries in `default_models` are never used by the pipeline, and "fails on every provider in the chain" in `pipeline.md` is inaccurate — one DeepSeek outage is exit 2. Decided: the chain is DeepSeek direct first, OpenRouter-DeepSeek second. So when no pair is given the runner must not pin `default_models[0]` alone; it needs a two-step chain (same model family, so verdict/draft quality stays comparable). Design point for the thread: `AIManager.request` tries exactly one pair when both are passed, so the fallback has to live either in the runner/workhorse (retry with the second pair on failure) or in a dedicated two-entry model list. `default_models` also contains two non-DeepSeek OpenRouter entries (llama, gpt-4.1-nano) that must not be reached. The same chain applies to the synonym judge with the pro models (`grounded_models` already lists deepseek-v4-pro then openrouter deepseek-v4-pro); cache/model-key handling must treat both as the same judge.

### C8. `ai_translation_check.py` rough edges

Default `-lang` is `ta` while every other script defaults to `ru`. `-delete` for RU clears only `ru_meaning_raw` even though it also scans `ru_meaning` and `ru_meaning_lit`. Uses `print()` instead of `tools/printer`. Tamil id 2750 contains Hangul (`상태`) — not checked whether the script flags foreign non-Latin scripts; worth a test.

---

## D. Efficiency

- **Full-table load per chunk.** Each generate chunk is a fresh subprocess that runs `.all()` on the whole pending pool and then slices 50 (`ai_generate_translation.py:356`). Each check chunk loads every `(DpdHeadword, Russian)` pair for the mode and then slices (`ai_meaning_checker.py:640`). A full `meaning_raw` pass is ~1,300 chunks, each loading ~65k ORM pairs. Fix: `COUNT` plus SQL `LIMIT`; or let the checker loop internally — it already saves progress every 50 words, so runner chunking adds nothing for `check`.
- **`--status`** spawns four `uv run` subprocesses that each load a full pool to print one count. Replace with count queries in-process (the checker counts already work this way).
- **Per-row commits** in the checker clear path and the synonym apply path. Low priority.

---

## E. Skill and docs drift

- Skill description in both `.claude/commands/translate.md` and `.agents/skills/translate/SKILL.md` still says "within the antigravity 5h quota window"; the pipeline dropped antigravity in commit `3e36c2f76`.
- Antigravity is retired for this pipeline (user, 2026-11-13). Remove every mention from `pipeline.md`, both skill descriptions, and the antigravity wording in `batch_runner.py` docstrings/error messages. Approved: remove the `antigravity_cli_work_models` key from `tools/ai_models.json`. No Python file reads that key (grep 2026-11-13: only `batch_runner.py`'s docstring and `registry.json` mention it), and upstream already dropped it. In the same change, update the `tools/ai_models.json` entry in `kamma/upstream_sync/registry.json` (its `local_changes` / notes at lines ~161-167 describe the antigravity key) and run `validate_registry.py`. **Do not touch `tools/ai_manager.py`** — it is an upstream copy; its antigravity probe stays as upstream ships it.
- `state.json` → `window_start` is a leftover from that quota gate. Remove it or rename to what it now means.
- `log.md` header documents `YYYY-MM-DD HH:MM | op mode lang | ok/attempted | note`; real lines are `- <ISO> | op=… mode=… lang=… chunk=… attempted=… ok=…`. It is tracked and grows one line per chunk (1,072 lines), including a trailing `attempted=0` line per session. Decided: one summary line per session (op, mode, lang, chunks, attempted, ok, start–end). Existing per-chunk history can stay as is.
- `pipeline.md` Op 2 says "see Phase 2" for the Tamil semantic checker; no such section exists.
- `pipeline.md` Op 4 does not describe the judge → review → apply workflow, the cache, `--provider/--model`, `--batch-size` or `--max-judgments`. Rewrite after section A lands.
- The menu shows no counts for Op 4/5/6. Cheap to add: lexical-scan counts, the Op 5 dry-run count, the `-reset-grounded -dry-run` count.
- `improvments.md`: filename typo, and 1,100 lines of a per-entry dump from 2026-07-06 that no longer matches the DB. Rename via the Atomic Rename Protocol and reduce to findings; the dump can be regenerated.
- Archived `review.md` cites `tests/kamma/translate/test_synonym_audit.py`; the tests now live in `tests/kamma_tests/translate/` (`test_synonym_audit.py`, `test_batch_runner.py`, `test_ai_generate_translation.py`, `test_ai_meaning_checker.py`). No tests exist for `ai_translation_check.py` or `ai_check_russian_meanings.py`.

---

## F. `batch_runner.py` integration (original item 3)

Recommendation: do **not** wrap `synonym_audit.py` as a chunked op. It is a single pass with its own cache and resume, and the full RU run is ~16 requests. Integrate lightly instead:

- show lexical-scan counts per field in `--status`;
- append one `log.md` line per audit run (matches the one-line-per-session decision) and record it in `state.json`;
- keep judge and apply as direct script calls documented in `pipeline.md`.

Revisit only if the audit becomes a release-pipeline gate.

---

## Suggested thread split

1. **Synonym audit: safe apply + production run** — A1–A7, then B for `ru_meaning_raw`. Highest value, smallest surface (one script + its test file).
2. **Checker/runner correctness** — C1, C2, C3, C5. C2 touches shared `tools/` code and needs the blast-radius check and the recorded-fixture harness.
3. **Pipeline hygiene** — C4, C6, C7, C8, D, E, F.
4. **Tamil synonym audit** — A6, then B for `ta_meaning`.

## Not verified

- No bug above was reproduced by running code; all come from reading the code path.
- Whether individual providers check `finish_reason` for truncated output — `AIManager.request` itself does not; provider classes were not read.
- Why the `ru_meaning_raw` near-dup pool fell from the July figures to 151 entries.
- The Tamil literal-gloss prefix convention.
- Current generate-pool sizes (`batch_runner.py --status` was not run).
