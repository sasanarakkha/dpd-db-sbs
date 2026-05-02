"""
Vibhanga rule word-filling workflow (interactive terminal loop).

For each rule:
1. Prompt for source value (suggested from last run) and PAT file path; Enter to accept, 'q' to quit.
2. Accept pasted rule text via stdin (or read existing PAT file); strip {variant readings}.
3. Save cleaned text to misc/pat/pcXX.txt and temp/text.txt.
4. Run copy_examples (first pass) — pre-populate vib/pat SBS fields for already-known DB words.
5. Extract unrecognized words (list_of_words_from_txt); print them and save backup TSV.
6. Pause for GUI entry: user adds new words in gui2 → Pass2Add tab.
7. Run copy_examples (second pass) — commit newly-added words to DB.
8. Save progress to misc/pat/vib_progress.json; suggest next PAT file; loop or quit.

Usage: uv run python scripts/change_in_db/vib_rule_workflow.py
       (or: bash scripts/bash/vib_rule.sh)
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import TextIO

from db.db_helpers import get_db_session
from scripts.change_in_db.copy_examples import update_column_for_some_criteria
from scripts.export.list_of_words_from_txt import (
    dps_make_words_to_add_list_from_text_no_field,
)
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr

VIB_PROGRESS_PATH = Path("misc/pat/vib_progress.json")


def load_progress() -> dict:
    """Load progress from JSON file."""
    if VIB_PROGRESS_PATH.exists():
        try:
            return json.loads(VIB_PROGRESS_PATH.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_progress(source: str, pat_file: str, complete: bool = True) -> None:
    """Save progress to JSON file."""
    VIB_PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    VIB_PROGRESS_PATH.write_text(
        json.dumps(
            {"last_source": source, "last_pat_file": pat_file, "complete": complete},
            ensure_ascii=False,
            indent=2,
        )
    )


def suggest_next_pat_file(last_pat: str) -> str:
    """Suggest the next PAT file name based on the last one."""
    match = re.search(r"([a-z]+)(\d+)\.txt$", last_pat)
    if match:
        prefix = match.group(1)
        num = int(match.group(2))
        return f"misc/pat/{prefix}{num + 1}.txt"
    return ""


def suggest_next_source(last_source: str) -> str:
    """Suggest the next source by incrementing the rule number."""
    m = re.match(r"^(.+\.)(\d+)$", last_source)
    if m:
        return f"{m.group(1)}{int(m.group(2)) + 1}"
    return ""


def normalize_pat_file(pat_input: str) -> str:
    """Expand a bare stem like 'pc64' to 'misc/pat/pc64.txt'."""
    if "/" not in pat_input and not pat_input.endswith(".txt"):
        return f"misc/pat/{pat_input}.txt"
    return pat_input


def strip_variant_readings(text: str) -> str:
    """Remove {variant readings} from text."""
    return re.sub(r"\{[^}]+\}", "", text).strip()


def collect_tty_pasted_text(stdin: TextIO) -> str:
    """Read multiline terminal input until EOF or a sentinel line."""
    lines: list[str] = []
    while True:
        try:
            line = stdin.readline()
        except KeyboardInterrupt:
            pr.amber("Input cancelled.")
            return ""

        if line == "":
            break

        if line.rstrip("\r\n") == "__END__":
            break

        lines.append(line)
    return "".join(lines)


def get_text_from_clipboard() -> str:
    """Read multiline text from the macOS clipboard."""
    result = subprocess.run(
        ["pbpaste"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def accept_pasted_text(stdin: TextIO | None = None) -> str:
    """Read multiline text from stdin until EOF or a sentinel line."""
    input_stream = stdin or sys.stdin

    if input_stream.isatty():
        pr.green(
            "Press Enter to read from clipboard, or type 'paste' for terminal paste mode."
        )
        mode = input_stream.readline().strip().lower()
        if mode in {"", "clip"}:
            pr.green("Reading rule text from clipboard...")
            return get_text_from_clipboard()

        pr.green("Paste the rule text below.")
        pr.green("Finish with Ctrl-D or type __END__ on its own line.")
        return collect_tty_pasted_text(input_stream)

    return input_stream.read()


def run_rule(
    source: str,
    pat_file: str,
    pth: ProjectPaths,
    dpspth: DPSPaths,
    db_session,
    resume: bool = False,
) -> bool:
    """Run the workflow for a single rule. Returns False if user wants to quit."""
    if resume:
        # Steps 1–3b already ran in the previous session; re-copy PAT → temp/text.txt
        # so word extraction sees the saved text without re-running copy_examples.
        pr.amber(f"Resuming rule {source} — re-running word extraction...")
        Path(dpspth.text_to_add_path).write_text(Path(pat_file).read_text())
    else:
        # Step 1 — Get text
        if Path(pat_file).exists():
            pr.green(f"Reading existing file: {pat_file}")
            text = Path(pat_file).read_text()
        else:
            text = accept_pasted_text()
            if not text.strip():
                pr.amber("No text provided. Skipping.")
                return True

        # Step 2 — Clean
        text = strip_variant_readings(text)

        # Step 3 — Save
        Path(pat_file).parent.mkdir(parents=True, exist_ok=True)
        Path(pat_file).write_text(text)
        Path(dpspth.text_to_add_path).write_text(text)
        pr.yes(f"Saved to {pat_file}:")
        pr.cyan(text)

        # Step 3b — First copy_examples run: pre-populate already-known words.
        # Running before word extraction ensures the matching SBS vib/pat fields are copied
        # for existing DB words before we filter against missing source coverage.
        pr.green(
            f"Pre-populating existing coverage for {source} (first copy_examples run)..."
        )
        update_column_for_some_criteria(source, "vib", "vib", dry_run=False)
        pr.yes("Existing words pre-populated.")

    # Step 4 — Extract words (now without false positives from already-covered words)
    words = dps_make_words_to_add_list_from_text_no_field(
        pth, dpspth, db_session, ["vib_source", "pat_source"]
    )
    if words:
        pr.cyan("")
        for word in words:
            pr.cyan(f"  {word}")
        pr.cyan("")

    # Step 5 — GUI pause
    pr.green("Add the above words in gui2/main.py → Pass2Add tab.")
    choice = input("Press Enter when done (or type 'q' to quit): ").strip().lower()
    if choice == "q":
        save_progress(source, pat_file, complete=False)
        return False

    # Step 6 — Second copy_examples run: commit newly-added words
    pr.green(f"Applying copy_examples for {source}...")
    update_column_for_some_criteria(source, "vib", "vib", dry_run=False)
    pr.yes("DB changes applied.")

    # Step 7 — Save progress
    save_progress(source, pat_file)
    pr.yes(f"Rule {source} done.")

    # Step 8 — Continue prompt
    next_pat = suggest_next_pat_file(pat_file)
    if next_pat:
        pr.green(f"Suggested next PAT file: {next_pat}")
    choice = input("Continue to next rule? [Enter] or quit [q]: ").strip().lower()
    if choice == "q":
        return False
    return True


def main() -> None:
    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)
    progress = load_progress()

    while True:
        incomplete = progress.get("last_source") and not progress.get("complete", True)

        if incomplete:
            source = progress["last_source"]
            pat_file = progress["last_pat_file"]
            pr.amber(f"Incomplete rule detected: {source} ({pat_file})")
            pr.amber(
                "Re-running word extraction — add any remaining words, then continue."
            )
            should_continue = run_rule(
                source, pat_file, pth, dpspth, db_session, resume=True
            )
        else:
            if progress.get("last_source"):
                next_source = suggest_next_source(progress["last_source"])
                next_pat = suggest_next_pat_file(progress["last_pat_file"])
                pr.green(
                    f"Last: {progress['last_source']} ({progress['last_pat_file']})"
                )
                raw = input(
                    f"Source [{next_source}] (Enter to accept, 'q' to quit): "
                ).strip()
                if raw.lower() == "q":
                    break
                source = raw or next_source
                if not source:
                    pr.no("No source available. Enter a source value.")
                    continue
                pat_raw = input(f"PAT file [{Path(next_pat).stem}]: ").strip()
                pat_file = normalize_pat_file(pat_raw) if pat_raw else next_pat
            else:
                source = input("Source (e.g. VIN2.5.6.10) [or Enter to quit]: ").strip()
                if not source:
                    break
                pat_raw = input("PAT file (e.g. pc64): ").strip()
                pat_file = normalize_pat_file(pat_raw)

            if not pat_file:
                pr.no("PAT file path is required.")
                continue

            should_continue = run_rule(source, pat_file, pth, dpspth, db_session)

        progress = load_progress()  # reload from file — preserves complete flag
        if not should_continue:
            break

    pr.yes("Workflow finished.")


if __name__ == "__main__":
    main()
