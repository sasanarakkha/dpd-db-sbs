# Technology Stack

## Core Technologies
- **Python (3.13):** Primary language for database management, data processing, exporters, and the modern GUI.
- **Go (1.22+):** Used for performance-critical modules where Python execution is a bottleneck.
- **SQLite:** The primary relational database for storing dictionary data.
- **Web Extensions (Manifest V3):** Built using the **WXT** framework and **Vite** for cross-browser compatibility (Chrome & Firefox) and security.
- **TypeScript:** Primary language for the browser extension, ensuring type safety and maintainability.

## System Dependencies
- **FFmpeg:** Used for audio processing tasks such as trimming and silence detection.

## Libraries and Frameworks
- **SQLAlchemy:** SQL Toolkit and Object-Relational Mapper (ORM) for Python.
- **GORM:** Object-Relational Mapper (ORM) for Go.
- **FastAPI & Uvicorn:** Modern, high-performance web framework and server for building the Webapp API.
- **Prometheus FastAPI Instrumentator:** Exposes performance and memory metrics for real-time monitoring.
- **Flet:** Framework to build interactive multi-platform apps in Python (replaces legacy PySimpleGUI).
- **MCP Python SDK & FastMCP:** Official SDK for implementing Model Context Protocol servers.

## Tooling and Infrastructure
- **Astral uv:** Fast Python package manager and resolver.
- **Ruff:** Extremely fast Python linter and code formatter.
- **ty:** Extremely fast Python type checker and language server from Astral.
- **CSS Management:** `identity/css/` is the **Single Source of Truth** for all project styles. CSS files are distributed to the Webapp, exporters, and documentation via `tools/css_manager.py`.
- **MkDocs & MkDocs Material:** Documentation generator and theme for project docs.
- **Pytest:** Testing framework for Python.
- **Typst:** New markup-based typesetting system for PDF generation.

## DPS Ecosystem
- **Fork Repository:** [dpd-db-sbs](https://github.com/sasanarakkha/dpd-db-sbs)
- **Recitations:** [pali-english-recitations](https://github.com/sasanarakkha/pali-english-recitations) (Source for SBS chanting data)
- **Courses:** [dpd-pali-courses](https://github.com/digitalpalidictionary/dpd-pali-courses) (Source for SBS class mapping)
- **Study Tools:** [study-tools](https://github.com/sasanarakkha/study-tools) (Export destination for Anki decks and class materials)

## Custom Tooling (DPS Fork)
The fork maintains extensive deviations from upstream to support Russian localization, SBS chanting data, and DPS course mapping. These are detailed in `kamma/upstream_sync/registry.json`.

### Modified Upstream Files
- **`db/models.py`:** Core schema extension adding `Russian` and `SBS` tables.

### DPS & SBS Unique Tooling
Unique files implementing the core DPS & SBS logic:
- **Exporters:** `export_dpd_sbs.py`, `main_sbs.py`, `export_epd_sbs.py`.
- **Logic:** `tools/sbs_table_functions.py`, `tools/utils_sbs.py`, `tools/paths_dps.py`.
- **GUI:** `gui2/dps_view.py` and associated `dps_*` modules in `gui2/` and `gui/`.
- **Docs:** `docs_rus/` (Russian documentation) and `mkdocs_ru.yaml`.

### Localized Shadow Copies (`*_ru.py`)
Key system components that have been "forked" within the repo to provide Russian-specific versions:
- **Exporters:** `export_dpd_ru.py`, `grammar_dict_ru.py`, `kindle_exporter_ru.py`.
- **Database:** `family_compound_ru.py`, `family_root_ru.py`, `help_abbrev_add_to_lookup_ru.py`.
- **Webapp:** `main_ru.py`, `data_classes_ru.py`.

### Unique Paths
- **`scripts/cl_dps/`:** Custom CLI workflow scripts for Mac/DPS environment.
- **`scripts/ru_exporter/` / `scripts/dps_archive/`:** Maintenance and legacy scripts.
- **`shared_data/sbs_csvs/` / `shared_data/rus/`:** Source data for localization.

## Project Management (upstream)
- **Project Board:** [DPD codebase](https://github.com/orgs/digitalpalidictionary/projects/1)

## Project Management (dps, local fork)
- **Project Board:** [DPD - SBS / Russian](https://github.com/orgs/sasanarakkha/projects/1)
