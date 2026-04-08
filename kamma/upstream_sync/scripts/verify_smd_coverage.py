#!/usr/bin/env python3

"""Verify every registry entry has a corresponding SMD section meeting the quality rubric."""

import re
import sys
from pathlib import Path

from kamma.upstream_sync.scripts.registry_helper import (
    load_registry,
    get_inspired_by_upstream_paths,
    get_modified_upstream_paths,
    get_strict_shadow_mappings,
)
from tools.printer import printer as pr

# Quality rubric minimums (unless sync_rule is MIRROR_EXACTLY or inspired_only)
MIN_LOCAL_CHANGES = 2
MIN_WATCH_FOR = 1


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

        sync_rule_match = re.search(r"\*\*Sync Rule\*\*:\s*(\S+)", block)
        sync_rule = sync_rule_match.group(1).strip() if sync_rule_match else ""

        local_changes = re.findall(r"^\s*\d+\.", block, re.MULTILINE)
        watch_for_items = (
            re.findall(r"^\s*-\s+", block.split("**Watch For**")[1], re.MULTILINE)
            if "**Watch For**" in block
            else []
        )

        entries[file_path] = {
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
        items.append((path, "modified_upstream"))

    mappings = get_strict_shadow_mappings(data)
    # We don't have category info in mappings easily, but we can check registry keys
    russian = data.get("russian_copies", {})
    for shadow in mappings:
        category = (
            "russian_copy"
            if isinstance(russian, dict) and shadow in russian
            else "sbs_copy"
        )
        items.append((shadow, category))

    for path in get_inspired_by_upstream_paths(data):
        items.append((path, "inspired_by_upstream"))

    return items


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
    pr.title("verify_smd_coverage.py")

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
    rubric_fails: list[str] = []

    for path, category in all_paths:
        if path not in smd_entries:
            gaps.append(f"  [{category}] MISSING: {path}")
        else:
            fails = check_rubric(path, category, smd_entries[path])
            rubric_fails.extend(fails)

    pr.green("coverage gaps")
    pr.yes("none") if not gaps else pr.no(f"{len(gaps)}")

    pr.green("rubric failures")
    pr.yes("none") if not rubric_fails else pr.no(f"{len(rubric_fails)}")

    if gaps:
        pr.red("\nMissing SMD entries:")
        for g in gaps:
            pr.red(g)

    if rubric_fails:
        pr.warning("\nRubric failures (entries need enrichment):")
        for f in rubric_fails:
            pr.warning(f)

    if gaps:
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
