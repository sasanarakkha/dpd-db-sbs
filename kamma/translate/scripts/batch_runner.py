"""Run AI translation and checking operations in resumable chunks, walking the default_models chain from tools/ai_models.json."""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from kamma.translate.scripts.ids_file import (
    read_ids_file,
    read_ids_scope,
    write_ids_file,
)
from kamma.translate.scripts.offpeak import require_offpeak
from kamma.translate.scripts.rejects import REJECTS_PATH, parked_ids
from kamma.translate.scripts.session_log import append_log_line, format_session_line
from tools.paths import ProjectPaths
from tools.printer import printer as pr

PROJECT_ROOT = Path(__file__).resolve().parents[3]
STATE_PATH = PROJECT_ROOT / "kamma" / "translate" / "state.json"
LOG_PATH = PROJECT_ROOT / "kamma" / "translate" / "log.md"
GENERATE_SCRIPT = (
    PROJECT_ROOT / "kamma" / "translate" / "scripts" / "ai_generate_translation.py"
)
CHECK_SCRIPT = (
    PROJECT_ROOT / "kamma" / "translate" / "scripts" / "ai_check_russian_meanings.py"
)
LAST_TRANSLATED_PATH = PROJECT_ROOT / "temp" / "last_translated.json"
PROCESSED_IDS_PATH = PROJECT_ROOT / "temp" / "ai_from_batch_api" / "processed_ids.json"

DEFAULT_CHUNK = 50

STATUS_POOLS: list[tuple[str, str]] = [
    ("meaning", "ru"),
    ("lit", "ru"),
    ("note", "ru"),
    ("meaning", "ta"),
]
STATUS_CHECK_MODES: list[str] = [
    "meaning",
    "meaning_raw",
    "russian_grammar_meaning_raw",
    "meaning_raw_list",
    "meaning_lit",
    "meaning_lit_list",
    "notes",
    "notes_raw",
]
STATUS_LEXICAL_FIELDS: list[str] = ["ru_meaning_raw", "ru_meaning"]

_ROWS_FILTERED_RE = re.compile(r"Rows filtered for the process: (\d+) / (\d+)")
_WORDS_TO_ANALYZE_RE = re.compile(r"Found (\d+) words to analyze")
_CHECKED_RE = re.compile(r"^checked (\d+)\s*$", re.MULTILINE)


def default_state() -> dict[str, Any]:
    """Return the default persisted-state shape."""
    return {
        "last_op": None,
        "totals": {"generated": 0, "checked": 0},
    }


def load_state(path: Path) -> dict[str, Any]:
    """Load persisted state, falling back to the default shape if the file is missing."""
    if not path.exists():
        return default_state()
    state = json.loads(path.read_text(encoding="utf-8"))
    state.pop("window_start", None)  # retired key
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    """Persist state as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_generate_counts(output: str) -> tuple[int, int] | None:
    """Parse the generator's "Rows filtered for the process: X / TOTAL" line into (attempted, total)."""
    match = _ROWS_FILTERED_RE.search(output)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def parse_check_attempted(output: str) -> int | None:
    """Parse the checker's "Found N words to analyze" line into an attempted count."""
    match = _WORDS_TO_ANALYZE_RE.search(output)
    if match is None:
        return None
    return int(match.group(1))


def parse_check_ok(output: str) -> int:
    """Parse the checker's "checked N" line (words with a parsed verdict); 0 when missing."""
    match = _CHECKED_RE.search(output)
    return int(match.group(1)) if match else 0


def check_chunk_result(output: str, returncode: int) -> tuple[int, int]:
    """Return (attempted, ok) for one check chunk from the checker's stdout and exit code."""
    attempted_val = parse_check_attempted(output)
    attempted = attempted_val if attempted_val is not None else 0
    ok = parse_check_ok(output) if returncode == 0 else 0
    return attempted, ok


def read_generated_ids(path: Path, since: datetime) -> list[int]:
    """Read ids from a fresh last_translated.json; [] if the file is missing, stale, or malformed."""
    if not path.exists():
        return []
    mtime = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    if mtime < since:
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    ids = data.get("ids", [])
    if not isinstance(ids, list):
        return []
    return [int(i) for i in ids]


def merge_processed_ids(path: Path, new_ids: list[int]) -> list[int]:
    """Union existing processed ids (tolerating a missing/malformed file) with new_ids, sorted."""
    return sorted(set(read_ids_file(path)) | set(new_ids))


