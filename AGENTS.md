# Project Rules (from original upstream)

These rules are specific to the dpd-db project. Global rules (security, etc.) are in `~/agents/AGENTS.md`.

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

## Shadow Files & Sync Templates
- "Shadow" (`*_ru.py`, `*_sbs.py`, `*_dps.py`) or "unique" files MUST have corresponding registry entries in `kamma/upstream_sync/` (specifically `registry.json` and `guide.md`). This registry MUST always be kept up-to-date.

## Engineering Standards
- **Surgical Logic Layering**: Avoid rewriting core logic in shadow copies. Layer localized changes (RU/SBS) clearly on top of the original structure for easy sync.
- **Namespace Isolation**:
  - **Tier 1 (Upstream copy)**: Exact upstream name, NO markers.
  - **Tier 2 (Shadow copy) / Tier 3 (New)**: Add a single locale suffix (`_ru`, `_sbs`). In mixed `*_dps.py` files, use `_dps` ONLY for logic shared by both, or non of them.
  - **No Double-Marking**: Never add a suffix if the name already has an intrinsic marker (e.g., `RPD`, `Ru`). Never use both a prefix and a suffix.
  - **HTML IDs**: Always prefix with `ru_`, `sbs_`, or `dps_`.
- **Clean Codebase**: Prefer modular abstractions. Use modern type hints and pathlib. Remove unused dependencies.

## Clean Root Folder Protocol
- The root directory MUST remain free of temporary scripts, logs, and artifacts.
- Run `tests/test_shadow_cleanup.py` during Sync/Cleanup to identify orphaned files. Archive unused scripts to `scripts/dps_archive/` and others to `archive/dps/`.
- Re-map or promote STILL IN USE orphans in `kamma/upstream_sync/registry.json`.

## Atomic Rename Protocol
Renames/moves are atomic. You MUST:
1. `grep_search` the old name across the entire repository.
2. Update all imports, hardcoded paths, scripts, workflows, registries (`kamma/upstream_sync/registry.json`), and docs.
3. Run a final verification search to empirically prove zero stale references remain.

## Project Principles
- **Docs Sanctity:** `docs/` is upstream-only. Put local docs in `docs_rus/` or `kamma/`.
- **Strict Parity:** For shadow copies, maintain strict logic parity with upstream. DO NOT introduce new solutions. Emulate upstream implementation exactly, only layering localized UI/data on top.
- **Templates:** Use standard Jinja2 (`{{ var }}`, `{% if %}`). Legacy Mako syntax (`${var}`, `% if`) is STRICTLY prohibited in localized templates.
- **Changes:** Must document tech stack changes in `kamma/tech.md` before implementation. Code changes must pass `uv run ruff check --fix` and `uv run ruff format`.
- **Verification:** Write tests for accurate data output (not UI components). Readme MUST be updated.
- **Research:** Always perform Google Search for framework/OS quirks.
- **Sync Tracking:** Only track and update exporters in the sync registry that contain localized data (Russian, SBS, or DPS-specific).
