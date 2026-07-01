#!/usr/bin/env python3

"""Derive a sync thread's current stage from artifact presence and print the next command."""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from kamma.upstream_sync.scripts.sync_triage import is_localized_noop
from tools.printer import printer as pr


@dataclass
class StageDescriptor:
    """Machine-readable description of a sync thread's current stage."""

    stage: str
    next_command: str
    owner: str
    dispatch: str
    gate_before: str | None
    gate_after: str | None
    reads: list[str]
    produces: list[str]
    stop_condition: str


def derive_stage(thread_dir: Path) -> StageDescriptor:
    """Derive the current stage descriptor for a sync thread."""
    manifest_path = thread_dir / "prep_manifest.json"
    retrospective_path = thread_dir / "retrospective.md"
    dynamic_plan_path = thread_dir / "dynamic_plan.md"
    docs_translation_plan_path = thread_dir / "docs_translation_plan.md"

    if retrospective_path.exists():
        return StageDescriptor(
            stage="Stage 5: Verification & After-sync (finalize)",
            next_command=f"uv run python3 kamma/upstream_sync/scripts/finalize_accepted_sync.py {thread_dir}",
            owner="FAST",
            dispatch="sync-fast",
            gate_before="Stage 5 acceptance (user says 'all is good, proceed')",
            gate_after=None,
            reads=["retrospective.md"],
            produces=["accepted_sync.json (updated)"],
            stop_condition="finalize_accepted_sync.py completes",
        )

    if not manifest_path.exists():
        return StageDescriptor(
            stage="Stage 1: Prep",
            next_command=f"uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py {thread_dir}",
            owner="FAST",
            dispatch="sync-fast",
            gate_before=None,
            gate_after="Commit 1 (upstream pull)",
            reads=[],
            produces=["prep_report.md", "prep_manifest.json"],
            stop_condition="prep_manifest.json exists and blocker_paths/discuss_paths resolved",
        )

    manifest: dict[str, object] = json.loads(manifest_path.read_text(encoding="utf-8"))

    if docs_translation_plan_path.exists():
        return StageDescriptor(
            stage="Stage 4.B: Docs Translation",
            next_command="Execute docs_translation_plan.md file-by-file (FAST / sync-fast subagent).",
            owner="FAST",
            dispatch="sync-fast",
            gate_before="docs_translation_plan.md approval",
            gate_after="Commit (docs translation)",
            reads=["docs_translation_plan.md"],
            produces=["docs_rus/* files", "handoff.md (updated)"],
            stop_condition="check_docs_parity.py --strict passes and commit prepared",
        )

    changed_upstream_paths = manifest.get("changed_upstream_paths", [])
    docs_pending = isinstance(changed_upstream_paths, list) and any(
        isinstance(path, str) and path.startswith("docs/")
        for path in changed_upstream_paths
    )

    if dynamic_plan_path.exists():
        if docs_pending:
            return StageDescriptor(
                stage="Stage 4.A: Docs Analysis",
                next_command=f"uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py {thread_dir}",
                owner="ADVANCED",
                dispatch="self",
                gate_before=None,
                gate_after="docs_translation_plan.md approval",
                reads=["prep_manifest.json"],
                produces=["docs_parity_report.md", "docs_translation_plan.md"],
                stop_condition="docs_translation_plan.md written and presented for approval",
            )
        return StageDescriptor(
            stage="Stage 3: Execution & Verification",
            next_command="Execute dynamic_plan.md item-by-item (FAST / sync-fast subagent).",
            owner="FAST",
            dispatch="sync-fast",
            gate_before=None,
            gate_after="Commit 2 (manual merge)",
            reads=["dynamic_plan.md", "prep_manifest.json"],
            produces=["handoff.md (updated)"],
            stop_condition="All items in dynamic_plan.md marked [x]",
        )

    if is_localized_noop(manifest):
        return StageDescriptor(
            stage="Fast-path (Stage 1 -> Commit 1 -> Stage 5)",
            next_command=f"uv run python3 kamma/upstream_sync/scripts/execute_sync.py {thread_dir}",
            owner="FAST",
            dispatch="sync-fast",
            gate_before=None,
            gate_after="Commit 1 (upstream pull)",
            reads=["prep_manifest.json"],
            produces=["retrospective.md (via Stage 5)"],
            stop_condition="execute_sync.py completes and Stage 5 retrospective written",
        )

    return StageDescriptor(
        stage="Stage 2: Analysis",
        next_command="Draft dynamic_plan.md (ADVANCED).",
        owner="ADVANCED",
        dispatch="self",
        gate_before=None,
        gate_after="Stage 2 approval (dynamic_plan.md presented to user)",
        reads=["prep_manifest.json", "prep_report.md"],
        produces=["dynamic_plan.md"],
        stop_condition="dynamic_plan.md written and approved by user",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("thread_dir", type=Path)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human-readable summary.",
    )
    args = parser.parse_args()

    if not args.thread_dir.exists():
        pr.red(f"Thread directory not found at {args.thread_dir}")
        sys.exit(1)

    descriptor = derive_stage(args.thread_dir)

    if args.json:
        print(json.dumps(asdict(descriptor), indent=2))
        return

    pr.tic()
    pr.green_title("sync_status.py")
    pr.summary("stage", descriptor.stage)
    pr.summary("next command", descriptor.next_command)
    pr.summary("owner", descriptor.owner)
    pr.summary("dispatch", descriptor.dispatch)
    pr.summary("gate before", descriptor.gate_before or "-")
    pr.summary("gate after", descriptor.gate_after or "-")
    pr.summary("reads", ", ".join(descriptor.reads) or "-")
    pr.summary("produces", ", ".join(descriptor.produces) or "-")
    pr.summary("stop condition", descriptor.stop_condition)
    pr.toc()


if __name__ == "__main__":
    main()
