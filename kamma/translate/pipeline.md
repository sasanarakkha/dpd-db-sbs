# Translate Pipeline Skill

## Purpose

Guided, resumable AI translation workflow for the `Russian` and `Tamil` tables.
The agent presents the menu below, recommends the next sensible operation based on
current state, and runs it only after the user picks. Batches are sized for the
Antigravity CLI (`agy`) 5-hour quota window.

**Workhorse scripts** (do not duplicate their logic — call them):

| Script | Job |
|--------|-----|
| `kamma/translate/scripts/ai_generate_translation.py` | Generate translations (`-lang ru\|ta`, `-mode meaning\|lit\|note`), `-remove` cleanup, `-json` batch-API export |
| `kamma/translate/scripts/ai_check_russian_meanings.py` | AI semantic check of RU columns (8 modes, resumable snapshots) |
| `kamma/translate/scripts/ai_translation_check.py` | Mechanical anomaly check (`-lang ru\|ta`): leftover Latin, length outliers |
| `kamma/translate/scripts/batch_runner.py` | Chunked, quota-aware wrapper around the two scripts above |
| `kamma/translate/scripts/synonym_audit.py` | Detect/trim duplicate and near-identical synonyms in meaning fields |
| `db/backup_tsv/backup_dps.py` | Backup Russian/SBS/Tamil tables to tracked TSVs |

**State & history**

- `kamma/translate/state.json` — quota window, resume time, last operation, totals.
  Owned by `batch_runner.py`; read it, never hand-edit during a run.
- `kamma/translate/log.md` — append-only, one line per chunk/run.
- Checker snapshots: `temp/ai_*_check/checked_ids.json` (per mode, auto-invalidated
  when English source text changes).
- Generation session ids: `temp/last_translated.json` (last run) and
  `temp/ai_from_batch_api/processed_ids.json` (session-merged, feeds `*_list` checker modes).

## Procedure

### 1. Read state

1. Run `uv run python3 kamma/translate/scripts/batch_runner.py --status`.
   It prints: quota window / resume time, last op, totals, and pending-work counts
   (dry-run row counts for generation per lang/mode, unchecked counts per checker mode).
2. If `resume_at` is in the future, tell the user how long until the antigravity
   window reopens and offer: wait, run a non-LLM operation (cleanups, mechanical
   check, synonym audit without `--ai`), or `--fallback` (paid providers — needs
   explicit user confirmation every time).

### 2. Present the menu

Show the menu with the current counts inline (both generation pool sizes and checker pending counts from `--status`) and ONE recommendation:

```
1. Translate NEW words        (meaning/ru: X, lit/ru: Y, note/ru: Z, meaning/ta: W pending)
2. Verify latest generation   (mechanical check + AI check of just-generated rows)
3. Check existing columns     (meaning: A, meaning_raw: B, russian_grammar_meaning_raw: C, meaning_lit: D, notes: E, notes_raw: F pending)
4. Synonym audit              (find near-identical synonyms; trim on approval)
5. Clean irrelevant rows      (empty RU rows / Latin-script TA rows)
6. Status only / exit
```

Recommended default order for a fresh cycle: 1 → 2 → (repeat 1–2 until pool empty)
→ 3 → 4 → 5.

### 3. Operations

**Chunk-by-chunk rule for all operations:** If the total pending count exceeds
100 (or whatever the user considers reasonable), offer to run either all at once
or chunk by chunk. For chunks, ask for chunk size (e.g. 5000, 10000) and run
with `--chunk <N> --max-chunks 1`, then ask to continue or stop after each chunk.

#### Op 1 — Translate NEW words

```bash
uv run python3 kamma/translate/scripts/batch_runner.py --op generate --mode meaning --lang ru
```

- Modes: `meaning` (ru/ta), `lit` (ru only), `note` (ru only).
- Default chunk 25, runs until the pool is empty or quota is exhausted (exit 3).
- Forces `-provider antigravity_cli`; add `--fallback` ONLY on explicit user request.
- On exit 3 (quota): report `resume_at` from state.json and stop. Do not silently
  switch to paid providers.
- After each chunk the runner merges the chunk's ids into
  `temp/ai_from_batch_api/processed_ids.json` so Op 2 can check the whole session.

#### Op 2 — Verify latest generation

Run both, in this order:

1. Mechanical: `uv run python3 kamma/translate/scripts/ai_translation_check.py -lang <ru|ta>`
2. AI semantic (RU only):
   `uv run python3 kamma/translate/scripts/batch_runner.py --op check --mode meaning_raw_list`
   — checks only the session ids; MISMATCH rows get `ru_meaning_raw` cleared
   automatically and re-enter the Op 1 pool (that IS the retranslate loop).
   For `lit`: `--mode meaning_lit_list` (report-only, no clearing).

