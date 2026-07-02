# tech.md — DPS Fork Tech Notes

## Tools & Platforms
- **Python 3.13** — database management, exporters, analysis pipeline, GUI, webapp, MCP server
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
- **antigravity-cli (agy)** — AI model transport provider for the analysis pipeline (uses stdin transport).

## Who This Is For
Internal development, with occasional external contributors submitting data via the
GUI onboarding workflow.

## Constraints
- **Strict Shadow Parity**: Files in the `strict_shadow` category (`registry.json`) must maintain strict logic parity with upstream equivalents. No new solutions, only layered localization.
- **Namespace Isolation**: Follow the three-tier naming convention for all localized shadow copies:
    - **Tier 1 (Identical)**: Unmarked names (upstream parity).
    - **Tier 2 (Modified)**: Mandatory locale suffix (`_ru`, `_sbs`, `_dps`, `_ta`).
    - **Tier 3 (New)**: Mandatory locale suffix.
    - **HTML IDs**: Always use a locale prefix (`ru_`, `sbs_`, `dps_`, `ta_`).
- **Inspired-by Files**: Files in the `inspired_by_upstream` category may diverge from upstream structure but must document the `divergence_reason` in the registry and document any local changes/watch items in the registry entry.
- **Upstream Sync Workflow**: All sync operations MUST follow the 4-stage workflow (plus the async Docs Translation Track) defined in `kamma/upstream_sync/guide.md`. Stage 1, Stage 3 batches, and Docs Track translation are dispatched to the `sync-fast` subagent (`.claude/agents/sync-fast.md`) as the execution spine, with context-overflow handoffs kept minimal. The async Docs Translation Track ensures `docs_rus/` stays in sync with `docs/` using the `check_docs_parity.py` tool.
- All changes must pass `ruff check --fix` and `ruff format` before completion.
- The root directory must stay clean. Never write temporary scripts, logs,
  probes, transcripts, dumps, generated reports, fixtures, or test output files
  to the repository root.
- All temporary or scratch artifacts belong under `temp/`. `temp/` is
  disposable trashcan storage: delete temporary files once they have fulfilled
  their purpose. Anything that must survive belongs in an appropriate tracked
  source, test, `kamma/threads/*`, or documentation file instead.
- All tests belong under `tests/` or an existing nested test package inside
  `tests/`.
- **Atomic Rename Protocol**: Renames/moves are atomic. All imports, paths, scripts, registries, and docs MUST be updated and staged in the same commit as the `git mv`.
- **Mandatory UI Tooling**: All Python scripts MUST use `tools.printer` (`pr`) for console output (UI, status, timing) instead of standard `print()`. Use `pr.tic()` / `pr.toc()` for script-level timing and `pr.bip()` / `pr.yes()` etc. for step-level timing. Standard `print()` is only allowed for outputting structured data intended for piping or when explicitly marked as debug (e.g., using `icecream`).
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
