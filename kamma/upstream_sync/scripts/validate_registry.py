#!/usr/bin/env python3

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
    errors: list[str] = []
    import fnmatch

    russian_copies = data.get("russian_copies", {})
    sbs_copies = data.get("sbs_copies", {})
    dps_copies = data.get("dps_copies", {})
    tamil_copies = data.get("tamil_copies", {})
    inspired = data.get("inspired_by_upstream", {})

    sections = {
        "modified_upstream_files": [
            entry["path"] if isinstance(entry, dict) else entry
            for entry in data.get("modified_upstream_files", [])  # type: ignore
        ],
        "russian_copies": list(russian_copies.keys())
        if isinstance(russian_copies, dict)
        else [],
        "sbs_copies": list(sbs_copies.keys()) if isinstance(sbs_copies, dict) else [],
        "dps_copies": list(dps_copies.keys()) if isinstance(dps_copies, dict) else [],
        "tamil_copies": list(tamil_copies.keys())
        if isinstance(tamil_copies, dict)
        else [],
        "inspired_by_upstream": list(inspired.keys())
        if isinstance(inspired, dict)
        else [],
        "unique_paths": data.get("unique_paths", []),
        "no_sync_files": data.get("no_sync_files", []),
        "skip_sync_patterns": data.get("skip_sync_patterns", []),
    }

    all_items = []
    for section, paths in sections.items():
        if isinstance(paths, list):
            for path in paths:
                if isinstance(path, str):
                    all_items.append((path, section))

    for i, (path1, sec1) in enumerate(all_items):
        for j, (path2, sec2) in enumerate(all_items):
            if i == j:
                continue

            # Exact match
            if path1 == path2:
                if i < j:  # Avoid double reporting
                    # Data classes exception
                    if path1 == "exporter/goldendict/data_classes_dps.py" and {
                        sec1,
                        sec2,
                    } == {"russian_copies", "sbs_copies"}:
                        continue
                    errors.append(
                        f"Overlap: '{path1}' exists in both {sec1} and {sec2}"
                    )

            # Directory containment
            elif path1.endswith("/") and path2.startswith(path1):
                errors.append(
                    f"Overlap: Directory '{path1}' ({sec1}) contains '{path2}' ({sec2})"
                )

            # Glob pattern
            elif "*" in path1:
                if fnmatch.fnmatch(path2, path1):
                    errors.append(
                        f"Overlap: Glob '{path1}' ({sec1}) matches '{path2}' ({sec2})"
                    )

    return errors


def validate_inspired_by_upstream(
    data: dict[str, object], repo_root: Path | None = None
) -> list[str]:
    errors: list[str] = []
    inspired = data.get("inspired_by_upstream", {})
    if not isinstance(inspired, dict):
        errors.append("inspired_by_upstream: must be an object")
        return errors

    for path, entry in inspired.items():
        label = f"inspired_by_upstream['{path}']"
        if not isinstance(entry, dict):
            errors.append(f"{label}: entry must be an object")
            continue

        upstream = entry.get("upstream")
        if not upstream or not isinstance(upstream, str):
            errors.append(f"{label}: missing or invalid 'upstream' path")
        elif repo_root:
            if not (repo_root / str(upstream)).exists():
                errors.append(f"{label}: upstream path '{upstream}' does not exist")

        reason = entry.get("divergence_reason")
        if not reason or not isinstance(reason, str) or not reason.strip():
            errors.append(f"{label}: missing or empty 'divergence_reason'")

        if repo_root:
            if path.endswith("/"):
                if not (repo_root / path).is_dir():
                    errors.append(f"{label}: local directory '{path}' does not exist")
            else:
                if not (repo_root / path).exists():
                    errors.append(f"{label}: local path '{path}' does not exist")

    return errors


def validate_skip_sync_patterns(data: dict[str, object]) -> list[str]:
    errors: list[str] = []
    patterns = data.get("skip_sync_patterns", [])
    if not isinstance(patterns, list):
        errors.append("skip_sync_patterns: must be a list")
        return errors

    for i, item in enumerate(patterns):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"skip_sync_patterns[{i}]: must be a non-empty string")

    return errors


def validate_registry_core(
    data: dict[str, object], repo_root: Path | None = None
) -> list[str]:
    errors: list[str] = []

    # Check for legacy keys
    if "ignored_files" in data:
        errors.append(
            "'ignored_files' is no longer valid; use 'skip_sync_patterns' instead"
        )
    if "folders_to_check" in data:
        errors.append("'folders_to_check' is no longer valid")

    errors.extend(validate_modified_upstream_files(data))

    unique_paths = data.get("unique_paths", [])
    errors.extend(validate_no_duplicates_in_list("unique_paths", unique_paths))  # type: ignore[arg-type]

    russian_copies: dict[str, str] = data.get("russian_copies", {})  # type: ignore[assignment]
    errors.extend(
        validate_no_duplicates_in_list(
            "russian_copies keys", list(russian_copies.keys())
        )
    )

    sbs_copies: dict[str, str] = data.get("sbs_copies", {})  # type: ignore[assignment]
    errors.extend(
        validate_no_duplicates_in_list("sbs_copies keys", list(sbs_copies.keys()))
    )

    dps_copies: dict[str, str] = data.get("dps_copies", {})  # type: ignore[assignment]
    errors.extend(
        validate_no_duplicates_in_list("dps_copies keys", list(dps_copies.keys()))
    )

    tamil_copies: dict[str, str] = data.get("tamil_copies", {})  # type: ignore[assignment]
    errors.extend(
        validate_no_duplicates_in_list("tamil_copies keys", list(tamil_copies.keys()))
    )

    if repo_root:
        errors.extend(
            validate_shadow_paths_exist("russian_copies", russian_copies, repo_root)
        )
        errors.extend(validate_shadow_paths_exist("sbs_copies", sbs_copies, repo_root))
        errors.extend(validate_shadow_paths_exist("dps_copies", dps_copies, repo_root))
        errors.extend(
            validate_shadow_paths_exist("tamil_copies", tamil_copies, repo_root)
        )

    errors.extend(validate_inspired_by_upstream(data, repo_root))
    errors.extend(validate_skip_sync_patterns(data))
    errors.extend(validate_cross_section_overlaps(data))

    return errors


def main() -> None:
    pr.tic()
    pr.green_title("validate_registry.py")

    registry_path = Path("kamma/upstream_sync/registry.json")
    if not registry_path.exists():
        pr.red(f"Registry not found at {registry_path}")
        sys.exit(1)

    data = load_registry(registry_path)
    repo_root = registry_path.parent.parent.parent

    pr.green("validating registry core")
    all_errors = validate_registry_core(data, repo_root)

    pr.green("checking cross-section overlaps")
    all_warnings = validate_cross_section_overlaps(data)

    if all_warnings:
        for w in all_warnings:
            pr.amber(w)

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
