#!/usr/bin/env python3

"""Validate registry.json schema integrity and data quality."""

import json
import sys
from pathlib import Path

from kamma.upstream_sync.scripts.sync_schema import (
    RegistryData,
    validate_repo_relative_paths,
)
from tools.printer import printer as pr

REQUIRED_TOP_LEVEL_SECTIONS = [
    "modified_upstream_files",
    "russian_copies",
    "sbs_copies",
    "dps_copies",
    "tamil_copies",
    "inspired_by_upstream",
    "unique_paths",
    "no_sync_files",
    "skip_sync_patterns",
]


def load_registry(registry_path: Path) -> dict[str, object]:
    with registry_path.open("r", encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def validate_required_top_level_sections(data: dict[str, object]) -> list[str]:
    """Validate that every registry category is explicitly present."""
    return [
        f"registry: missing required top-level section '{section}'"
        for section in REQUIRED_TOP_LEVEL_SECTIONS
        if section not in data
    ]


VALID_SYNC_RULES = {"PORT", "MIRROR_EXACTLY", "PRESERVE", "DISCUSS", "inspired_only"}


def validate_entry_rubric(label: str, entry: dict[str, object]) -> list[str]:
    """Enforce merge guidance rubric for an entry."""
    errors: list[str] = []
    sync_rule = entry.get("sync_rule")
    if not isinstance(sync_rule, str) or not sync_rule.strip():
        sync_rule = ""
    else:
        sync_rule = sync_rule.strip()

    if sync_rule and sync_rule not in VALID_SYNC_RULES:
        errors.append(f"{label}: unknown Sync Rule '{sync_rule}'")

    local_changes = entry.get("local_changes", [])
    watch_for = entry.get("watch_for", [])

    if not isinstance(local_changes, list):
        errors.append(f"{label}: 'local_changes' must be a list")
        local_changes = []
    if not isinstance(watch_for, list):
        errors.append(f"{label}: 'watch_for' must be a list")
        watch_for = []

    # Enforce minimums
    if sync_rule not in ["MIRROR_EXACTLY", "inspired_only"] and len(local_changes) < 1:
        pr.amber(
            f"Rubric Warning: {label}: only {len(local_changes)} local-change(s), need 1"
        )

    if sync_rule != "MIRROR_EXACTLY" and len(watch_for) < 1:
        pr.amber(f"Rubric Warning: {label}: missing watch_for section")

    return errors


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
        path = str(entry.get("path", ""))
        errors.extend(
            validate_entry_rubric(f"modified_upstream_files[{i}] ({path})", entry)
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


def validate_shadow_mapping(
    label: str, data: dict[str, object], repo_root: Path | None = None
) -> list[str]:
    """Validate one strict-shadow registry mapping section."""
    errors: list[str] = []
    value = data.get(label, {})
    if not isinstance(value, dict):
        return [f"{label}: must be an object"]

    seen: set[str] = set()
    for shadow, entry in value.items():
        if not isinstance(shadow, str) or not shadow.strip():
            errors.append(f"{label}: shadow path must be a non-empty string")
            continue
        if shadow in seen:
            errors.append(f"{label}: duplicate entry '{shadow}'")
        seen.add(shadow)

        if not isinstance(entry, dict):
            errors.append(f"{label}['{shadow}']: entry must be an object")
            continue
        upstream = entry.get("upstream")
        if not isinstance(upstream, str) or not upstream.strip():
            errors.append(f"{label}['{shadow}']: missing or invalid 'upstream' path")
            continue

        errors.extend(validate_entry_rubric(f"{label}['{shadow}']", entry))

        if repo_root:
            shadow_path = repo_root / shadow
            upstream_path = repo_root / upstream
            if "*" not in shadow:
                if shadow.endswith("/"):
                    if not shadow_path.is_dir():
                        errors.append(
                            f"{label}: shadow directory '{shadow}' does not exist in repo"
                        )
                elif not shadow_path.exists():
                    errors.append(
                        f"{label}: shadow file '{shadow}' does not exist in repo"
                    )
            if "*" not in upstream:
                if upstream.endswith("/"):
                    if not upstream_path.is_dir():
                        errors.append(
                            f"{label}: upstream source '{upstream}' does not exist"
                        )
                elif not upstream_path.exists():
                    errors.append(
                        f"{label}: upstream source '{upstream}' does not exist"
                    )

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
                    errors.append(
                        f"Overlap: '{path1}' exists in both {sec1} and {sec2}"
                    )

            # Directory containment
            elif path1.endswith("/") and path2.startswith(path1):
                errors.append(
                    f"Overlap: Directory '{path1}' ({sec1}) contains '{path2}' ({sec2})"
                )

            # Glob pattern
            elif "*" in path1 and fnmatch.fnmatch(path2, path1):
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
        elif repo_root and not (repo_root / upstream).exists():
            errors.append(f"{label}: upstream path '{upstream}' does not exist")

        reason = entry.get("divergence_reason")
        if not reason or not isinstance(reason, str) or not reason.strip():
            errors.append(f"{label}: missing or empty 'divergence_reason'")

        errors.extend(validate_entry_rubric(label, entry))

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


def append_path_safety_error(
    errors: list[str],
    label: str,
    path: str,
    allow_globs: bool = False,
) -> None:
    """Append a registry path-safety error for one path if validation fails."""
    try:
        validate_repo_relative_paths([path], label, allow_globs=allow_globs)
    except ValueError as exc:
        errors.append(str(exc).replace(f"{label}[0]", label, 1))


def validate_registry_path_safety(data: dict[str, object]) -> list[str]:
    """Reject registry paths that could escape the repo or become unsafe git pathspecs."""
    errors: list[str] = []

    entries = data.get("modified_upstream_files", [])
    if isinstance(entries, list):
        for index, entry in enumerate(entries):
            if isinstance(entry, dict):
                path = entry.get("path")
                if isinstance(path, str):
                    append_path_safety_error(
                        errors,
                        f"modified_upstream_files[{index}].path",
                        path,
                    )

    for category in ["russian_copies", "sbs_copies", "dps_copies", "tamil_copies"]:
        mapping = data.get(category, {})
        if isinstance(mapping, dict):
            for shadow, entry in mapping.items():
                if isinstance(shadow, str):
                    append_path_safety_error(
                        errors, f"{category} key '{shadow}'", shadow
                    )
                if isinstance(entry, dict):
                    upstream = entry.get("upstream")
                    if isinstance(upstream, str):
                        append_path_safety_error(
                            errors,
                            f"{category}['{shadow}']",
                            upstream,
                        )

    inspired = data.get("inspired_by_upstream", {})
    if isinstance(inspired, dict):
        for local_path, entry in inspired.items():
            if isinstance(local_path, str):
                append_path_safety_error(
                    errors,
                    f"inspired_by_upstream key '{local_path}'",
                    local_path,
                )
            if isinstance(entry, dict):
                upstream = entry.get("upstream")
                if isinstance(upstream, str):
                    append_path_safety_error(
                        errors,
                        f"inspired_by_upstream['{local_path}'].upstream",
                        upstream,
                    )

    for list_name, allow_globs in [
        ("unique_paths", True),
        ("no_sync_files", False),
        ("skip_sync_patterns", True),
    ]:
        values = data.get(list_name, [])
        if isinstance(values, list):
            for index, value in enumerate(values):
                if isinstance(value, str):
                    append_path_safety_error(
                        errors,
                        f"{list_name}[{index}]",
                        value,
                        allow_globs=allow_globs,
                    )

    return errors


def validate_registry_schema(data: dict[str, object]) -> list[str]:
    """Validate registry item types with the typed schema parser."""
    try:
        RegistryData.from_raw(data)
    except (ValueError, TypeError) as exc:
        message = str(exc)
        for label in ("unique_paths", "no_sync_files"):
            for suffix in ("must be a string", "must be a non-empty string"):
                prefix = f"field '{label}["
                if message.startswith(prefix) and message.endswith(suffix):
                    index = message.removeprefix(prefix).split("]", maxsplit=1)[0]
                    return [f"{label}[{index}]: must be a non-empty string"]
        return [message]
    return []


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

    errors.extend(validate_required_top_level_sections(data))
    errors.extend(validate_registry_schema(data))
    errors.extend(validate_modified_upstream_files(data))

    unique_paths = data.get("unique_paths", [])
    if isinstance(unique_paths, list):
        errors.extend(validate_no_duplicates_in_list("unique_paths", unique_paths))
    else:
        errors.append("unique_paths: must be a list")

    for label in ["russian_copies", "sbs_copies", "dps_copies", "tamil_copies"]:
        errors.extend(validate_shadow_mapping(label, data, repo_root))

    errors.extend(validate_inspired_by_upstream(data, repo_root))
    errors.extend(validate_skip_sync_patterns(data))
    errors.extend(validate_registry_path_safety(data))
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
