"""Checks localized templates for legacy Mako syntax and Jinja2 formatting violations."""

import re
import pytest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]

_LOCALIZED_TEMPLATE_DIRS = [
    "exporter/webapp/ru_templates",
    "exporter/webapp/sbs_templates",
    "exporter/goldendict/sbs_templates",
    "exporter/goldendict/ru_components/templates",
    "exporter/kindle/ru_components/templates",
]


def get_template_files() -> list[str]:
    files: list[str] = []
    for rel in _LOCALIZED_TEMPLATE_DIRS:
        d = _PROJECT_ROOT / rel
        if d.exists():
            files.extend(
                str(f)
                for f in d.rglob("*")
                if f.suffix in (".html", ".jinja", ".jinja2")
            )
    return sorted(set(files))


@pytest.mark.parametrize("filepath", get_template_files())
def test_no_mako_syntax(filepath: str) -> None:
    """Template must not contain legacy Mako syntax.

    Checks for:
    - ${...} variable substitution (Mako style)
    - Line-level % if / % for / % end control tags (Mako style)

    Note: patterns are anchored to avoid false positives inside Jinja2 {% if %} tags.
    """
    p = Path(filepath)
    if not p.exists():
        pytest.skip(f"File not found: {filepath}")
    content = p.read_text(encoding="utf-8")
    violations: list[str] = []
    for i, line in enumerate(content.splitlines(), 1):
        if re.search(r"\$\{", line):
            violations.append(
                f"  line {i}: Mako variable substitution: {line.strip()!r}"
            )
        if re.match(r"^\s*%\s+(if|for|end)", line):
            violations.append(f"  line {i}: Mako control tag: {line.strip()!r}")
    if violations:
        pytest.fail(
            f"{filepath}: contains legacy Mako syntax:\n" + "\n".join(violations)
        )


@pytest.mark.parametrize("filepath", get_template_files())
def test_no_spacing_violation(filepath: str) -> None:
    """Jinja2 block tags must have a space after {%  (e.g. {% if %} not {%if %})."""
    p = Path(filepath)
    if not p.exists():
        pytest.skip(f"File not found: {filepath}")
    content = p.read_text(encoding="utf-8")
    bad_lines = [
        i + 1
        for i, line in enumerate(content.splitlines())
        if re.search(r"\{%[a-zA-Z]", line)
    ]
    if bad_lines:
        pytest.fail(f"{filepath}: missing space after {{%}} on lines: {bad_lines}")