For Tamil there is no semantic checker yet (see Phase 2) — mechanical check only.

#### Op 3 — Check existing columns

⚠️ Before any mode that CLEARS fields, require explicit user confirmation and
recommend `uv run python3 db/backup_tsv/backup_dps.py` first.

| Checker mode | Compares | On MISMATCH |
|---|---|---|
| `meaning` | meaning_1 vs ru_meaning (+lit) | report only |
| `meaning_raw` | meaning_1 vs ru_meaning_raw | **clears ru_meaning_raw** |
| `russian_grammar_meaning_raw` | grammar shape of ru_meaning_raw | report only |
| `meaning_lit` | meaning_lit vs ru_meaning_lit | report only |
| `notes` | notes vs ru_notes (human) | report only |
| `notes_raw` | notes vs ru_notes (`[пер. ИИ]`) | **clears ru_notes** |

Evaluate the pending count for the selected mode (from Step 1) and suggest a realistic option to the user:

- **Tiny pool (< 100 pending)**: Recommend running **all at once** (`--chunk 0`).
- **Medium pool (100 - 5000 pending)**: Recommend running **chunk by chunk** with a chunk size of **500 - 1000**.
- **Large pool (> 5000 pending)**: Recommend starting with a trial run of **500 - 1000** first, or running in chunks of **5000**. Avoid running all at once as it could run into rate limits or take extremely long without intermediate feedback.

Ask the user: run all at once, or chunk by chunk?

- **All at once**: `--chunk 0` (defaults to all remaining unchecked)
- **Chunk by chunk**: run with `--chunk <N> --max-chunks 1`. After each chunk, ask if they want to continue or stop.

```bash
uv run python3 kamma/translate/scripts/batch_runner.py --op check --mode <mode>               # all
uv run python3 kamma/translate/scripts/batch_runner.py --op check --mode <mode> --chunk <size> --max-chunks 1  # one chunk
```

Reports land in `temp/ai_<mode>_check/<timestamp>_mismatches.txt` — after the run,
read the report and summarize mismatches for the user. Snapshots make re-runs
incremental; `--reset` on the underlying script starts a mode from scratch.

#### Op 4 — Synonym audit

```bash
uv run python3 kamma/translate/scripts/synonym_audit.py --field ru_meaning_raw          # report
uv run python3 kamma/translate/scripts/synonym_audit.py --field ru_meaning_raw --fix    # safe dedup
uv run python3 kamma/translate/scripts/synonym_audit.py --field ru_meaning_raw --ai     # + AI near-dup judging
```

- Fields: `ru_meaning`, `ru_meaning_raw`, `ta_meaning`.
- `--fix` removes only exact duplicates after normalization (safe).
- `--ai --fix-ai` trims AI-confirmed near-duplicates — destructive; require explicit
  user confirmation and a fresh `backup_dps.py` run first.
- Present the report summary; the user decides fix scope.

#### Op 5 — Clean irrelevant rows

```bash
uv run python3 kamma/translate/scripts/ai_generate_translation.py -remove -lang <ru|ta> --dry-run
```

Show the dry-run list first; on user confirmation re-run without `--dry-run`.
(RU: deletes rows where both ru_meaning and ru_meaning_raw are empty;
TA: deletes ta_meaning rows contaminated with Latin script.)

### 4. Batch & quota protocol

- One "session" = repeated chunks until pool empty (exit 0) or quota hit (exit 3).
- On exit 3: `state.json` gets `resume_at = now + 5h` (conservative assumption about
  agy's rolling window). Report it, append the log line, stop the turn.
- Never bypass `resume_at` except via `--force` at the user's explicit request.
- `--fallback` (paid chain) always requires fresh explicit user consent — never
  carry consent over from a previous run.
- The runner appends one line per chunk to `kamma/translate/log.md`:
  `YYYY-MM-DD HH:MM | op mode lang | ok/attempted | note`

### 5. End of session

Summarize: chunks run, rows translated/checked/cleared, reports written, current
pool counts, and (if quota-paused) the resume time and exact resume command.

## Safety rules

- Field-clearing checker modes, `-remove`, and `--fix-ai` are destructive: dry-run /
  report first, explicit confirmation, recommend `backup_dps.py` beforehand.
- This skill never commits. Data changes live in `dpd.db`; TSV backups are the
  durable artifact the user commits when satisfied.
- Economy: never re-run LLM generation to fix formatting problems — use local text
  manipulation (synonym_audit, SQL/py one-offs in `temp/`).
