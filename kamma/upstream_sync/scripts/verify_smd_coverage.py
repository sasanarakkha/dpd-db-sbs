#!/usr/bin/env python3

"""Verify sync-relevant registry entries have SMD sections meeting the quality rubric."""

import re
import sys
from pathlib import Path

from kamma.upstream_sync.scripts.registry_helper import (
    get_inspired_by_upstream_paths,
    get_modified_upstream_paths,
    get_shadow_mappings_by_category,
    load_registry,
)
from tools.printer import printer as pr

# Quality rubric minimums (unless sync_rule is MIRROR_EXACTLY or inspired_only)
MIN_LOCAL_CHANGES = 2
MIN_WATCH_FOR = 1
VALID_SYNC_RULES = {"PORT", "MIRROR_EXACTLY", "PRESERVE", "DISCUSS", "inspired_only"}


def extract_smd_entries(smd_path: Path) -> dict[str, dict[str, object]]:
    """Parse a single SMD file and return a dict keyed by the File path."""
    entries: dict[str, dict[str, object]] = {}
    if not smd_path.exists():
        return entries

    content = smd_path.read_text(encoding="utf-8")
    # Split on entry boundaries — each entry starts with a "**File**:" line
    blocks = re.split(r"(?=\*\*File\*\*:)", content)

    for block in blocks:
        file_match = re.search(r"\*\*File\*\*:\s*`?([^`\n]+)`?", block)
        if not file_match:
            continue
        file_path = file_match.group(1).strip()

        category_match = re.search(r"\*\*Category\*\*:\s*([^\n]+)", block)
        category = category_match.group(1).strip() if category_match else ""

        sync_rule_match = re.search(r"\*\*Sync Rule\*\*:\s*(\S+)", block)
        sync_rule = sync_rule_match.group(1).strip() if sync_rule_match else ""

        local_changes = re.findall(r"^\s*\d+\.", block, re.MULTILINE)
        watch_for_items = (
            re.findall(r"^\s*-\s+", block.split("**Watch For**")[1], re.MULTILINE)
            if "**Watch For**" in block
            else []
        )

        entries[file_path] = {
            "category": category,
            "sync_rule": sync_rule,
            "local_changes_count": len(local_changes),
            "watch_for_count": len(watch_for_items),
        }
    return entries


def extract_all_smd_entries(smd_dir: Path) -> dict[str, dict[str, object]]:
    """Aggregate entries across all .md files in smd_dir."""
    all_entries: dict[str, dict[str, object]] = {}
    for smd_file in smd_dir.glob("*.md"):
        if smd_file.name == "index.md":
            continue
        file_entries = extract_smd_entries(smd_file)
        for path, entry in file_entries.items():
            if path in all_entries:
                raise ValueError(
                    f"Duplicate SMD entry for '{path}' found in {smd_file.name}"
                )
            all_entries[path] = entry
    return all_entries


def collect_registry_paths(data: dict[str, object]) -> list[tuple[str, str]]:
    """Return list of (path, category) for every entry in all categories."""
    items: list[tuple[str, str]] = []

    for path in get_modified_upstream_paths(data):
        items.append((path, "modified_upstream_files"))

    for category, mapping in get_shadow_mappings_by_category(data).items():
        for shadow in mapping:
            items.append((shadow, category))

    for path in get_inspired_by_upstream_paths(data):
        items.append((path, "inspired_by_upstream"))

    return items


def check_category_alignment(
    registry_items: list[tuple[str, str]],
    smd_entries: dict[str, dict[str, object]],
) -> list[str]:
    """Return SMD category mismatches for registry-covered entries."""
    violations: list[str] = []
    for path, expected_category in registry_items:
        entry = smd_entries.get(path)
        if entry is None:
            continue
        actual_category = entry.get("category")
        if actual_category != expected_category:
            if isinstance(actual_category, str) and actual_category.strip():
                actual_label = f"'{actual_category}'"
            else:
                actual_label = "missing"
            violations.append(
                f"  [{expected_category}] {path}: SMD category is {actual_label}"
            )
    return violations


