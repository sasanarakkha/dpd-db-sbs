# scripts/patch/

## Purpose & Rationale
`scripts/patch/` provides a targeted database patching mechanism for applying surgical fixes to `dpd.db` outside the normal build cycle.

## Architectural Logic
"Hotfix" pattern:
1. **Isolation:** Patches are standalone scripts that apply a single, well-scoped fix.
2. **Idempotency:** Designed to be safe to re-run (check-before-write).
3. **Emergency use:** Used for urgent fixes that cannot wait for a full rebuild.

## Relationships & Data Flow
- **Target:** Directly modifies `dpd.db` via `db/` models.
- **Triggered by:** Manual invocation during incident response or data emergencies.

## Interface
- `uv run python scripts/patch/patch_dpd.py`
