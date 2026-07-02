#!/usr/bin/env python3

"""Derive a sync thread's current stage from artifact presence and print the next command."""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from kamma.upstream_sync.scripts.sync_triage import is_localized_noop
from tools.printer import printer as pr

GUIDE_PATH = Path(__file__).resolve().parent.parent / "guide.md"

HEADING_PATTERN = re.compile(r"^(#{1,6})\s")


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
    guide_anchor: str


def derive_stage(thread_dir: Path) -> StageDescriptor:
    """Derive the current stage descriptor for a sync thread.

    Known limitation: on the non-fast-path, the Stage 3 -> Stage 4 verification
    gate (all `dynamic_plan.md` items marked `[x]`) is not distinguished from
    Stage 3 itself — that would require parsing `dynamic_plan.md` checkboxes,
    which is out of scope. `derive_stage` only advances past Stage 3 once
    `retrospective.md` exists.
    """
    manifest_path = thread_dir / "prep_manifest.json"
    retrospective_path = thread_dir / "retrospective.md"
    dynamic_plan_path = thread_dir / "dynamic_plan.md"

    if retrospective_path.exists():
        return StageDescriptor(
            stage="Stage 4: Verification & After-sync (finalize)",
            next_command=f"uv run python3 kamma/upstream_sync/scripts/finalize_accepted_sync.py {thread_dir}",
            owner="FAST",
            dispatch="sync-fast",
            gate_before="Stage 4 acceptance (user says 'all is good, proceed')",
            gate_after=None,
            reads=["retrospective.md"],
            produces=["accepted_sync.json (updated)"],
            stop_condition="finalize_accepted_sync.py completes",
            guide_anchor="### Stage 4: Verification & After-sync (ADVANCED Acceptance)",
        )

    if not manifest_path.exists():
        return StageDescriptor(
            stage="Stage 1: Prep",
            next_command=f"uv run python3 kamma/upstream_sync/scripts/stage1.py {thread_dir}",
            owner="FAST",
            dispatch="sync-fast",
            gate_before=None,
            gate_after="Commit 1 (upstream pull)",
            reads=[],
            produces=["prep_report.md", "prep_manifest.json"],
            stop_condition="prep_manifest.json exists and blocker_paths/discuss_paths resolved",
            guide_anchor="### Stage 1: Prep (FAST Factual Collection)",
        )

    manifest: dict[str, object] = json.loads(manifest_path.read_text(encoding="utf-8"))

    if dynamic_plan_path.exists():
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
            guide_anchor="### Stage 3: Execution & Verification (FAST Implementation)",
        )

    if is_localized_noop(manifest):
        if (thread_dir / "execute_sync_done.json").exists():
            return StageDescriptor(
                stage="Fast-path (Stage 4: write retrospective + finalize)",
                next_command=(
                    "Write retrospective.md, then run "
                    f"uv run python3 kamma/upstream_sync/scripts/finalize_accepted_sync.py {thread_dir}"
                ),
                owner="FAST",
                dispatch="sync-fast",
                gate_before="Stage 4 acceptance",
                gate_after=None,
                reads=["prep_manifest.json", "execute_sync_done.json"],
                produces=["retrospective.md", "accepted_sync.json (updated)"],
                stop_condition="finalize_accepted_sync.py completes",
                guide_anchor="### Stage 4: Verification & After-sync (ADVANCED Acceptance)",
            )
        return StageDescriptor(
            stage="Fast-path (Stage 1 -> Commit 1 -> Stage 4)",
            next_command=f"uv run python3 kamma/upstream_sync/scripts/execute_sync.py {thread_dir}",
            owner="FAST",
            dispatch="sync-fast",
            gate_before=None,
            gate_after="Commit 1 (upstream pull)",
            reads=["prep_manifest.json"],
            produces=["retrospective.md (via Stage 4)"],
            stop_condition="execute_sync.py completes and Stage 4 retrospective written",
            guide_anchor="### Stage 1: Prep (FAST Factual Collection)",
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
        guide_anchor="### Stage 2: Analysis (ADVANCED Strategic Planning)",
    )


def extract_guide_section(guide_text: str, anchor: str) -> str:
    """Return the guide.md section starting at *anchor*, up to the next same-or-higher heading."""
    lines = guide_text.splitlines()
    anchor_index = next(
        (i for i, line in enumerate(lines) if line.strip() == anchor.strip()), None
    )
    if anchor_index is None:
        raise ValueError(f"guide_anchor not found in guide.md: {anchor!r}")

    heading_match = HEADING_PATTERN.match(lines[anchor_index])
    if heading_match is None:
        raise ValueError(f"guide_anchor is not a markdown heading: {anchor!r}")
    anchor_level = len(heading_match.group(1))

    end_index = len(lines)
    for i in range(anchor_index + 1, len(lines)):
        match = HEADING_PATTERN.match(lines[i])
        if match and len(match.group(1)) <= anchor_level:
            end_index = i
            break

    return "\n".join(lines[anchor_index:end_index]).strip() + "\n"


def print_stage_instructions(descriptor: StageDescriptor, guide_path: Path) -> int:
    """Print the guide.md section for the descriptor's stage; return an exit code."""
    guide_text = guide_path.read_text(encoding="utf-8")
    try:
        section = extract_guide_section(guide_text, descriptor.guide_anchor)
    except ValueError as exc:
        pr.red(str(exc))
        return 1
    print(section)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("thread_dir", type=Path)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human-readable summary.",
    )
    parser.add_argument(
        "--instructions",
        action="store_true",
        help="Print the guide.md section for the current stage instead of a summary.",
    )
    args = parser.parse_args()

    if not args.thread_dir.exists():
        pr.red(f"Thread directory not found at {args.thread_dir}")
        sys.exit(1)

    descriptor = derive_stage(args.thread_dir)

    if args.instructions:
        sys.exit(print_stage_instructions(descriptor, GUIDE_PATH))

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
