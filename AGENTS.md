# Project Rules (from original upstream)

Apply these in addition to your baseline global instructions `~/.claude/CLAUDE.md`.

## Project Overview

Digital Pali Dictionary.

## Python Type Hints
- Please add type hints to all code, especially when it is missing in existing code.
- Use modern type hints not old type hints
  - Use `dict[str, str]` not `Dict[str, str]`
  - Use `tuple[str, str]` not `Tuple[str, str]`
  - Use `list[str]` not `List[str]`
  - Use `| None` not Optional[None]

## Use Path from Pathlib
- Use Path for anything related to filepaths, not os.

## Flet
- When answering questions about Flet refer to the /resources/flet-docs folder.

## Context7
Use Context7 MCP (`mcp__plugin_context7_context7__resolve-library-id` + `query-docs`) for up-to-date docs on project libraries:
- `SQLAlchemy` — ORM, sessions, queries, relationships
- `Flet` — GUI widgets and layout
- `FastAPI` — webapp routes and middleware (`exporter/webapp/`)
- `aksharamukha` — transliteration script names and options
- `requests` — HTTP client usage

## GitHub (upstream repository)
- Unless otherwise specified the repository in question is https://github.com/digitalpalidictionary/dpd-db.
- **Solve:** Read the specified GitHub issue using `get_issue` and offer solutions. Show code snippets of suggested changes.

## DPD Database Model (`db/models.py`)
Key models include `DpdHeadword` (main entries), `DpdRoot`, `Lookup`, and `Family*` groupings. 
**`DpdHeadword` relationships:** `.rt` → `DpdRoot`, `.fr` → `FamilyRoot`, `.fw` → `FamilyWord`, `.it` → `InflectionTemplates`, `.su` → `SuttaInfo`
For full table & column documentation, you MUST read `docs/technical/dpd_headwords_table.md`.
**JSON pack/unpack:** Many string columns store JSON. Access via `foo_pack(list)` / `foo_unpack` property.

---

## Tools/printer.py
Use `from tools.printer import printer as pr` for colored terminal output and timing. See `tools/printer.py` for the full API. If initialized with a log file path, operations log to TSV.
- Use `icecream` (`from icecream import ic`) for debug output, not `print()`.

# Localized Rules (local fork)

## Project Overview
Fork of the Digital Pāli Dictionary (DPD) database repository serving as the central development and synchronization hub for Russian (RU) and SBS localized versions.

## Local additions to DPD Database Model
Key additions: `SBS` (SBS study tools data), `Russian` (Russian translations), `Sinhala` (Sinhala translations).
Existing tables have extra `*_ru` columns (e.g., `root_ru_meaning`, `html_ru`). 
**`DpdHeadword` additional relationships:** `.ru` → `Russian`, `.sbs` → `SBS`

## Use Path from Pathlib
- For local development, use Path for anything related to filepaths, not os. Use files: `tools/paths_ru.py` ; `tools/paths_dps.py`

## GitHub Issue Reference Mapping
- "local issue #" refers to https://github.com/sasanarakkha/dpd-db-sbs.

## Local Commit Exception
- Only human-run Bash scripts under `scripts/cl_dps/` may perform their own `git commit` operations, and only for narrowly scoped local automation explicitly documented by that script.
- Agents MUST NOT run `git commit` directly and MUST NOT add autonomous commit behavior to Python scripts or scripts outside `scripts/cl_dps/`.

## Shadow Files & Sync Templates
- "Shadow" (`*_ru.py`, `*_sbs.py`, `*_dps.py`, `*_ta.py`) or "unique" files MUST have corresponding sync documentation in `kamma/upstream_sync/`.
- **Shadow Documentation Gate:** Any new, renamed, moved, or reclassified shadow/local copy MUST update registry.json and the matching `kamma/upstream_sync/smd/*.md` entry in the same change. Do not report the work complete until `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` and `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` pass.
- **Single Category Rule:** one local path may appear in exactly one registry category. Use `russian_copies` only for Russian-only shadows, `sbs_copies` only for SBS-only shadows, `tamil_copies` only for Tamil-only shadows, and `dps_copies` for mixed/shared RU/SBS/Tamil/DPS fork shadows or local upstream shadows that do not belong cleanly to one locale.
- The SMD `Category` line MUST exactly match the `registry.json` category. Do not rely on memory or chat context; update the registry and SMD while making the code change.

