# plan.md — Repeating Check of Russian against English

**Issue:** sasanarakkha/dpd-db-sbs #40
**Spec:** see `spec.md` in this folder. Read it first.

## Approach: Snapshot-Based Drift Detection

Store a hash of the composed English content alongside each checked ID. Before each run, compare stored hashes against current DB values; changed IDs are removed from the snapshot and re-checked naturally by the existing query (which already excludes checked IDs).

The snapshot layer is orthogonal to batch vs individual processing: both `compare_meanings_batch` and `compare_meanings_individual` (`tools/ai_batch_processor.py`) mutate the same `checked_ids` set via `mark_as_checked_safe` and call `AIManager` the same way, so the reconcile-at-save design covers both paths with no path-specific code. The user's primary workflow is `--individual`, so verification must cover it explicitly.

**Files touched (complete list — do not touch anything else):**

| File | Action |
|------|--------|
| `tools/meaning_snapshot_ru.py` | NEW — snapshot load/save, hashing, invalidation |
| `tools/ai_meaning_checker.py` | MODIFY — integrate snapshot |
| `scripts/other/ai_check_russian_meanings.py` | MODIFY — `--reset`, `--no-auto-invalidate`, default flipped to individual |
| `scripts/other/ai_generate_translation.py` | MODIFY — drop regenerated IDs from checker snapshots |
| `tests/tools/test_meaning_snapshot_ru.py` | NEW — unit tests |
| `kamma/upstream_sync/registry.json` | MODIFY — add new file to `unique_paths` |
| `docs_rus/dpd_rus.md`, `docs_rus/features/features.md` | MODIFY only if they describe the one-time check workflow |

**Hard "do not" rules for the implementer:**
- Do NOT modify `tools/ai_batch_processor.py`.
- Do NOT add chunking/batching to the `id.in_(...)` query — the existing code already passes ~18K IDs in one `in_()` and works; keep parity.
- Do NOT migrate existing `print()` calls to `pr` except on lines you are already changing.
- Do NOT invalidate IDs whose stored hash is `""` — seed them instead (see Task 1.1). A full re-check on migration is a cost bug, not a feature.
- Do NOT use `python -c` inline scripts; use `temp/<name>.py` if a one-shot script is needed, delete after.

---

## Phase 1: Snapshot Module

### Task 1.1 — Create `tools/meaning_snapshot_ru.py`

New file. Start with a one-sentence module docstring:
`"""Snapshot storage and drift detection for the AI Russian meaning checker (issue #40): hashes of checked English content, with invalidation when the DB value changes."""`

Imports: `hashlib`, `json`, `from pathlib import Path`, `from sqlalchemy.orm import Session`, `from db.models import DpdHeadword`. No other imports needed.

Implement exactly these functions:

```python
def normalize_text(value: str | None) -> str:
    """Strip and collapse all whitespace runs to single spaces."""
    if not value:
        return ""
    return " ".join(value.split())


def compute_field_hash(value: str | None) -> str:
    """16-hex-char SHA-256 of the normalized text. Never returns ''."""
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()[:16]
```

Note: `compute_field_hash("")` returns the hash of the empty string (a real 16-char value), so the `""` sentinel in snapshots can never collide with a computed hash.

```python
def compose_english_content(headword: DpdHeadword, mode: str) -> str:
    """Single source of truth for the English content sent to the AI per mode."""
    if mode in ("notes", "notes_raw"):
        return headword.notes or ""
    if mode in ("meaning_lit", "meaning_lit_list"):
        return headword.meaning_lit or ""
    # meaning, meaning_raw, meaning_ru_raw, meaning_raw_list
    if headword.meaning_lit:
        return f"{headword.meaning_1}; lit. {headword.meaning_lit}"
    return headword.meaning_1 or ""
```

This must produce byte-identical strings to the existing inline block in `tools/ai_meaning_checker.py` (`get_words_for_comparison_with_session`, the `english_content` if/elif/else around lines 317–329). Task 2.1 replaces that block with a call to this helper.

