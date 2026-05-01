# Plan: docs_rus Link & Asset Checker

## Architecture Decisions
- Single script in `scripts/rus_exporter/docs_check_ru.py` handles both checks.
  Rationale: both checks share the same file walk loop; splitting would duplicate setup code.
- Auto-fix only for list-item dead links (not prose inline links) to avoid silently breaking readable text.
- Image check is report-only with `sys.exit(1)`; CI will catch broken images before MkDocs build.
- CI step placed after "Populate index folders" (indexes may add links) and before "Build MkDocs site" so broken images fail fast.

---

## Phase 1 — Test fixture

- [ ] Create `tests/test_docs_check_ru.py`
  - Set up a `tmp_path` fixture with a minimal `docs_rus/` tree:
    - `index.md` containing:
      - A live `.md` list link (target file exists)
      - A dead `.md` list link (target file does NOT exist)
      - A live image ref (file exists)
      - A dead image ref (file does NOT exist)
      - An external URL image ref (should be skipped)
      - An image ref with `#only-dark` suffix (resolve without suffix)
    - Corresponding real and missing target files
  - Import `run_check` (or equivalent callable) from `scripts.rus_exporter.docs_check_ru`.
  - **Test A:** Dead list-item link is removed from file; live link preserved.
  - **Test B:** Dead image ref is returned in the broken list; live and external refs are not.
  - **Test C:** `#only-dark` suffix is stripped before path resolution.
  → verify: `uv run pytest tests/test_docs_check_ru.py -v` — all tests **fail** (script not yet written)

---

## Phase 2 — Implementation

- [ ] Create `scripts/rus_exporter/docs_check_ru.py`
  - One-sentence module docstring: purpose of the script.
  - Imports: `re`, `sys`, `Path`, `tools.printer.printer as pr`.
  - Define `DOCS_DIR = Path("docs_rus")`.
  - Define `IMG_REF_RE = re.compile(r"!\[.*?\]\(([^)]+)\)")`.
  - Define `LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+\.md(?:#[^)]*)?)\)")`.
  - `strip_fragment(path: str) -> str` — removes `#...` from path string.
  - `check_file(file_path: Path) -> list[str]`:
    - Read lines.
    - For each line: check list-item dead `.md` links → remove if dead, keep if alive.
    - Check image refs → collect broken ones.
    - Write file back only if lines changed.
    - Return list of broken image paths as `"relative/file.md: image/path.png"` strings.
  - `main() -> None`:
    - `pr.green("check docs_rus links and assets")`
    - Walk `DOCS_DIR.rglob("*.md")`.
    - Accumulate broken images.
    - Print summary with `pr.yes("ok")` or `pr.no(f"{n} broken images")` + `pr.warning` per item + `sys.exit(1)`.
  → verify: `uv run pytest tests/test_docs_check_ru.py -v` — all tests **pass**

- [ ] Run `uv run ruff check --fix scripts/rus_exporter/docs_check_ru.py && uv run ruff format scripts/rus_exporter/docs_check_ru.py`
  → verify: no errors reported

- [ ] Run script against real `docs_rus/`:
  `uv run python scripts/rus_exporter/docs_check_ru.py`
  → verify: output shows `pr.yes("ok")` or lists specific broken items; no Python exceptions

---

## Phase 3 — CI integration

- [ ] Edit `.github/workflows/ru_static.yml`
  - Add step between "Populate index folders" and "Update CSS Variables":
    ```yaml
    - name: Check docs_rus links and assets
      run: uv run python3 scripts/rus_exporter/docs_check_ru.py
    ```
  → verify: YAML is valid (load with Python yaml module — no error)
  → verify: step appears in correct position in the file (after `docs_add_indexes.py`, before `docs_update_css.py`)

---

## Phase 4 — Quality gates

- [ ] Confirm all tests pass: `uv run pytest tests/test_docs_check_ru.py -v`
- [ ] Confirm ruff clean: `uv run ruff check scripts/rus_exporter/docs_check_ru.py tests/test_docs_check_ru.py`
- [ ] Confirm script runs cleanly end-to-end on real `docs_rus/`
- [ ] Confirm workflow YAML is syntactically valid
  → verify: all checks green, no exceptions, no ruff errors
