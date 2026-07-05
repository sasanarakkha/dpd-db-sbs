#!/usr/bin/env python3

"""Chain the six known Stage 1 prep commands, stopping at the first failure."""

import argparse
import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from kamma.upstream_sync.scripts.prep_analyzer import PrepAnalyzer
from kamma.upstream_sync.scripts.registry_helper import (
    get_registry_path,
    read_line_list,
)
from kamma.upstream_sync.scripts.sync_runtime import effective_blocker_paths
from kamma.upstream_sync.scripts.sync_status import derive_stage
from kamma.upstream_sync.scripts.validate_registry import validate_registry_core
from tools.printer import printer as pr

type StepResult = tuple[bool, str]


@dataclass
class Stage1Step:
    """One step in the Stage 1 chain: a subprocess command or an in-process callable."""

    name: str
    remediation: str
    run: Callable[[], StepResult]


def run_subprocess_step(argv: list[str]) -> StepResult:
    """Run a subprocess command, returning (success, combined stdout+stderr)."""
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    return result.returncode == 0, result.stdout + result.stderr


def run_registry_validation() -> StepResult:
    """Validate registry.json in-process via validate_registry_core."""
    registry_path = get_registry_path()
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    repo_root = registry_path.parent.parent.parent
    errors = validate_registry_core(data, repo_root)
    if errors:
        return False, "\n".join(errors)
    return True, "registry.json is valid"


def run_prep_analyzer(thread_dir: Path) -> StepResult:
    """Run PrepAnalyzer.run() in-process, wrapping failures as a step result."""
    try:
        PrepAnalyzer(thread_dir).run()
    except (ValueError, RuntimeError, OSError) as exc:
        return False, str(exc)
    return True, f"wrote {thread_dir / 'prep_report.md'} and prep_manifest.json"


def run_triage_and_status(thread_dir: Path) -> StepResult:
    """Derive the stage verdict and fail if unresolved blocker/discuss paths remain.

    Acknowledged blockers (`<thread_dir>/run_acknowledged_blockers.txt`) are
    subtracted from `blocker_paths` before the verdict, mirroring
    `sync_runtime.verify_manifest`. Acknowledgment clears this chain verdict
    only — it does not enable the fast-path, since `is_localized_noop` still
    treats any `blocker_paths` entry as non-fast-path.
    """
    manifest_path = thread_dir / "prep_manifest.json"
    manifest: dict[str, object] = json.loads(manifest_path.read_text(encoding="utf-8"))
    descriptor = derive_stage(thread_dir)
    blockers_raw = manifest.get("blocker_paths") or []
    blockers = blockers_raw if isinstance(blockers_raw, list) else []
    discuss = manifest.get("discuss_paths") or []
    acknowledged = read_line_list(thread_dir / "run_acknowledged_blockers.txt")
    effective_blockers = effective_blocker_paths(thread_dir, blockers)
    summary = f"stage: {descriptor.stage}; next: {descriptor.next_command}"
    if acknowledged and not effective_blockers:
        pr.amber(f"Acknowledged blockers cleared: {acknowledged}")
    if effective_blockers or discuss:
        return (
            False,
            f"{summary}; blocker_paths={effective_blockers}; discuss_paths={discuss}",
        )
    return True, summary


def build_default_steps(thread_dir: Path) -> list[Stage1Step]:
    """Return the six-step Stage 1 chain in spec order."""
    return [
        Stage1Step(
            name="shadow health check",
            remediation="fix reported shadow/upstream drift, see tests/check_shadow_modifications.py output",
            run=lambda: run_subprocess_step(
                ["uv", "run", "python3", "tests/check_shadow_modifications.py"]
            ),
        ),
        Stage1Step(
            name="lint gate (F821,E999)",
            remediation="fix the reported ruff errors before continuing",
            run=lambda: run_subprocess_step(
                [
                    "uv",
                    "run",
                    "ruff",
                    "check",
                    "tools/",
                    "scripts/",
                    "db/",
                    "exporter/",
                    "--select",
                    "F821,E999",
                    "--quiet",
                ]
            ),
        ),
        Stage1Step(
            name="registry validation",
            remediation="fix kamma/upstream_sync/registry.json per the reported errors",
            run=run_registry_validation,
        ),
        Stage1Step(
            name="git fetch upstream",
            remediation="resolve the git fetch failure (network access or 'upstream' remote config)",
            run=lambda: run_subprocess_step(["git", "fetch", "upstream"]),
        ),
        Stage1Step(
            name="prep analyzer",
            remediation="resolve the PrepAnalyzer failure (e.g. bootstrap accepted_sync.json)",
            run=lambda: run_prep_analyzer(thread_dir),
        ),
        Stage1Step(
            name="triage + stage verdict",
            remediation="resolve blocker_paths/discuss_paths in prep_manifest.json before continuing",
            run=lambda: run_triage_and_status(thread_dir),
        ),
    ]


def run_stage1(thread_dir: Path, steps: list[Stage1Step] | None = None) -> int:
    """Run the Stage 1 chain, short-circuiting on the first failing step."""
    pr.tic()
    pr.green_title("stage1.py")
    chain = steps if steps is not None else build_default_steps(thread_dir)

    for step in chain:
        pr.green(f"running: {step.name}")
        success, output = step.run()
        if output:
            pr.white(output)
        if not success:
            pr.red(f"FAILED: {step.name}")
            pr.red(f"remediation: {step.remediation}")
            pr.toc()
            return 1
        pr.green(f"OK: {step.name}")

    pr.toc()
    return 0


def main() -> None:
    """Parse arguments and run the Stage 1 chain for the given thread directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("thread_dir", type=Path)
    args = parser.parse_args()

    sys.exit(run_stage1(args.thread_dir))


if __name__ == "__main__":
    main()
