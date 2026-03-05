import json
import os
import ast
from pathlib import Path
import pytest


def get_registry_path():
    return Path("conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json")


def load_registry():
    path = get_registry_path()
    if not path.exists():
        pytest.skip("dps_sync_registry.json not found")
    with open(path, "r") as f:
        return json.load(f)


def get_python_pairs():
    registry = load_registry()
    pairs = []

    for shadow, upstream in registry.get("russian_copies", {}).items():
        if shadow.endswith(".py") and upstream.endswith(".py"):
            pairs.append((shadow, upstream))

    for shadow, upstream in registry.get("sbs_copies", {}).items():
        if shadow.endswith(".py") and upstream.endswith(".py"):
            pairs.append((shadow, upstream))

    return pairs


def extract_ast_info(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            return None

    imports = set()
    functions = set()
    classes = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for alias in node.names:
                    imports.add(f"{node.module}.{alias.name}")
        elif isinstance(node, ast.FunctionDef):
            functions.add(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.add(node.name)

    return {"imports": imports, "functions": functions, "classes": classes}


@pytest.mark.parametrize("shadow, upstream", get_python_pairs())
def test_shadow_copy_parity(shadow, upstream):
    """
    Test that the shadow copy maintains parity with the upstream file.
    Specifically:
    1. It should have all the imports that the upstream file has (to catch missing dependencies).
    2. It should have all the classes/functions the upstream file has (structural parity).
    """
    upstream_info = extract_ast_info(upstream)
    shadow_info = extract_ast_info(shadow)

    if not upstream_info:
        pytest.skip(f"Upstream file {upstream} not found or invalid.")

    if not shadow_info:
        pytest.fail(f"Shadow file {shadow} not found or invalid.")

    # Check for missing imports
    missing_imports = upstream_info["imports"] - shadow_info["imports"]

    # Check for missing functions
    missing_functions = upstream_info["functions"] - shadow_info["functions"]

    # Check for missing classes
    missing_classes = upstream_info["classes"] - shadow_info["classes"]

    errors = []
    # Note: Sometimes shadow copies intentionally drop things or rename things.
    # However, for a strict check, any missing import might be a missing dependency.
    # We will log them as errors. In practice, this might need a whitelist.
    if missing_imports:
        errors.append(f"Missing imports: {missing_imports}")
    if missing_functions:
        errors.append(f"Missing functions: {missing_functions}")
    if missing_classes:
        errors.append(f"Missing classes: {missing_classes}")

    if errors:
        pytest.fail(
            f"Parity mismatch in {shadow} compared to {upstream}:\n" + "\n".join(errors)
        )
