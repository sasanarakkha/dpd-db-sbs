#!/usr/bin/env python3

"""Generate a factual upstream sync report and manifest from an explicit upstream range."""

import argparse
import fnmatch
import json
import subprocess
from datetime import datetime
from pathlib import Path

from kamma.upstream_sync.scripts.registry_helper import (
    get_inspired_by_upstream_mapping,
    get_modified_upstream_paths,
    get_no_sync_files,
    get_registry_path,
    get_shadow_mappings_by_category,
    get_skip_sync_patterns,
    load_accepted_sync_state,
    load_registry,
)
from kamma.upstream_sync.scripts.sync_schema import AcceptedSyncState
from kamma.upstream_sync.scripts.validate_registry import validate_registry_core
from tools.printer import printer as pr

type GitChange = tuple[str, str]
type MappedAction = dict[str, str]
type SourceAction = dict[str, str]


def match_sources(
    path: str, source_map: dict[str, list[SourceAction]]
) -> list[SourceAction] | None:
    """Return actions for *path* from *source_map*, or None if no mapping matches."""
    for src, actions in source_map.items():
        if src.endswith("/") and path.startswith(src):
            return actions
        if path == src:
            return actions
    return None


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


def get_local_tracked_files() -> list[str]:
    """Return all git-tracked local file paths, respecting .gitignore."""
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "ls-files", "-z"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [path for path in result.stdout.split("\0") if path]


def get_upstream_tree_paths(ref: str) -> set[str]:
    """Return every file path present in the upstream tree at *ref*."""
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "ls-tree",
            "-r",
            "-z",
            "--name-only",
            ref,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return {path for path in result.stdout.split("\0") if path}


def get_upstream_ever_added_paths(ref: str) -> set[str]:
    """Return every file path ever added in upstream's full history up to *ref*."""
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "log",
            ref,
            "--diff-filter=A",
            "--name-only",
            "-z",
            "--pretty=format:",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return {path for path in result.stdout.split("\0") if path}


