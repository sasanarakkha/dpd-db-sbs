# scripts/moving/

## Purpose & Rationale
`scripts/moving/` provides the distribution pipeline — copying built database artifacts and dictionary files to target locations (file servers, class folders, deployment directories).

## Architectural Logic
"Distribution" pattern:
1. **Build:** Artifacts are assembled by `scripts/bash/` or `scripts/build/`.
2. **Distribute:** `distribute.py` copies files to configured destinations.
3. **Configuration:** Target paths are configurable for different deployment scenarios.

## Relationships & Data Flow
- **Input:** Built database files (`dpd.db`, `dpd-*.zip`) and exported artifacts.
- **Output:** Files copied to file servers, class directories, or server mounts.
- **Triggered by:** `dpd-makedict` workflow and CI/release processes.

## Interface
- `uv run python scripts/moving/distribute.py`
