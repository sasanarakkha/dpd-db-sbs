# Translate Pipeline Skill

## Purpose

Guided, resumable AI translation workflow for the `Russian` and `Tamil` tables.
The agent presents the menu below, recommends the next sensible operation based on
current state, and runs it only after the user picks. All AI operations walk
one model chain: `tools/ai_models.json` → `default_models` (DeepSeek Flash direct,
then the OpenRouter fallback entries). Nothing is pinned by the runner.

**Workhorse scripts** (do not duplicate their logic — call them):

| Script | Job |
|--------|-----|
| `kamma/translate/scripts/ai_generate_translation.py` | Generate translations (`-lang ru\|ta`, `-mode meaning\|lit\|note`), `-remove` cleanup, `-json` batch-API export |
| `kamma/translate/scripts/ai_check_russian_meanings.py` | AI semantic check of RU columns (8 modes, resumable snapshots) |
| `kamma/translate/scripts/ai_translation_check.py` | Mechanical anomaly check (`-lang ru\|ta`): leftover Latin, length outliers |
| `kamma/translate/scripts/batch_runner.py` | Chunked, resumable wrapper around the two scripts above (walks the `default_models` chain) |
| `kamma/translate/scripts/synonym_audit.py` | Detect/trim duplicate and near-identical synonyms in meaning fields |
| `kamma/translate/scripts/model_benchmark.py` | Not part of the menu: benchmark candidate models (judge / generate / check) on fixed samples, read-only; per-call JSONL, 60 s timeout, resumable. Use before changing `default_models` |
| `db/backup_tsv/backup_dps.py` | Backup Russian/SBS/Tamil tables to tracked TSVs |

**State & history**

- `kamma/translate/state.json` — session start, last operation, totals.
  Owned by `batch_runner.py`; read it, never hand-edit during a run.
- `kamma/translate/log.md` — append-only, one line per session
  (`<start> → <end> | op=… mode=… lang=… chunks=N attempted=A ok=O exit=<code>`; audit runs: `op=4 … field=…`).
- `kamma/translate/rejects.json` — reject memory: `{"<id>": {"count", "reason", "last"}}`.
  The checker increments it each time it clears a `ru_meaning_raw` draft; ids with
  count ≥ 2 are parked (excluded from the Op 1 pool). Regeneration adds the last
  reject reason to the prompt. **Un-park = delete the id's entry** from the file.
- Checker snapshots: `temp/ai_*_check/checked_ids.json` (per mode, auto-invalidated
  when English source text changes).
- Generation session ids: `temp/last_translated.json` (last run) and
  `temp/ai_from_batch_api/processed_ids.json` (`{lang, mode, ids}`, merged per chunk; reset only
  when a generate session starts with a different lang/mode; feeds `*_list` checker modes and `ai_translation_check.py --ids-file`).

## Procedure

### 1. Read state

1. Run `uv run python3 kamma/translate/scripts/batch_runner.py --status`.
   It is read-only and in-process (count queries only). It prints: last op, totals, generation
   pool sizes per lang/mode (Op 1), unchecked counts per checker mode (Op 2/3), lexical
   synonym-flagged rows per field and the last audit (Op 4), rows Op 5 would remove, rows
   Op 6 would re-ground, parked rejects, and checker snapshot sizes.

### 2. Present the menu

Show the menu with the current counts inline (both generation pool sizes and checker pending counts from `--status`) and ONE recommendation:

```
1. Translate NEW words        (meaning/ru: X, lit/ru: Y, note/ru: Z, meaning/ta: W pending)
2. Verify latest generation   (mechanical check + AI check of just-generated rows)
3. Check existing columns     (meaning: A, meaning_raw: B, russian_grammar_meaning_raw: C, meaning_lit: D, notes: E, notes_raw: F pending)
4. Synonym audit              (find near-identical synonyms; trim on approval)
5. Clean irrelevant rows      (empty RU rows / Latin-script TA rows)
6. Re-ground existing drafts  (clear rooted ru_meaning_raw drafts → back into pool 1)
7. Status only / exit
```

Recommended default order for a fresh cycle: 1 → 2 → (repeat 1–2 until pool empty)
→ 3 → 4 → 5.

### 3. Operations

**Model chain:** with `--provider`/`--model` omitted, every AI script walks `tools/ai_models.json` → `default_models` in order (DeepSeek Flash first, then the OpenRouter fallback) — no flags needed. Only pass `--provider`/`--model` explicitly if the user asks for a specific model, and always pass both together (never one alone).

