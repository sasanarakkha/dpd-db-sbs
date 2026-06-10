# spec.md — Repeating Check of Russian against English

**Issue:** sasanarakkha/dpd-db-sbs #40

## Overview

The AI meaning checker (issue #28) validates Russian translations against English meanings using AI. It does a full scan of all words, tracking checked IDs so it doesn't re-check the same words. Issue #40 asks for this process to be **repeating** — able to run again after upstream English meanings change, without manually wiping the checked IDs files.

## Problem

Currently the checker does a one-time full scan per year (~18K+ words). When it finishes, all IDs are in the `checked_ids` file. If the English content changes in the upstream sync, the corresponding Russian translation may be stale — but the checker skips those IDs because they're already "done".

The only current workaround is to manually delete the checked IDs JSON files and restart from scratch, which is expensive in AI API calls.

## What It Should Do

1. **Smart invalidation**: Before each analysis run, compare a stored hash of the English content (exactly the composed string that was sent to the AI) against the current database value. Any ID where the English changed gets removed from the checked set, causing the checker to re-check it naturally.

2. **Hash the composed content, not a single column**: In `meaning`, `meaning_raw`, `meaning_ru_raw`, and `meaning_raw_list` modes the string sent to the AI is `meaning_1` plus `"; lit. {meaning_lit}"` when `meaning_lit` exists (`tools/ai_meaning_checker.py`, English-content block in `get_words_for_comparison_with_session`). Hashing `meaning_1` alone would miss `meaning_lit`-only changes. The composition logic is extracted into one helper (`compose_english_content`) used by both the comparison query and invalidation, so the two can never drift apart.

3. **Cost-free migration**: Existing v1 files (plain JSON list of IDs) auto-migrate to v2 (dict ID → hash). Migrated IDs get an **empty hash**, which is a reserved sentinel meaning "baseline unknown". On the next invalidation pass, empty hashes are **seeded from the current DB value** — NOT invalidated. Assumption: what is in the DB at migration time is what was checked. This misses English changes that happened between the last check and migration (the same blind spot that exists today), but costs zero AI calls. A full ~18K re-check on migration is explicitly NOT wanted — it is the exact expense issue #40 exists to avoid.

4. **Automatic by default**: Invalidation runs automatically before analysis. A `--no-auto-invalidate` flag disables it.

5. **Manual reset option**: A `--reset` flag deletes the checked-IDs snapshot file for the given mode and exits (for a fresh annual cycle).

6. **Same interface, new default**: The existing `scripts/other/ai_check_russian_meanings.py` CLI is unchanged in structure; the two new flags are additive. One behavior change requested by the user: the default processing mode flips from batch to **individual** (the user's actual workflow; batch is kept as an opt-in via `--batch` for possible future use).

7. **Regeneration invalidation**: When `scripts/other/ai_generate_translation.py` regenerates a Russian translation (direct mode, `translation_generate()`, lang `ru`), the affected IDs are removed from the corresponding checker snapshot files, so the new translations re-enter the check queue. Without this, a word whose mismatched `ru_meaning_raw` was cleared and later regenerated would never be re-checked (its English hash is unchanged). Limitation: only the direct DB-writing path gets this hook; the JSONL batch-API export path (`make_json`) does not.

## Constraints

- Must use existing `tools/ai_meaning_checker.py` — layer on top, no rewriting of core query/comparison logic.
- **`tools/ai_batch_processor.py` is NOT modified.** Hashes for newly checked IDs are reconciled inside the checker at save time, from an `english_by_id` map built from the comparisons (see plan, Task 2.1). This avoids threading per-ID English values through the batch processor's call sites.
- New module is `tools/meaning_snapshot_ru.py` (Tier 3 new local file → `_ru` locale suffix per Namespace Isolation rules). It must be added to `unique_paths` in `kamma/upstream_sync/registry.json` in the same change; both registry validators must pass.
- Hash: normalize (strip + collapse all whitespace runs to single spaces), then SHA-256 truncated to 16 hex chars (64 bits — collision risk negligible at ~18K entries). Hash chosen over storing the raw normalized string to keep snapshot files small; trade-off: hashes are not human-debuggable.
- The empty string `""` is reserved as the "baseline unknown — seed from DB on next invalidation" sentinel and is never produced as a real hash value.
- All new/modified code: `pathlib.Path`, modern type hints, `tools/printer.py` (`pr`) for new output, no `sys.path` hacks. Existing `print()` calls in untouched code paths are left as-is (scope discipline).
- Tests live in `tests/tools/` (project convention), as `tests/tools/test_meaning_snapshot_ru.py`.

## Snapshot File Format

- v1 (current, legacy): `[12345, 12346, ...]` — plain JSON list of ints.
- v2 (new): `{"format_version": 2, "checked": {"12345": "a1b2c3d4e5f60718", ...}}` — keys are stringified ints (JSON requirement), values are 16-hex-char hashes or `""` (sentinel).
- `meaning_raw_list` shares its snapshot file with `meaning_raw`, and `meaning_lit_list` with `meaning_lit` (existing behavior, kept). This is safe because each pair composes identical English content, so hashes are interchangeable.

## English Content per Mode (single source of truth: `compose_english_content`)

| Mode | English content that is hashed |
|------|-------------------------------|
| `notes`, `notes_raw` | `headword.notes` |
| `meaning_lit`, `meaning_lit_list` | `headword.meaning_lit` |
| `meaning`, `meaning_raw`, `meaning_ru_raw`, `meaning_raw_list` | `f"{meaning_1}; lit. {meaning_lit}"` if `meaning_lit` else `meaning_1` |

## How We'll Know It's Done

- Running the checker after an upstream sync where `meaning_1` **or** `meaning_lit` changed → those IDs are invalidated and re-checked automatically; a summary line reports counts.
- First run after migration from v1: zero IDs invalidated, all IDs seeded from current DB, zero extra AI calls.
- `--reset` deletes the snapshot file for the given mode; `--no-auto-invalidate` skips invalidation.
- Running the checker without flags uses individual processing; `--batch` opts back into batch mode.
- After `translation_generate()` regenerates a Russian translation, the word's ID is gone from the matching checker snapshot files (covered by unit test; visible as a "dropped from" summary line during generation runs).
- All tests in `tests/tools/test_meaning_snapshot_ru.py` pass, including v1→v2 migration and seeding.
- `kamma/upstream_sync/scripts/validate_registry.py` and `verify_smd_coverage.py` pass.
- Full validation clean on every touched file: `ruff check --fix`, `ruff format`, `pyright`, `pyrefly check --min-severity warn`.
- Relevant docs updated (`docs_rus/dpd_rus.md` / `docs_rus/features/features.md` checker description, script docstring).

## What's Not Included

- No change to the AI comparison logic or to `tools/ai_batch_processor.py`.
- No re-check when the Russian side is edited **manually** (in the DB or GUI). The only Russian-side trigger is the regeneration hook (point 7); general Russian-edit tracking is out of scope.
- No hook in the JSONL batch-API export/ingestion path of `ai_generate_translation.py`.
- No scheduling or automation — this is still a manually triggered script.
- No new reporting format — existing mismatch reports are unchanged.
- No migration of existing `print()` calls to `pr` outside the lines actually touched.
