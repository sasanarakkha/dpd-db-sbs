"""Gather facts about a target script and output compact JSON. Zero LLM cost."""

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REGISTRY_PATH = REPO_ROOT / "kamma" / "upstream_sync" / "registry.json"


def _relative_path(file_path: Path) -> Path:
    return file_path.resolve().relative_to(REPO_ROOT)


def _extract_docstring(file_path: Path) -> str:
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        return ast.get_docstring(tree) or ""
    except (SyntaxError, OSError):
        return ""


def _count_lines(file_path: Path) -> int:
    try:
        return len(file_path.read_text(encoding="utf-8").splitlines())
    except OSError:
        return 0


def _find_callers(file_path: Path) -> list[str]:
    """Search for importers/callers of the given module within the repo.

    Covers both Python imports (from X import / import X) and bare-path
    invocations (shell scripts, subprocess calls, CI configs, Makefiles, etc.).
    """
    rel = str(_relative_path(file_path))
    stem = file_path.stem
    import_pattern = rf"(?:from\s+[\w.]*{re.escape(stem)}\s+import|import\s+[\w.]*{re.escape(stem)}\b)"
    path_pattern = rf"\b{re.escape(file_path.name)}\b|{re.escape(rel)}"
    callers: set[str] = set()
    try:
        for pattern in (import_pattern, path_pattern):
            result = subprocess.run(
                ["rg", "--no-heading", "--hidden", "-l", pattern, "-g", "!*.db"],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                timeout=15,
                check=False,
            )
            if result.returncode in (0, 1) and result.stdout.strip():
                callers.update(result.stdout.strip().split("\n"))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    callers.discard(str(_relative_path(file_path)))
    callers.discard(str(file_path))
    callers = {c for c in callers if not c.startswith("kamma/")}
    return sorted(callers)


def _imports_from_repo(file_path: Path) -> list[str]:
    """List local modules imported by the file that exist in this repo."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            if module is not None:
                imports.append(module.split(".")[0])
    return sorted(set(imports))


def _check_registry(file_path: Path) -> dict[str, str | bool]:
    """Check registry.json for this file; return category and membership."""
    rel = str(_relative_path(file_path))
    try:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"in_registry": False, "registry_category": ""}

    for category, entries in registry.items():
        if isinstance(entries, list):
            for entry in entries:
                entry_path = entry if isinstance(entry, str) else entry.get("path", "")
                if entry_path == rel:
                    return {"in_registry": True, "registry_category": category}
        elif isinstance(entries, dict):
            for value in entries.values():
                entry_path = value if isinstance(value, str) else value.get("path", "")
                if entry_path == rel:
                    return {"in_registry": True, "registry_category": category}
    return {"in_registry": False, "registry_category": ""}


def _check_test(file_path: Path) -> bool:
    """Check if a corresponding test file exists under tests/."""
    rel_path = _relative_path(file_path)
    stem = file_path.stem
    test_dir = REPO_ROOT / "tests" / rel_path.parent
    candidates = [
        test_dir / f"test_{stem}.py",
        REPO_ROOT / "tests" / f"test_{stem}.py",
    ]
    return any(c.exists() for c in candidates)


def _has_entrypoint(file_path: Path) -> bool:
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and (
                isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__"
            )
        ):
            return True
    return False


def main() -> None:
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: archive_check.py <file_path>"}))
        sys.exit(1)

    file_rel = sys.argv[1]
    file_path = (REPO_ROOT / file_rel).resolve()

    if not file_path.exists():
        print(json.dumps({"error": f"File not found: {file_rel}"}))
        sys.exit(1)

    registry_info = _check_registry(file_path)

    result: dict[str, object] = {
        "file": file_rel,
        "docstring": _extract_docstring(file_path),
        "size_lines": _count_lines(file_path),
        "callers": _find_callers(file_path),
        "in_registry": registry_info["in_registry"],
        "registry_category": registry_info["registry_category"],
        "has_test": _check_test(file_path),
        "has_entrypoint": _has_entrypoint(file_path),
        "imports_from_repo": _imports_from_repo(file_path),
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