```python
def load_snapshot(path: Path) -> dict[int, str]:
    """Load v2 snapshot; auto-migrate v1 (plain list) to empty-hash entries."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if isinstance(data, list):  # v1: [12345, ...] -> sentinel "" = seed later
        return {int(i): "" for i in data}
    if isinstance(data, dict) and "checked" in data:
        return {int(k): str(v) for k, v in data["checked"].items()}
    return {}


def save_snapshot(path: Path, snapshot: dict[int, str]) -> None:
    """Write v2 format. Keys serialized as strings (JSON requirement)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format_version": 2,
        "checked": {str(k): v for k, v in sorted(snapshot.items())},
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
```

Split the invalidation into a **pure** reconcile function (easy to test, no DB) and a thin DB wrapper:

```python
def reconcile_snapshot(
    snapshot: dict[int, str], current_hashes: dict[int, str]
) -> tuple[int, int]:
    """Mutate snapshot in place against current DB hashes.

    Returns (n_invalidated, n_seeded).
    - stored == "" (sentinel): seed with current hash, count as seeded.
    - stored != current: delete from snapshot (will be re-checked), count as invalidated.
    - stored == current: keep.
    - id missing from current_hashes (deleted headword): delete, count as invalidated.
    """
    n_invalidated = 0
    n_seeded = 0
    for headword_id in list(snapshot.keys()):
        current = current_hashes.get(headword_id)
        if current is None:
            del snapshot[headword_id]
            n_invalidated += 1
        elif snapshot[headword_id] == "":
            snapshot[headword_id] = current
            n_seeded += 1
        elif snapshot[headword_id] != current:
            del snapshot[headword_id]
            n_invalidated += 1
    return n_invalidated, n_seeded


def invalidate_changed(
    snapshot: dict[int, str], db_session: Session, mode: str
) -> tuple[int, int]:
    """Query current English content for all snapshot IDs and reconcile."""
    if not snapshot:
        return 0, 0
    headwords = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.id.in_(list(snapshot.keys())))
        .all()
    )
    current_hashes = {
        hw.id: compute_field_hash(compose_english_content(hw, mode))
        for hw in headwords
    }
    return reconcile_snapshot(snapshot, current_hashes)


def remove_ids_from_snapshot(path: Path, ids: set[int]) -> int:
    """Remove IDs from a snapshot file so they re-enter the check queue.

    Used by the translation generator after regenerating Russian content.
    Returns the number of IDs actually removed. No-op if the file is
    missing or none of the IDs are present.
    """
    snapshot = load_snapshot(path)
    if not snapshot:
        return 0
    removed = 0
    for headword_id in ids:
        if headword_id in snapshot:
            del snapshot[headword_id]
            removed += 1
    if removed:
        save_snapshot(path, snapshot)
    return removed
```

- [ ] File created with the functions above, docstring first, modern type hints throughout.

### Task 1.2 — Unit tests: `tests/tools/test_meaning_snapshot_ru.py`

New file, one-sentence docstring. Use `tmp_path` pytest fixture for files and `types.SimpleNamespace` (with attrs `notes`, `meaning_lit`, `meaning_1`, `id`) as fake headwords for `compose_english_content` — no DB session needed anywhere (`reconcile_snapshot` is pure; do not write DB tests for `invalidate_changed`).

