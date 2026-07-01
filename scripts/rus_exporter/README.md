# scripts/rus_exporter/

## Purpose & Rationale
`scripts/rus_exporter/` provides Russian-specific export and distribution utilities — packaging GoldenDict/MDict dictionaries for the RU localized variant, checking download indexes, and managing documentation indexes.

## Architectural Logic
"Localized Export" pattern:
1. **Build:** Assembles Russian-specific export artifacts from `dpd.db`.
2. **Package:** Zips GoldenDict/MDict packages with Russian content.
3. **Verify:** Checks download indexes and documentation for completeness.

## Relationships & Data Flow
- **Input:** Reads Russian localization data from `dpd.db` (Russian model).
- **Output:** Exported archive files (`dpd-ru-*.zip`) and updated documentation indexes.
- **Triggered by:** Release workflow or manual invocation.

## Interface
- `uv run python scripts/rus_exporter/ru_zip_goldendict_mdict.py`
- `uv run python scripts/rus_exporter/zip_dpd.py`
- `uv run python scripts/rus_exporter/docs_add_indexes.py`
- `uv run python scripts/rus_exporter/docs_check_ru.py`
- `uv run python scripts/rus_exporter/check_tpr_download_index.py`
- `uv run python scripts/rus_exporter/set_config.py`
