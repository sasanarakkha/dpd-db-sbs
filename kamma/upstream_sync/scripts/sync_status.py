#!/usr/bin/env python3

"""Derive a sync thread's current stage from artifact presence and print the next command."""

import json
import sys
from pathlib import Path

from kamma.upstream_sync.scripts.sync_triage import is_localized_noop
from tools.printer import printer as pr


def derive_stage(thread_dir: Path) -> tuple[str, str]:
    """Derive the current stage label and exact next command for a sync thread."""
    manifest_path = thread_dir / "prep_manifest.json"
    retrospective_path = thread_dir / "retrospective.md"
    dynamic_plan_path = thread_dir / "dynamic_plan.md"
    docs_translation_plan_path = thread_dir / "docs_translation_plan.md"

    if retrospective_path.exists():
        return (
            "Stage 5: Verification & After-sync (finalize)",
            f"uv run python3 kamma/upstream_sync/scripts/finalize_accepted_sync.py {thread_dir}",
        )

    if not manifest_path.exists():
        return (
            "Stage 1: Prep",
            f"uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py {thread_dir}",
        )

    manifest: dict[str, object] = json.loads(manifest_path.read_text(encoding="utf-8"))

    if docs_translation_plan_path.exists():
        return (
            "Stage 4.B: Docs Translation",
            "Execute docs_translation_plan.md file-by-file (FAST / sync-fast subagent).",
        )

    changed_upstream_paths = manifest.get("changed_upstream_paths", [])
    docs_pending = isinstance(changed_upstream_paths, list) and any(
        isinstance(path, str) and path.startswith("docs/")
        for path in changed_upstream_paths
    )

    if dynamic_plan_path.exists():
        if docs_pending:
            return (
                "Stage 4.A: Docs Analysis",
                f"uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py {thread_dir}",
            )
        return (
            "Stage 3: Execution & Verification",
            "Execute dynamic_plan.md item-by-item (FAST / sync-fast subagent).",
        )

    if is_localized_noop(manifest):
        return (
            "Fast-path (Stage 1 -> Commit 1 -> Stage 5)",
            f"uv run python3 kamma/upstream_sync/scripts/execute_sync.py {thread_dir}",
        )

    return (
        "Stage 2: Analysis",
        "Draft dynamic_plan.md (ADVANCED).",
    )


def main() -> None:
    pr.tic()
    pr.green_title("sync_status.py")

    if len(sys.argv) != 2:
        pr.red("Usage: sync_status.py <thread_dir>")
        sys.exit(1)

    thread_dir = Path(sys.argv[1])
    if not thread_dir.exists():
        pr.red(f"Thread directory not found at {thread_dir}")
        sys.exit(1)

    stage, command = derive_stage(thread_dir)
    pr.summary("stage", stage)
    pr.summary("next command", command)
    pr.toc()


if __name__ == "__main__":
    main()
