"""Verify every registry entry has a corresponding SMD section meeting the quality rubric."""

import re
import sys
from pathlib import Path

from kamma.upstream_sync.registry_helper import load_registry
from tools.printer import printer as pr

# Quality rubric minimums (unless sync_rule is MIRROR_EXACTLY)
MIN_LOCAL_CHANGES = 2
MIN_WATCH_FOR = 1


def extract_smd_entries(smd_path: Path) -> dict[str, dict[str, object]]:
    """Parse smd.md and return a dict keyed by the File path."""
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


def collect_registry_paths(data: dict[str, object]) -> list[tuple[str, str]]:
    """Return list of (path, category) for every entry in all categories."""
    items: list[tuple[str, str]] = []

    for entry in data.get("modified_upstream_files", []):  # type: ignore[union-attr]
        if isinstance(entry, dict):
            path = entry.get("path", "")
            if isinstance(path, str) and path:
                items.append((path, "modified_upstream"))
        elif isinstance(entry, str):
            items.append((entry, "modified_upstream"))

    for shadow in data.get("russian_copies", {}).keys():  # type: ignore[union-attr]
        items.append((shadow, "russian_copy"))

    for shadow in data.get("sbs_copies", {}).keys():  # type: ignore[union-attr]
        items.append((shadow, "sbs_copy"))

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

    if sync_rule != "MIRROR_EXACTLY":
        if local_changes < MIN_LOCAL_CHANGES:
            violations.append(
                f"  [{category}] {path}: only {local_changes} local-change(s), need {MIN_LOCAL_CHANGES}"
            )
        if watch_for < MIN_WATCH_FOR:
            violations.append(f"  [{category}] {path}: missing Watch For section")
    return violations


def main() -> None:
    pr.tic()
    pr.title("verify_smd_coverage.py")

    smd_path = Path("kamma/upstream_sync/smd.md")
    data = load_registry()

    pr.green("loading registry")
    all_paths = collect_registry_paths(data)
    pr.yes(f"{len(all_paths)}")

    pr.green("loading smd.md")
    smd_entries = extract_smd_entries(smd_path)
    pr.yes(f"{len(smd_entries)} entries")

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
