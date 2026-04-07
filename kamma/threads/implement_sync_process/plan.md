# Plan: Implement Upstream Sync Process Improvements

> **Executing model**: Follow sequentially. Do NOT skip steps. Mark tasks `[~]` before starting,
> `[x]` on completion. Do not make design choices. If ambiguity appears that is not
> resolved by this plan or the locked thread context, raise a `[DISCUSS]` flag and stop.
>
> **Primary context**: `analysis_summary.md` in this folder.
> **Audit source**: `kamma/archive/improvement_sync_proccess/audit_results.md`.
> **Design source**: `kamma/archive/improvement_sync_proccess/design.md`.
>
> `suggestions.md` has been fully absorbed into this plan and is no longer an active
> source of decisions.

---

## Phase 0: Baseline, Consumers, and Overlap Audit

- [x] Read these current consumers and references end-to-end:
  - `kamma/upstream_sync/registry.json`
  - `kamma/upstream_sync/validate_registry.py`
  - `kamma/upstream_sync/verify_smd_coverage.py`
  - `kamma/upstream_sync/registry_helper.py`
  - `tests/test_shadow_parity.py`
  - `tests/test_shadow_cleanup.py`
  - `tests/check_shadow_modifications.py`
  - `kamma/upstream_sync/guide.md`
  - `kamma/upstream_sync/README.md`
  - `kamma/upstream_sync/templates/sync_thread_plan.md`
  - `kamma/upstream_sync/templates/sync_thread_spec.md`
  - `docs/technical/upstream_sync_infrastructure.md`
- [x] Run `uv run python3 kamma/upstream_sync/validate_registry.py` and record the baseline result.
- [x] Run `uv run python3 kamma/upstream_sync/verify_smd_coverage.py` and record the baseline result.
- [x] Audit current registry overlaps before editing the schema:
  - exact-path overlap
  - directory containment overlap
  - glob-pattern overlap
- [x] Explicitly inspect and record the outcome for these known current collisions:
  - `unique_paths: "scripts/bash/*.sh"` vs planned inspired entries under `scripts/bash/`
  - `unique_paths: "scripts/export/"` vs `sbs_copies: "scripts/export/dps_anki_updater.py"`
  - `unique_paths: "docs_rus/dpd_rus.md"` vs planned inspired entry `docs_rus/`
- [x] Record whether the current test/docs/tooling surface already assumes `smd.md`,
  `ignored_files`, or `folders_to_check`.

**Phase 0 complete when:** Baseline command results are recorded, all current consumer
files are reviewed, and registry overlap risks are written down before any migration.

---

## Phase 1: Registry Migration and Validator Hardening

### 1.1 — Migrate `registry.json`

- [x] Move the following entries from `russian_copies` or `sbs_copies` into a new top-level
`inspired_by_upstream` object using this schema:

```json
"inspired_by_upstream": {
  "local/path": {
    "upstream": "upstream/path",
    "divergence_reason": "One sentence."
  }
}
```