def get_upstream_changes(from_sha: str, to_sha: str) -> list[GitChange]:
    """Return list of changed upstream paths for the explicit sync range."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status", "-z", from_sha, to_sha],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"failed to diff upstream range '{from_sha}..{to_sha}'"
        ) from exc

    return parse_name_status_z(result.stdout)


def parse_name_status_z(output: str) -> list[GitChange]:
    """Parse `git diff --name-status -z` output without corrupting spaced paths."""
    fields = output.split("\0")
    if fields and fields[-1] == "":
        fields.pop()

    changes: list[GitChange] = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if not status:
            continue

        if status.startswith("R"):
            if index + 1 >= len(fields):
                raise RuntimeError("malformed NUL-delimited git rename output")
            old_path = fields[index]
            new_path = fields[index + 1]
            index += 2
            changes.extend([("D", old_path), ("A", new_path)])
            continue

        if index >= len(fields):
            raise RuntimeError("malformed NUL-delimited git diff output")
        changes.append((status, fields[index]))
        index += 1

    return changes


class PrepAnalyzer:
    """Build the Stage 1 factual report and machine-readable manifest."""

    def __init__(self, thread_dir: str | Path):
        self.thread_dir = Path(thread_dir)
        self.registry = load_registry()
        self.accepted_sync: AcceptedSyncState = load_accepted_sync_state()
        self.skip_patterns = get_skip_sync_patterns(self.registry)
        self.no_sync_files = get_no_sync_files(self.registry)
        self.modified_upstream = set(get_modified_upstream_paths(self.registry))
        self.shadow_mappings_by_category = get_shadow_mappings_by_category(
            self.registry
        )
        self.inspired_mappings = get_inspired_by_upstream_mapping(self.registry)

    def _path_exists(self, path: str) -> bool:
        """Return True if path exists in the local worktree."""
        return Path(path).exists()

    def _all_registered_local_paths(self) -> list[str]:
        """Return all registered local paths from the registry."""
        paths: list[str] = []
        for mapping in [
            self.registry.russian_copies,
            self.registry.sbs_copies,
            self.registry.dps_copies,
            self.registry.tamil_copies,
        ]:
            paths.extend(mapping.keys())
        paths.extend(self.registry.inspired_by_upstream.keys())
        paths.extend(self.registry.unique_paths)
        return paths

    def _is_collision(self, path: str) -> tuple[bool, str]:
        """Return (collides, reason) for an added upstream path."""
        if self._path_exists(path):
            return True, "exists in local worktree"
        for local_path in self._all_registered_local_paths():
            if local_path.endswith("/"):
                if path.startswith(local_path):
                    return True, f"collides with registered local path '{local_path}'"
            elif path == local_path:
                return True, f"collides with registered local path '{local_path}'"
        return False, ""

    def _is_registered_local(self, path: str) -> bool:
        """Return True if path is covered by any registered local path entry."""
        for local_path in self._all_registered_local_paths():
            if local_path.endswith("/"):
                if path.startswith(local_path):
                    return True
            elif path == local_path:
                return True
        return False

    def compute_unregistered_audit(self, to_sha: str) -> tuple[list[str], list[str]]:
        """Scan the full local tree for unregistered or upstream-deleted-orphan paths.

        Returns (unregistered_local_paths, upstream_deleted_orphans):
        - unregistered_local_paths: local files absent from the upstream tree at
          *to_sha*, never present anywhere in upstream history, and not covered
          by any registry category.
        - upstream_deleted_orphans: local files absent from the upstream tree at
          *to_sha* but found somewhere in upstream's full history (i.e. upstream
          deleted them at some point) — needs a human keep/delete decision.
        """
        current_upstream_paths = get_upstream_tree_paths(to_sha)
        ever_upstream_paths = get_upstream_ever_added_paths(to_sha)

        unregistered: list[str] = []
        orphans: list[str] = []

        for path in get_local_tracked_files():
            if self.is_skipped(path):
                continue
            if path in current_upstream_paths:
                continue
            if self._is_registered_local(path):
                continue
            if path in ever_upstream_paths:
                orphans.append(path)
            else:
                unregistered.append(path)

        return sorted(unregistered), sorted(orphans)

    def is_skipped(self, path: str) -> bool:
        """Return True when the path is outside sync scanning scope."""
        for entry in self.no_sync_files:
            if path == entry or path.startswith(entry.rstrip("/") + "/"):
                return True
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
        from_sha = self.accepted_sync.last_accepted_upstream_sha
        if from_sha == "BOOTSTRAP_REQUIRED":
            raise ValueError("accepted sync state is not bootstrapped")

        target_ref = self.accepted_sync.last_accepted_upstream_ref
        to_sha = resolve_target_upstream_sha(target_ref)
        changes = get_upstream_changes(from_sha, to_sha)

        tracked_modified: list[str] = []
        shadow_sources_modified: list[tuple[str, list[str]]] = []
        inspired_sources_modified: list[tuple[str, list[str]]] = []
        untracked: list[str] = []
        deleted: list[str] = []
        blocker_paths: list[str] = []
        discuss_paths: list[str] = []
        needs_classification_paths: list[str] = []
        collision_reasons: dict[str, str] = {}

        source_to_shadows: dict[str, list[SourceAction]] = {}
        for category, mapping in self.shadow_mappings_by_category.items():
            for shadow, entry in mapping.items():
                source_to_shadows.setdefault(entry.upstream, []).append(
                    {
                        "category": category,
                        "local_path": shadow,
                        "source_path": entry.upstream,
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
            entry.path
            for entry in self.registry.modified_upstream_files
            if entry.discuss
        }

        mapped_actions: dict[str, list[MappedAction]] = {}
        changed_upstream_paths: set[str] = set()

        for status, path in changes:
            if self.is_skipped(path):
                continue

            if status == "D":
                deleted.append(path)
                blocker_paths.append(path)
                shadow_actions = match_sources(path, source_to_shadows)
                if shadow_actions is not None:
                    mapped_actions[path] = self.build_mapped_actions(
                        shadow_actions, path
                    )
                inspired_actions = match_sources(path, source_to_inspired)
                if inspired_actions is not None:
                    mapped_actions.setdefault(path, []).extend(
                        self.build_mapped_actions(inspired_actions, path)
                    )
                continue

            changed_upstream_paths.add(path)

            if path in self.modified_upstream:
                tracked_modified.append(path)
                if path in discuss_lookup:
                    discuss_paths.append(path)

            found_source = False

            shadow_actions = match_sources(path, source_to_shadows)
            if shadow_actions is not None:
                manifest_actions = self.build_mapped_actions(shadow_actions, path)
                shadow_sources_modified.append(
                    (path, [action["local_path"] for action in manifest_actions])
                )
                mapped_actions[path] = manifest_actions
                found_source = True

            inspired_actions = match_sources(path, source_to_inspired)
            if inspired_actions is not None:
                manifest_actions = self.build_mapped_actions(inspired_actions, path)
                inspired_sources_modified.append(
                    (path, [action["local_path"] for action in manifest_actions])
                )
                mapped_actions.setdefault(path, []).extend(manifest_actions)
                found_source = True

            if not found_source and (
                status == "A" or path not in self.modified_upstream
            ):
                if status == "A":
                    collides, reason = self._is_collision(path)
                    if collides:
                        untracked.append(path)
                        blocker_paths.append(path)
                        collision_reasons[path] = reason
                    else:
                        needs_classification_paths.append(path)
                else:
                    untracked.append(path)

        unregistered_local_paths, upstream_deleted_orphans = (
            self.compute_unregistered_audit(to_sha)
        )

        report = self.generate_report(
            tracked=tracked_modified,
            shadows=shadow_sources_modified,
            inspired=inspired_sources_modified,
            untracked=untracked,
            deleted=deleted,
            blockers=sorted(set(blocker_paths)),
            needs_classification=sorted(needs_classification_paths),
            collision_reasons=collision_reasons,
            from_sha=from_sha,
            to_sha=to_sha,
            unregistered_local_paths=unregistered_local_paths,
            upstream_deleted_orphans=upstream_deleted_orphans,
        )
        manifest = self.generate_manifest(
            from_sha=from_sha,
            to_sha=to_sha,
            changed_upstream_paths=sorted(changed_upstream_paths),
            deleted_upstream_paths=sorted(set(deleted)),
            blocker_paths=sorted(set(blocker_paths)),
            needs_classification_paths=sorted(needs_classification_paths),
            mapped_actions=mapped_actions,
            discuss_paths=sorted(set(discuss_paths)),
            unregistered_local_paths=unregistered_local_paths,
            upstream_deleted_orphans=upstream_deleted_orphans,
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
        needs_classification: list[str],
        collision_reasons: dict[str, str],
        from_sha: str,
        to_sha: str,
        unregistered_local_paths: list[str],
        upstream_deleted_orphans: list[str],
    ) -> str:
        """Render the human-readable Stage 1 report."""
        lines = ["# Upstream Sync Preparation Report\n"]
        lines.append("## Upstream Range")
        lines.append(f"- From: `{from_sha}`")
        lines.append(f"- To: `{to_sha}`")
        lines.append("")

        lines.append("## Registry Validation Status")
        raw_registry: dict[str, object] = json.loads(
            get_registry_path().read_text(encoding="utf-8")
        )
        errors = validate_registry_core(raw_registry)
        if not errors:
            lines.append("OK: Registry is valid.\n")
        else:
            lines.append("FAIL: Registry validation errors:")
            for error in errors:
                lines.append(f"- {error}")
            lines.append("")

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

        lines.append("## Needs Classification (Stage 2)")
        if needs_classification:
            lines.append(
                "These upstream additions have no local collision. Register them in `registry.json` during Stage 2."
            )
            for path in needs_classification:
                lines.append(f"- {path}")
        else:
            lines.append("_No paths need classification._")
        lines.append("")

        lines.append("## Unregistered Local Paths (Stage 2)")
        if unregistered_local_paths:
            lines.append(
                "These local files have no upstream counterpart (current or historical) and are not "
                "covered by any registry category. Classify them in `registry.json`/SMD during Stage 2 "
                "(typically `unique_paths`, or a shadow/inspired category if a counterpart exists)."
            )
            for path in unregistered_local_paths:
                lines.append(f"- {path}")
        else:
            lines.append("_No unregistered local paths._")
        lines.append("")

        lines.append("## Upstream-Deleted Orphans (Stage 2)")
        if upstream_deleted_orphans:
            lines.append(
                "These local files match a path upstream once had but has since deleted. Decide during "
                "Stage 2 whether to keep them as an intentional fork divergence (register the decision) or "
                "delete them locally to match upstream."
            )
            for path in upstream_deleted_orphans:
                lines.append(f"- {path}")
        else:
            lines.append("_No upstream-deleted orphans._")
        lines.append("")

        lines.append("## Stage 1 Blocker Paths")
        if blockers:
            lines.append(
                "Resolve these paths before running `execute_sync.py`; rerun prep after registry/SMD or run-specific scope changes."
            )
            for path in blockers:
                reason = collision_reasons.get(path)
                suffix = f" ({reason})" if reason else ""
                lines.append(f"- {path}{suffix}")
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
        needs_classification_paths: list[str],
        mapped_actions: dict[str, list[MappedAction]],
        discuss_paths: list[str],
        unregistered_local_paths: list[str],
        upstream_deleted_orphans: list[str],
    ) -> dict[str, object]:
        """Return the machine-readable Stage 1 manifest."""
        return {
            "from_upstream_sha": from_sha,
            "to_upstream_sha": to_sha,
            "target_upstream_ref": self.accepted_sync.last_accepted_upstream_ref,
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "changed_upstream_paths": changed_upstream_paths,
            "deleted_upstream_paths": deleted_upstream_paths,
            "blocker_paths": blocker_paths,
            "needs_classification_paths": needs_classification_paths,
            "mapped_actions": mapped_actions,
            "discuss_paths": discuss_paths,
            "unregistered_local_paths": unregistered_local_paths,
            "upstream_deleted_orphans": upstream_deleted_orphans,
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
