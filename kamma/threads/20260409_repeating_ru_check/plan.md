# plan.md — Repeating Check of Russian against English

**Issue:** sasanarakkha/dpd-db-sbs #40

## Approach: Snapshot-Based Drift Detection

Store a hash of the English field value alongside each checked ID in the existing JSON files. Before each analysis run, compare stored hashes against current DB values. IDs where the English changed are invalidated — removed from the snapshot — and picked up naturally by the existing checker query.

**Hash strategy**: Normalize (strip + collapse whitespace), then SHA-256 truncated to 16 hex chars. Catches all real content changes; ignores trivial formatting.

**File format change** (backward-compatible):
- v1 (current): `[12345, 12346, ...]` — plain list of ints
- v2 (new): `{"format_version": 2, "checked": {"12345": "a1b2c3d4", ...}}` — dict with hashes
- Migration: v1 files auto-migrate; empty hashes always mismatch, triggering one full re-check

---

## Phase 1: Snapshot Module

### Task 1.1 — Create `tools/meaning_snapshot.py`
- [ ] `compute_field_hash(value: str) -> str` — normalize + SHA-256[:16]
- [ ] `get_english_field_for_mode(mode: str) -> str` — returns DB column name per mode
- [ ] `load_snapshot(path: Path) -> dict[int, str]` — load v2; auto-migrate v1
- [ ] `save_snapshot(path: Path, data: dict[int, str]) -> None`
- [ ] `invalidate_changed(snapshot: dict[int, str], db_session, mode: str) -> set[int]` — query DB, compare hashes, remove changed IDs

### Task 1.2 — Tests for snapshot module
- [ ] Create `tests/test_meaning_snapshot.py`
- [ ] Test: v1 → v2 migration (empty hashes, all IDs preserved)
- [ ] Test: `compute_field_hash` is stable and whitespace-invariant
- [ ] Test: `invalidate_changed` removes correct IDs when field changes
- [ ] Test: `invalidate_changed` keeps IDs when field is unchanged

### Phase 1 Completion
- [ ] `uv run pytest tests/test_meaning_snapshot.py -v` — all pass
- [ ] `uv run ruff check tools/meaning_snapshot.py`

---

## Phase 2: Integrate into Checker

### Task 2.1 — Modify `tools/ai_meaning_checker.py`
- [ ] Import `meaning_snapshot`
- [ ] `__init__`: add `self.snapshot: dict[int, str]` via `load_snapshot()`
- [ ] `load_checked_ids()`: return `set(self.snapshot.keys())` for query compat
- [ ] `save_checked_ids()`: delegate to `save_snapshot()`
- [ ] `mark_as_checked(id, english_value)`: store hash via `compute_field_hash()`
- [ ] `run_analysis()`: call `invalidate_changed()` at start; print summary with `pr`

### Task 2.2 — Modify `tools/ai_batch_processor.py`
- [ ] `mark_as_checked_safe()`: add optional `snapshot: dict[int, str] | None` and `english_value: str` params
- [ ] When `snapshot` provided, store hash alongside the ID in the set

### Task 2.3 — Integration tests
- [ ] Test: checker loads snapshot, runs invalidation before query
- [ ] Test: after checking a word, its hash is stored correctly

### Phase 2 Completion
- [ ] `uv run pytest tests/test_meaning_snapshot.py -v` — full suite passes
- [ ] `uv run ruff check tools/ai_meaning_checker.py tools/ai_batch_processor.py`

---

## Phase 3: CLI Enhancements

### Task 3.1 — Modify `scripts/other/ai_check_russian_meanings.py`
- [ ] Add `--no-auto-invalidate` flag (invalidation runs by default)
- [ ] Add `--reset` flag: wipes `checked_ids` file for the given mode, exits cleanly
- [ ] Print invalidation summary: "Invalidated N IDs where English meaning changed"

### Task 3.2 — End-to-end test
- [ ] Run with `--limit 3` on real DB: verify invalidation summary appears
- [ ] Run `--reset --mode meaning`: verify snapshot file is wiped

### Phase 3 Completion
- [ ] `uv run python3 scripts/other/ai_check_russian_meanings.py --mode meaning --limit 3` — runs without error
- [ ] `uv run ruff check scripts/other/ai_check_russian_meanings.py`
- [ ] Full suite still passes

---

## Commit (user prepares)

```
feat(ru-check): add snapshot-based drift detection for repeating checks #40

- tools/meaning_snapshot.py: hash-based change detection for checked IDs
- tools/ai_meaning_checker.py: integrate snapshot, auto-invalidate on run
- tools/ai_batch_processor.py: pass english_value through mark_as_checked_safe
- scripts/other/ai_check_russian_meanings.py: --reset and --no-auto-invalidate flags
- tests/test_meaning_snapshot.py: migration, hash stability, invalidation tests
```