**Entries to move (from `russian_copies`):**
- `".github/workflows/ru_release.yml"` → upstream: `".github/workflows/draft_release.yml"`, divergence_reason: `"Different pipeline logic for RU release lifecycle."`
- `".github/workflows/ru_release_test.yml"` → upstream: `".github/workflows/draft_release.yml"`, divergence_reason: `"Different pipeline logic for RU release testing."`
- `".github/workflows/ru_static.yml"` → upstream: `".github/workflows/static.yml"`, divergence_reason: `"Different CI configuration for RU static build."`
- `"scripts/bash/generate_components.sh"` → upstream: `"scripts/bash/generate_components.py"`, divergence_reason: `"Language mismatch: Bash vs Python; localized build orchestration."`
- `"scripts/bash/make_dpd.sh"` → upstream: `"scripts/bash/makedict.py"`, divergence_reason: `"Language mismatch: Bash vs Python; localized DPD build logic."`
- `"scripts/bash/make_ru_dpd.sh"` → upstream: `"scripts/bash/makedict.py"`, divergence_reason: `"Language mismatch: Bash vs Python; RU-specific build entry point."`
- `"docs_rus/"` → upstream: `"docs/"`, divergence_reason: `"Content-diverged Russian documentation; not a translation of upstream docs."`
- `"mkdocs_ru.yaml"` → upstream: `"mkdocs.yaml"`, divergence_reason: `"Different build config: different nav structure and RU-specific plugins."`
- `"exporter/goldendict/export_dpd_ru.py"` → upstream: `"exporter/goldendict/export_dpd.py"`, divergence_reason: `"Significant divergence in data structures and RU output logic."`
- `"exporter/goldendict/export_help_ru.py"` → upstream: `"exporter/goldendict/export_help.py"`, divergence_reason: `"Localized help export with RU-specific content structure."`
- `"exporter/goldendict/export_roots_ru.py"` → upstream: `"exporter/goldendict/export_roots.py"`, divergence_reason: `"RU-specific data injection makes mechanical parity impractical."`
- `"exporter/goldendict/export_variant_spelling_ru.py"` → upstream: `"exporter/goldendict/export_variant_spelling.py"`, divergence_reason: `"RU output logic diverges from upstream structure."`
- `"exporter/goldendict/main_ru.py"` → upstream: `"exporter/goldendict/main.py"`, divergence_reason: `"RU-specific dictionary entry point with different build orchestration."`
- `"tools/paths_ru.py"` → upstream: `"tools/paths.py"`, divergence_reason: `"Fundamental path redirection logic for RU build outputs."`

**Entries to move (from `sbs_copies`):**
- `"exporter/goldendict/export_dpd_sbs.py"` → upstream: `"exporter/goldendict/export_dpd.py"`, divergence_reason: `"Significant structural divergence for SBS output format."`
- `"exporter/goldendict/export_epd_sbs.py"` → upstream: `"exporter/goldendict/export_epd.py"`, divergence_reason: `"SBS-specific output logic diverges from upstream."`
- `"exporter/goldendict/export_help_sbs.py"` → upstream: `"exporter/goldendict/export_help.py"`, divergence_reason: `"SBS-specific help content structure."`
- `"exporter/goldendict/export_roots_sbs.py"` → upstream: `"exporter/goldendict/export_roots.py"`, divergence_reason: `"SBS data injection makes mechanical parity impractical."`
- `"exporter/goldendict/main_sbs.py"` → upstream: `"exporter/goldendict/main.py"`, divergence_reason: `"SBS-specific dictionary entry point."`
- `"tools/paths_dps.py"` → upstream: `"tools/paths.py"`, divergence_reason: `"Fundamental path redirection for DPS/SBS build outputs."`
- `"tools/fast_api_utils_dps.py"` → upstream: `"tools/fast_api_utils.py"`, divergence_reason: `"DPS-specific FastAPI utilities; architectural divergence from upstream."`

**Also in this step:**
- [x] Remove the `folders_to_check` top-level key entirely.
- [x] Rename `ignored_files` to `skip_sync_patterns`.
- [x] Resolve broad-pattern collisions created by the migration:
  - no `unique_paths` glob or directory may swallow a strict shadow or inspired entry
  - do not leave `docs_rus/` and `docs_rus/dpd_rus.md` split across categories
  - do not leave `scripts/bash/*.sh` covering inspired entries moved out of shadow status
- [x] Do NOT touch `db/models.py` or `exporter/goldendict/data_classes_dps.py`.

### 1.2 — TDD: Write failing validator tests first (RED)

- [x] Write `tests/test_validate_registry.py`. The tests must FAIL before the validator
is updated. Verify they fail by running:

```bash
uv run pytest tests/test_validate_registry.py -v
```

Test cases to cover:
- `test_inspired_by_upstream_valid`
- `test_inspired_by_upstream_missing_upstream`
- `test_inspired_by_upstream_missing_divergence_reason`
- `test_inspired_by_upstream_empty_divergence_reason`
- `test_inspired_by_upstream_missing_upstream_target_path`
- `test_skip_sync_patterns_valid`
- `test_skip_sync_patterns_not_a_list`
- `test_skip_sync_patterns_blank_item_rejected`
- `test_ignored_files_rejected`
- `test_folders_to_check_rejected`
- `test_cross_category_overlap_rejected`

### 1.3 — Update `validate_registry.py` (GREEN)

