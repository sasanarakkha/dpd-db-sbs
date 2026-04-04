"""Validate registry.json schema integrity and data quality."""

import json
import sys
from pathlib import Path

from tools.printer import printer as pr


def load_registry(registry_path: Path) -> dict[str, object]:
    with registry_path.open("r") as f:
        return json.load(f)  # type: ignore[no-any-return]


def validate_modified_upstream_files(data: dict[str, object]) -> list[str]:
    errors: list[str] = []
    entries = data.get("modified_upstream_files", [])
    seen_paths: set[str] = set()
    for i, entry in enumerate(entries):  # type: ignore[union-attr]
        if not isinstance(entry, dict):
            errors.append(
                f"modified_upstream_files[{i}]: must be an object, got {type(entry).__name__}"
            )
            continue
        if "path" not in entry:
            errors.append(f"modified_upstream_files[{i}]: missing 'path' field")
        else:
            path = entry["path"]
            if not isinstance(path, str):
                errors.append(f"modified_upstream_files[{i}]: 'path' must be a string")
            elif path in seen_paths:
                errors.append(f"modified_upstream_files: duplicate path '{path}'")
            else:
                seen_paths.add(path)
        if "discuss" not in entry:
            errors.append(f"modified_upstream_files[{i}]: missing 'discuss' field")
        elif not isinstance(entry["discuss"], bool):
            errors.append(f"modified_upstream_files[{i}]: 'discuss' must be a bool")
        else:
            if entry["discuss"]:
                reason = entry.get("discuss_reason", "")
                if not isinstance(reason, str) or not reason.strip():
                    errors.append(
                        f"modified_upstream_files[{i}] ({entry.get('path')}): "
                        "discuss=true requires a non-empty 'discuss_reason'"
                    )
    return errors


def validate_no_duplicates_in_list(label: str, items: list[str]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            errors.append(f"{label}: duplicate entry '{item}'")
        seen.add(item)
    return errors


def validate_shadow_paths_exist(
    label: str, mapping: dict[str, str], repo_root: Path
) -> list[str]:
    errors: list[str] = []
    for shadow in mapping:
        # Directory entries end with /; wildcard entries skip existence check
        if "*" in shadow:
            continue
        shadow_path = repo_root / shadow
        if shadow.endswith("/"):
            if not shadow_path.is_dir():
                errors.append(
                    f"{label}: shadow directory '{shadow}' does not exist in repo"
                )
        else:
            if not shadow_path.exists():
                errors.append(f"{label}: shadow file '{shadow}' does not exist in repo")
    return errors


def validate_cross_section_overlaps(data: dict[str, object]) -> list[str]:
    warnings: list[str] = []
    russian = set(data.get("russian_copies", {}).keys())  # type: ignore[union-attr]
    sbs = set(data.get("sbs_copies", {}).keys())  # type: ignore[union-attr]
    overlap = russian & sbs
    for path in sorted(overlap):
        warnings.append(
            f"WARN cross-category overlap (russian_copies + sbs_copies): '{path}'"
        )
    return warnings


def main() -> None:
    pr.tic()
    pr.title("validate_registry.py")

    registry_path = Path("kamma/upstream_sync/registry.json")
    if not registry_path.exists():
        pr.red(f"Registry not found at {registry_path}")
        sys.exit(1)

    data = load_registry(registry_path)
    repo_root = registry_path.parent.parent.parent

    all_errors: list[str] = []
    all_warnings: list[str] = []

    # 1. modified_upstream_files schema
    pr.green("checking modified_upstream_files schema")
    errs = validate_modified_upstream_files(data)
    all_errors.extend(errs)
    pr.yes("ok") if not errs else pr.no(f"{len(errs)} errors")

    # 2. unique_paths duplicates
    pr.green("checking unique_paths duplicates")
    unique_paths = data.get("unique_paths", [])
    errs = validate_no_duplicates_in_list("unique_paths", unique_paths)  # type: ignore[arg-type]
    all_errors.extend(errs)
    pr.yes("ok") if not errs else pr.no(f"{len(errs)} errors")

    # 3. russian_copies key duplicates (JSON disallows these, but validate values)
    pr.green("checking russian_copies keys")
    russian_copies: dict[str, str] = data.get("russian_copies", {})  # type: ignore[assignment]
    errs = validate_no_duplicates_in_list(
        "russian_copies keys", list(russian_copies.keys())
    )
    all_errors.extend(errs)
    pr.yes("ok") if not errs else pr.no(f"{len(errs)} errors")

    # 4. sbs_copies key duplicates
    pr.green("checking sbs_copies keys")
    sbs_copies: dict[str, str] = data.get("sbs_copies", {})  # type: ignore[assignment]
    errs = validate_no_duplicates_in_list("sbs_copies keys", list(sbs_copies.keys()))
    all_errors.extend(errs)
    pr.yes("ok") if not errs else pr.no(f"{len(errs)} errors")

    # 5. shadow paths exist
    pr.green("checking russian shadow paths exist")
    errs = validate_shadow_paths_exist("russian_copies", russian_copies, repo_root)
    all_errors.extend(errs)
    pr.yes("ok") if not errs else pr.no(f"{len(errs)} missing")

    pr.green("checking sbs shadow paths exist")
    errs = validate_shadow_paths_exist("sbs_copies", sbs_copies, repo_root)
    all_errors.extend(errs)
    pr.yes("ok") if not errs else pr.no(f"{len(errs)} missing")

    # 6. cross-section overlaps (warn only)
    pr.green("checking cross-section overlaps")
    warns = validate_cross_section_overlaps(data)
    all_warnings.extend(warns)
    pr.yes("ok") if not warns else pr.no(f"{len(warns)} overlaps")

    # Report
    if all_warnings:
        for w in all_warnings:
            pr.warning(w)

    if all_errors:
        pr.red(f"\n{len(all_errors)} error(s) found:")
        for e in all_errors:
            pr.red(f"  {e}")
        pr.toc()
        sys.exit(1)
    else:
        pr.summary("result", "registry.json is valid")
        pr.toc()
        sys.exit(0)


if __name__ == "__main__":
    main()
