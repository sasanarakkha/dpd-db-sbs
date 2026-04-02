# Project Rules (from original upstream)

These rules are specific to the dpd-db project. Global rules (security, etc.) are in `~/.claude/CLAUDE.md`.

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

## Debugging
- Use `icecream` for debugging, not `print()`.
- Import: `from icecream import ic`
- Usage: `ic(variable_name)`

## Imports
- NEVER use `sys.path` hacks or manual directory traversal (e.g., `Path(__file__).resolve().parents[n]`) to handle absolute imports.
- Assume the script will be run from the project root or within a correctly configured environment where absolute imports work naturally.

## Dependencies

### uv
- Use astral uv to manage dependencies.
- Install with "uv add" not "pip install" or "uv pip install" etc.
- DO NOT run any scripts with uv UNLESS specifically asked to do so.

## Flet
- When answering questions about Flet refer to the /resources/flet-docs folder.


## GitHub (upstream repository)
- Unless otherwise specified the repository in question is https://github.com/digitalpalidictionary/dpd-db.
- DO NOT add or commit to GitHub, unless specifically instructed to do so.

### Commit
- Only ever commit when asked. NEVER unasked.
- "Commit" means commit the changed files using execute_command.
- Use this format, all in lowercase. #issue number area: change1, change2 . E.g. `#67 webapp: updated css, fixed overflow`
- Maximum number of characters in the first line is 72. Do not exceed that. 

### Solve
- "Solve" means read the specified GitHub issue using get_issue and offer solutions. Don't think about it, don't ask questions, just read it.
- Ask the user to open the necessary files that you need.
- Is this a straightforward solution, or does it need to be solved at a higher level?
- Show code snippets of suggested changes.


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
  - You MUST update the corresponding files in `conductor/templates/upstream_sync_rehearsal/` (specifically `dps_sync_registry.json` and `guide.md` if needed).
  - This template MUST always be kept up-to-date with the local repository state to ensure accurate upstream synchronization.

## Engineering Standards for Maintainability & Collaboration
- **Mandatory Header Descriptions**: EVERY `.py` and `.sh` file MUST start with a concise one-sentence docstring or comment explaining its purpose. This description MUST be updated if the file's primary responsibility changes.
- **Surgical Logic Layering**: When modifying shadow copies, avoid rewriting core logic. Layer localized changes (RU/SBS) clearly on top of the original upstream structure to ensure easy synchronization.
- **Namespace Isolation**: Always use specific prefixes (`ru_`, `sbs_`, `dps_`) for localized functions, variables, and IDs to prevent collisions in shared environments like GoldenDict.
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
- Orphaned files STILL in use must be either re-mapped in `dps_sync_registry.json` (if source moved) or promoted to `unique_paths` (if source deleted but local logic requires it).
- All temporary artifacts created during a session MUST be purged before finalization.