- [x] Add validation so the Phase 1.2 tests pass.

Required behavior:
1. `validate_inspired_by_upstream(data)`:
   - each entry must be a dict
   - `upstream` must be a non-empty string
   - `divergence_reason` must be a non-empty string
2. Validate both paths for inspired entries:
   - local path exists in the repo
   - declared upstream path exists in the repo
3. `validate_skip_sync_patterns(data)`:
   - must be a list
   - every item must be a string
   - every item must be non-empty after `.strip()`
4. If `ignored_files` exists, error:
   - `"'ignored_files' is no longer valid; use 'skip_sync_patterns' instead"`
5. If `folders_to_check` exists, error or warning per test expectations.
6. Extend cross-section overlap validation to check:
   - `russian_copies`
   - `sbs_copies`
   - `inspired_by_upstream`
   - `unique_paths`
   - `no_sync_files`
7. Overlap validation must detect:
   - exact duplicates
   - directory containment
   - glob collisions where a broad pattern swallows a categorized path
8. Default policy:
   - cross-category nesting is not allowed unless explicitly designed

### 1.4 — Update `registry_helper.py`

- [x] Add typed helper functions for:
- modified upstream paths
- inspired-by local paths
- strict shadow mappings
- skip-sync patterns

Keep helpers simple and reusable by validator, SMD coverage, and prep analyzer.

### 1.5 — Verify Phase 1

- [x] `uv run pytest tests/test_validate_registry.py -v`
- [x] `uv run python3 kamma/upstream_sync/validate_registry.py`
- [x] `uv run ruff check --fix kamma/upstream_sync/validate_registry.py tests/test_validate_registry.py kamma/upstream_sync/registry_helper.py`
- [x] `uv run ruff format kamma/upstream_sync/validate_registry.py tests/test_validate_registry.py kamma/upstream_sync/registry_helper.py`

**Phase 1 complete when:** Registry schema is migrated, overlap-safe, and validator
tests pass.

---

## Phase 2: SMD Restructuring and Coverage Tooling

### 2.1 — Split `smd.md` into `kamma/upstream_sync/smd/`

- [x] Create these files and move existing SMD content into them:
- `kamma/upstream_sync/smd/db.md`
- `kamma/upstream_sync/smd/exporter.md`
- `kamma/upstream_sync/smd/gui.md`
- `kamma/upstream_sync/smd/scripts.md`
- `kamma/upstream_sync/smd/tools.md`
- `kamma/upstream_sync/smd/root.md`
- `kamma/upstream_sync/smd/index.md`

Required ordering:
1. create domain files
2. update tooling to read them
3. update active references
4. verify coverage and references
5. delete old `kamma/upstream_sync/smd.md`

For `inspired_by_upstream` entries:
- if existing prose exists, change `Sync Rule` to `inspired_only`
- remove strict-parity rubric requirements from `Local Changes`
- keep `Watch For` as high-value upstream review notes

For inspired entries with no existing SMD prose, create a minimal stub:

```markdown
**File**: `path/to/file`
- **Category**: inspired_by_upstream
- **Sync Rule**: inspired_only
- **Divergence Reason**: [copy from registry.json divergence_reason]
- **Watch For**:
  - Review upstream changes for algorithmic improvements worth backporting.
```

### 2.2 — TDD: Add coverage-tool tests first (RED)

- [x] Create `tests/test_verify_smd_coverage.py`. Tests must fail before tooling is updated.

Test cases to cover:
- aggregate entries across multiple `smd/*.md` files
- fail on duplicate file entry across two domain files
- include `inspired_by_upstream` paths in coverage checks
- `inspired_only` skips the minimum local-changes rubric
- `inspired_only` still requires `Watch For`

### 2.3 — Update `verify_smd_coverage.py` (GREEN)

- [x] Changes required:
1. Replace single-file loading with globbed loading from `kamma/upstream_sync/smd/*.md`
2. Aggregate entries across files
3. Fail on duplicate file-path entries across multiple SMD files
4. Pull `inspired_by_upstream` entries from `registry_helper.py`
5. Support `sync_rule == "inspired_only"` by skipping the minimum local-change check
6. Keep `Watch For` required for inspired entries

