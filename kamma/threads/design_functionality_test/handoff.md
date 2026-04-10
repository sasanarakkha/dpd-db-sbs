# Handoff: Design Sync Functionality Smoke Test

**Thread:** `design_functionality_test`  
**Branch:** sbs-ru  
**Status:** Not started

---

## Why This Exists

After every upstream sync, we run automated parity and namespace tests (`pytest`). These catch structural issues — wrong symbol names, missing registry entries, etc. But they do **not** catch runtime breakage: broken JS, malformed HTML output, missing template data, silent failures in exporters.

Real-world breakage only shows up during manual use. Manual testing is slow, inconsistent, and easy to skip under time pressure.

This thread designs and implements a **smoke test** — a single script that emulates actual usage against a small fixture database. Fast enough to run after every sync. Reliable enough to catch the most common breakage patterns.

---

## Where This Fits in the Sync Workflow

The smoke test is run **twice per sync** at two phase boundaries (see `kamma/upstream_sync/guide.md`):

**Checkpoint A — after all shadow porting is done (end of Stage 3)**  
Verifies: the sync porting didn't break anything.

**Checkpoint B — after orphan cleanup/archiving (end of Stage 4)**  
Verifies: the cleanup didn't break anything independently.

**Why two runs:** sync porting and orphan archiving are independent failure sources. If tests pass at A but fail at B, the cause is the cleanup — not the sync. A single final test cannot isolate this.

Once implemented, the guide gets one new line at each checkpoint:
```
uv run python3 tests/smoke_test_sync.py
```

---

## What to Test

The smoke test should cover the most common real-world breakage patterns. These are the things that break silently and only show up during actual use:

### 1. GoldenDict RU export
- Run `main_ru.py` against the fixture DB
- Verify output files exist and are non-empty
- Spot-check HTML output contains expected `ru_` prefixed IDs (e.g. `ru_feedback_`, `ru_family_root_`, `ru_grammar_`)
- Verify family JSON files are generated and parseable

### 2. GoldenDict SBS export
- Run `main_sbs.py` against the fixture DB
- Same checks with `sbs_` prefixed IDs

### 3. JS static validation
- Check that `ru_main.js`, `ru_feedback_template.js`, and other shadow JS files have no syntax errors
- Can be done with `node --check` or a simple regex check for balanced braces — no browser needed

### 4. Webapp (RU + SBS templates)
- Render `ru_templates/home.html` and `sbs_templates/home.html` with minimal fixture data
- Verify toggle button IDs are present: `history-toggle-button`, `settings-toggle-button`
- Verify language switcher is present
- Verify `initPanelToggle` and `initCollapseToggle` are referenced in `home.js`

### 5. Family JSON (RU)
- Run `families_to_json_ru.py` against the fixture DB
- Verify at least one JSON file is produced per family type (compound, root, word, idiom, set)

### 6. Template rendering
- Render `dpd_headword_ru.jinja` and `dpd_headword_sbs.jinja` for a fixture headword
- Verify output is valid HTML (no unclosed tags, no Jinja errors)
- Verify no `${...}` Mako syntax leaks through (would indicate a template regression)

---

## Fixture Database

Do **not** use the full production DB. Build a small fixture:
- ~20 headwords covering: a root word, a compound, a word with family data, a word with examples
- Enough rows in Russian/SBS tables to exercise the RU/SBS template paths
- Stored as a fixture TSV or SQLite file in `tests/fixtures/`

The fixture should be checked in and stable — not regenerated from the live DB on every run.

---

## Deliverables

1. **`tests/smoke_test_sync.py`** — the main script. Single entry point, runs all checks, exits 0 on pass / 1 on failure. Output: clear green/red per check, total pass/fail summary.

2. **`tests/fixtures/`** — fixture DB or TSV files used by the smoke test.

3. **`kamma/upstream_sync/guide.md` updated** — add `uv run python3 tests/smoke_test_sync.py` at two points:
   - Stage 3 verification (after all porting)
   - Stage 4 cleanup verification (after orphan archiving)

---

## Constraints

- Must complete in under 2 minutes on a normal dev machine
- Must not require GoldenDict, a browser, or a running server to execute
- Must work against the fixture DB, not the live production DB
- Must follow project code standards: `from tools.printer import printer as pr`, type hints, `Path` not `os`, no `sys.path` hacks

---

## Context Files to Read First

Before implementing, read:
- `kamma/upstream_sync/guide.md` — the sync workflow this test plugs into
- `tests/test_namespace_isolation.py` — example of how existing sync tests are structured
- `tests/check_shadow_modifications.py` — the current shadow check (this test complements it, doesn't replace it)
- `exporter/goldendict/main_ru.py` — entry point for GoldenDict RU export
- `exporter/goldendict/main_sbs.py` — entry point for GoldenDict SBS export
- `scripts/build/families_to_json_ru.py` — family JSON generation
- `exporter/webapp/ru_templates/home.html` + `sbs_templates/home.html` — webapp templates to verify

---

## When Done — Required Updates

After the script is implemented and passing, you MUST update two files:

1. **`kamma/upstream_sync/guide.md`** — add `uv run python3 tests/smoke_test_sync.py` at both checkpoints in Stage 3 verification and Stage 4 cleanup verification sections.

2. **`kamma/threads/sync_april_2026/handoff.md`** — find the Stage 4 section and replace the placeholder test commands with the actual smoke test command. Stage 4 is the active sync that will USE this test. The agent running Stage 4 must see `smoke_test_sync.py` referenced explicitly so nothing is missed.

This thread exists specifically to unblock Stage 4 of the April 2026 sync. When you finish here, Stage 4 is ready to run.

---

## How to Start

New session, say:
> "Read `kamma/threads/design_functionality_test/handoff.md`. Plan and implement `tests/smoke_test_sync.py` — a sync smoke test as described. Start with a plan, present it for approval before writing any code."
