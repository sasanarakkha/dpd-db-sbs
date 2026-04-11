"""Verify that files in each registry copy category use the correct locale suffix/prefix."""

import json
from pathlib import Path

import pytest


REGISTRY_PATH = Path("kamma/upstream_sync/registry.json")

# Locale markers that MUST appear in basenames for each category (any one is sufficient)
REQUIRED_MARKERS: dict[str, tuple[str, ...]] = {
    "russian_copies": ("_ru", "ru_", "-ru"),
    "sbs_copies": ("_sbs", "sbs_", "-sbs"),
    "dps_copies": ("_dps", "dps_", "-dps"),
}

# Locale markers that must NOT appear in other categories' file basenames
FORBIDDEN_MARKERS: dict[str, tuple[str, ...]] = {
    "russian_copies": ("_sbs", "-sbs", "_dps", "-dps"),
    "sbs_copies": ("_ru", "-ru", "_dps", "-dps"),
    "dps_copies": ("_ru", "-ru", "_sbs", "-sbs"),
}


def load_registry() -> dict[str, object]:
    if not REGISTRY_PATH.exists():
        pytest.skip("registry.json not found")
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def file_basename(path: str) -> str:
    """Return the last non-empty path component (handles trailing-slash directory paths)."""
    return Path(path.rstrip("/")).name


def is_directory_entry(path: str) -> bool:
    """Directory entries end with '/' and are excluded from basename checks."""
    return path.endswith("/")


def test_files_have_correct_locale_marker() -> None:
    """
    Files in russian_copies must contain '_ru' or 'ru_' in their basename.
    Files in sbs_copies must contain '_sbs' or 'sbs_'.
    Files in dps_copies must contain '_dps' or 'dps_'.
    Directory entries (path ending in '/') are excluded.
    """
    registry = load_registry()
    errors: list[str] = []

    for category, required_markers in REQUIRED_MARKERS.items():
        for path in registry.get(category, {}):  # type: ignore[union-attr]
            if is_directory_entry(path):
                continue
            name = file_basename(path)
            if not any(marker in name for marker in required_markers):
                errors.append(
                    f"{category}: '{path}' — basename '{name}' must contain one of {required_markers}"
                )

    assert errors == [], (
        "Registry category naming violations found.\n"
        "Each file must carry the correct locale marker for its category.\n\n"
        + "\n".join(errors)
    )


def test_no_cross_category_locale_contamination() -> None:
    """
    Files in russian_copies must NOT have '_sbs' or '_dps' in their basename.
    Files in sbs_copies must NOT have '_ru' or '_dps'.
    Files in dps_copies must NOT have '_ru' or '_sbs'.
    Directory entries (path ending in '/') are excluded.
    """
    registry = load_registry()
    errors: list[str] = []

    for category, forbidden_markers in FORBIDDEN_MARKERS.items():
        for path in registry.get(category, {}):  # type: ignore[union-attr]
            if is_directory_entry(path):
                continue
            name = file_basename(path)
            for marker in forbidden_markers:
                if marker in name:
                    errors.append(
                        f"{category}: '{path}' — basename '{name}' "
                        f"contains forbidden marker '{marker}' for this category"
                    )

    assert errors == [], (
        "Registry cross-category locale contamination found.\n"
        "A file's locale suffix must match its registry category.\n\n"
        + "\n".join(errors)
    )