Test cases (one test function each, names given):
- [ ] `test_normalize_collapses_whitespace` — `normalize_text(" a \n b\t c ") == "a b c"`; `normalize_text(None) == ""`; `normalize_text("") == ""`.
- [ ] `test_hash_stable_and_whitespace_invariant` — `compute_field_hash("a  b\n") == compute_field_hash("a b")`; result is 16 chars; `compute_field_hash("") != ""` (sentinel never collides); two different inputs give different hashes.
- [ ] `test_compose_meaning_mode_with_and_without_lit` — meaning mode: with `meaning_lit="x"` returns `"m1; lit. x"`; with `meaning_lit=""`/`None` returns `meaning_1`.
- [ ] `test_compose_lit_and_notes_modes` — `meaning_lit` mode returns `meaning_lit`; `notes` mode returns `notes`.
- [ ] `test_load_missing_and_corrupt_file` — nonexistent path → `{}`; file with invalid JSON → `{}`.
- [ ] `test_v1_migration` — write `[1, 2, 3]` to a file; `load_snapshot` returns `{1: "", 2: "", 3: ""}` (int keys, empty-string sentinels).
- [ ] `test_v2_roundtrip_int_keys` — `save_snapshot(path, {12345: "abcd"})` then `load_snapshot(path) == {12345: "abcd"}`; raw file JSON has `"format_version": 2` and string key `"12345"`.
- [ ] `test_reconcile_seeds_empty_hashes` — snapshot `{1: ""}`, current `{1: "h1"}` → returns `(0, 1)`, snapshot becomes `{1: "h1"}`.
- [ ] `test_reconcile_invalidates_changed` — snapshot `{1: "old"}`, current `{1: "new"}` → `(1, 0)`, snapshot `{}`.
- [ ] `test_reconcile_keeps_unchanged` — snapshot `{1: "h1"}`, current `{1: "h1"}` → `(0, 0)`, snapshot unchanged.
- [ ] `test_reconcile_drops_deleted_headwords` — snapshot `{1: "h1"}`, current `{}` → `(1, 0)`, snapshot `{}`.
- [ ] `test_remove_ids_from_snapshot` — save `{1: "a", 2: "b"}` to a file; `remove_ids_from_snapshot(path, {2, 99})` returns `1`; reload gives `{1: "a"}`. Missing file → returns `0` without creating the file.

### Phase 1 Completion (all must pass before Phase 2)
- [ ] `uv run pytest tests/tools/test_meaning_snapshot_ru.py -v`
- [ ] `uv run ruff check --fix tools/meaning_snapshot_ru.py tests/tools/test_meaning_snapshot_ru.py && uv run ruff format tools/meaning_snapshot_ru.py tests/tools/test_meaning_snapshot_ru.py`
- [ ] `uv run pyright tools/meaning_snapshot_ru.py tests/tools/test_meaning_snapshot_ru.py`
- [ ] `uv run --with pyrefly pyrefly check --min-severity warn tools/meaning_snapshot_ru.py tests/tools/test_meaning_snapshot_ru.py`

---

## Phase 2: Integrate into Checker

### Task 2.1 — Modify `tools/ai_meaning_checker.py`

Reminder: do NOT touch `tools/ai_batch_processor.py`. All snapshot bookkeeping lives in the checker.

- [ ] Add imports at top (with the other `tools.` imports):
  ```python
  from tools.meaning_snapshot_ru import (
      compose_english_content,
      compute_field_hash,
      invalidate_changed,
      load_snapshot,
      save_snapshot,
  )
  from tools.printer import printer as pr
  ```
- [ ] In `__init__`, after the mode→file mapping and before `self.checked_ids = ...`, add:
  ```python
  self.snapshot: dict[int, str] = {}
  self.english_by_id: dict[int, str] = {}
  ```
  (`self.checked_ids_file` values from `DPSPaths` are already `Path` objects — no conversion needed.)
- [ ] Replace the body of `load_checked_ids` (keep the method name and `-> set[int]` signature so the `__init__` call site is unchanged):
  ```python
  def load_checked_ids(self) -> set[int]:
      """Load the snapshot (v2, auto-migrating v1) and return its IDs."""
      self.snapshot = load_snapshot(self.checked_ids_file)
      return set(self.snapshot.keys())
  ```
  Delete the old `import json` / `os.path.exists` body entirely.
- [ ] Replace the body of `save_checked_ids` (keep name, called from `generate_report`):
  ```python
  def save_checked_ids(self):
      """Reconcile newly checked IDs into the snapshot and persist it."""
      try:
          for headword_id in self.checked_ids:
              if headword_id not in self.snapshot:
                  english = self.english_by_id.get(headword_id)
                  # "" = baseline-unknown sentinel; seeded from DB next run
                  self.snapshot[headword_id] = (
                      compute_field_hash(english) if english else ""
                  )
          save_snapshot(self.checked_ids_file, self.snapshot)
      except Exception as e:
          pr.warning(f"Could not save checked IDs: {e}")
  ```
  Note: `self.checked_ids` is the same set object the batch processor mutates via `mark_as_checked_safe`, so by `generate_report` time it contains the newly checked IDs — this reconcile is where they get their hashes.
