# scripts/change_in_db/

## Purpose & Rationale
`scripts/change_in_db/` provides targeted, batch operations that modify database content directly — applying corrections, filling examples, cleaning up data, and running rule-based updates against the DPD database.

## Architectural Logic
"Direct Database Mutation" pattern:
1. **Query:** Selects relevant rows from `dpd.db` based on specific criteria.
2. **Transform:** Applies corrections, copies values, or runs business rules in memory.
3. **Persist:** Writes changes back in atomic transactions via `db/` models.

## Relationships & Data Flow
- **Target:** Modifies `dpd.db` tables (`DpdHeadword`, `SBS`, `Russian`, etc.).
- **Source:** Corrections TSVs from `shared_data/` or inline rules.
- **Triggered by:** Manual invocation or as part of a build/release workflow.

## Interface
- `uv run python scripts/change_in_db/apply_all_additions.py`
- `uv run python scripts/change_in_db/apply_all_corrections.py`
- `uv run python scripts/change_in_db/class_relation.py`
- `uv run python scripts/change_in_db/copy_examples.py`
- `uv run python scripts/change_in_db/dhp_examples_copy.py`
- `uv run python scripts/change_in_db/example_cleanup.py`
- `uv run python scripts/change_in_db/fill_dhp_examples.py`
- `uv run python scripts/change_in_db/source_cleanup.py`
- `uv run python scripts/change_in_db/update_sbs_chants_in_db.py`
- `uv run python scripts/change_in_db/update_yojana_km.py`
- `uv run python scripts/change_in_db/vib_rule_workflow.py`
