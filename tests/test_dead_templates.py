"""Detect template files in local shadow dirs that have zero references in the codebase."""

from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Template directories to audit (relative to project root)
TEMPLATE_DIRS: list[Path] = [
    PROJECT_ROOT / "exporter/goldendict/ru_components/templates",
    PROJECT_ROOT / "exporter/goldendict/sbs_templates",
    PROJECT_ROOT / "exporter/webapp/ru_templates",
    PROJECT_ROOT / "exporter/webapp/sbs_templates",
]

# File extensions to search when looking for references
SEARCH_EXTENSIONS: frozenset[str] = frozenset({".py", ".jinja", ".html", ".js"})

# File extensions of templates to audit
TEMPLATE_EXTENSIONS: frozenset[str] = frozenset({".jinja", ".html"})


def collect_template_files() -> dict[str, Path]:
    """Return dict of template_name -> Path for all audited templates."""
    templates: dict[str, Path] = {}
    for d in TEMPLATE_DIRS:
        if not d.exists():
            continue
        for ext in TEMPLATE_EXTENSIONS:
            for p in d.glob(f"*{ext}"):
                templates[p.name] = p
    return templates


def collect_search_files() -> list[Path]:
    """Return all project files that can reference template names."""
    files: list[Path] = []
    # Avoid scanning too many files unnecessarily.
    # We only care about source code and other templates.
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in SEARCH_EXTENSIONS:
            continue
        # Skip __pycache__ and hidden files/dirs (.git, .venv, etc)
        if any(part.startswith(".") or part == "__pycache__" for part in path.parts):
            continue
        files.append(path)
    return files


def get_dead_templates() -> list[tuple[str, str]]:
    """
    Returns list of (template_path_relative, template_name) for templates with zero references.
    """
    templates = collect_template_files()
    if not templates:
        return []

    # Map to track found templates
    found: set[str] = set()
    search_files = collect_search_files()

    for f in search_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            # For each template name we haven't found yet, check if it's in this file
            remaining = set(templates.keys()) - found
            for name in remaining:
                # Skip self-reference
                if f.resolve() == templates[name].resolve():
                    continue
                if name in content:
                    found.add(name)

            # If we found everything, we can stop early
            if len(found) == len(templates):
                break
        except OSError:
            continue

    dead: list[tuple[str, str]] = []
    for name, path in templates.items():
        if name not in found:
            rel = str(path.relative_to(PROJECT_ROOT))
            dead.append((rel, name))

    return dead


def test_no_dead_templates() -> None:
    """
    Every template file in local shadow directories must have at least one reference
    (the filename as a string) somewhere in the codebase.

    If this test fails:
      1. Read the failing template path in the error message.
      2. Grep for the filename across the repo to confirm zero references.
      3. Delete the dead template file.
      4. Re-run this test to confirm it passes.
    """
    dead = get_dead_templates()

    if dead:
        lines = [f"  {rel} (search for '{name}')" for rel, name in dead]
        pytest.fail(
            f"Found {len(dead)} dead template(s) with zero references in the codebase:\n"
            + "\n".join(lines)
            + "\n\nDelete these files and re-run the test."
        )
