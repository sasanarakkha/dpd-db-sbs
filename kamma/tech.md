# tech.md — DPS Fork Tech Notes

## Tools & Platforms
- **Python 3.13** — database management, exporters, GUI, webapp, MCP server
- **Go 1.22+** — performance-critical modules (compound deconstruction)
- **SQLite + SQLAlchemy** — primary database and ORM
- **Flet** — cross-platform GUI for lexicographers
- **FastAPI + Uvicorn** — webapp API
- **MCP Python SDK / FastMCP** — Model Context Protocol server
- **TypeScript + WXT + Vite** — browser extension (Chrome/Firefox)
- **uv** — Python package manager (never pip)
- **Ruff** — linter and formatter
- **ty** — type checker
- **Pytest** — testing framework
- **Typst** — PDF generation

## Who This Is For
Internal development, with occasional external contributors submitting data via the
GUI onboarding workflow.

## Constraints
- Shadow files (`*_ru.py`, `*_sbs.py`, `*_dps.py`) must maintain strict logic parity
  with upstream equivalents — no new solutions, only layered localization.
- All changes must pass `ruff check --fix` and `ruff format` before completion.
- The root directory must stay clean — no temporary scripts or artifacts.
- Releases are time-boxed to Uposatha days (~monthly).

## Resources
- Upstream repo: github.com/digitalpalidictionary/dpd-db
- Fork repo: github.com/sasanarakkha/dpd-db-sbs
- SBS recitations: github.com/sasanarakkha/pali-english-recitations
- DPD Pāḷi courses: github.com/digitalpalidictionary/dpd-pali-courses
- Study tools: github.com/sasanarakkha/study-tools

## What the output looks like
- SQLite `.db` file with all tables including `Russian` and `SBS`
- Dictionary packages: `.zip` for GoldenDict/MDict, `.mobi` for Kindle, `.kobo`, `.pdf`
- Anki `.apkg` decks exported to the study-tools repo
- A running FastAPI server and Flet GUI for interactive use
