#!/usr/bin/env python3
"""Initialize a new upstream sync kamma thread and copy the standard templates."""

import datetime
from pathlib import Path

from kamma.upstream_sync.scripts.registry_helper import load_accepted_sync_state
from tools.printer import printer as pr

ROOT = Path(__file__).resolve().parents[3]
TEMPLATES_DIR = ROOT / "kamma/upstream_sync/templates"
THREADS_DIR = ROOT / "kamma/threads"
ACCEPTED_SYNC_PATH = ROOT / "kamma/upstream_sync/accepted_sync.json"


def short_sha(commit_sha: str) -> str:
    """Return a display-sized SHA while preserving non-SHA sentinels."""
    if len(commit_sha) == 40:
        return commit_sha[:12]
    return commit_sha


def render_spec_template(content: str, date_human: str) -> str:
    """Fill the sync spec template with date and accepted upstream state."""
    accepted_sync = load_accepted_sync_state(ACCEPTED_SYNC_PATH)
    from_sha = accepted_sync.last_accepted_upstream_sha
    target_ref = accepted_sync.last_accepted_upstream_ref

    return (
        content.replace("<DATE>", date_human)
        .replace(
            "- **From**: `<FILL: last accepted upstream SHA from accepted_sync.json>`",
            f"- **From**: `{from_sha}`",
        )
        .replace("- **To**: `upstream/main` at", f"- **To**: `{target_ref}` at")
    )


def render_handoff(date_human: str) -> str:
    """Build the initial restartable handoff for a new sync thread."""
    accepted_sync = load_accepted_sync_state(ACCEPTED_SYNC_PATH)
    from_sha = accepted_sync.last_accepted_upstream_sha
    from_date = accepted_sync.last_accepted_upstream_date
    target_ref = accepted_sync.last_accepted_upstream_ref

    return (
        f"# Handoff: Upstream Sync {date_human}\n\n"
        "## Status\n\n"
        "Not started.\n\n"
        "## Current Stage\n\n"
        "Stage 1 FAST Prep pending.\n\n"
        "## Last upstream sync\n\n"
        f"- **Commit / tag**: `{short_sha(from_sha)}`\n"
        f"- **Full SHA**: `{from_sha}`\n"
        f"- **Date**: `{from_date}`\n"
        f"- **Ref**: `{target_ref}`\n\n"
        "## Completed Work\n\n"
        "- Sync thread initialized.\n\n"
        "## Commands Already Run\n\n"
        "- `scripts/cl_dps/dpd-kamma-sync`\n\n"
        "## Files Changed\n\n"
        "- `plan.md`\n"
        "- `spec.md`\n"
        "- `handoff.md`\n\n"
        "## Open Decisions\n\n"
        "- None yet.\n\n"
        "## Errors, Issues, And Repeated Mistakes\n\n"
        "- None yet.\n\n"
        "## Next Model\n\n"
        "FAST\n\n"
        "## Restart Prompt\n\n"
        "```text\n"
        "Dispatch Stage 1 to the sync-fast subagent (.claude/agents/sync-fast.md).\n\n"
        "Continue upstream sync thread: <thread_dir>.\n"
        "First read:\n"
        "1. <thread_dir>/handoff.md\n"
        "2. Run `uv run python3 kamma/upstream_sync/scripts/sync_status.py <thread_dir> "
        "--instructions` for the current stage's guide section.\n"
        "3. <thread_dir>/plan.md\n\n"
        "Task: run `uv run python3 kamma/upstream_sync/scripts/stage1.py <thread_dir>`.\n"
        "Do not perform analysis or strategic planning.\n"
        "Stop before Stage 2 and update handoff.md.\n"
        "```\n\n"
        "Do not continue in this session.\n"
    )


def main() -> None:
    pr.tic()
    pr.green_title("init_sync_thread.py")

    today = datetime.datetime.now(datetime.UTC).date()
    date_str = today.strftime("%Y%m%d")
    date_human = today.strftime("%Y-%m-%d")

    thread_id = f"{date_str}_upstream_sync"
    thread_dir = THREADS_DIR / thread_id

    # --- Guard: already exists ---
    if thread_dir.exists():
        pr.amber(f"Thread folder already exists: {thread_dir}")
        pr.amber("Delete it first or pick a different date.")
        pr.toc()
        return

    # --- Create thread folder ---
    thread_dir.mkdir(parents=True)
    pr.green(f"Created: {thread_dir}")

    # --- Copy and date-stamp templates ---
    for template_name, target_name in [
        ("sync_thread_plan.md", "plan.md"),
        ("sync_thread_spec.md", "spec.md"),
    ]:
        src = TEMPLATES_DIR / template_name
        dst = thread_dir / target_name
        content = src.read_text(encoding="utf-8")
        if target_name == "spec.md":
            content = render_spec_template(content, date_human)
        else:
            content = content.replace("<DATE>", date_human)
        dst.write_text(content, encoding="utf-8")
        pr.green(f"Written: {dst}")

    # --- Write handoff stub ---
    handoff = thread_dir / "handoff.md"
    handoff.write_text(render_handoff(date_human), encoding="utf-8")
    pr.green(f"Written: {handoff}")

    # --- Done ---
    pr.green(f"Thread ready: {thread_dir}")
    pr.green("Next steps:")
    pr.green(f"  1. Review the auto-filled upstream diff range in {thread_dir}/spec.md")
    pr.green(
        "  2. Dispatch Stage 1 to the sync-fast subagent (.claude/agents/sync-fast.md)."
    )
    pr.green(f"     Continue upstream sync thread: {thread_dir}.")
    pr.green("     First read:")
    pr.green(f"       - {thread_dir}/handoff.md")
    pr.green(
        "       - uv run python3 kamma/upstream_sync/scripts/sync_status.py "
        f"{thread_dir} --instructions"
    )
    pr.green(f"       - {thread_dir}/plan.md")
    pr.green(
        "     Task: run `uv run python3 kamma/upstream_sync/scripts/stage1.py <thread_dir>`."
    )
    pr.green("     Do not perform analysis or strategic planning.")
    pr.green("     Stop before Stage 2 and update handoff.md.")
    pr.green("After the sync completes:")
    pr.green(
        "  3. Write <thread_dir>/retrospective.md (copy from "
        "kamma/upstream_sync/templates/retrospective.md) before finalize."
    )
    pr.green(
        "  4. Run `/kamma:3-review`, then `/kamma:4-finalize` to close the thread."
    )
    pr.toc()


if __name__ == "__main__":
    main()
