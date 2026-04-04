"""Identifies orphaned original files missing from upstream and archives them if they are unused in the active codebase."""

import argparse
import fnmatch
import json
import shutil
import subprocess
from pathlib import Path

from tools.printer import printer as pr

REGISTRY_PATH = Path("kamma/upstream_sync/registry.json")


def run_git(args: list[str]) -> list[str]:
    result = subprocess.run(["git"] + args, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def is_localized(filename: str) -> bool:
    """Check if a file has localized markers in its name."""
    name = Path(filename).name.lower()
    patterns = ["ru_", "_ru.", "rus_", "_rus.", "sbs_", "_sbs.", "dps_", "_dps."]
    for p in patterns:
        if p.startswith("_") and p.endswith("."):
            base = Path(name).stem
            if base.endswith(p[:-1]):
                return True
        elif p.endswith("_"):
            if name.startswith(p):
                return True
    return False


def is_excluded(filename: str, exclusions: list[str]) -> bool:
    """Check if a file matches any pattern in no_sync_files/unique_paths."""
    for pattern in exclusions:
        if pattern.endswith("/"):
            if filename.startswith(pattern):
                return True
        elif "*" in pattern:
            if fnmatch.fnmatch(filename, pattern):
                return True
        elif filename == pattern:
            return True
    return False


def load_codebase_contents(skip_paths: set[str]) -> dict[str, str]:
    """Pre-load searchable text files from the active codebase."""
    contents: dict[str, str] = {}
    extensions = {".py", ".sh", ".md", ".json", ".js", ".html", ".jinja"}
    skip_dirs = {".git", ".venv", "archive", "dps_archive"}
    root = Path(".")
    for p in root.rglob("*"):
        if any(d in p.parts for d in skip_dirs):
            continue
        if p.suffix not in extensions:
            continue
        rel = str(p).lstrip("./")
        if rel in skip_paths:
            continue
        try:
            contents[rel] = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass
    return contents


def main() -> None:
    pr.tic()
    pr.title("test_shadow_cleanup.py")

    parser = argparse.ArgumentParser(
        description="Find and optionally archive orphaned original files."
    )
    parser.add_argument("--folder", help="The specific folder to scan for orphans")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        dest="dry_run",
        help="Simulate archiving without moving files (default).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Actually archive files. Overrides --dry-run.",
    )
    args = parser.parse_args()
    dry_run = not args.apply

    if dry_run:
        pr.warning("DRY RUN — pass --apply to archive files")

    if not REGISTRY_PATH.exists():
        pr.no(f"Registry not found at {REGISTRY_PATH}")
        return

    registry: dict[str, object] = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    no_sync: list[str] = registry.get("no_sync_files", []) + registry.get(
        "unique_paths", []
    )  # type: ignore[operator]
    russian_copies: dict[str, str] = registry.get("russian_copies", {})  # type: ignore[assignment]
    sbs_copies: dict[str, str] = registry.get("sbs_copies", {})  # type: ignore[assignment]
    all_shadows_map: dict[str, str] = {**russian_copies, **sbs_copies}

    scan_folder = args.folder
    if not scan_folder:
        pr.no("Please provide a folder using --folder. Example: --folder db/")
        return

    pr.green("scanning folder")
    pr.yes(scan_folder)

    upstream_files: set[str] = set(
        run_git(["ls-tree", "-r", "as_upstream", "--name-only"])
    )
    current_files: list[str] = run_git(
        ["ls-tree", "-r", "HEAD", "--name-only", scan_folder]
    )

    orphans: list[str] = []
    for f in current_files:
        if is_excluded(f, no_sync):
            continue
        if f in all_shadows_map:
            continue
        if is_localized(f):
            continue
        if f not in upstream_files:
            orphans.append(f)

    pr.green("orphaned original files")
    pr.yes(str(len(orphans))) if not orphans else pr.no(str(len(orphans)))

    if not orphans:
        pr.toc()
        return

    pr.green("pre-loading codebase for usage check")
    skip: set[str] = {str(REGISTRY_PATH), "tests/test_shadow_cleanup.py"}
    searchable = load_codebase_contents(skip)
    pr.yes("done")

    archived = 0
    for orphan in orphans:
        orphan_name = Path(orphan).name
        orphan_stem = Path(orphan).stem

        direct_usages: list[str] = []
        for path, content in searchable.items():
            if orphan_name in content or (
                len(orphan_stem) > 5 and orphan_stem in content
            ):
                if Path(path).resolve() != Path(orphan).resolve():
                    direct_usages.append(path)

        shadows = [s for s, u in all_shadows_map.items() if u == orphan]
        shadow_usages: dict[str, list[str]] = {}
        for s in shadows:
            s_name = Path(s).name
            s_stem = Path(s).stem
            s_usages = [
                path
                for path, content in searchable.items()
                if (s_name in content or (len(s_stem) > 5 and s_stem in content))
                and Path(path).resolve() != Path(s).resolve()
            ]
            if s_usages:
                shadow_usages[s] = s_usages

        if direct_usages or shadow_usages:
            pr.warning(f"MANUAL INVESTIGATION REQUIRED: {orphan}")
            if direct_usages:
                pr.warning(f"  original referenced in: {direct_usages}")
            for s, usages in shadow_usages.items():
                pr.warning(f"  shadow {s} referenced in: {usages}")
        else:
            archive_base = (
                Path("scripts/dps_archive")
                if orphan.startswith("scripts/")
                else Path("archive/dps")
            )
            dest = archive_base / orphan
            if dry_run:
                pr.warning(f"[DRY RUN] would archive: {orphan} -> {dest}")
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                orphan_path = Path(orphan)
                if orphan_path.exists():
                    shutil.move(str(orphan_path), str(dest))
                    pr.green("archived")
                    pr.yes(orphan)
                    archived += 1
                    for s in shadows:
                        s_path = Path(s)
                        if s_path.exists():
                            s_dest = archive_base / s
                            s_dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(s_path), str(s_dest))
                            pr.green("  shadow archived")
                            pr.yes(s)

    if dry_run:
        pr.summary("dry run complete", f"{len(orphans)} orphans found, none archived")
    else:
        pr.summary("archived", str(archived))

    pr.toc()


if __name__ == "__main__":
    main()