def check_unregistered_smd_entries(
    registry_items: list[tuple[str, str]],
    smd_entries: dict[str, dict[str, object]],
) -> list[str]:
    """Return SMD entries that no longer correspond to sync registry paths."""
    registered_paths = {path for path, _category in registry_items}
    return [
        f"  UNREGISTERED: {path}"
        for path in sorted(smd_entries)
        if path not in registered_paths
    ]


def check_rubric(
    path: str,
    category: str,
    entry: dict[str, object],
) -> list[str]:
    """Return list of rubric violations for an SMD entry."""
    violations: list[str] = []
    sync_rule = str(entry.get("sync_rule", ""))
    local_changes = int(entry.get("local_changes_count", 0))  # type: ignore[arg-type]
    watch_for = int(entry.get("watch_for_count", 0))  # type: ignore[arg-type]

    if sync_rule not in VALID_SYNC_RULES:
        violations.append(f"  [{category}] {path}: unknown Sync Rule '{sync_rule}'")

    if sync_rule not in ["MIRROR_EXACTLY", "inspired_only"]:
        if local_changes < MIN_LOCAL_CHANGES:
            violations.append(
                f"  [{category}] {path}: only {local_changes} local-change(s), need {MIN_LOCAL_CHANGES}"
            )

    # Watch For is required for everyone except maybe MIRROR_EXACTLY?
    # Spec says: "inspired_only still requires Watch For"
    if sync_rule != "MIRROR_EXACTLY":
        if watch_for < MIN_WATCH_FOR:
            violations.append(f"  [{category}] {path}: missing Watch For section")

    return violations


def main() -> None:
    pr.tic()
    pr.green_title("verify_smd_coverage.py")

    smd_dir = Path("kamma/upstream_sync/smd")
    data = load_registry()

    pr.green("loading registry")
    all_paths = collect_registry_paths(data)
    pr.yes(f"{len(all_paths)}")

    pr.green("loading smd/*.md")
    try:
        smd_entries = extract_all_smd_entries(smd_dir)
        pr.yes(f"{len(smd_entries)} entries")
    except ValueError as e:
        pr.no("duplicate")
        pr.red(str(e))
        sys.exit(1)

    gaps: list[str] = []
    category_fails: list[str] = []
    unregistered_fails: list[str] = []
    rubric_fails: list[str] = []

    for path, category in all_paths:
        if path not in smd_entries:
            gaps.append(f"  [{category}] MISSING: {path}")
        else:
            fails = check_rubric(path, category, smd_entries[path])
            rubric_fails.extend(fails)
    category_fails.extend(check_category_alignment(all_paths, smd_entries))
    unregistered_fails.extend(check_unregistered_smd_entries(all_paths, smd_entries))

    pr.green("coverage gaps")
    pr.yes("none") if not gaps else pr.no(f"{len(gaps)}")

    pr.green("category mismatches")
    pr.yes("none") if not category_fails else pr.no(f"{len(category_fails)}")

    pr.green("unregistered smd entries")
    pr.yes("none") if not unregistered_fails else pr.no(f"{len(unregistered_fails)}")

    pr.green("rubric failures")
    pr.yes("none") if not rubric_fails else pr.no(f"{len(rubric_fails)}")

    if gaps:
        pr.red("\nMissing SMD entries:")
        for g in gaps:
            pr.red(g)

    if category_fails:
        pr.red("\nSMD category mismatches:")
        for f in category_fails:
            pr.red(f)

    if unregistered_fails:
        pr.red("\nUnregistered SMD entries:")
        for f in unregistered_fails:
            pr.red(f)

    if rubric_fails:
        pr.amber("\nRubric failures (entries need enrichment):")
        for f in rubric_fails:
            pr.amber(f)

    if gaps or category_fails or unregistered_fails:
        pr.toc()
        sys.exit(1)

    pr.summary(
        "result",
        "SMD coverage complete"
        if not rubric_fails
        else "coverage ok, rubric needs work",
    )
    pr.toc()
    sys.exit(0 if not rubric_fails else 2)


if __name__ == "__main__":
    main()
