# scripts/archive/

## Purpose & Rationale
`scripts/archive/` is the project's historical record — scripts that have been replaced, superseded, or are no longer actively maintained. They are retained for reference, reproducibility of past results, and potential revival if needed.

## Architectural Logic
"Retirement" pattern:
1. **Preservation:** Scripts are kept intact (not deleted) to preserve the historical record.
2. **Isolation:** Archived scripts are clearly separated from active code to avoid accidental use.
3. **Self-documenting:** Filenames reflect the original purpose; no active integration with the build pipeline.

## Relationships & Data Flow
- **No active data flow:** These scripts are not wired into any current workflow or CI pipeline.
- **Reference only:** May contain logic or approaches worth consulting when re-implementing similar features.

## Interface
No active interface. Browse the directory for historical implementations.