- [ ] Add a new public method after `save_checked_ids`:
  ```python
  def apply_invalidation(self, db_session) -> tuple[int, int]:
      """Drop snapshot entries whose English content changed in the DB.

      Returns (n_invalidated, n_seeded). Persists immediately so an
      interrupted run loses nothing (invalidated IDs simply re-check later).
      """
      n_invalidated, n_seeded = invalidate_changed(
          self.snapshot, db_session, self.mode
      )
      self.checked_ids = set(self.snapshot.keys())
      save_snapshot(self.checked_ids_file, self.snapshot)
      return n_invalidated, n_seeded
  ```
- [ ] In `get_words_for_comparison_with_session`, replace ONLY the `english_content` composition block (the `if self.mode in ["notes", "notes_raw"]: ... else: ... meaning_1` if/elif/else, currently around lines 317–329) with:
  ```python
  english_content = compose_english_content(headword, self.mode)
  ```
  Leave the `russian_meaning` block and everything else in that loop untouched.
- [ ] In `run_analysis`, change the signature to:
  ```python
  def run_analysis(
      self,
      db_session=None,
      use_batch: bool = True,
      limit: Optional[int] = None,
      auto_invalidate: bool = True,
  ):
  ```
  Inside, immediately after `session = db_session or globals()["db_session"]` and before `comparisons = ...`, add:
  ```python
  if auto_invalidate:
      n_invalidated, n_seeded = self.apply_invalidation(session)
      pr.white(
          f"Invalidated {n_invalidated} IDs (English changed), "
          f"seeded {n_seeded} baseline hashes"
      )
  ```
  And right after `comparisons = self.get_words_for_comparison_with_session(session)` (before the `limit` slice), add:
  ```python
  self.english_by_id = {c.headword_id: c.english_meaning for c in comparisons}
  ```
  (Built before the limit slice on purpose — it is only a lookup map; entries for unprocessed IDs are never used.)

### Task 2.2 — Checker-level tests (append to `tests/tools/test_meaning_snapshot_ru.py`)

These test the reconcile-at-save logic without AI or DB: construct `RussianMeaningChecker.__new__(RussianMeaningChecker)` (bypass `__init__` to avoid `BatchProcessor`/DB), then set `checked_ids_file` (a `tmp_path` file), `snapshot`, `english_by_id`, `checked_ids` attributes by hand and call `save_checked_ids()`.

- [ ] `test_save_checked_ids_hashes_new_ids` — `snapshot={}`, `checked_ids={1}`, `english_by_id={1: "dog"}` → after save, `load_snapshot(file)[1] == compute_field_hash("dog")`.
- [ ] `test_save_checked_ids_unknown_english_gets_sentinel` — `snapshot={}`, `checked_ids={2}`, `english_by_id={}` → after save, `load_snapshot(file)[2] == ""`.
- [ ] `test_save_checked_ids_keeps_existing_hashes` — `snapshot={3: "keep"}`, `checked_ids={3}` → after save, value still `"keep"`.

### Phase 2 Completion
- [ ] `uv run pytest tests/tools/test_meaning_snapshot_ru.py -v`
- [ ] `uv run ruff check --fix tools/ai_meaning_checker.py && uv run ruff format tools/ai_meaning_checker.py`
- [ ] `uv run pyright tools/ai_meaning_checker.py` and `uv run --with pyrefly pyrefly check --min-severity warn tools/ai_meaning_checker.py` — pre-existing errors in untouched lines may be reported; new code must be clean. Note any pre-existing findings in the thread log instead of fixing them (scope).

---

## Phase 3: CLI Flags & Regeneration Hook

### Task 3.1 — Modify `scripts/other/ai_check_russian_meanings.py`