**Off-peak rule:** DeepSeek charges full price in peak hours: Mon–Fri 01:00–04:00 and 06:00–10:00 UTC, except Chinese public holidays (all other hours, weekends and holidays are half price). `batch_runner.py` and `synonym_audit.py --ai` refuse to start in peak (exit 1, prints the next off-peak start) unless `--allow-peak` is given; a runner session that reaches peak mid-run stops cleanly after the current chunk (exit 0). Holidays are coded per year in `kamma/translate/scripts/offpeak.py` (`CN_HOLIDAYS`). If the current year is missing, every AI run is blocked even with `--allow-peak` — add the year from the State Council notice "国务院办公厅关于<year>年部分节假日安排的通知" (usually published early November).

**Chunk-by-chunk rule for all operations:** Run with the default chunk size of 50 words (`--chunk 50` or default).
- For a test run or initial verification, run exactly 1 chunk of 50 words (`--max-chunks 1`).
- For a full run, omit `--max-chunks` so the runner automatically loops through all words in chunks of 50.

#### Op 1 — Translate NEW words

```bash
uv run python3 kamma/translate/scripts/batch_runner.py --op generate --mode meaning --lang ru
```

- Modes: `meaning` (ru/ta), `lit` (ru only), `note` (ru only).
- Default chunk 50, runs until the pool is empty (exit 0) or a chunk fails on
  every provider (exit 2 — a real error; report it and stop, do not loop).
- The runner merges each chunk's ids into `temp/ai_from_batch_api/processed_ids.json` so Op 2
  can check them. A re-run with the same `--lang`/`--mode` (after exit 2 or a peak stop) keeps
  the earlier ids; a different `--lang`/`--mode` starts a fresh file. Delete the file to start
  fresh by hand.
- Ids with 2+ rejects in `rejects.json` are skipped (parked).

#### Op 2 — Verify latest generation

Run both, in this order:

1. Mechanical: `uv run python3 kamma/translate/scripts/ai_translation_check.py -lang <ru|ta> --ids-file temp/ai_from_batch_api/processed_ids.json`
   (restricts the scan to the session ids; `-lang` defaults to `ru`; `-delete` clears every flagged RU column — destructive, confirm first).
2. AI semantic (RU only):
   `uv run python3 kamma/translate/scripts/batch_runner.py --op check --mode meaning_raw_list`
   — checks only the session ids; MISMATCH rows get `ru_meaning_raw` cleared
   automatically and re-enter the Op 1 pool (that IS the retranslate loop).
   For `lit`: `--mode meaning_lit_list` (report-only, no clearing).
   Only a `MISMATCH` verdict clears; `PARTIAL_MATCH` rows are listed separately and kept.

For Tamil there is no semantic checker yet (not yet supported) — mechanical check only.

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

Evaluate the pending count for the selected mode (from Step 1) and recommend chunking:

- Always recommend running chunk-by-chunk with a chunk size of 50 (`--chunk 50` or default) to ensure progress is saved and mismatches cleared every 50 words.
- For a test run or initial verification of a new mode, run exactly 1 chunk of 50 words (`--max-chunks 1`).
- For a full run to process the entire pool, omit `--max-chunks` so the runner loops through all words 50 at a time until complete.

Ask the user: run a single test chunk of 50 words, or run all remaining words in 50-word chunks?

The checker is configured to save checked IDs and clear database mismatches incrementally in chunks of 50, meaning no progress is lost if the process is interrupted:
```bash
uv run python3 kamma/translate/scripts/batch_runner.py --op check --mode <mode>               # all
uv run python3 kamma/translate/scripts/batch_runner.py --op check --mode <mode> --chunk <size> --max-chunks 1  # one chunk
```

> [!IMPORTANT]
> For long runs (> 1,000 words), prevent your Mac from sleeping (while still allowing the screen to turn off) by prefixing the command with `caffeinate -i`:
> ```bash
> caffeinate -i uv run python3 kamma/translate/scripts/batch_runner.py --op check --mode <mode>
> ```

Reports land in `temp/ai_<mode>_check/<timestamp>_mismatches.txt` — after the run,
read the report and summarize mismatches for the user. Snapshots make re-runs
incremental; `--reset` on the underlying script starts a mode from scratch.

#### Op 4 — Synonym audit

