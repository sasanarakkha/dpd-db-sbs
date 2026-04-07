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

Key SQLAlchemy classes and their roles:

| Class | Table | Purpose |
|---|---|---|
| `DpdHeadword` | `dpd_headwords` | Main dictionary entries — ~60 columns + many `@cached_property` helpers |
| `DpdRoot` | `dpd_roots` | Pāḷi verbal roots |
| `Lookup` | `lookup` | Fast lookup index — every inflected form → headword IDs |
| `SuttaInfo` | `sutta_info` | Sutta metadata (SC, CST, BJT links) |
| `InflectionTemplates` | `inflection_templates` | Stem/ending grids used to generate inflection tables |
| `FamilyRoot` | `family_root` | Root family groupings with HTML |
| `FamilyWord` | `family_word` | Word family groupings |
| `FamilyCompound` | `family_compound` | Compound family groupings |
| `FamilyIdiom` | `family_idiom` | Idiom groupings |
| `FamilySet` | `family_set` | Thematic set groupings |
| `BoldDefinition` | `bold_definitions` | Bold-text definitions extracted from commentaries |
| `DbInfo` | `db_info` | Key-value store for metadata and cached sets |

**`DpdHeadword` relationships:** `.rt` → `DpdRoot`, `.fr` → `FamilyRoot`, `.fw` → `FamilyWord`, `.it` → `InflectionTemplates`, `.su` → `SuttaInfo`

**JSON pack/unpack pattern:** Many string columns store JSON. Access via `foo_pack(list)` / `foo_unpack` property (e.g. `headwords_pack`, `headwords_unpack` on `Lookup`).

**Key `DpdHeadword` columns:** `id`, `lemma_1` (unique headword), `pos`, `meaning_1`, `root_key`, `family_root`, `family_compound`, `stem`, `pattern`, `inflections`, `inflections_html`, `construction`

Full column docs: `docs/technical/dpd_headwords_table.md` | Full model: `db/models.py`

---

## Tools/printer.py
This module provides colored console output with timing and TSV logging.

### Import
```python
from tools.printer import printer as pr
```

### Usage

#### Timer Methods
- `pr.tic()` - Start the main clock (class method)
- `pr.toc()` - Stop the main clock and print elapsed time (class method)
- `pr.bip()` - Start a mini clock for the current operation
- `pr.bop()` - End mini clock and return elapsed time as string
- `pr.print_bop()` - Print the elapsed time right-aligned

#### Output Methods (need ending)
These methods do NOT print a newline - follow with `pr.yes()` or `pr.no()`:
- `pr.green(message)` - Print left-aligned green message and start timer
- `pr.cyan(message)` - Print left-aligned cyan message and start timer
- `pr.white(message)` - Print indented white message and start timer

#### Output Methods (complete line)
These methods complete a line started by green/cyan/white:
- `pr.yes(message)` - Print right-aligned blue message with timing (max 8 chars)
- `pr.no(message)` - Print right-aligned red message with timing (max 8 chars)

#### Output Methods (standalone - return)
These methods print and return (no ending needed):
- `pr.title(text)` - Print bright yellow title and start timer
- `pr.green_title(message)` - Print green title and start timer
- `pr.counter(counter, total, word)` - Print progress counter with timing
- `pr.summary(key, value)` - Print key-value summary in green
- `pr.red(message)` - Print red message
- `pr.amber(message)` - Print amber message

#### Logging
- If initialized with a log file path, all operations are logged to TSV format
- Log includes: timestamp, level, operation, type, message, elapsed time, count, session


# Localized Rules (local fork)

## Project Overview

This is a fork of the Digital Pāli Dictionary (DPD) database repository. The primary purpose of this fork is to serve as the central development and synchronization hub for the Russian (RU) and SBS localized versions and additions to the DPD database.

## Local additions to DPD Database Model (`db/models.py`)

Key additional SQLAlchemy classes and their roles:

| Class | Table | Purpose |
|---|---|---|
| `SBS` | `sbs` | Data relevant to the SBS study tools build upon dpd_db |
| `Russian` | `russian` | Russian translation of the english columns from dpd_headwords |
| `Sinhala` | `sinhala` | Sinhala translation of the english columns from dpd_headwords |

Existing tables which has additional columns:

| Class | Table | columns added |
|---|---|---|
| `DpdRoot` | `dpd_roots` | root_ru_meaning ; sanskrit_root_ru_meaning |
| `FamilyRoot` | `family_root` | root_ru_meaning ; html_ru ; data_ru |
| `FamilyWord` | `family_word` | html_ru ; data_ru |
| `FamilyCompound` | `family_compound` | html_ru ; data_ru |
| `FamilyIdiom` | `family_idiom` | html_ru ; data_ru |
| `FamilySet` | `family_set` | html_ru ; data_ru ; set_ru |


**`DpdHeadword` additional relationships:** `.ru` → `Russian`, `.sbs` → `SBS`

## Use Path from Pathlib
- For local development, use Path for anything related to filepaths, not os. Use files: tools/paths_ru.py ; tools/paths_dps.py

## GitHub Issue Reference Mapping
- When mentioning "local issue #", refer to the issues at https://github.com/sasanarakkha/dpd-db-sbs.

