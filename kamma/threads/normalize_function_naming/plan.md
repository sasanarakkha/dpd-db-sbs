# Plan: Normalize Function Naming in Shadow Files

> **Executing model**: Follow sequentially. Do NOT skip steps. Mark tasks `[~]` before starting,
> `[x]` on completion. Do not make design choices. If ambiguity appears that is not
> resolved by this plan, raise a `[DISCUSS]` flag and stop.
>
> **Primary context**: `AGENTS.md` (Namespace Isolation section — three-tier convention).
> **Scope**: All `*_ru.py`, `*_sbs.py`, `*_dps.py` files across the entire project.

---

## Background

During the `implement_sync_process` thread, an executing model applied a blanket `ru_` prefix
to all top-level functions in localized shadow files. This was reverted because it:
- Created double-marking (`ru_func_name_ru()` — prefix + suffix)
- Obscured whether a function was identical to upstream or actually modified
- Mixed locale signals (`ru_db_search_gd_sbs()`)

The correct convention (from `AGENTS.md`) is:

| Tier | Relationship to upstream | Naming rule |
|---|---|---|
| 1 | Identical copy | No locale marker — keep upstream name |
| 2 | Modified from upstream | Locale suffix only: `_ru`, `_sbs`, or `_dps` |
| 3 | New (no upstream equivalent) | Descriptive name; locale suffix if locale not in name |

HTML IDs in templates always require a locale prefix (`ru_`, `sbs_`, `dps_`). This thread
focuses on Python function/class names only.

---

## Phase 0: Classification Audit

### 0.1 — Collect all shadow files

Gather all shadow file paths from the registry:
- `kamma/upstream_sync/registry.json` — keys `russian_copies`, `sbs_copies` (strict shadows)
- Also scan for `*_ru.py`, `*_sbs.py`, `*_dps.py` files not in registry (verify coverage)

### 0.2 — For each shadow file, classify every top-level function/class

For each function/class in a shadow file:

1. Look up the upstream source file (from registry or by naming convention)
2. Check if the function exists in upstream:
   - **Not in upstream** → Tier 3 (new)
   - **Exists in upstream** → compare bodies:
     - Identical → Tier 1
     - Different → Tier 2

3. Check current name against convention:
   - Tier 1: name should match upstream exactly (no `_ru`/`_sbs`/`_dps` suffix added)
   - Tier 2: name should end with `_ru`, `_sbs`, or `_dps` as appropriate
   - Tier 3: name should contain locale signal (suffix preferred, `ru_` prefix only if justified)

4. Flag violations: names that don't match their tier

### 0.3 — Output classification report

Write `kamma/threads/normalize_function_naming/classification_report.md` with:
- One section per shadow file
- Table: function name | tier | current convention-compliant? | proposed rename (if any)
- Summary counts: total functions, violations, Tier 1/2/3 breakdown

**Phase 0 complete when:** Report exists and covers 100% of shadow file functions.

---

## Phase 1: Review and Approve Renames

### 1.1 — Present report to user

Stop. User reviews `classification_report.md` and approves/adjusts proposed renames before
any code is touched.

**[GATE: Do not proceed to Phase 2 without explicit user approval of the rename list.]**

---

## Phase 2: Apply Renames

### 2.1 — Apply renames file by file

For each approved rename:
- Update function definition
- Update all call sites within the same file
- Update all call sites across the project (grep for old name, confirm each)
- Do NOT change function logic — names only

### 2.2 — Update `tests/test_namespace_isolation.py`

Replace the current blanket-prefix enforcement with three-tier logic:
- Tier 1 functions: must NOT have a locale suffix added (must match upstream name)
- Tier 2 functions: must end with `_ru`, `_sbs`, or `_dps`
- Tier 3 functions: must contain a locale signal (suffix or prefix)
- No function may have both `ru_` prefix AND `_ru` suffix simultaneously

### 2.3 — Run ruff

```bash
uv run ruff check --fix <all changed files>
uv run ruff format <all changed files>
```

**Phase 2 complete when:** All renames applied, no `NameError` or import errors, ruff clean.

---

## Phase 3: Verification

> Reference: `conductor/archive/upstream_sync_rehearsal_20260311/plan.md` Phase 5 and 7
> defines the standard functional verification checklist for this codebase.
> Apply only the items relevant to the files changed by this thread.

### 3.1 — Automated tests (structural, parity, namespace)

```bash
uv run pytest tests/test_namespace_isolation.py -v
uv run pytest tests/test_template_syntax.py -v
uv run pytest tests/test_shadow_parity.py -v
uv run pytest tests/test_shadow_cleanup.py -v
```

### 3.2 — Functional export verification (manual)

For each export subsystem that had renamed functions, verify it still builds correctly:

- **GoldenDict/SBS export**: run `exporter/goldendict/main_sbs.py` — confirm output produced
- **GoldenDict/RU export**: run `exporter/goldendict/main_ru.py` — confirm output produced
- **Webapp (RU)**: run `exporter/webapp/main_ru.py` — confirm app starts and search works
- **Kindle (RU)**: run `exporter/kindle/kindle_exporter_ru.py` — confirm output produced
- **GUI2**: open GUI and confirm it loads without errors

Only verify subsystems where functions were actually renamed. Skip subsystems with zero renames.

### 3.3 — Full suite

```bash
uv run pytest --tb=short -q
```

All 140+ tests must pass (as per rehearsal standard).

**Phase 3 complete when:** All automated tests green, manual exports verified for changed subsystems.

---

## Commit Preparation

Stage all changed files. Draft commit message:

```
normalize function naming in shadow files: three-tier convention applied
```

Present staged files and commit message to user for manual review and commit.
