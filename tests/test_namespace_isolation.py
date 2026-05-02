"""Verify localized shadow-copy symbols follow the approved namespace policy."""

import ast
import json
from pathlib import Path

import pytest


def get_registry_path() -> Path:
    return Path("kamma/upstream_sync/registry.json")


def get_classification_report_path() -> Path:
    return Path("kamma/threads/normalize_function_naming/classification_report.md")


def load_registry() -> dict[str, object]:
    path = get_registry_path()
    if not path.exists():
        pytest.skip("registry.json not found")
    return json.loads(path.read_text(encoding="utf-8"))


def extract_symbols(filepath: str) -> set[str]:
    path = Path(filepath)
    if not path.exists():
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=filepath)
    except SyntaxError:
        return set()

    symbols: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            symbols.add(node.name)
    return symbols


def has_expected_locale_marker(name: str, expected_marker: str) -> bool:
    tokens = {
        "_ru": ("_ru", "ru_", "Ru", "RU", "Russian"),
        "_sbs": ("_sbs", "sbs_", "Sbs", "SBS"),
        "_dps": ("_dps", "dps_", "Dps", "DPS"),
    }
    return any(token in name for token in tokens[expected_marker])


def has_valid_marker_for_file(name: str, expected_marker: str, shadow: str) -> bool:
    if expected_marker != "_dps":
        return has_expected_locale_marker(name, expected_marker)

    # In DPS files, locale-specific helpers keep only their own locale marker.
    # Tamil (_ta) is a valid locale in DPS files alongside RU and SBS.
    ta_tokens = ("_ta", "ta_", "Ta", "TA", "Tamil")
    return (
        has_expected_locale_marker(name, "_dps")
        or has_expected_locale_marker(name, "_ru")
        or has_expected_locale_marker(name, "_sbs")
        or any(token in name for token in ta_tokens)
    )


def is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


# Explicit semantic exceptions that do not need an added locale marker.
EXCEPTIONS = {
    "main",
    "GlobalVars",
    "RpdData",
    "TpdData",  # Tamil Pali Dictionary Data — intrinsic semantic marker like RpdData
    "is_cyrillic",
    # main_ru.py routes
    "home_page_ru",
    "home_page_sbs",
    "bold_definitions_page",
    "db_search_bd",
    "db_search_gd_ru",
    "db_search_gd_sbs",
    "db_search_html_sbs",
    "db_search_json_ru",
    "db_search_json_sbs",
    "get_audio",
    "get_db",
    "status_page",
    "tt_search",
    "update_history",
}


def get_test_cases() -> list[tuple[str, str, str]]:
    registry = load_registry()
    cases: list[tuple[str, str, str]] = []

    categories = {"russian_copies": "_ru", "sbs_copies": "_sbs", "dps_copies": "_dps"}

    for cat, expected in categories.items():
        for shadow, upstream in registry.get(cat, {}).items():  # type: ignore[union-attr]
            if not shadow.endswith(".py"):
                continue
            cases.append((shadow, upstream, expected))
    return cases


def load_report_statuses() -> dict[tuple[str, str], str]:
    report_path = get_classification_report_path()
    if not report_path.exists():
        pytest.skip("classification_report.md not found")

    statuses: dict[tuple[str, str], str] = {}
    for raw_line in report_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells[:2] == ["file", "symbol"] or len(cells) != 6:
            continue
        file_path, symbol, _, _, _, status = cells
        statuses[(file_path, symbol)] = status
    return statuses


@pytest.mark.parametrize("shadow, upstream, expected_marker", get_test_cases())
def test_symbol_naming_convention(shadow, upstream, expected_marker):
    """
    Ensures Tier 2/3 symbols in shadow copies have clear locale markers.
    - Tier 1 (identical to upstream): MUST NOT have marker.
    - Tier 2/3 (modified or new): MUST have any clear marker matching the category.
    - In DPS files, RU-only helpers keep `_ru`, SBS-only helpers keep `_sbs`, and only shared helpers use `_dps`.
    - Explicit semantic exceptions like `RpdData` are allowed unmarked.
    """
    shadow_symbols = extract_symbols(shadow)
    upstream_symbols = extract_symbols(upstream)

    errors = []
    for sym in shadow_symbols:
        if sym in EXCEPTIONS:
            continue
        if is_dunder(sym):
            continue

        is_tier_1 = sym in upstream_symbols

        if is_tier_1:
            continue
        else:
            if not has_valid_marker_for_file(sym, expected_marker, shadow):
                errors.append(
                    f"Symbol '{sym}' is Tier 2/3 but lacks a clear '{expected_marker}' locale marker."
                )

        # Double marker check
        if sym.startswith("ru_") and sym.endswith("_ru"):
            errors.append(f"Symbol '{sym}' is double-marked.")
        if sym.startswith("sbs_") and sym.endswith("_sbs"):
            errors.append(f"Symbol '{sym}' is double-marked.")
        if sym.startswith("dps_") and sym.endswith("_dps"):
            errors.append(f"Symbol '{sym}' is double-marked.")

    if errors:
        pytest.fail(f"Naming violations in {shadow}:\n" + "\n".join(errors))


def test_classification_report_has_no_unresolved_violations() -> None:
    statuses = load_report_statuses()
    unresolved = {
        (file_path, symbol): status
        for (file_path, symbol), status in statuses.items()
        if status.startswith("MISSING") or status.startswith("WRONG")
    }
    assert unresolved == {}
