# scripts/dps_archive/

## Purpose & Rationale
`scripts/dps_archive/` is the historical record for DPS fork (Russian/SBS) scripts that have been replaced, superseded, or are no longer actively maintained. Retained for reproducibility and reference.

## Architectural Logic
"Retirement" pattern:
1. **Preservation:** DPS-specific archived scripts are kept for historical reference.
2. **Isolation:** Separated from active `dps_*` and `scripts/` code to avoid accidental use.
3. **Self-documenting:** Filenames reflect the original DPS/RU/SBS purpose.

## Relationships & Data Flow
- **No active data flow:** Not wired into any current workflow.
- **Reference only:** May contain useful patterns for DPS-specific operations.

## Interface
No active interface. Browse the directory for historical DPS/RU/SBS implementations.
