"""Run AI translation and checking operations in resumable chunks with antigravity quota tracking."""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

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

QUOTA_WAIT = timedelta(hours=5)
QUOTA_MARKER = "possible quota exhaustion"
DEFAULT_CHUNK = 25

STATUS_GENERATE_PROBES: list[tuple[str, str]] = [
    ("meaning", "ru"),
    ("lit", "ru"),
    ("note", "ru"),
    ("meaning", "ta"),
]

_ROWS_FILTERED_RE = re.compile(r"Rows filtered for the process: (\d+) / (\d+)")
_WORDS_TO_ANALYZE_RE = re.compile(r"Found (\d+) words to analyze")


def default_state() -> dict[str, Any]:
    """Return the default persisted-state shape."""
    return {
        "window_start": None,
        "quota_exhausted_at": None,
        "resume_at": None,
        "last_op": None,
        "totals": {"generated": 0, "checked": 0},
        "note": "resume_at assumes a conservative 5h wait after quota exhaustion",
    }


def load_state(path: Path) -> dict[str, Any]:
    """Load persisted state, falling back to the default shape if the file is missing."""
    if not path.exists():
        return default_state()
    return json.loads(path.read_text(encoding="utf-8"))


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


def detect_quota_exhaustion(output: str) -> bool:
    """Return True if the quota-exhaustion marker appears anywhere in subprocess output."""
    return QUOTA_MARKER in output


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
    existing: list[int] = []
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                existing = [int(i) for i in loaded]
        except json.JSONDecodeError:
            existing = []
    return sorted(set(existing) | set(new_ids))


def build_generate_command(
    mode: str,
    lang: str,
    chunk: int,
    fallback: bool,
    provider: str | None = None,
    model: str | None = None,
) -> list[str]:
    """Build the subprocess command for a real (non-dry-run) generate chunk."""
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
    if provider:
        cmd.extend(["-provider", provider])
    if model:
        cmd.extend(["-model", model])
    if not fallback and not provider:
        cmd.extend(["-provider", "antigravity_cli"])
    return cmd


def build_status_probe_command(mode: str, lang: str) -> list[str]:
    """Build the subprocess command for a --status dry-run pool-size probe."""
    return [
        "uv",
        "run",
        "python3",
        str(GENERATE_SCRIPT),
        "-mode",
        mode,
        "-lang",
        lang,
        "--dry-run",
        "-limit",
        "1",
    ]


def build_check_command(
    mode: str, chunk: int, provider: str | None = None, model: str | None = None
) -> list[str]:
    """Build the subprocess command for a check chunk."""
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
    if provider:
        cmd.extend(["--provider", provider])
    if model:
        cmd.extend(["--model", model])
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