### 2.4 — Update `gen_smd_scaffold.py`

- [x] Update scaffold generation so it can emit:
- normal stubs for strict shadow and modified-upstream entries
- `inspired_only` stubs for inspired entries

### 2.5 — Verify Phase 2

- [x] `uv run pytest tests/test_verify_smd_coverage.py -v`
- [x] `uv run python3 kamma/upstream_sync/verify_smd_coverage.py`
- [x] Manually verify that active references to `smd.md` have been updated before deletion
- [x] Delete `kamma/upstream_sync/smd.md` only after coverage and reference checks pass
- [x] Re-run `uv run python3 kamma/upstream_sync/verify_smd_coverage.py`
- [x] `uv run ruff check --fix kamma/upstream_sync/verify_smd_coverage.py kamma/upstream_sync/gen_smd_scaffold.py tests/test_verify_smd_coverage.py`
- [x] `uv run ruff format kamma/upstream_sync/verify_smd_coverage.py kamma/upstream_sync/gen_smd_scaffold.py tests/test_verify_smd_coverage.py`

**Phase 2 complete when:** SMD domain files replace `smd.md`, coverage tooling is
tested, and no active reference still points at the old file.

---

## Phase 3: Shadow Tooling, New Scanners, and Prep Analyzer

### 3.1 — Update `tests/test_shadow_parity.py`

- [x] Narrow parity enforcement to true strict shadows only.

In `get_python_pairs()`, exclude paths moved to `inspired_by_upstream`.

Verify:

```bash
uv run pytest tests/test_shadow_parity.py --tb=short -q
```

### 3.2 — Review `tests/check_shadow_modifications.py`

- [x] Read the current file and keep its role strict-shadow-only.

Required outcome:
- it must continue to track only real shadow pairs
- it must not silently become enforcement for inspired files
- add comments or small logic updates if needed so the scope remains explicit

Verify:

```bash
uv run python3 tests/check_shadow_modifications.py
```

### 3.3 — Review `tests/test_shadow_cleanup.py`

- [x] Do NOT assume it currently reads `ignored_files`; it does not in the live codebase.

Instead:
- inspect whether registry migration or overlap cleanup affects this script
- update help text, comments, or logic only if needed
- keep behavior correct after removal of `folders_to_check`

Verify:

```bash
uv run pytest tests/test_shadow_cleanup.py --tb=short -q
```

### 3.4 — Implement `tests/test_namespace_isolation.py`

- [x] Write the test first. It should enforce namespace isolation on localized files.

Defaults:
- full scan by default
- mark `slow` if needed
- use targeted invocation in verification commands instead of limiting to changed files only

Test logic:
- scan `.py` files in `russian_copies` and `sbs_copies`
- inspect top-level defs with `ast`
- fail on names not starting with `ru_`, `sbs_`, or `dps_`, excluding:
  - `main`
  - double-underscore names
  - names also present in the upstream source file
- scan `.html` and `.jinja2` for `id="..."` attributes and require prefixed IDs

### 3.5 — Implement `tests/test_template_syntax.py`

- [x] Write the test first. It should scan localized template files for legacy Mako syntax.

Test logic:
- recursively scan `.html` and `.jinja2` files under localized copy paths
- fail on:
  - `${`
  - `% if`
  - `% for`

### 3.6 — TDD: Write failing `prep_analyzer.py` tests first (RED)

- [x] Write `tests/test_prep_analyzer.py`. It must fail before implementation.

Do NOT mock `subprocess.run` directly. Instead:
- create a helper boundary such as `run_git_diff()` or `get_changed_paths()`
- mock that helper, or use a temporary git repo fixture

Test cases to cover:
- modified file mapped to `modified_upstream_files`
- added file not in registry
- deleted file
- renamed file (`R*`)
- `skip_sync_patterns` exclusion
- modified upstream source for strict shadows
- modified upstream source for inspired entries

### 3.7 — Implement `kamma/upstream_sync/prep_analyzer.py` (GREEN)

- [x] ```python
"""Generate a factual upstream diff report mapped to registry categories."""
```

Implementation requirements:
1. Parse `git diff --name-status as_upstream HEAD`
2. Support statuses:
   - `M`
   - `A`
   - `D`
   - `R*`