```bash
uv run python3 kamma/translate/scripts/synonym_audit.py --field ru_meaning_raw                 # report (no AI, no writes)
uv run python3 kamma/translate/scripts/synonym_audit.py --field ru_meaning_raw --fix           # strict duplicates only
uv run python3 kamma/translate/scripts/synonym_audit.py --field ru_meaning_raw --ai            # judge → review TSV (no writes)
uv run python3 kamma/translate/scripts/synonym_audit.py --field ru_meaning_raw --apply-tsv PATH  # apply the reviewed TSV
```

- Fields: `ru_meaning`, `ru_meaning_raw`, `ta_meaning` (`--ai` is not supported for `ta_meaning`).
- `--fix` removes only strict duplicates (case, `ё`/`е`, spacing, trailing dot; brackets kept).
- `--ai` follows the model chain, honours the off-peak rule and **never writes the DB**. It writes
  `temp/synonym_audit/<ts>_review.tsv` (columns `id, field, lemma, english, current_value,
  proposed_value, dropped, max_ratio, verdict, judge_model, decision`).
- **Review protocol:** the user opens the TSV; to reject a row delete it or set `decision=n`;
  `proposed_value` may be hand-edited and is applied as edited.
- `--apply-tsv PATH` is the only way to apply AI trims: no AI, no cache; each row is committed
  and logged immediately to `temp/synonym_audit/<ts>_applied.tsv` (undo record: `id, field, old, new`).
  Rows rejected, unchanged or stale (DB value no longer equals `current_value`) are skipped; a file
  whose rows target another `--field` aborts before any write. Destructive — require explicit
  user confirmation and a fresh `backup_dps.py` run first.
- Every run appends a line to `log.md` and records `last_audit` in `state.json`.

#### Op 5 — Clean irrelevant rows

```bash
uv run python3 kamma/translate/scripts/ai_generate_translation.py -remove -lang <ru|ta> --dry-run
```

Show the dry-run list first; on user confirmation re-run without `--dry-run`.
(RU: deletes rows where `ru_meaning`, `ru_meaning_raw`, `ru_meaning_lit`, `ru_notes` and `ru_cognate` are all empty;
TA: deletes ta_meaning rows contaminated with Latin script.)

#### Op 6 — Re-ground existing drafts

One-shot reset that re-enters existing AI drafts into the Op 1 pool so they
are regenerated with same-root grounded prompts. Selects only drafts whose
prompt actually changes: `root_key` non-empty AND ≥1 verified same-root
`ru_meaning` exists (~26k of ~65k pending drafts as of 2026-07-09).

⚠️ Destructive (clears `ru_meaning_raw`). Protocol:

1. Fresh backup first: `uv run python3 db/backup_tsv/backup_dps.py`
2. Dry-run and show the user the count:
   `uv run python3 kamma/translate/scripts/ai_generate_translation.py -reset-grounded -dry-run [-limit N]`
3. On explicit confirmation, re-run without `-dry-run`.
4. Proceed straight to Op 1 (meaning/ru) to regenerate, then Op 2 to verify.

- Do NOT run Op 5 between the reset and regeneration: cleared rows match
  Op 5's empty-row filter and would be deleted (losing any `ru_notes`).
- Runs directly, not through `batch_runner.py`; the regeneration itself is
  ordinary Op 1.
- Rollout: pilot with `-limit 100` → regenerate → human-review quality →
  full reset only after the pilot is approved.
- ru only. There is no lit-mode analog: `ru_meaning_lit` has no
  raw/verified split, so a bulk overwrite could destroy human work.

### 4. Batch protocol

- One "session" = repeated chunks until pool empty (exit 0), peak hours begin (exit 0, clean
  stop), or a chunk fails on every provider in the chain / the checker verifies nothing (exit 2) —
  a real error. Report it and stop the turn; the user re-runs the same command when ready.
- A run refused by the off-peak guard (exit 1) changed nothing; wait for off-peak or ask the user
  about `--allow-peak`.
- The runner appends one line per session to `kamma/translate/log.md` (format above).

### 5. End of session

Summarize: chunks run, rows translated/checked/cleared, reports written, and
current pool counts.

## Safety rules

- Field-clearing checker modes, `-remove`, `ai_translation_check.py -delete`, `-reset-grounded` and
  `synonym_audit.py --apply-tsv` are destructive: dry-run / report first, explicit confirmation,
  recommend `backup_dps.py` beforehand.
- This skill never commits. Data changes live in `dpd.db`; TSV backups are the
  durable artifact the user commits when satisfied.
- Economy: never re-run LLM generation to fix formatting problems — use local text
  manipulation (synonym_audit, SQL/py one-offs in `temp/`).