def append_log(path: Path, line: str) -> None:
    """Append a single line to the append-only run log."""
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def print_status() -> None:
    """Print persisted state, generate-pool pending counts, and checker snapshot sizes."""
    state = load_state(STATE_PATH)
    pr.white(f"window_start: {state['window_start']}")
    pr.white(f"quota_exhausted_at: {state['quota_exhausted_at']}")
    pr.white(f"resume_at: {state['resume_at']}")
    pr.white(f"last_op: {state['last_op']}")
    pr.white(f"totals: {state['totals']}")

    pr.white("")
    pr.white("Pending work (generate pool sizes):")
    for mode, lang in STATUS_GENERATE_PROBES:
        cmd = build_status_probe_command(mode, lang)
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        counts = parse_generate_counts(result.stdout)
        total = counts[1] if counts else "?"
        pr.white(f"  {mode}/{lang}: {total} pending")

    pr.white("")
    pr.white("Pending work (checker pending counts):")
    from db.db_helpers import get_db_session
    from kamma.translate.scripts.ai_meaning_checker import RussianMeaningChecker
    from tools.paths import ProjectPaths

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    try:
        for mode in [
            "meaning",
            "meaning_raw",
            "russian_grammar_meaning_raw",
            "meaning_raw_list",
            "meaning_lit",
            "meaning_lit_list",
            "notes",
            "notes_raw",
        ]:
            checker = RussianMeaningChecker(mode=mode)
            n_pending = checker.get_total_count_with_session(db_session)
            pr.white(f"  {mode}: {n_pending} pending")
    finally:
        db_session.close()

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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run AI translation/checking operations in resumable, quota-aware chunks."
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
        help="safety cap on number of chunks (default: 0 = until done/quota)",
    )
    parser.add_argument(
        "--fallback",
        action="store_true",
        help="generate only: omit the forced -provider antigravity_cli",
    )
    parser.add_argument(
        "--force", action="store_true", help="ignore a future resume_at"
    )
    parser.add_argument(
        "--status", action="store_true", help="print status summary and exit"
    )
    parser.add_argument(
        "--provider",
        help="explicit provider preference to pass to workhorse script",
    )
    parser.add_argument(
        "--model",
        help="explicit model to pass to workhorse script",
    )
    args = parser.parse_args()

    if args.status:
        print_status()
        sys.exit(0)

    if args.op is None:
        parser.error("--op is required unless --status is given")

    state = load_state(STATE_PATH)

    resume_at_raw = state.get("resume_at")
    if resume_at_raw and not args.force:
        resume_at = datetime.fromisoformat(resume_at_raw)
        now = datetime.now().astimezone()
        if resume_at > now:
            remaining = resume_at - now
            pr.amber(
                f"Quota resume gate: {remaining} remaining until {resume_at.isoformat()}."
            )
            rerun_cmd = (
                f"uv run python3 kamma/translate/scripts/batch_runner.py "
                f"--op {args.op} --mode {args.mode} --lang {args.lang} "
                f"--chunk {args.chunk} --force"
            )
            pr.white(f"Wait, or force an early resume with: {rerun_cmd}")
            sys.exit(1)

    chunks_run = 0
    while True:
        if args.max_chunks and chunks_run >= args.max_chunks:
            pr.green(f"Reached --max-chunks ({args.max_chunks}) — stopping.")
            sys.exit(0)

        chunk_start = datetime.now().astimezone()
        if args.op == "generate":
            cmd = build_generate_command(
                args.mode,
                args.lang,
                args.chunk,
                args.fallback,
                args.provider,
                args.model,
            )
        else:
            cmd = build_check_command(args.mode, args.chunk, args.provider, args.model)

        pr.cyan(f"Running: {' '.join(cmd)}")
        output, returncode = run_subprocess_capture(cmd)
        chunks_run += 1

        if args.op == "generate":
            counts = parse_generate_counts(output)
            attempted = counts[0] if counts else 0
            new_ids = read_generated_ids(LAST_TRANSLATED_PATH, chunk_start)
            ok = len(new_ids)
            if new_ids:
                merged = merge_processed_ids(PROCESSED_IDS_PATH, new_ids)
                PROCESSED_IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
                PROCESSED_IDS_PATH.write_text(json.dumps(merged), encoding="utf-8")
        else:
            attempted_val = parse_check_attempted(output)
            attempted = attempted_val if attempted_val is not None else 0
            ok = attempted if returncode == 0 else 0

        now_iso = datetime.now().astimezone().isoformat()
        append_log(
            LOG_PATH,
            f"- {now_iso} | op={args.op} mode={args.mode} lang={args.lang if args.op == 'generate' else '-'} "
            f"chunk={args.chunk} attempted={attempted} ok={ok}",
        )

        state["totals"]["generated" if args.op == "generate" else "checked"] += ok
        state["last_op"] = args.op
        if ok > 0:
            if state.get("window_start") is None:
                state["window_start"] = now_iso
            state["quota_exhausted_at"] = None
            state["resume_at"] = None
        save_state(STATE_PATH, state)

        if attempted == 0:
            pr.green("pool empty — done")
            sys.exit(0)

        if detect_quota_exhaustion(output) or (
            ok == 0 and attempted > 0 and not args.fallback
        ):
            quota_exhausted_at = datetime.now().astimezone()
            resume_at = quota_exhausted_at + QUOTA_WAIT
            state["quota_exhausted_at"] = quota_exhausted_at.isoformat()
            state["resume_at"] = resume_at.isoformat()
            save_state(STATE_PATH, state)
            append_log(
                LOG_PATH,
                f"- {quota_exhausted_at.isoformat()} | quota-paused — resume_at={resume_at.isoformat()}",
            )
            pr.red(f"Quota exhausted — resume after {resume_at.isoformat()}.")
            rerun_cmd = (
                f"uv run python3 kamma/translate/scripts/batch_runner.py "
                f"--op {args.op} --mode {args.mode} --lang {args.lang} --chunk {args.chunk}"
            )
            pr.white(f"Re-run later with: {rerun_cmd}")
            sys.exit(3)

        if ok == 0 and attempted > 0:
            pr.red("All providers failing — stopping (will not loop forever).")
            sys.exit(2)


if __name__ == "__main__":
    main()