3. Filter out paths matching `skip_sync_patterns`
4. Classify remaining changes into report sections:
   - Modified — Tracked Files
   - Modified — Shadow Sources
   - Modified — Inspired Sources
   - Untracked Changes
   - Registry Validation Status
   - SMD Coverage Status
5. Prefer internal summary helpers over scraping printer-formatted output from other scripts
6. Write `prep_report.md` to the thread folder passed as CLI argument

### 3.8 — Verify Phase 3

- [x] `uv run pytest tests/test_shadow_parity.py --tb=short -q`
- [x] `uv run python3 tests/check_shadow_modifications.py`
- [x] `uv run pytest tests/test_shadow_cleanup.py --tb=short -q`
- [x] `uv run pytest tests/test_namespace_isolation.py tests/test_template_syntax.py tests/test_prep_analyzer.py -v`
- [x] `uv run ruff check --fix tests/test_shadow_parity.py tests/check_shadow_modifications.py tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py tests/test_prep_analyzer.py kamma/upstream_sync/prep_analyzer.py`
- [x] `uv run ruff format tests/test_shadow_parity.py tests/check_shadow_modifications.py tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py tests/test_prep_analyzer.py kamma/upstream_sync/prep_analyzer.py`

**Phase 3 complete when:** Parity enforcement is narrowed to strict shadows, new
isolation and syntax scanners pass, and the prep analyzer emits classification reports.

**Phase 3 complete when:** Strict-shadow tooling is aligned with the new categories,
new scanners exist, and prep analyzer output is tested.

---

## Phase 3.5: Review Fixes (retroactive, added after review)

### 3.5a — Create `tests/test_template_syntax.py` with two guards

> **Note:** Templates are already Jinja2 — no Mako→Jinja2 conversion is needed or was done.
> The thread's executing model introduced a spacing regression (`{% if` → `{%if`) which was
> reverted. The test below prevents both that regression and any future accidental Mako reintroduction.

- [x] Create `tests/test_template_syntax.py` with two parametrized tests:
  - `test_no_mako_syntax`: detects real Mako syntax — `${...}` substitutions and
    line-level `% if` / `% for` / `% end` control tags (anchored to avoid false
    positives inside `{% if %}` Jinja2 tags)
  - `test_no_spacing_violation`: detects `{%[a-zA-Z]` — missing space after `{%`
  - Run: `uv run pytest tests/test_template_syntax.py -v` — 254 passed ✓

### 3.5b — Document three-tier function naming convention in `AGENTS.md`

The current "Namespace Isolation" section in AGENTS.md instructs blanket `ru_`/`sbs_`/`dps_`
prefix on all localized functions. This caused a large, inconsistent rename that was
reverted. Replace with the three-tier convention:

**Convention:**
- **Tier 1 — Identical copy from upstream**: No locale marker. Keep upstream name exactly.
  Signal: safe to overwrite during sync.
- **Tier 2 — Modified from upstream**: Locale suffix only (`_ru`, `_sbs`, or `_dps`).
  Never apply both a prefix and a suffix. Signal: check upstream diff before syncing.
- **Tier 3 — New (no upstream counterpart)**: Use a descriptive name. Add locale suffix
  if the locale is not already clear from the name. `ru_` prefix only when a suffix
  would be genuinely ambiguous (must be justified, not default).
- **HTML IDs**: Always prefix with locale (`ru_`, `sbs_`, `dps_`) — unchanged rule,
  as HTML IDs share the DOM and collision is real.

- [x] Update "Namespace Isolation" bullet in `AGENTS.md` to describe the three-tier system
- [x] Run: `uv run ruff check --fix tests/test_template_syntax.py && uv run ruff format tests/test_template_syntax.py`

**Phase 3.5 complete when:** Spacing test is green and AGENTS.md reflects the three-tier convention.

---

## Phase 4: Documentation and Template Migration

### 4.1 — Rewrite `kamma/upstream_sync/guide.md`

Replace the old workflow description with the locked 3-stage process:
- Prep
- Manual Sync boundary action
- Analysis
- Execution + Verification

