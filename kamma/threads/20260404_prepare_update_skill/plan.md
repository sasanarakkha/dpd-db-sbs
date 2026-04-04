# Plan: Prepare Upstream Sync Infrastructure

> **Executing model**: Follow sequentially. Mark tasks `[~]` before starting, `[x]` on
> completion. Do NOT skip steps or invent shortcuts.

---

## Non-Goals (explicit)

- Execute destructive sync flows
- Run cleanup in `--apply` mode
- Author the `/update-upstream` skill (that's `implement_update_upstream` thread)
- Normalize historical references in archives/session logs

---

## Key Design Decisions

### Safety Gates
- **Gate A**: Read-only analysis is allowed on the current dirty worktree.
- **Gate B**: File-moving, staging, and commit work is blocked until user approves dirty execution OR work is in an isolated worktree.
- `tests/test_shadow_cleanup.py` is excluded from verification until refactored to default to `--dry-run`.

### Shared Registry Helper
Add `kamma/upstream_sync/registry_helper.py` BEFORE updating consumers. Centralizes:
- `get_registry_path() -> Path`
- `load_registry() -> dict[str, object]`
- `get_modified_upstream_paths(data) -> list[str]` (handles both string and object entries)

### Compatibility Constraint
During migration, consumers must continue to work if `modified_upstream_files` entries are either strings or objects. The shared helper handles this transparently.

### SMD Scope
SMD coverage is **per registry entry**, not per child file. Directory mappings get one SMD section describing preservation rules for the directory class.

### SMD Quality Rubric
An SMD entry is complete only if it has:
- `File`, `Category`, `Sync Rule`
- At least 2 concrete `Local Changes` bullets (unless `MIRROR_EXACTLY`)
- At least 1 `Watch For` bullet
- For `DISCUSS` entries: explanation of why blind porting is dangerous

### Active vs Historical References
- **Must migrate now**: runtime scripts, tests/checkers, policy docs
- **May remain as history**: `conductor/templates/`, `conductor/archive/`, `kamma/archive/`, thread artifacts, session logs

---

## Phase A: Read-Only Baseline

- [ ] **A.1** Record worktree state. Acknowledge dirty tree. Set Gate A (read-only OK), Gate B (mutations blocked until approved).
- [ ] **A.2** Read `conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json`. Confirm counts: modified=12, russian=47, sbs=18, unique=37 (4 dupes), no_sync=6, folders=7, ignored=11.
- [ ] **A.3** Identify the 4 `unique_paths` duplicates (do NOT remove yet):
  - `scripts/rus_exporter/`
  - `db/families/family_set_ru_update.py`
  - `db_tests/sbs_consistency_tests.py`
  - `docs_rus/dpd_rus.md`
- [ ] **A.4** Document all consumer scripts with exact line numbers (5 scripts):
  - `scripts/bash/full_sync.sh`
  - `scripts/cl_dps/dpd-sync-folders`
  - `tests/test_shadow_parity.py`
  - `tests/check_shadow_modifications.py`
  - `tests/test_shadow_cleanup.py`
- [ ] **A.5** Document policy/doc references (CLAUDE.md, AGENTS.md, conductor/tech-stack.md).
- [ ] **A.6** Define allowed-legacy grep locations (conductor/templates/**, conductor/archive/**, kamma/archive/**, session logs).

**Phase A complete when:** Zero files modified. Entry counts confirmed. All consumers inventoried.

---

## Phase B: Infrastructure Migration

> Requires Gate B approval before execution.

### B.1 Create canonical directory and shared helper

- [ ] **B.1.1** Create `kamma/upstream_sync/`.
- [ ] **B.1.2** Write `kamma/upstream_sync/registry_helper.py`:
  - `get_registry_path() -> Path`
  - `load_registry() -> dict[str, object]`
  - `get_modified_upstream_paths(data) -> list[str]` (handles string + object entries)
  - Modern type hints, `pathlib.Path`, one-sentence description at top.
- [ ] **B.1.3** `uv run ruff check --fix kamma/upstream_sync/registry_helper.py && uv run ruff format kamma/upstream_sync/registry_helper.py`

### B.2 Migrate registry to v2

- [ ] **B.2.1** Copy + transform `dps_sync_registry.json` -> `kamma/upstream_sync/registry.json`:
  - Remove 4 `unique_paths` duplicates (37 -> 33).
  - Convert `modified_upstream_files` strings to objects: `{ "path": "...", "discuss": false, "discuss_reason": "" }`.
  - Set `discuss: true` + reason for: `db/models.py`, `gui2/main.py`, `.gitignore`, `AGENTS.md`.
  - Add optional `sync_rule` field to `russian_copies`/`sbs_copies` where appropriate.
- [ ] **B.2.2** Copy `improvements.md` -> `kamma/upstream_sync/improvements.md`.
- [ ] **B.2.3** Write `kamma/upstream_sync/guide.md` (process reference only — no AI instructions; registry category definitions, shadow copy merge strategies, common error patterns, manual sync checklist).
- [ ] **B.2.4** Write `kamma/upstream_sync/README.md` (folder-level explainer: what belongs, what doesn't, canonical file list, relationship to thread-local artifacts).

### B.3 Update consumers (use shared helper where possible)

> NOTE: Use `python3` in all shell commands. `check_shadow_modifications.py` is a
> standalone script, NOT a pytest test.

- [ ] **B.3.1** `scripts/bash/full_sync.sh` — use `python3`, read from new registry path, extract paths from objects via `registry_helper`.
- [ ] **B.3.2** `scripts/cl_dps/dpd-sync-folders` — identical change.
- [ ] **B.3.3** `tests/test_shadow_parity.py` — import from `registry_helper` or update `get_registry_path()` to return `Path("kamma/upstream_sync/registry.json")`.
- [ ] **B.3.4** `tests/check_shadow_modifications.py` — update hardcoded path to new location (standalone script, NOT pytest).
- [ ] **B.3.5** `tests/test_shadow_cleanup.py` — update BOTH path occurrences (including any internal skip strings).

### B.4 Update policy/doc references

- [ ] **B.4.1** `CLAUDE.md` — update "Shadow Files & Sync Templates" and "Clean Root Folder Protocol" sections: `conductor/templates/upstream_sync_rehearsal/` → `kamma/upstream_sync/`, `dps_sync_registry.json` → `registry.json`.
- [ ] **B.4.2** `AGENTS.md` — mirror CLAUDE.md changes (these sections are mirrored).
- [ ] **B.4.3** `conductor/tech-stack.md` — update registry reference line.
- [ ] **B.4.4** `scripts/bash/README.md` — update if `full_sync.sh` behavior or usage changes.
- [ ] **B.4.5** `scripts/cl_dps/README.md` — update if `dpd-sync-folders` changes.

### B.5 Legacy marker

- [ ] **B.5.1** Create `conductor/templates/upstream_sync_rehearsal/LEGACY_NOTICE.md`:
  ```
  # Legacy Notice
  These files are archived references. The canonical sync tooling has moved to
  `kamma/upstream_sync/`. Do NOT modify files in this directory.
  ```
- [ ] **B.5.2** Verify `conductor/templates/` is in `no_sync_files` in new registry. Add if missing.

### B.6 Verify migration

- [ ] **B.6.1** `uv run pytest tests/test_shadow_parity.py --tb=short -q`
- [ ] **B.6.2** `uv run python3 tests/check_shadow_modifications.py`
- [ ] **B.6.3** Grep for stale active references to `upstream_sync_rehearsal/dps_sync_registry` — must appear ONLY in allowed-legacy locations.

**Phase B complete when:** All 5 consumers + 3 policy docs updated. Tests pass. No active code references old path.

---

## Phase C: Validation Tooling

- [ ] **C.1** Write `kamma/upstream_sync/validate_registry.py`:
  - Purpose: "Validate registry.json schema integrity and data quality."
  - Checks:
    - Every `modified_upstream_files` entry is an object with `path`, `discuss` (bool), `discuss_reason` (non-empty when `discuss=true`).
    - No duplicates in `unique_paths`.
    - No duplicates within `russian_copies` keys or `sbs_copies` keys.
    - Every shadow path in `russian_copies`/`sbs_copies` values exists in repo.
    - Directory entries (paths ending with `/`) handled correctly.
    - Wildcard entries (`gui2/dps_*`, `scripts/bash/*.sh`) handled correctly.
    - Cross-section overlap: fail on same-category dupes, warn on cross-category overlaps.
  - Uses `tools/printer.py`, `pathlib.Path`, modern type hints, one-sentence description.
- [ ] **C.2** `uv run ruff check --fix kamma/upstream_sync/validate_registry.py && uv run ruff format kamma/upstream_sync/validate_registry.py`
- [ ] **C.3** `uv run python3 kamma/upstream_sync/validate_registry.py` — fix any issues.

- [ ] **C.4** Write `kamma/upstream_sync/verify_smd_coverage.py`:
  - Purpose: "Verify every registry entry has a corresponding SMD section meeting the quality rubric."
  - Reads registry, extracts all paths from all categories. Reads `smd.md`, extracts `**File**:` entries.
  - Enforces quality rubric: min 2 Local Changes (unless MIRROR_EXACTLY), min 1 Watch For.
  - Reports gaps. Uses `tools/printer.py`, `pathlib.Path`.
- [ ] **C.5** `uv run ruff check --fix kamma/upstream_sync/verify_smd_coverage.py && uv run ruff format kamma/upstream_sync/verify_smd_coverage.py`

**Phase C complete when:** Both validators pass against current state.

---

## Phase D: Shadow Module Descriptions (smd.md)

### D.1 Auto-scaffold

- [ ] **D.1.1** Write `kamma/upstream_sync/gen_smd_scaffold.py`:
  - Purpose: "Generate a stub SMD entry for every path in registry.json."
  - Reads `registry.json`, iterates all categories, outputs Markdown stubs to stdout.
  - Each stub: path, category, sync_rule placeholder, empty local-changes list.
  - One-sentence description at top; uses `tools/printer.py`; uses `pathlib.Path`.
  - Ruff check + format.
- [ ] **D.1.2** Run scaffold generator:
  ```
  uv run python3 kamma/upstream_sync/gen_smd_scaffold.py > kamma/upstream_sync/smd.md
  ```
  Add the SMD format header:
  ```markdown
  # Shadow Module Descriptions (SMD)
  > Read this file before touching ANY file during sync.
  > If a file has no SMD entry, STOP and flag it.

  ## Format per entry
  - **File**: path
  - **Category**: modified_upstream | russian_copy | sbs_copy
  - **Sync Rule**: PORT / MIRROR_EXACTLY / PRESERVE / DISCUSS
  - **Local Changes**: numbered list of concrete changes
  - **Watch For**: specific pitfalls during sync
  ```

### D.2 Enrich high-risk entries first (read each file before writing)

- [ ] **D.2.1** `db/models.py` — DISCUSS. SBS table (~30 cols), Russian table (~5 cols), Sinhala table, `.sbs`/`.ru`/`.si` relationships on DpdHeadword, `root_ru_meaning`/`sanskrit_root_ru_meaning` on DpdRoot, hybrid properties.
- [ ] **D.2.2** `gui2/main.py` — DISCUSS. `fast_api_utils_dps` import, DpsView tab, AnalysisView tab.
- [ ] **D.2.3** `tools/paths.py` → `tools/paths_ru.py` AND `tools/paths_dps.py` (triple shadow). Document RuPaths and DPSPaths classes. **Watch For**: New upstream constants MUST be ported to BOTH shadow files.
- [ ] **D.2.4** `exporter/goldendict/templates/` → `ru_components/templates/` AND `sbs_templates/` (triple shadow). Document localized HTML templates with `ru_`/`sbs_` prefixed IDs. **Watch For**: New upstream templates need BOTH shadow dirs.
- [ ] **D.2.5** `exporter/webapp/templates/` → `ru_templates/` AND `sbs_templates/`. Critical: `dpd_headword.html` is complex and prone to merge errors.
- [ ] **D.2.6** `.gitignore` — DISCUSS. Document DPS-specific exclusions.
- [ ] **D.2.7** `AGENTS.md` — DISCUSS. Fork identity and sync policy references.
- [ ] **D.2.8** `CLAUDE.md` — DISCUSS. Fork-local rules.

### D.3 Complete remaining Modified Upstream Files

- [ ] **D.3.1** `exporter/webapp/data_classes.py` — PORT.
- [ ] **D.3.2** `exporter/webapp/static/app.js` — PORT.
- [ ] **D.3.3** `exporter/webapp/static/home.js` — PORT.
- [ ] **D.3.4** `gui2/pass2_add_view.py` — PORT.
- [ ] **D.3.5** `tools/ai_manager.py` — PORT.
- [ ] **D.3.6** `conductor/product-guidelines.md` — PRESERVE.
- [ ] **D.3.7** `conductor/product.md` — PRESERVE.
- [ ] **D.3.8** `conductor/tech-stack.md` — PRESERVE.
- [ ] **D.3.9** `exporter/goldendict/export_epd.py` → `export_epd_sbs.py` (SBS only).
- [ ] **D.3.10** `exporter/goldendict/data_classes.py` → `data_classes_dps.py` (shared RU+SBS shadow).

### D.4 Complete Russian Shadow Copies (47 entries, grouped by area)

- [ ] **D.4.1** GoldenDict exporters (7 files): read each shadow, document local changes.
- [ ] **D.4.2** Webapp (5 files): read each shadow, document local changes.
- [ ] **D.4.3** DB families (5 files): read each shadow, document `html_ru`/`data_ru` columns.
- [ ] **D.4.4** Other exporters (5 files): read each shadow, document local changes.
- [ ] **D.4.5** Build/deploy scripts (8 files): document Russian-specific build paths.
- [ ] **D.4.6** Tools (6 files): document core Russian utilities.
- [ ] **D.4.7** Other remaining entries: document per file.

### D.5 Complete SBS Shadow Copies (18 entries, grouped by area)

- [ ] **D.5.1** GoldenDict exporters (6 files).
- [ ] **D.5.2** Build/deploy scripts (5 files).
- [ ] **D.5.3** Tools (3 files).
- [ ] **D.5.4** Other remaining entries.

### D.6 Verify SMD coverage

- [ ] **D.6.1** `uv run python3 kamma/upstream_sync/verify_smd_coverage.py` — zero gaps, quality rubric met.

**Phase D complete when:** Every registry entry has a complete SMD section. `verify_smd_coverage.py` passes with zero gaps.

---

## Phase E: Safe Cleanup Enablement

- [ ] **E.1** Refactor `tests/test_shadow_cleanup.py` to default to `--dry-run`. Require explicit `--apply` for actual file moves. Script must never archive files unless `--apply` is explicitly passed.
- [ ] **E.2** Modernize: `Path` usage, modern type hints, `Path.read_text()`.
- [ ] **E.3** `uv run ruff check --fix tests/test_shadow_cleanup.py && uv run ruff format tests/test_shadow_cleanup.py`
- [ ] **E.4** `uv run python3 tests/test_shadow_cleanup.py --dry-run` — verify safe default.

**Phase E complete when:** Script is safe to run by default. No mutations without `--apply`.

---

## Phase F: Docs, Modernization, and Final Verification

### F.1 Modernize touched Python files

- [ ] **F.1.1** Ensure `tests/test_shadow_parity.py`, `tests/check_shadow_modifications.py` use `Path`, modern type hints.
- [ ] **F.1.2** `uv run ruff check --fix` and format all new/modified Python files.

### F.2 Documentation

- [ ] **F.2.1** Verify CLAUDE.md, AGENTS.md, tech-stack.md all point to `kamma/upstream_sync/`.
- [ ] **F.2.2** Write `docs/technical/upstream_sync_infrastructure.md` — canonical location, registry purpose, SMD purpose, validator scripts, legacy status of `conductor/templates/upstream_sync_rehearsal/`.
- [ ] **F.2.3** Update `kamma/upstream_sync/README.md` if deliverables changed during execution.

### F.3 Final verification

- [ ] **F.3.1** `uv run python3 kamma/upstream_sync/validate_registry.py` — must pass.
- [ ] **F.3.2** `uv run python3 kamma/upstream_sync/verify_smd_coverage.py` — must pass.
- [ ] **F.3.3** `uv run pytest tests/test_shadow_parity.py --tb=short -q`
- [ ] **F.3.4** `uv run python3 tests/check_shadow_modifications.py`
- [ ] **F.3.5** `uv run python3 tests/test_shadow_cleanup.py --dry-run`
- [ ] **F.3.6** Grep for stale active references — only in allowed-legacy locations.

### F.4 Stage and present commit

- [ ] **F.4.1** Record all touched files. Confirm no unrelated changes included.
- [ ] **F.4.2** Stage after user approval.
- [ ] **F.4.3** Present commit message:
  ```
  #sync kamma: migrate registry to kamma/upstream_sync, create SMD and validators
  ```

**Phase F complete when:** All automated checks pass. Files staged. Commit message presented.

---

## Files Created/Modified Summary

### New files:
- `kamma/upstream_sync/registry.json`
- `kamma/upstream_sync/registry_helper.py`
- `kamma/upstream_sync/smd.md`
- `kamma/upstream_sync/guide.md`
- `kamma/upstream_sync/improvements.md`
- `kamma/upstream_sync/README.md`
- `kamma/upstream_sync/gen_smd_scaffold.py`
- `kamma/upstream_sync/validate_registry.py`
- `kamma/upstream_sync/verify_smd_coverage.py`
- `conductor/templates/upstream_sync_rehearsal/LEGACY_NOTICE.md`
- `docs/technical/upstream_sync_infrastructure.md`

### Modified files:
- `scripts/bash/full_sync.sh`
- `scripts/cl_dps/dpd-sync-folders`
- `tests/test_shadow_parity.py`
- `tests/check_shadow_modifications.py`
- `tests/test_shadow_cleanup.py`
- `CLAUDE.md`
- `AGENTS.md`
- `conductor/tech-stack.md`
- `scripts/bash/README.md` (if behavior changed)
- `scripts/cl_dps/README.md` (if behavior changed)
