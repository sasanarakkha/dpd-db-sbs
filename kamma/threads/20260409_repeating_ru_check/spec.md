# spec.md — Repeating Check of Russian against English

**Issue:** sasanarakkha/dpd-db-sbs #40

## Overview

The AI meaning checker (issue #28) validates Russian translations against English meanings using AI. It does a full scan of all words, tracking checked IDs so it doesn't re-check the same words. Issue #40 asks for this process to be **repeating** — able to run again after upstream English meanings change, without manually wiping the checked IDs files.

## Problem

Currently the checker does a one-time full scan per year (~18K+ words). When it finishes, all IDs are in the `checked_ids` file. If `meaning_1` or `meaning_lit` changes in the upstream sync, the corresponding Russian translation may be stale — but the checker skips those IDs because they're already "done".

The only current workaround is to manually delete the checked IDs JSON files and restart from scratch, which is expensive in AI API calls.

## What It Should Do

1. **Smart invalidation**: Before each analysis run, compare the stored English field value (as a hash) against the current database value. Any ID where the English changed gets removed from the checked set, causing the checker to re-check it naturally.

2. **Automatic by default**: Invalidation runs automatically before analysis. A `--no-auto-invalidate` flag disables it.

3. **Manual reset option**: A `--reset` flag wipes all checked IDs for a fresh start (once per year or when needed).

4. **Same interface**: The existing `scripts/other/ai_check_russian_meanings.py` CLI is unchanged in structure — users run the same command as before.

## Constraints

- Must use existing `tools/ai_meaning_checker.py` — no rewriting core logic.
- Hash normalization: strip + collapse whitespace before hashing. Catches real content changes; ignores trivial formatting.
- Must auto-migrate from current v1 format (plain JSON list) to v2 (dict with hashes). Migration causes one full re-check, which is correct.
- All code: `pathlib.Path`, modern type hints, `tools/printer.py` for output, no `sys.path` hacks.

## Mode-to-Field Mapping

| Mode | English field to hash |
|------|----------------------|
| `meaning`, `meaning_raw`, `meaning_ru_raw`, `meaning_raw_list` | `meaning_1` |
| `meaning_lit`, `meaning_lit_list` | `meaning_lit` |
| `notes`, `notes_raw` | `notes` |

## How We'll Know It's Done

- Running the checker after an upstream sync where `meaning_1` changed → automatically re-checks those words without manual intervention.
- `--reset` flag wipes checked IDs for a fresh annual cycle.
- All tests pass, including migration from v1 format.
- Lint clean: `uv run ruff check . && uv run ruff format .`

## What's Not Included

- No change to the AI comparison logic itself.
- No scheduling or automation — this is still a manually triggered script.
- No new reporting format — existing mismatch reports are unchanged.