## Shadow Files & Sync Templates
- If you perform any task which creates or modifies any "shadow" (`*_ru.py`, `*_sbs.py`, `*_dps.py`) or "unique" files (files that exist only in this fork):
  - You MUST update the corresponding files in `kamma/upstream_sync/` (specifically `registry.json` and `guide.md` if needed).
  - This registry MUST always be kept up-to-date with the local repository state to ensure accurate upstream synchronization.

## Engineering Standards for Maintainability & Collaboration
- **Surgical Logic Layering**: When modifying shadow copies, avoid rewriting core logic. Layer localized changes (RU/SBS) clearly on top of the original upstream structure to ensure easy synchronization.
- **Namespace Isolation**: Apply locale markers to Python functions and HTML IDs in shadow files using the three-tier convention:
    - **Tier 1 — Identical copy from upstream**: No locale marker. Keep the upstream function name exactly. Signal: safe to overwrite during sync.
    - **Tier 2 — Modified from upstream**: Add locale suffix only (`_ru`, `_sbs`, or `_dps`). The suffix matches the file's locale. Signal: check upstream diff before syncing.
    - **Tier 3 — New (no upstream counterpart)**: Use a descriptive name. Add locale suffix if the locale is not already clear from the name. A `ru_` prefix is only appropriate when a suffix would be genuinely ambiguous.
    - **Never double-mark**: a function must not have both a locale prefix and a locale suffix (e.g. `ru_func_name_ru()` is wrong).
    - **HTML IDs**: Always prefix with locale (`ru_`, `sbs_`, `dps_`) — HTML IDs share the DOM and collision is real regardless of tier.
- **Clean Codebase**:
    - Prefer modular abstractions over threading state across layers.
    - Keep imports clean and remove unused dependencies immediately.
    - Use modern type hints and pathlib for all file operations.

## Clean Root Folder Protocol
- The root directory MUST remain free of temporary scripts, logs, and artifacts.
- During any 'Sync' or 'Cleanup' phase, the agent MUST run `tests/test_shadow_cleanup.py` to identify orphaned files.
- Orphaned files NOT in use must be ARCHIVED:
    - Scripts go to `scripts/dps_archive/`.
    - Other files go to `archive/dps/`.
- Orphaned files STILL in use must be either re-mapped in `kamma/upstream_sync/registry.json` (if source moved) or promoted to `unique_paths` (if source deleted but local logic requires it).
- All temporary artifacts created during a session MUST be purged before finalization.

## Atomic Rename Protocol
A file or directory rename/move is an atomic operation that is NOT complete until all references are updated.
- **Mandatory Search**: Whenever you rename a file, you MUST immediately use `grep_search` to find all occurrences of the old filename and path throughout the repository.
- **Scope of Updates**: You are responsible for updating:
    - Language-specific imports (Python, TypeScript, Go).
    - Hardcoded paths in bash scripts, python scripts, and `justfile`.
    - GitHub Actions workflows (`.github/workflows/`).
    - Registry files (`kamma/upstream_sync/registry.json`).
    - Documentation references in `docs/` and `README.md`.
- **Validation**: You MUST run a verification search after your edits to confirm that zero references to the old name remain in tracked files.

## Project Principles
- **Strict Upstream Logic Parity:** For all shadow copies (localized Russian or SBS versions), you MUST maintain strict logic parity with the original upstream source files. When fixing bugs or implementing updates in shadow copies, DO NOT introduce new solutions. Instead, refer back to the original source as the absolute authority and emulate its implementation exactly, only layering localized data or UI updates on top.
- **Template Standards**:
    - **Syntax**: Use standard Jinja2 syntax (`{{ var }}`, `{% if %}`, `{% for %}`).
    - **Legacy Removal**: Legacy Mako-style syntax (`${var}`, `% if`, `% for`) is strictly prohibited in localized templates.
- **The Tech Stack is Deliberate:** Changes to the tech stack must be documented in `tech-stack.md` *before* implementation
- **Data Output Verification:** Write tests to verify accurate data output. Automated tests are NOT required for UI elements, CSS, or HTML, as these are best verified and tweaked by a human. Do not test UI components - user interaction will reveal UI issues. Do not test internal function implementation details.
- **User Experience First:** Every decision should prioritize user experience
- **README Maintenance:** Each project folder contains a `README.md`, which MUST be updated if anything within the folder changes to ensure documentation stays in sync with code.
- **Documentation is Mandatory:** Once a task is finished and approved by the user, the `docs/` folder MUST be updated with all relevant changes. This is not optional.
- **Code Quality is Mandatory:** All changed files MUST pass `uv run ruff check --fix` and `uv run ruff format` before task completion. This is not optional.
- **Proactive Research:** Always perform a Google Search during the planning and task execution phases for any framework-specific (e.g., Flet), OS-specific (e.g., Linux window management), or non-trivial technical requirements to identify known quirks, limitations, or best practices.
- **Focused Exporter Tracking:** During synchronization, only track and update exporters that contain localized data (Russian, SBS, or DPS-specific). Ignore changes to upstream exporters that have no localized counterparts or relevance to localized data. Maintain a list of relevant exporters in the sync registry.