Also update:
- category semantics
- discuss-flag protocol
- references from `smd.md` to `smd/` or `smd/index.md`
- legacy `ignored_files` / `folders_to_check` references

Move historical workflow content to `kamma/upstream_sync/archive_improvements.md`
under a clearly historical heading.

### 4.2 — Create `kamma/upstream_sync/stages/`

Create:
- `kamma/upstream_sync/stages/prep.md`
- `kamma/upstream_sync/stages/analysis.md`
- `kamma/upstream_sync/stages/execution.md`

Each file should state:
- stage input/output contract
- required report sections
- a blank template/checklist

### 4.3 — Update thread templates

Update both:
- `kamma/upstream_sync/templates/sync_thread_plan.md`
- `kamma/upstream_sync/templates/sync_thread_spec.md`

Required changes:
- switch from `smd.md` to `smd/index.md` or `smd/`
- remove legacy 7-phase assumptions
- align with the 3-stage process and category model

### 4.4 — Update `kamma/upstream_sync/README.md`

README must become the quick-start entry point and include:
- 3-stage workflow overview
- quick commands
- link to `guide.md`
- link to `smd/index.md`

### 4.5 — Update technical documentation

Update `docs/technical/upstream_sync_infrastructure.md` so it reflects:
- `inspired_by_upstream`
- `skip_sync_patterns`
- `smd/` directory instead of `smd.md`
- current registry consumers

### 4.6 — Create `kamma/upstream_sync/new_improvements.md`

Create as a blank intake file with a short header explaining:
- it is temporary
- entries are promoted to `archive_improvements.md` after review

### 4.7 — Verify Phase 4

- [ ] Read new `guide.md` and confirm old active workflow text is gone
- [ ] Confirm `archive_improvements.md` retains historical material
- [ ] Confirm `stages/` contains 3 files
- [ ] Confirm both thread templates are updated
- [ ] Confirm `README.md` and `docs/technical/upstream_sync_infrastructure.md` match the new schema and SMD layout
- [ ] Confirm no active docs still refer to `ignored_files`, `folders_to_check`, or `smd.md` except clearly historical/archive sections

**Phase 4 complete when:** Docs, templates, and technical references all match the
new process and schema.

---

## Phase 5: Final Verification

Run targeted affected checks first, then full verification.

### 5.1 — Targeted verification

- [ ] `uv run pytest tests/test_validate_registry.py tests/test_verify_smd_coverage.py tests/test_namespace_isolation.py tests/test_template_syntax.py tests/test_prep_analyzer.py -v`
- [ ] `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py --tb=short -q`
- [ ] `uv run python3 tests/check_shadow_modifications.py`
- [ ] `uv run python3 kamma/upstream_sync/validate_registry.py`
- [ ] `uv run python3 kamma/upstream_sync/verify_smd_coverage.py`
- [ ] `uv run python3 kamma/upstream_sync/prep_analyzer.py /tmp/test_prep/`
- [ ] `uv run ruff check --fix kamma/upstream_sync tests/test_validate_registry.py tests/test_verify_smd_coverage.py tests/test_shadow_parity.py tests/test_shadow_cleanup.py tests/check_shadow_modifications.py tests/test_namespace_isolation.py tests/test_template_syntax.py tests/test_prep_analyzer.py`
- [ ] `uv run ruff format kamma/upstream_sync tests/test_validate_registry.py tests/test_verify_smd_coverage.py tests/test_shadow_parity.py tests/test_shadow_cleanup.py tests/check_shadow_modifications.py tests/test_namespace_isolation.py tests/test_template_syntax.py tests/test_prep_analyzer.py`
- [ ] `uv run ty check kamma/upstream_sync tests`

### 5.2 — Full-suite verification

- [ ] Record whether the baseline suite was already green before this work
- [ ] `uv run pytest --tb=short -q`
- [ ] If unrelated pre-existing failures exist, report them separately from this task's regressions

### 5.3 — Acceptance confirmation

- [ ] Check every acceptance criterion in `spec.md` explicitly
- [ ] Confirm `prep_report.md` contains all required sections and does not crash on non-empty diff input

**Phase 5 complete when:** Targeted tests and validators pass, full-suite status is
reported honestly against the baseline, and the thread acceptance criteria are met.
