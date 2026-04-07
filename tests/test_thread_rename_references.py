"""Ensure live repo surfaces stop referencing files renamed by the thread."""

from pathlib import Path


REPLACED_PATHS = {
    "exporter/webapp/main_ru.py": "exporter/webapp/main_dps.py",
    "scripts/backup/backup_ru_sbs.py": "scripts/backup/backup_dps.py",
    "scripts/build/db_rebuild_from_tsv_ru_sbs.py": "scripts/build/db_rebuild_from_tsv_dps.py",
}

LIVE_SEARCH_ROOTS = (
    Path(".github"),
    Path("scripts"),
    Path("tests"),
    Path("kamma/upstream_sync"),
)

TEXT_SUFFIXES = {".py", ".md", ".json", ".yml", ".yaml", ".sh"}


def iter_live_files() -> list[Path]:
    files: list[Path] = []
    current_file = Path(__file__).resolve()

    for root in LIVE_SEARCH_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
                continue
            if path.resolve() == current_file:
                continue
            files.append(path)

    return files


def test_live_files_do_not_reference_replaced_paths() -> None:
    violations: list[str] = []

    for path in iter_live_files():
        text = path.read_text(encoding="utf-8")
        for old_path, new_path in REPLACED_PATHS.items():
            if old_path in text:
                violations.append(f"{path}: replace '{old_path}' with '{new_path}'")

    assert violations == []
