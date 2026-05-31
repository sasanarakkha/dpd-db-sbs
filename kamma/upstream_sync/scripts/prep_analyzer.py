#!/usr/bin/env python3

"""Generate a factual upstream sync report and manifest from an explicit upstream range."""

import argparse
import fnmatch
import json
import subprocess
from datetime import datetime
from pathlib import Path

from kamma.upstream_sync.scripts.registry_helper import (
    AcceptedSyncState,
    get_inspired_by_upstream_mapping,
    get_modified_upstream_paths,
    get_shadow_mappings_by_category,
    get_skip_sync_patterns,
    load_accepted_sync_state,
    load_registry,
)
from kamma.upstream_sync.scripts.validate_registry import validate_registry_core
from kamma.upstream_sync.scripts.verify_smd_coverage import (
    check_rubric,
    collect_registry_paths,
    extract_all_smd_entries,
)
from tools.printer import printer as pr

type GitChange = tuple[str, str]
type MappedAction = dict[str, str]
type SourceAction = dict[str, str]


def expand_git_change(status: str, path: str) -> list[GitChange]:
    """Represent git renames as a factual delete plus add pair."""
    if not status.startswith("R"):
        return [(status, path)]

    parts = path.split()
    if len(parts) != 2:
        return [(status, path)]
    old_path, new_path = parts
    return [("D", old_path), ("A", new_path)]


def resolve_target_upstream_sha(ref: str = "upstream/main") -> str:
    """Resolve a git ref to a concrete commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", ref],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"failed to resolve upstream ref '{ref}'") from exc
    return result.stdout.strip()


def get_upstream_changes(from_sha: str, to_sha: str) -> list[GitChange]:
    """Return list of changed upstream paths for the explicit sync range."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status", from_sha, to_sha],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"failed to diff upstream range '{from_sha}..{to_sha}'"
        ) from exc

    changes: list[GitChange] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            changes.extend(expand_git_change(status, f"{parts[1]} {parts[2]}"))
        else:
            changes.append((status, parts[1]))
    return changes