## Engineering Standards
- **Request Scope Discipline:** Only implement the change explicitly requested by the user. Do not make adjacent improvements, cleanups, restorations, formatting changes, or "while here" fixes unless the user asked for them. If an unrequested change seems useful, necessary, or safer, stop and ask before implementing it.
- **Surgical Logic Layering**: Avoid rewriting core logic in shadow copies. Layer localized changes (RU/SBS) clearly on top of the original structure for easy sync.
- **Namespace Isolation**:
  - **Tier 1 (Upstream copy)**: Exact upstream name, NO markers.
  - **Tier 2 (Shadow copy) / Tier 3 (New)**: Add a single locale suffix (`_ru`, `_sbs`, `-ru`, `-sbs`). In mixed `*_dps.py` files, use `_dps` or `-dps` ONLY for logic shared by both, or non of them.
  - **No Double-Marking**: Never add a suffix if the name already has an intrinsic marker (e.g., `RPD`, `Ru`). Never use both a prefix and a suffix.
  - **HTML IDs**: Always prefix with `ru_`, `sbs_`, or `dps_`.
- **Clean Codebase**: Prefer modular abstractions. Use modern type hints and pathlib. Remove unused dependencies.
- **No Inline Scripting**: NEVER use `python -c "..."` or `python3 -c "..."` in Bash. If you need a one-shot script, write it to `temp/<descriptive_name>.py` and run `uv run python temp/<descriptive_name>.py`. Delete the file when done. This rule exists because inline scripts are invisible in code review, cannot be re-run, and cannot be linted.
- **UI Migrations**: When migrating UI or logging (e.g., to `printer.py`), perform a "runtime sweep" to catch undefined variables (`NameError`) in callbacks or rarely-triggered code paths.

## Clean Root Folder Protocol
- The root directory MUST remain free of temporary scripts, logs, and artifacts.
- Run `tests/test_shadow_cleanup.py` during Sync/Cleanup to identify orphaned files. Archive unused scripts to `scripts/dps_archive/` and others to `archive/dps/`.
- Re-map or promote STILL IN USE orphans in `kamma/upstream_sync/registry.json`.

## Atomic Rename Protocol
Renames/moves are atomic. You MUST:
1. `grep_search` the old name across the entire repository.
2. Update all imports, hardcoded paths, scripts, workflows, registries (`kamma/upstream_sync/registry.json`), and docs.
3. Run a final verification search to empirically prove zero stale references remain.
4. Stage `registry.json` and all affected `kamma/upstream_sync/smd/*.md` files **in the same commit** as the `git mv`. Never let a rename land in git while its registry/SMD documentation is still in the working tree.

## Economy & Cost Management
- NEVER re-run batch LLM processing for trivial changes like filename dates or field labels. Use local text manipulation (e.g., regex, rename) instead.

## Project Principles
- **Docs Sanctity:** `docs/` is upstream-only. Put local docs in `docs_rus/` or `kamma/`. Use relative symlinks (e.g., `docs_rus/changelog.md` -> `../docs/changelog.md`) for files in `docs/` that do not require translation. This ensures permanent parity for "no-translate" content.
- **Strict Parity:** For shadow copies, maintain strict logic parity with upstream. DO NOT introduce new solutions. Emulate upstream implementation exactly, only layering localized UI/data on top.
- **Templates:** Use standard Jinja2 (`{{ var }}`, `{% if %}`). Legacy Mako syntax (`${var}`, `% if`) is STRICTLY prohibited in localized templates.
- **Changes:** Must document tech stack changes in `kamma/tech.md` before implementation. Code changes must pass `uv run ruff check --fix` and `uv run ruff format`.

## Pre-Completion Validation (MANDATORY)

**Before reporting ANY Python code changes as complete, run ALL of:**

1. `uv run ruff check --fix <file>`
2. `uv run ruff format <file>`
3. `uv run pyright <file>`
4. `uv run --with pyrefly pyrefly check --min-severity warn <file>`
5. `uv run pytest tests/test_<feature>.py -v` (for affected tests)

**Do NOT report completion until all checks pass.** This is non-negotiable. Do not skip or defer these. Pyrefly warnings count as failures unless explicitly approved by the user. Type safety is mandatory, not optional.
- **Verification:** Write tests for accurate data output (not UI components). Readme MUST be updated.
- **Research:** Always perform Google Search for framework/OS quirks.
- **Sync Tracking:** Only track and update exporters in the sync registry that contain localized data (Russian, SBS, or DPS-specific).
