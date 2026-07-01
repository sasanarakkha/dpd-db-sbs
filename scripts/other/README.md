# scripts/other/

## Purpose & Rationale
`scripts/other/` holds miscellaneous, uncategorized scripts that don't fit neatly into the other `scripts/` subdirectories — experimental tools, one-off analyses, and AI-assisted utilities.

## Architectural Logic
"Ad-hoc Utility" pattern:
1. **Self-contained:** Each script is independent with minimal coupling to the rest of the codebase.
2. **Single purpose:** Designed for a specific task rather than ongoing workflow integration.

## Relationships & Data Flow
- **Varies by script:** May read from `dpd.db`, call external AI APIs, or process exported data.
- **No standard pipeline:** Each script is invoked manually as needed.

## Interface
- `uv run python scripts/other/add_combined_view.py`
- `uv run python scripts/other/ai_batch_openai_meaning.py`
- `uv run python scripts/other/ai_check_russian_meanings.py`
- `uv run python scripts/other/ai_generate_translation.py`
