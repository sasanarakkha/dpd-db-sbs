"""Verify every pr.X() call in the codebase has a matching method on Printer."""

import ast
import re
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRINTER_PATH = PROJECT_ROOT / "tools/printer.py"

# Directories to scan for pr.X() usage
SCAN_DIRS: list[Path] = [
    PROJECT_ROOT / "exporter",
    PROJECT_ROOT / "scripts",
    PROJECT_ROOT / "tools",
    PROJECT_ROOT / "db",
    PROJECT_ROOT / "gui2",
    PROJECT_ROOT / "tests",
]

# Regex: matches pr.method_name( — word boundary ensures no false matches like expr.pr.x
PR_CALL_PATTERN = re.compile(r"\bpr\.([a-z_]+)\(")


def extract_printer_methods() -> set[str]:
    """
    Parse tools/printer.py with AST and return all method names defined
    inside the Printer class body.
    """
    if not PRINTER_PATH.exists():
        pytest.skip("tools/printer.py not found")

    tree = ast.parse(
        PRINTER_PATH.read_text(encoding="utf-8"), filename=str(PRINTER_PATH)
    )

    methods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Printer":
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.add(item.name)
    return methods


def collect_pr_calls() -> dict[str, set[str]]:
    """
    Scan all .py files in SCAN_DIRS for pr.X() calls.
    Returns a dict: method_name -> set of file paths that call it.
    """
    calls: dict[str, set[str]] = {}

    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            continue
        for py_file in scan_dir.rglob("*.py"):
            # Skip __pycache__ and this test file
            if (
                "__pycache__" in py_file.parts
                or py_file.name == "test_printer_method_coverage.py"
            ):
                continue
            try:
                text = py_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for match in PR_CALL_PATTERN.finditer(text):
                method = match.group(1)
                calls.setdefault(method, set()).add(
                    str(py_file.relative_to(PROJECT_ROOT))
                )

    return calls


def test_all_pr_calls_have_printer_methods() -> None:
    """
    Every pr.X() call found in the codebase must correspond to a real method
    defined on the Printer class in tools/printer.py.

    If this test fails:
      Option A — The method is genuinely missing from Printer: add it.
      Option B — The call is a bug (wrong method name): fix the call site.

    Never add the method name to an exceptions list. The test exists precisely
    to force resolution of missing methods before they cause runtime errors.
    """
    printer_methods = extract_printer_methods()
    pr_calls = collect_pr_calls()

    errors: list[str] = []
    for method, callers in sorted(pr_calls.items()):
        if method not in printer_methods:
            caller_list = "\n".join(f"      {f}" for f in sorted(callers))
            errors.append(
                f"  pr.{method}() — method does not exist on Printer\n"
                f"    Called from:\n{caller_list}"
            )

    assert errors == [], (
        f"Found {len(errors)} pr.X() call(s) with no matching Printer method.\n"
        "Add the missing method(s) to tools/printer.py, or fix the call sites.\n\n"
        + "\n".join(errors)
    )
