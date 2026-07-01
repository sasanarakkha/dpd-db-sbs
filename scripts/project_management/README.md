# scripts/project_management/

## Purpose & Rationale
`scripts/project_management/` provides tooling for assessing the project's overall health — tracking code quality, data integrity, and maintenance status.

## Architectural Logic
"Health Assessment" pattern:
1. **Scan:** Iterates over project modules and data stores.
2. **Analyse:** Applies heuristics and thresholds to identify concerning patterns.
3. **Report:** Outputs actionable findings for maintainers.

## Relationships & Data Flow
- **Input:** Project source tree, `dpd.db`, and version control metadata.
- **Output:** Terminal reports and optionally structured output for dashboards.
- **Consumption:** Guides maintainers on cleanup and refactoring priorities.

## Interface
- `uv run python scripts/project_management/project_health_check.py`