def build_generate_command(
    mode: str,
    lang: str,
    chunk: int,
    provider: str | None = None,
    model: str | None = None,
) -> list[str]:
    """Build the subprocess command for a real (non-dry-run) generate chunk.

    Provider flags are passed only when an explicit pair is given; otherwise the
    workhorse walks the default_models chain.
    """
    cmd = [
        "uv",
        "run",
        "python3",
        str(GENERATE_SCRIPT),
        "-mode",
        mode,
        "-lang",
        lang,
        "-limit",
        str(chunk),
    ]
    if provider and model:
        cmd += ["-provider", provider, "-model", model]
    return cmd


def build_check_command(
    mode: str, chunk: int, provider: str | None = None, model: str | None = None
) -> list[str]:
    """Build the subprocess command for a check chunk.

    Provider flags are passed only when an explicit pair is given; otherwise the
    workhorse walks the default_models chain.
    """
    cmd = [
        "uv",
        "run",
        "python3",
        str(CHECK_SCRIPT),
        "--mode",
        mode,
        "--limit",
        str(chunk),
    ]
    if provider and model:
        cmd += ["--provider", provider, "--model", model]
    return cmd


def run_subprocess_capture(cmd: list[str]) -> tuple[str, int]:
    """Run a subprocess, streaming stdout to the console while also collecting it."""
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="")
        lines.append(line)
    process.wait()
    return "".join(lines), process.returncode


def collect_status(db_session: Session) -> dict[str, Any]:
    """Gather every pending-work count with read-only, in-process queries."""
    from kamma.translate.scripts import ai_generate_translation as gen
    from kamma.translate.scripts.ai_meaning_checker import RussianMeaningChecker
    from kamma.translate.scripts.synonym_audit import count_lexical_flagged

    state = load_state(STATE_PATH)
    return {
        "state": state,
        "generate": {
            f"{mode}/{lang}": gen.count_pool(mode, lang) for mode, lang in STATUS_POOLS
        },
        "checker": {
            mode: RussianMeaningChecker(mode=mode).get_total_count_with_session(
                db_session
            )
            for mode in STATUS_CHECK_MODES
        },
        "op4": {
            field: count_lexical_flagged(db_session, field)
            for field in STATUS_LEXICAL_FIELDS
        },
        "op5": gen.irrelevant_ru_query().count(),
        "op6": gen.count_reset_grounded(),
        "parked": len(parked_ids(REJECTS_PATH)),
        "last_audit": state.get("last_audit"),
    }


def print_status() -> None:
    """Print persisted state, pending counts for every operation, and checker snapshot sizes."""
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    try:
        status = collect_status(db_session)
    finally:
        db_session.close()

    pr.white(f"last_op: {status['state']['last_op']}")
    pr.white(f"totals: {status['state']['totals']}")

    pr.white("")
    pr.white("Op 1 — generate pool (pending):")
    for name, count in status["generate"].items():
        pr.white(f"  {name}: {count} pending")

    pr.white("")
    pr.white("Op 2 — checker (pending):")
    for mode, count in status["checker"].items():
        pr.white(f"  {mode}: {count} pending")

    pr.white("")
    pr.white("Op 4 — synonym audit (lexical flagged rows):")
    for field, count in status["op4"].items():
        pr.white(f"  {field}: {count} flagged")
    last_audit = status["last_audit"]
    if last_audit:
        pr.white(
            f"  last audit: {last_audit.get('field')} / {last_audit.get('mode')} "
            f"flagged {last_audit.get('flagged')} at {last_audit.get('ts')}"
        )
    else:
        pr.white("  last audit: none recorded")

    pr.white("")
    pr.white(f"Op 5 — remove_irrelevant (ru): {status['op5']} rows would be removed")
    pr.white(f"Op 6 — re-ground drafts (ru): {status['op6']} rows would be cleared")
    pr.white(f"Parked rejects (rejected 2+ times): {status['parked']}")

    pr.white("")
    pr.white("Checker snapshot sizes:")
    for snapshot_path in sorted(PROJECT_ROOT.glob("temp/ai_*_check/checked_ids.json")):
        mode = snapshot_path.parent.name.removeprefix("ai_").removesuffix("_check")
        try:
            ids = json.loads(snapshot_path.read_text(encoding="utf-8"))
            n = len(ids) if isinstance(ids, list) else 0
        except json.JSONDecodeError:
            n = 0
        pr.white(f"  {mode}: {n} already checked")


def _peak_gate(chunks_run: int, allow_peak: bool) -> bool:
    """Return True to start the next chunk. The first chunk may exit 1 via the guard;
    a later chunk hitting peak (or an unrecorded holiday year) stops the session cleanly."""
    if chunks_run == 0:
        require_offpeak(allow_peak)
        return True
    try:
        require_offpeak(allow_peak)
    except SystemExit:
        pr.amber("peak hours started — stopping")
        return False
    return True


