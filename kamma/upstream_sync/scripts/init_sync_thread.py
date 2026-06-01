#!/usr/bin/env python3
"""Initialize a new upstream sync kamma thread and copy the standard templates."""

import datetime
from pathlib import Path

from tools.printer import printer as pr


TEMPLATES_DIR = Path("kamma/upstream_sync/templates")
THREADS_DIR = Path("kamma/threads")


def main() -> None:
    pr.tic()
    pr.green_title("init_sync_thread.py")

    today = datetime.date.today()
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
        content = src.read_text(encoding="utf-8").replace("<DATE>", date_human)
        dst.write_text(content, encoding="utf-8")
        pr.green(f"Written: {dst}")

    # --- Write handoff stub ---
    handoff = thread_dir / "handoff.md"
    handoff.write_text(
        f"# Handoff: Upstream Sync {date_human}\n\n"
        "## Status\n\nNot started.\n\n"
        "## Last upstream sync\n\n"
        "- **Commit / tag**: `<FILL>`\n"
        "- **Date**: `<FILL>`\n\n"
        "## Notes\n\n"
        "_Add cross-session notes here._\n",
        encoding="utf-8",
    )
    pr.green(f"Written: {handoff}")

    # --- Done ---
    pr.green(f"Thread ready: {thread_dir}")
    pr.green("Next steps:")
    pr.green(f"  1. Fill in the upstream diff range in {thread_dir}/spec.md")
    pr.green("  2. Switch to FAST. Start a fresh session.")
    pr.green(f"  3. Continue upstream sync thread: {thread_dir}.")
    pr.green("  4. First read:")
    pr.green(f"     - {thread_dir}/handoff.md")
    pr.green("     - kamma/upstream_sync/guide.md")
    pr.green(f"     - {thread_dir}/plan.md")
    pr.green("  5. Your task: run Stage 1 FAST Prep exactly as defined in the plan.")
    pr.green("     Do not perform analysis or strategic planning.")
    pr.green("     Stop before Stage 2 and update handoff.md.")
    pr.green("After the sync completes:")
    pr.green(
        "  6. Write kamma/upstream_sync/new_improvements.md with lessons from this run."
    )
    pr.green(
        "  7. Run `/kamma:3-review`, then `/kamma:4-finalize` to close the thread."
    )
    pr.toc()


if __name__ == "__main__":
    main()
