# Spec: docs_rus Link & Asset Checker

## Overview
A combined script (`scripts/rus_exporter/docs_check_ru.py`) that:
1. **Auto-fixes** dead internal `.md` links that appear as list items — removes the entire line.
2. **Reports** broken local image references (`.png`, `.jpg`, `.svg`, `.gif`) and exits with code 1 if any found.

Integrated as a CI step in `.github/workflows/ru_static.yml` before the MkDocs build.

## What it should do

### Internal link check (auto-fix)
- Scan all `*.md` files in `docs_rus/` recursively.
- Find list items of the form `- [text](target.md)` or `- [text](target.md#anchor)`.
- Resolve the path relative to the containing file.
- If the target `.md` file does not exist on disk → remove the line.
- Count and report fixed lines.

### Image asset check (report only)
- Find all `![alt](path)` references in the same files.
- Skip `http://` and `https://` URLs.
- Resolve local paths relative to the containing file.
- Strip MkDocs-style suffixes (`#only-dark`, `#only-light`, other `#anchor` fragments) before resolving.
- If the resolved path does not exist → record as broken.
- At the end: print all broken paths and exit 1 if any exist.

### Output style
- `pr.green("check docs_rus links and assets")`
- Per fix: `pr.warning(f"removed dead link: {file}: {line.strip()}")`
- On success: `pr.yes("ok")`
- On broken images: `pr.no(f"{n} broken images")` + `pr.warning(f)` per item, then `sys.exit(1)`

## Affected files
- **New:** `scripts/rus_exporter/docs_check_ru.py`
- **New:** `tests/test_docs_check_ru.py`
- **Modified:** `.github/workflows/ru_static.yml` — add step after "Populate index folders"

## Assumptions & uncertainties
- MkDocs `#only-dark` / `#only-light` suffixes must be stripped from image paths before existence check.
- Only list items (`- `) are auto-removed for dead links; inline links elsewhere are reported-only (no destructive removal of prose).
- Non-`.md` link targets (e.g., `#anchor`-only, external URLs) are skipped.
- Script runs from project root (`docs_rus/` is at `./docs_rus/`).

## Constraints
- Follows `scripts/rus_exporter/` naming convention (parallel to `docs_add_indexes.py`).
- No `sys.path` hacks; runs via `uv run python`.
- Must pass `ruff check --fix` and `ruff format`.
- No inline `python -c` usage.

## How we'll know it's done
- Script runs locally: auto-removes dead link lines, reports broken images.
- Tests pass: `uv run pytest tests/test_docs_check_ru.py -v`.
- CI step in `ru_static.yml` runs without error on a clean `docs_rus/`.
- CI fails if a broken image ref is introduced.

## What's not included
- Checking external URLs (HTTP liveness checks).
- Checking non-list-item prose links (reported if broken, not auto-removed).
- Checking links in `docs/` (upstream-only, not in scope).