def _run_chunks(
    args: argparse.Namespace, state: dict[str, Any], totals: dict[str, int]
) -> int:
    """Run chunks until done/failure/cap; return the process exit code."""
    while True:
        if args.max_chunks and totals["chunks"] >= args.max_chunks:
            pr.green(f"Reached --max-chunks ({args.max_chunks}) — stopping.")
            return 0

        if not _peak_gate(totals["chunks"], args.allow_peak):
            return 0

        # A re-run with the same lang/mode (after exit 2 or a peak stop) keeps the
        # ids Op 2 has not checked yet; a new lang/mode starts a fresh file.
        if (
            args.op == "generate"
            and totals["chunks"] == 0
            and read_ids_scope(PROCESSED_IDS_PATH) != (args.lang, args.mode)
        ):
            write_ids_file(PROCESSED_IDS_PATH, args.lang, args.mode, [])

        chunk_start = datetime.now().astimezone()
        if args.op == "generate":
            cmd = build_generate_command(
                args.mode, args.lang, args.chunk, args.provider, args.model
            )
        else:
            cmd = build_check_command(args.mode, args.chunk, args.provider, args.model)

        pr.cyan(f"Running: {' '.join(cmd)}")
        output, returncode = run_subprocess_capture(cmd)
        totals["chunks"] += 1

        if args.op == "generate":
            counts = parse_generate_counts(output)
            attempted = counts[0] if counts else 0
            new_ids = read_generated_ids(LAST_TRANSLATED_PATH, chunk_start)
            ok = len(new_ids)
            if new_ids:
                merged = merge_processed_ids(PROCESSED_IDS_PATH, new_ids)
                write_ids_file(PROCESSED_IDS_PATH, args.lang, args.mode, merged)
        else:
            attempted, ok = check_chunk_result(output, returncode)

        totals["attempted"] += attempted
        totals["ok"] += ok

        state["totals"]["generated" if args.op == "generate" else "checked"] += ok
        state["last_op"] = args.op
        save_state(STATE_PATH, state)

        if attempted == 0:
            pr.green("pool empty — done")
            return 0

        if ok == 0 and attempted > 0:
            pr.red("All providers failing — stopping (will not loop forever).")
            rerun_cmd = (
                f"uv run python3 kamma/translate/scripts/batch_runner.py "
                f"--op {args.op} --mode {args.mode} --lang {args.lang} --chunk {args.chunk}"
            )
            pr.white(f"Re-run with: {rerun_cmd}")
            return 2


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run AI translation/checking operations in resumable chunks."
    )
    parser.add_argument(
        "--op",
        choices=["generate", "check"],
        default=None,
        help="which workhorse to drive",
    )
    parser.add_argument(
        "--mode",
        default="meaning",
        help="mode passed through to the workhorse script (default: meaning)",
    )
    parser.add_argument(
        "--lang", choices=["ru", "ta"], default="ru", help="generate only (default: ru)"
    )
    parser.add_argument(
        "--chunk",
        type=int,
        default=DEFAULT_CHUNK,
        help=f"rows per subprocess call (default: {DEFAULT_CHUNK})",
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=0,
        help="safety cap on number of chunks (default: 0 = until done/failure)",
    )
    parser.add_argument(
        "--status", action="store_true", help="print status summary and exit"
    )
    parser.add_argument(
        "--provider",
        help="explicit provider to pin (must be given together with --model; "
        "default: the workhorse walks the default_models chain)",
    )
    parser.add_argument(
        "--model",
        help="explicit model to pin (must be given together with --provider)",
    )
    parser.add_argument(
        "--allow-peak",
        action="store_true",
        help="run during DeepSeek peak hours (full price)",
    )
    args = parser.parse_args()

    if args.status:
        print_status()
        sys.exit(0)

    if args.op is None:
        parser.error("--op is required unless --status is given")

    if bool(args.provider) != bool(args.model):
        parser.error(
            "--provider and --model must be given together (or neither) — a lone "
            "--provider would be ignored and the default_models chain used."
        )

    state = load_state(STATE_PATH)
    totals = {"chunks": 0, "attempted": 0, "ok": 0}
    start = datetime.now().astimezone().isoformat()
    exit_code = 1
    try:
        exit_code = _run_chunks(args, state, totals)
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 1
        raise
    finally:
        end = datetime.now().astimezone().isoformat()
        append_log_line(
            LOG_PATH,
            format_session_line(
                start,
                end,
                {
                    "op": args.op,
                    "mode": args.mode,
                    "lang": args.lang if args.op == "generate" else "-",
                    "chunks": totals["chunks"],
                    "attempted": totals["attempted"],
                    "ok": totals["ok"],
                },
                exit_code,
            ),
        )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