class PrepAnalyzer:
    """Build the Stage 1 factual report and machine-readable manifest."""

    def __init__(self, thread_dir: str | Path):
        self.thread_dir = Path(thread_dir)
        self.registry = load_registry()
        self.accepted_sync: AcceptedSyncState = load_accepted_sync_state()
        self.skip_patterns = get_skip_sync_patterns(self.registry)
        self.modified_upstream = set(get_modified_upstream_paths(self.registry))
        self.shadow_mappings_by_category = get_shadow_mappings_by_category(
            self.registry
        )
        self.inspired_mappings = get_inspired_by_upstream_mapping(self.registry)

    def is_skipped(self, path: str) -> bool:
        """Return True when the path is outside sync scanning scope."""
        for pattern in self.skip_patterns:
            if pattern.endswith("/") and path.startswith(pattern):
                return True
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    def build_mapped_action(
        self, category: str, local_path: str, source_path: str, changed_path: str
    ) -> MappedAction:
        """Build one mapped action, including exact local target path when derivable."""
        action: MappedAction = {"category": category, "local_path": local_path}
        if source_path.endswith("/") and local_path.endswith("/"):
            relative_path = changed_path.removeprefix(source_path)
            action["local_target_path"] = f"{local_path}{relative_path}"
        else:
            action["local_target_path"] = local_path
        return action

    def build_mapped_actions(
        self, actions: list[SourceAction], changed_path: str
    ) -> list[MappedAction]:
        """Build manifest actions for a changed upstream path."""
        return [
            self.build_mapped_action(
                action["category"],
                action["local_path"],
                action["source_path"],
                changed_path,
            )
            for action in actions
        ]

    def run(self) -> None:
        """Generate the Stage 1 report and manifest in the thread folder."""
        from_sha = self.accepted_sync["last_accepted_upstream_sha"]
        if from_sha == "BOOTSTRAP_REQUIRED":
            raise ValueError("accepted sync state is not bootstrapped")

        target_ref = self.accepted_sync["last_accepted_upstream_ref"]
        to_sha = resolve_target_upstream_sha(target_ref)
        changes = [
            expanded_change
            for status, path in get_upstream_changes(from_sha, to_sha)
            for expanded_change in expand_git_change(status, path)
        ]

        tracked_modified: list[str] = []
        shadow_sources_modified: list[tuple[str, list[str]]] = []
        inspired_sources_modified: list[tuple[str, list[str]]] = []
        untracked: list[str] = []
        deleted: list[str] = []
        blocker_paths: list[str] = []
        discuss_paths: list[str] = []

        source_to_shadows: dict[str, list[SourceAction]] = {}
        for category, mapping in self.shadow_mappings_by_category.items():
            for shadow, source in mapping.items():
                source_to_shadows.setdefault(source, []).append(
                    {
                        "category": category,
                        "local_path": shadow,
                        "source_path": source,
                    }
                )

        source_to_inspired: dict[str, list[SourceAction]] = {}
        for local, source in self.inspired_mappings.items():
            source_to_inspired.setdefault(source, []).append(
                {
                    "category": "inspired_by_upstream",
                    "local_path": local,
                    "source_path": source,
                }
            )

        discuss_lookup = {
            entry["path"]
            for entry in self.registry.get("modified_upstream_files", [])  # type: ignore[union-attr]
            if isinstance(entry, dict) and entry.get("discuss") is True
        }

        mapped_actions: dict[str, list[MappedAction]] = {}
        changed_upstream_paths: set[str] = set()

        for status, path in changes:
            if self.is_skipped(path):
                continue

            if status == "D":
                deleted.append(path)
                blocker_paths.append(path)
                for src, actions in source_to_shadows.items():
                    if src.endswith("/") and path.startswith(src):
                        mapped_actions[path] = self.build_mapped_actions(actions, path)
                        break
                    if path == src:
                        mapped_actions[path] = self.build_mapped_actions(actions, path)
                        break

                for src, actions in source_to_inspired.items():
                    if src.endswith("/") and path.startswith(src):
                        mapped_actions.setdefault(path, []).extend(
                            self.build_mapped_actions(actions, path)
                        )
                        break
                    if path == src:
                        mapped_actions.setdefault(path, []).extend(
                            self.build_mapped_actions(actions, path)
                        )
                        break
                continue

            changed_upstream_paths.add(path)

            if path in self.modified_upstream:
                tracked_modified.append(path)
                if path in discuss_lookup:
                    discuss_paths.append(path)

            found_source = False

            for src, actions in source_to_shadows.items():
                if src.endswith("/") and path.startswith(src):
                    manifest_actions = self.build_mapped_actions(actions, path)
                    shadow_sources_modified.append(
                        (path, [action["local_path"] for action in manifest_actions])
                    )
                    mapped_actions[path] = manifest_actions
                    found_source = True
                    break
                if path == src:
                    manifest_actions = self.build_mapped_actions(actions, path)
                    shadow_sources_modified.append(
                        (path, [action["local_path"] for action in manifest_actions])
                    )
                    mapped_actions[path] = manifest_actions
                    found_source = True
                    break

            for src, actions in source_to_inspired.items():
                if src.endswith("/") and path.startswith(src):
                    manifest_actions = self.build_mapped_actions(actions, path)
                    inspired_sources_modified.append(
                        (path, [action["local_path"] for action in manifest_actions])
                    )
                    mapped_actions.setdefault(path, []).extend(manifest_actions)
                    found_source = True
                    break
                if path == src:
                    manifest_actions = self.build_mapped_actions(actions, path)
                    inspired_sources_modified.append(
                        (path, [action["local_path"] for action in manifest_actions])
                    )
                    mapped_actions.setdefault(path, []).extend(manifest_actions)
                    found_source = True
                    break

            if status == "A" or (
                not found_source and path not in self.modified_upstream
            ):
                untracked.append(path)
                if status == "A" and not found_source:
                    blocker_paths.append(path)

        report = self.generate_report(
            tracked=tracked_modified,
            shadows=shadow_sources_modified,
            inspired=inspired_sources_modified,
            untracked=untracked,
            deleted=deleted,
            blockers=sorted(set(blocker_paths)),
            from_sha=from_sha,
            to_sha=to_sha,
        )
        manifest = self.generate_manifest(
            from_sha=from_sha,
            to_sha=to_sha,
            changed_upstream_paths=sorted(changed_upstream_paths),
            deleted_upstream_paths=sorted(set(deleted)),
            blocker_paths=sorted(set(blocker_paths)),
            mapped_actions=mapped_actions,
            discuss_paths=sorted(set(discuss_paths)),
        )

        self.thread_dir.mkdir(parents=True, exist_ok=True)
        report_path = self.thread_dir / "prep_report.md"
        report_path.write_text(report, encoding="utf-8")
        manifest_path = self.thread_dir / "prep_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )
        pr.green(f"Wrote report to {report_path}")
        pr.green(f"Wrote manifest to {manifest_path}")

    def generate_report(
        self,
        tracked: list[str],
        shadows: list[tuple[str, list[str]]],
        inspired: list[tuple[str, list[str]]],
        untracked: list[str],
        deleted: list[str],
        blockers: list[str],
        from_sha: str,
        to_sha: str,
    ) -> str:
        """Render the human-readable Stage 1 report."""
        lines = ["# Upstream Sync Preparation Report\n"]
        lines.append("## Upstream Range")
        lines.append(f"- From: `{from_sha}`")
        lines.append(f"- To: `{to_sha}`")
        lines.append("")

        lines.append("## Registry Validation Status")
        errors = validate_registry_core(self.registry)
        if not errors:
            lines.append("OK: Registry is valid.\n")
        else:
            lines.append("FAIL: Registry validation errors:")
            for error in errors:
                lines.append(f"- {error}")
            lines.append("")

        lines.append("## SMD Coverage Status")
        smd_dir = Path("kamma/upstream_sync/smd")
        try:
            smd_entries = extract_all_smd_entries(smd_dir)
            all_paths = collect_registry_paths(self.registry)
            gaps: list[str] = []
            rubric_fails: list[str] = []
            for path, category in all_paths:
                if path not in smd_entries:
                    gaps.append(f"MISSING: {path} [{category}]")
                else:
                    rubric_fails.extend(check_rubric(path, category, smd_entries[path]))

            if not gaps and not rubric_fails:
                lines.append("OK: SMD coverage is complete and rubric-compliant.\n")
            else:
                if gaps:
                    lines.append("FAIL: Missing SMD entries:")
                    for gap in gaps:
                        lines.append(f"- {gap}")
                if rubric_fails:
                    lines.append("WARN: SMD rubric failures:")
                    for failure in rubric_fails:
                        lines.append(f"- {failure}")
                lines.append("")
        except Exception as exc:
            lines.append(f"FAIL: Error checking SMD coverage: {exc}\n")

        lines.append("## Modified - Tracked Files")
        if tracked:
            for path in sorted(set(tracked)):
                lines.append(f"- {path}")
        else:
            lines.append("_No tracked files modified._")
        lines.append("")

        lines.append("## Modified - Shadow Sources")
        if shadows:
            for src, shadows_list in sorted(shadows):
                lines.append(f"- `{src}` -> shadows: {', '.join(shadows_list)}")
        else:
            lines.append("_No shadow sources modified._")
        lines.append("")

        lines.append("## Modified - Inspired Sources")
        if inspired:
            for src, inspired_list in sorted(inspired):
                lines.append(f"- `{src}` -> inspired: {', '.join(inspired_list)}")
        else:
            lines.append("_No inspired sources modified._")
        lines.append("")

        lines.append("## New Or Unmapped Upstream Changes")
        if untracked:
            for path in sorted(set(untracked)):
                lines.append(f"- {path}")
        else:
            lines.append("_No new or unmapped upstream changes._")
        lines.append("")

        if deleted:
            lines.append("## Deleted Files")
            for path in sorted(set(deleted)):
                lines.append(f"- {path}")
            lines.append("")

        lines.append("## Stage 1 Blocker Paths")
        if blockers:
            lines.append(
                "Resolve these paths before running `execute_sync.py`; rerun prep after registry/SMD or run-specific scope changes."
            )
            for path in blockers:
                lines.append(f"- {path}")
        else:
            lines.append("_No Stage 1 blockers._")
        lines.append("")

        return "\n".join(lines)

    def generate_manifest(
        self,
        from_sha: str,
        to_sha: str,
        changed_upstream_paths: list[str],
        deleted_upstream_paths: list[str],
        blocker_paths: list[str],
        mapped_actions: dict[str, list[MappedAction]],
        discuss_paths: list[str],
    ) -> dict[str, object]:
        """Return the machine-readable Stage 1 manifest."""
        return {
            "from_upstream_sha": from_sha,
            "to_upstream_sha": to_sha,
            "target_upstream_ref": self.accepted_sync["last_accepted_upstream_ref"],
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "changed_upstream_paths": changed_upstream_paths,
            "deleted_upstream_paths": deleted_upstream_paths,
            "blocker_paths": blocker_paths,
            "mapped_actions": mapped_actions,
            "discuss_paths": discuss_paths,
        }


def main() -> None:
    """Parse arguments and generate the Prep report and manifest."""
    parser = argparse.ArgumentParser()
    parser.add_argument("thread_dir")
    args = parser.parse_args()

    analyzer = PrepAnalyzer(args.thread_dir)
    analyzer.run()


if __name__ == "__main__":
    main()