- [ ] Flip the default processing mode to **individual** (user's primary workflow; batch kept as opt-in). Replace the current block
  ```python
  # Determine processing mode
  use_batch = True
  if args.individual:
      use_batch = False
  elif args.batch:
      use_batch = True
  ```
  with:
  ```python
  # Determine processing mode (default: individual; batch is opt-in)
  use_batch = args.batch and not args.individual
  ```
  Update the two help strings: `--batch` → `"Use batch processing (default: individual)"`; `--individual` → `"Use individual processing (the default; flag kept for compatibility)"`. Keep both flags — do not remove `--individual`. Do NOT change the `use_batch: bool = True` default in `RussianMeaningChecker.run_analysis` (the CLI always passes it explicitly; changing the library default is out of scope).
- [ ] Add two arguments after the existing `--output`:
  ```python
  parser.add_argument(
      "--reset",
      action="store_true",
      help="Delete the checked-IDs snapshot for the given mode and exit",
  )
  parser.add_argument(
      "--no-auto-invalidate",
      action="store_true",
      help="Skip invalidation of checked IDs whose English content changed",
  )
  ```
- [ ] After `checker = RussianMeaningChecker(mode=args.mode)` insert, in this order:
  ```python
  if args.reset:
      checker.checked_ids_file.unlink(missing_ok=True)
      pr.yes(f"checked-IDs snapshot reset for mode '{args.mode}'")
      pr.toc()
      return

  if not args.no_auto_invalidate:
      n_invalidated, n_seeded = checker.apply_invalidation(db_session)
      pr.white(
          f"Invalidated {n_invalidated} IDs (English changed), "
          f"seeded {n_seeded} baseline hashes"
      )
  ```
  This runs BEFORE `total_count = checker.get_total_count_with_session(db_session)` so the displayed count includes invalidated words.
- [ ] In the `checker.run_analysis(...)` call, pass `auto_invalidate=False` (the CLI already applied or skipped invalidation above; this prevents a redundant second pass).
- [ ] Update the module docstring's mention of behavior if it claims one-time checking (currently it doesn't — verify, don't rewrite).

### Task 3.2 — End-to-end verification (real DB, manual)

- [ ] `uv run python scripts/other/ai_check_russian_meanings.py --mode meaning --limit 3` — runs without error; the "Invalidated N IDs ... seeded M" line appears; on first run after migration expect N=0 and M=size of the old v1 file; the snapshot JSON file is now v2 format with non-empty hashes for the seeded IDs.
- [ ] `uv run python scripts/other/ai_check_russian_meanings.py --mode meaning --individual --limit 2` — the individual path (user's primary workflow) also stores hashes: after the run, the 2 newly checked IDs appear in the snapshot with non-empty hash values.
- [ ] Drift simulation without AI cost: open the mode's snapshot file, change one stored hash to `"0000000000000000"`, re-run with `--limit 0`-equivalent dry approach — instead, run `--no-auto-invalidate` first to confirm the count excludes it, then run normally and confirm "Invalidated 1 IDs". (Do not let the run proceed past the count check if avoiding AI calls: Ctrl-C after the summary lines print is acceptable; invalidation is already persisted.)
- [ ] `uv run python scripts/other/ai_check_russian_meanings.py --mode meaning --reset` — file is gone (`ls` the path from `tools/paths_dps.py: ai_meaning_checked`); restore from git if the wiped file was real data: `git checkout -- <path>` (check `git status` for the snapshot path first; if untracked, copy it aside before testing reset).

### Task 3.3 — Regeneration hook in `scripts/other/ai_generate_translation.py`

When a Russian translation is regenerated, the word's old checker verdict is stale; drop the ID from the matching snapshot files so the checker re-checks it. Only the direct path (`translation_generate`) gets this — do NOT touch `make_json` or the batch-API ingestion.

- [ ] Add imports: `from pathlib import Path` (not currently imported) and `from tools.meaning_snapshot_ru import remove_ids_from_snapshot`.
- [ ] Add a module-level constant after `LANG_CONFIG` (the `dpspth = DPSPaths()` instance already exists at module level):
  ```python
  # generation mode -> checker snapshot files holding verdicts for the regenerated field
  SNAPSHOTS_BY_MODE: dict[str, list[Path]] = {
      "meaning": [dpspth.ai_meaning_raw_checked, dpspth.ai_meaning_ru_raw_checked],
      "lit": [dpspth.ai_meaning_lit_checked],
      "note": [dpspth.ai_notes_raw_checked],
  }
  ```
  Rationale for the mapping: generation `meaning` writes `ru_meaning_raw`, which checker modes `meaning_raw`/`meaning_raw_list` (file `ai_meaning_raw_checked`) and `meaning_ru_raw` (file `ai_meaning_ru_raw_checked`) validate; `lit` writes `ru_meaning_lit` (checker `meaning_lit`/`meaning_lit_list`); `note` writes `ru_notes` with the `[пер. ИИ]` prefix, which only checker mode `notes_raw` looks at (`notes` mode excludes AI translations) — so NOT `ai_notes_checked`.
- [ ] In `translation_generate()`: initialize `regenerated_ids: set[int] = set()` before the loop; add `regenerated_ids.add(word.id)` as the first line inside the `if meaning_result:` block (over-collecting in the rare lit-mode no-row case is harmless — removal of an absent ID is a no-op). After the loop add:
  ```python
  if lang == "ru" and regenerated_ids:
      for snapshot_path in SNAPSHOTS_BY_MODE.get(mode, []):
          removed = remove_ids_from_snapshot(snapshot_path, regenerated_ids)
          if removed:
              pr.white(
                  f"{removed} regenerated IDs dropped from "
                  f"{snapshot_path.name} (will be re-checked)"
              )
  ```
- [ ] Verification without AI cost: the behavior is covered by `test_remove_ids_from_snapshot`. Optional manual check during a routine generation run: if a regenerated ID was present in a snapshot, the "dropped from" line prints and the ID is gone from the file.

### Phase 3 Completion
- [ ] `uv run ruff check --fix scripts/other/ai_check_russian_meanings.py scripts/other/ai_generate_translation.py && uv run ruff format scripts/other/ai_check_russian_meanings.py scripts/other/ai_generate_translation.py`
- [ ] `uv run pyright scripts/other/ai_check_russian_meanings.py scripts/other/ai_generate_translation.py`
- [ ] `uv run --with pyrefly pyrefly check --min-severity warn scripts/other/ai_check_russian_meanings.py scripts/other/ai_generate_translation.py`
  (`ai_generate_translation.py` has pre-existing legacy hints (`List`, `Dict`, `os.path`) — do not modernize untouched lines; new code must be clean, note pre-existing findings in the thread log.)
- [ ] `uv run pytest tests/tools/test_meaning_snapshot_ru.py -v` (full file, final)

---

## Phase 4: Registry & Docs

### Task 4.1 — Registry
- [ ] In `kamma/upstream_sync/registry.json`, add `"tools/meaning_snapshot_ru.py"` to the `unique_paths` array, next to the existing `tools/ai_*.py` entries (around `tools/ai_related.py`). No SMD entry is required for `unique_paths` (the existing `tools/ai_meaning_checker.py` and `tools/ai_batch_processor.py` are in this category with no SMD entries).
- [ ] `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` — passes.
- [ ] `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` — passes.

### Task 4.2 — Docs
- [ ] Grep `docs_rus/dpd_rus.md` and `docs_rus/features/features.md` for the meaning-checker description. If either describes the check as one-time / requiring manual reset, add one sentence (in Russian, matching surrounding style) stating that changed English meanings are re-checked automatically. If neither describes the workflow at that level of detail, make no doc change and note that in the thread log.
- [ ] No `kamma/tech.md` change needed (no new dependencies or stack changes — stdlib `hashlib`/`json` only). Verify this stays true; if a dependency gets added, document it there first.

---

## Commit (user prepares — do not commit autonomously)

```
feat(ru-check): add snapshot-based drift detection for repeating checks #40

- tools/meaning_snapshot_ru.py: hash snapshot of checked English content;
  v1 list auto-migrates with DB-seeded baselines (zero extra AI calls)
- tools/ai_meaning_checker.py: auto-invalidate changed English before runs;
  compose_english_content extracted as single source of truth
- scripts/other/ai_check_russian_meanings.py: --reset, --no-auto-invalidate;
  individual processing is now the default (batch via --batch)
- scripts/other/ai_generate_translation.py: regenerated IDs re-enter the
  check queue (dropped from checker snapshots)
- tests/tools/test_meaning_snapshot_ru.py: hashing, migration, reconcile,
  save-time hash bookkeeping
- kamma/upstream_sync/registry.json: register new unique tool
```

Stage `registry.json` in the same commit as the new file (Shadow Documentation Gate).
