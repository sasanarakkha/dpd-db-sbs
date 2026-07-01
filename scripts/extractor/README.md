# scripts/extractor/

## Purpose & Rationale
`scripts/extractor/` provides the modular extraction pipeline for the deconstructor subsystem — parsing dictionary entries from external sources (Cone, CPD) and normalizing them into the project's internal format.

## Architectural Logic
"Modular Extraction Pipeline" pattern:
1. **Readers** (`_read_cone.py`, `_read_cpd.py`) — parse source-specific formats.
2. **Normalizers** (`_normalize.py`) — clean and standardise extracted data.
3. **Mappers** (`_pos_mapping.py`) — map external POS tags to internal ones.
4. **Loaders** (`_load_cone.py`, `_load_cpd.py`) — orchestrate reading, transforming, and persisting.
5. **Entrypoints** (`extract_cone.py`, `extract_cpd.py`) — top-level invocation.

## Relationships & Data Flow
- **Input:** Raw dictionary data from external sources in `resources/`.
- **Output:** Populates deconstructor tables in `dpd.db`.
- **AI integration:** `_ai_extraction.py` handles AI-assisted extraction via `_prompts.py`.

## Interface
- `uv run python scripts/extractor/extract_cone.py`
- `uv run python scripts/extractor/extract_cpd.py`
