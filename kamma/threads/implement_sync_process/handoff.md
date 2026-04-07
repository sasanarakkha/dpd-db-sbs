# Handoff: Implement Upstream Sync Process Improvements

## Status

- **Phases 0–3**: COMPLETE (registry migration, validator hardening, SMD split, prep analyzer, namespace isolation test, template syntax test).
- **Phase 3.5**: COMPLETE (review fixes — see below).
- **Phase 4**: NOT STARTED.
- **Phase 5**: NOT STARTED.

## What Happened This Session (review + Phase 3.5)

A review session (`kamma:3-review`) caught two important issues from the thread's execution:

### Issue 1 — Template spacing regression (RESOLVED)
The executing model introduced `{%if` (missing space after `{%`) during Mako→Jinja2 work.
User reverted all staged template changes via git. Further investigation confirmed:
- **The templates were already Jinja2 — no Mako conversion was ever needed.**
- The test `test_no_mako_syntax` had a false-positive bug (`% if` matched inside `{% if %}` Jinja2 tags).

**Resolution**: Created `tests/test_template_syntax.py` with:
- Correct anchored Mako detection (no false positives)
- Spacing guard (`{%[a-zA-Z]` pattern)
- **254 tests passing**

### Issue 2 — Blanket `ru_` prefix renames (RESOLVED by design + revert)
The executing model added `ru_` prefix to ALL functions in localized files indiscriminately,
creating double-marking like `ru_db_search_gd_sbs()`. User reverted these renames.

**Resolution**: Designed a three-tier naming convention (now in `AGENTS.md`):
- Tier 1 (identical to upstream): no marker
- Tier 2 (modified from upstream): locale suffix only (`_ru`, `_sbs`, `_dps`)
- Tier 3 (new, no upstream counterpart): descriptive name + locale suffix if not obvious
- Rule: never both prefix AND suffix on the same function

A new thread `normalize_function_naming` was created to audit and apply this convention correctly across all shadow files.

## Code State

All changes are **STAGED, not committed**. Files staged include:
- `tests/test_template_syntax.py` (new)
- `AGENTS.md` (namespace isolation section updated)
- `kamma/threads/implement_sync_process/plan.md` (phase 3.5 marked complete)
- `kamma/threads/normalize_function_naming/plan.md` (new thread)
- `kamma/threads.md` (new thread entry)
- All prior Phase 0–3 staged files remain staged

## Next Task

**Begin Phase 4: Documentation and Template Migration**
- 4.1 Rewrite `kamma/upstream_sync/guide.md` (3-stage workflow, new category semantics)
- 4.2 Create `kamma/upstream_sync/stages/` (prep.md, analysis.md, execution.md)
- 4.3 Update thread templates in `kamma/upstream_sync/templates/`
- 4.4 Update `kamma/upstream_sync/README.md`
- 4.5 Update `docs/technical/upstream_sync_infrastructure.md`

## Recommended Session Order

1. `implement_sync_process` Phase 4 (documentation)
2. `normalize_function_naming` thread (audit + rename shadow file functions)
3. `implement_sync_process` Phase 5 (final verification + commit prep)

## Blockers

None.
