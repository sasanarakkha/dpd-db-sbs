#!/usr/bin/env python3
"""Initialize a new upstream sync kamma thread, copy templates, and register it in kamma/threads.md."""

import datetime
from pathlib import Path


TEMPLATES_DIR = Path("kamma/upstream_sync/templates")
THREADS_DIR = Path("kamma/threads")
THREADS_FILE = Path("kamma/threads.md")


def main() -> None:
    today = datetime.date.today()
    date_str = today.strftime("%Y%m%d")
    date_human = today.strftime("%Y-%m-%d")

    thread_id = f"{date_str}_upstream_sync"
    thread_dir = THREADS_DIR / thread_id

    # --- Guard: already exists ---
    if thread_dir.exists():
        print(f"⚠️  Thread folder already exists: {thread_dir}")
        print("   Delete it first or pick a different date.")
        return

    # --- Create thread folder ---
    thread_dir.mkdir(parents=True)
    print(f"📂 Created: {thread_dir}")

    # --- Copy and date-stamp templates ---
    for template_name, target_name in [
        ("sync_thread_plan.md", "plan.md"),
        ("sync_thread_spec.md", "spec.md"),
    ]:
        src = TEMPLATES_DIR / template_name
        dst = thread_dir / target_name
        content = src.read_text(encoding="utf-8").replace("<DATE>", date_human)
        dst.write_text(content, encoding="utf-8")
        print(f"📄 Written:  {dst}")

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
    print(f"📄 Written:  {handoff}")

    # --- Register in kamma/threads.md ---
    entry_heading = f"## [ ] Thread: Upstream Sync {date_human}"
    entry_link = f"*Link: [./threads/{thread_id}/](./threads/{thread_id})*"
    full_entry = f"\n\n---\n\n{entry_heading}\n{entry_link}\n"

    existing = THREADS_FILE.read_text(encoding="utf-8")
    if entry_link in existing:
        print("⚠️  Entry already in kamma/threads.md — skipping registration.")
    else:
        THREADS_FILE.write_text(existing.rstrip() + full_entry, encoding="utf-8")
        print(f"📝 Registered in {THREADS_FILE}")

    # --- Done ---
    print()
    print(f"✅ Thread ready: {thread_dir}")
    print()
    print("Next steps:")
    print(f"  1. Fill in the upstream diff range in {thread_dir}/spec.md")
    print("  2. Switch to FAST. Start a fresh session.")
    print(f"  3. Continue upstream sync thread: {thread_dir}.")
    print("  4. First read:")
    print(f"     - {thread_dir}/handoff.md")
    print("     - kamma/upstream_sync/guide.md")
    print(f"     - {thread_dir}/plan.md")
    print("  5. Your task: run Stage 1 FAST Prep exactly as defined in the plan.")
    print("     Do not perform analysis or strategic planning.")
    print("     Stop before Stage 2 and update handoff.md.")
    print()
    print("After the sync completes:")
    print(
        "  6. Write kamma/upstream_sync/new_improvements.md with lessons from this run."
    )
    print("  7. Run `/kamma:3-review`, then `/kamma:4-finalize` to close the thread.")


if __name__ == "__main__":
    main()
