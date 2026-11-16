"""Audit Russian and Tamil meaning fields for duplicate or near-identical synonyms and optionally trim them."""

import argparse
import csv
import datetime
import difflib
import hashlib
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Russian, Tamil
from kamma.translate.scripts.offpeak import require_offpeak
from kamma.translate.scripts.session_log import (
    append_log_line,
    format_session_line,
    update_state,
)
from tools.paths import ProjectPaths
from tools.printer import printer as pr

if TYPE_CHECKING:
    from tools.ai_manager import AIManager

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PROJECT_ROOT / "temp" / "synonym_audit"
CACHE_PATH = REPORT_DIR / "judgments.jsonl"
LOG_PATH = PROJECT_ROOT / "kamma" / "translate" / "log.md"
STATE_PATH = PROJECT_ROOT / "kamma" / "translate" / "state.json"

FIELD_MODEL: dict[str, type[Russian] | type[Tamil]] = {
    "ru_meaning": Russian,
    "ru_meaning_raw": Russian,
    "ta_meaning": Tamil,
}

_BRACKETS_RE = re.compile(r"\([^)]*\)")
_WHITESPACE_RE = re.compile(r"\s+")
_FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*(.*?)\s*```$", re.DOTALL)

JUDGE_SYSTEM_PROMPT = """You are a Russian lexicographer editing a Pāli–Russian dictionary. For each
entry you receive the Pāli headword, its English glosses, and a numbered list
of Russian translation variants. Decide which variants are redundant
duplicates.

Drop a variant ONLY if it translates the same English gloss as another kept
variant AND is interchangeable with it in a dictionary entry.

KEEP a variant if it: corresponds to a different English gloss; differs in
grammatical form, aspect, or voice; starts with "досл." (literal rendering);
contains "(комм)" (commentary gloss) or a bracketed grammar/usage note; or
adds any other lexicographic value. When in doubt, keep.

Never drop a variant that starts with "досл." — literal glosses are always
kept. If a "досл." variant expresses nearly the same sense as a non-literal
variant, drop the non-literal variant instead and keep the "досл." one.

Respond with ONLY a JSON object mapping each entry id to the list of variant
indexes to drop, e.g. {"123": [2], "456": []}. Use [] when nothing should be
dropped. Output no other text, no markdown fences, no explanations."""

RETRY_SLEEP_SECONDS = 2.0
MAX_CONSECUTIVE_FAILURES = 5


def split_meanings(field: str) -> list[str]:
    """Split a `;`-joined meaning field into stripped, non-empty parts, ignoring `;` inside brackets."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for char in field:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == ";" and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return [part.strip() for part in parts if part.strip()]


def normalize(part: str) -> str:
    """Normalize a meaning fragment for duplicate comparison."""
    text = part.lower().replace("ё", "е")
    text = _BRACKETS_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text.rstrip(".").strip()


def strict_key(part: str) -> str:
    """Key for strict duplicates: case, ё and trailing dot ignored, brackets kept."""
    text = part.lower().replace("ё", "е")
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text.rstrip(".").strip()


def find_exact_dups(parts: list[str]) -> list[int]:
    """Return indexes of parts whose strict key already appeared earlier."""
    seen: set[str] = set()
    dup_indexes: list[int] = []
    for i, part in enumerate(parts):
        norm = strict_key(part)
        if norm in seen:
            dup_indexes.append(i)
        else:
            seen.add(norm)
    return dup_indexes


def find_near_dups(parts: list[str], threshold: float) -> list[tuple[int, int, float]]:
    """Return (i, j, ratio) pairs at/above threshold, excluding already-flagged exact dups."""
    exact = set(find_exact_dups(parts))
    pairs: list[tuple[int, int, float]] = []
    for i in range(len(parts)):
        if i in exact:
            continue
        for j in range(i + 1, len(parts)):
            if j in exact:
                continue
            ratio = difflib.SequenceMatcher(
                None, normalize(parts[i]), normalize(parts[j])
            ).ratio()
            if ratio >= threshold:
                pairs.append((i, j, ratio))
    return pairs


def rebuild_field(parts: list[str], drop: set[int]) -> str:
    """Rejoin the kept parts, preserving original order and casing."""
    kept = [part for i, part in enumerate(parts) if i not in drop]
    return "; ".join(kept)


@dataclass
class JudgeEntry:
    """A single flagged headword entry queued for AI alignment judging.

    `parts` is always the original, unfiltered `find_exact_dups`/`find_near_dups`
    index space — never pre-filtered — so drop indexes returned by the model
    line up with the entry's real variant list.
    """

    id: int
    field: str
    lemma_1: str
    english: str
    parts: list[str]


def build_judge_prompt(entries: list[JudgeEntry]) -> str:
    """Render the per-entry judge user prompt for a batch of flagged entries."""
    blocks: list[str] = []
    for entry in entries:
        lines = [
            f"Entry id: {entry.id}",
            f"Pāli headword: {entry.lemma_1}",
            f"English glosses: {entry.english}",
            "Russian variants:",
        ]
        lines.extend(f"  {i}. {part}" for i, part in enumerate(entry.parts))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n\nReturn the JSON object now."


def _is_literal_gloss(part: str) -> bool:
    """True if a variant is a "досл." (literal-gloss) variant, which must never be dropped."""
    return part.strip().lower().startswith("досл.")


def _strip_fences(content: str) -> str:
    """Remove a surrounding markdown code fence (``` or ```json) from a reply."""
    text = content.strip()
    match = _FENCE_RE.match(text)
    return match.group(1).strip() if match else text


def parse_judge_response(
    content: str | None, entries: list[JudgeEntry]
) -> dict[int, set[int] | None] | None:
    """Parse a judge batch response into per-entry drop-index sets.

    Returns None if the whole response is unusable (no content, or not a JSON
    object) — signalling the caller to retry the batch. Otherwise returns one
    verdict per entry: a missing entry id, a non-list value, or an
    out-of-range index resolves to None (FAILED) for that entry only, without
    invalidating the rest of the batch.

    Hard guard: any proposed index whose part is a "досл." (literal-gloss)
    variant is silently removed from the drop set before the drop-all check,
    regardless of what the model proposed. This is enforced in code, not just
    the prompt, because DeepSeek-v4-pro was empirically found to drop
    "досл." variants despite the system prompt explicitly instructing it to
    keep them, under two different prompt wordings (see
    kamma/threads/20260709_synonym-rerun-pro/plan.md Drift Log). If guarding
    strips the drop set down to drop-all, the entry is FAILED.
    """
    if content is None:
        return None
    try:
        parsed = json.loads(_strip_fences(content))
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None

    results: dict[int, set[int] | None] = {}
    for entry in entries:
        raw_indexes = parsed.get(str(entry.id))
        if not isinstance(raw_indexes, list):
            results[entry.id] = None
            continue
        if any(not isinstance(i, int) or isinstance(i, bool) for i in raw_indexes):
            results[entry.id] = None
            continue
        indexes = set(raw_indexes)
        in_range = all(0 <= i < len(entry.parts) for i in indexes)
        if not in_range:
            results[entry.id] = None
            continue
        indexes = {i for i in indexes if not _is_literal_gloss(entry.parts[i])}
        if len(indexes) >= len(entry.parts):
            results[entry.id] = None
            continue
        results[entry.id] = indexes
    return results


@dataclass
class CacheRecord:
    """One persisted judgment, keyed for lookup by (id, field, variants_hash, model)."""

    id: int
    field: str
    variants_hash: str
    model: str
    verdict: str  # "trim" | "keep" | "failed"
    drop_indexes: list[int] | None
    timestamp: str


def variants_hash(parts: list[str]) -> str:
    """Hash the original (non-normalized) parts list — the cache staleness key."""
    return hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()


def verdict_from_drop(drop: set[int] | None) -> str:
    """Map a tri-state drop-index result to its cache verdict string."""
    if drop is None:
        return "failed"
    return "trim" if drop else "keep"


def make_cache_record(
    entry: JudgeEntry, drop: set[int] | None, model_key: str
) -> CacheRecord:
    """Build the cache record for one entry's judgment."""
    verdict = verdict_from_drop(drop)
    drop_indexes = sorted(drop) if drop is not None else None
    return CacheRecord(
        id=entry.id,
        field=entry.field,
        variants_hash=variants_hash(entry.parts),
        model=model_key,
        verdict=verdict,
        drop_indexes=drop_indexes,
        timestamp=datetime.datetime.now().astimezone().isoformat(),
    )


def load_judgment_cache(path: Path) -> dict[tuple[int, str, str, str], CacheRecord]:
    """Load the judgment cache, keyed by (id, field, variants_hash, model). Later lines win."""
    cache: dict[tuple[int, str, str, str], CacheRecord] = {}
    if not path.exists():
        return cache
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
            record = CacheRecord(**raw)
        except (json.JSONDecodeError, TypeError):
            continue
        cache[(record.id, record.field, record.variants_hash, record.model)] = record
    return cache


def append_judgment(path: Path, record: CacheRecord) -> None:
    """Append one judgment record to the JSONL cache, creating the directory if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def find_cached_judgment(
    cache: dict[tuple[int, str, str, str], CacheRecord],
    entry_id: int,
    field: str,
    vhash: str,
) -> CacheRecord | None:
    """Return the latest non-failed judgment for an entry from any model, else None."""
    best: CacheRecord | None = None
    for (rec_id, rec_field, rec_hash, _model), record in cache.items():
        if (rec_id, rec_field, rec_hash) != (entry_id, field, vhash):
            continue
        if record.verdict == "failed":
            continue
        if best is None or record.timestamp > best.timestamp:
            best = record
    return best


def update_failure_streak(streak: int, request_failures: int, any_success: bool) -> int:
    """Consecutive failed AI requests; any successful request resets it."""
    if any_success:
        return 0
    return streak + request_failures


@dataclass
class JudgeResult:
    """Outcome of judging one batch with one model or a model chain."""

    verdicts: dict[int, set[int] | None]
    request_failures: int
    any_success: bool
    model: str
    transport_failed: bool = False


def resolve_chain(
    ai_manager: "AIManager", provider: str | None, model: str | None
) -> list[tuple[str, str]]:
    """Explicit pair -> only that pair; otherwise the initialised DEFAULT_MODELS pairs in order."""
    if provider and model:
        return [(provider, model)]
    return [
        (prov, mod)
        for prov, mod, *_ in ai_manager.DEFAULT_MODELS
        if prov in ai_manager.providers
    ]


# Request outcome states.
_OK = "ok"
_UNPARSEABLE = "unparseable"
_TRANSPORT = "transport"


def _judge_request(
    ai_manager: "AIManager",
    entries: list[JudgeEntry],
    provider: str | None,
    model: str | None,
) -> tuple[dict[int, set[int] | None] | None, str]:
    """Make one judge request for a batch. Returns (parsed, state).

    state is `transport` when the provider raised or returned no content,
    `unparseable` when content could not be parsed as the batch JSON object,
    else `ok`. Per-entry validation failures inside a parsed batch do not mark
    the whole request failed.
    """
    prompt = build_judge_prompt(entries)
    try:
        response = ai_manager.request(
            prompt,
            prompt_sys=JUDGE_SYSTEM_PROMPT,
            provider_preference=provider,
            model=model,
        )
    except Exception as exc:  # noqa: BLE001 - provider/client failures should enter retry flow.
        pr.red(f"AI judge request failed: {exc}")
        return None, _TRANSPORT
    if response.content is None:
        return None, _TRANSPORT
    parsed = parse_judge_response(response.content, entries)
    return parsed, (_OK if parsed is not None else _UNPARSEABLE)


def judge_entries(
    ai_manager: "AIManager",
    entries: list[JudgeEntry],
    provider: str | None,
    model: str | None,
) -> JudgeResult:
    """Judge a batch with one pair: one retry on batch failure, then per-entry fallback.

    `transport_failed` is set when a request pair failed twice at transport
    level (no content / exception); the caller may then try the next pair.
    """
    model_label = model or "default"
    request_failures = 0
    any_success = False

    def attempt(
        batch: list[JudgeEntry],
    ) -> tuple[dict[int, set[int] | None] | None, bool]:
        """Request twice; return (parsed, transport_failed_both_times)."""
        nonlocal request_failures, any_success
        states: list[str] = []
        for n in range(2):
            parsed, state = _judge_request(ai_manager, batch, provider, model)
            if state == _OK:
                any_success = True
                return parsed, False
            request_failures += 1
            states.append(state)
            if n == 0:
                time.sleep(RETRY_SLEEP_SECONDS)
        return None, all(state == _TRANSPORT for state in states)

    parsed, both_transport = attempt(entries)
    if parsed is not None:
        return JudgeResult(parsed, request_failures, any_success, model_label)
    if both_transport:
        return JudgeResult(
            {entry.id: None for entry in entries},
            request_failures,
            any_success,
            model_label,
            transport_failed=True,
        )

    # Batch judging failed twice (unparseable) — judge entries individually.
    results: dict[int, set[int] | None] = {}
    transport_failed = False
    for entry in entries:
        single, single_transport = attempt([entry])
        transport_failed = transport_failed or single_transport
        results[entry.id] = single[entry.id] if single is not None else None
    return JudgeResult(
        results, request_failures, any_success, model_label, transport_failed
    )


def judge_with_chain(
    ai_manager: "AIManager",
    entries: list[JudgeEntry],
    chain: list[tuple[str, str]],
) -> JudgeResult:
    """Judge a batch walking `chain`; advance only on transport failure.

    The returned result's `model` is the pair that answered (or the last pair
    tried when every pair failed at transport level).
    """
    request_failures = 0
    any_success = False
    last: JudgeResult | None = None
    for provider, model in chain:
        last = judge_entries(ai_manager, entries, provider, model)
        request_failures += last.request_failures
        any_success = any_success or last.any_success
        if not last.transport_failed:
            break
    if last is None:
        return JudgeResult({entry.id: None for entry in entries}, 0, False, "none")
    return JudgeResult(
        last.verdicts, request_failures, any_success, last.model, last.transport_failed
    )


def _tsv_safe(value: str) -> str:
    """Strip characters that would corrupt a TSV cell."""
    return value.replace("\t", " ").replace("\n", " ").replace("\r", " ")


TSV_HEADER: list[str] = [
    "id",
    "field",
    "lemma",
    "english",
    "current_value",
    "proposed_value",
    "dropped",
    "max_ratio",
    "verdict",
    "judge_model",
    "decision",
]

_REJECT_DECISIONS = {"n", "no", "skip"}


def build_tsv_row(
    *,
    entry_id: int,
    field: str,
    lemma: str,
    english: str,
    current_value: str,
    proposed_value: str,
    parts: list[str],
    drop: set[int],
    max_ratio: float,
    verdict: str,
    judge_model: str,
) -> list[str]:
    """Build one review-TSV row in TSV_HEADER order; `decision` is left empty for the reviewer."""
    dropped = " | ".join(parts[i] for i in sorted(drop))
    return [
        str(entry_id),
        field,
        _tsv_safe(lemma),
        _tsv_safe(english),
        _tsv_safe(current_value),
        _tsv_safe(proposed_value),
        _tsv_safe(dropped),
        f"{max_ratio:.4f}",
        verdict,
        judge_model,
        "",
    ]


class TsvFieldMismatchError(ValueError):
    """A review TSV row targets a different field than the one being applied."""


def apply_review_tsv(
    session: Session,
    model_cls: type[Russian] | type[Tamil],
    field: str,
    tsv_path: Path,
    applied_path: Path,
) -> dict[str, int]:
    """Apply a reviewed TSV: write approved rows, committing and logging each one.

    A row is rejected (`decision` n/no/skip), unchanged (empty or identical
    `proposed_value`), stale (DB value differs from `current_value`), or
    applied. Any row with a different `field` aborts before any write.
    """
    with tsv_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    wrong = [row for row in rows if row.get("field") != field]
    if wrong:
        raise TsvFieldMismatchError(
            f"{len(wrong)} row(s) in {tsv_path.name} have a field other than {field!r} "
            f"(first: id {wrong[0].get('id')}, field {wrong[0].get('field')!r}); nothing applied."
        )

    totals = {"applied": 0, "rejected": 0, "unchanged": 0, "stale": 0}
    applied_path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not applied_path.exists()
    with applied_path.open("a", encoding="utf-8", newline="") as out:
        writer = csv.writer(out, delimiter="\t")
        if new_file:
            writer.writerow(["id", "field", "old", "new"])
        for row in rows:
            decision = (row.get("decision") or "").strip().lower()
            current = row.get("current_value") or ""
            proposed = row.get("proposed_value") or ""
            if decision in _REJECT_DECISIONS:
                totals["rejected"] += 1
                continue
            if not proposed or proposed == current:
                totals["unchanged"] += 1
                continue
            record = session.get(model_cls, int(row["id"]))
            if record is None:
                totals["stale"] += 1
                continue
            db_value = str(getattr(record, field) or "")
            if db_value != current:
                totals["stale"] += 1
                continue
            setattr(record, field, proposed)
            session.commit()
            writer.writerow(
                [row["id"], field, _tsv_safe(db_value), _tsv_safe(proposed)]
            )
            out.flush()
            totals["applied"] += 1
    return totals


def append_audit_log(
    log_path: Path,
    *,
    start: str,
    end: str,
    mode: str,
    field: str,
    flagged: int,
    changed: int,
    exit_code: int,
) -> None:
    """Append one session line for an audit run, in the same format as batch_runner."""
    line = format_session_line(
        start,
        end,
        {
            "op": 4,
            "mode": mode,
            "lang": "ru",
            "chunks": 0,
            "attempted": flagged,
            "ok": changed,
            "field": field,
        },
        exit_code,
    )
    append_log_line(log_path, line)


def record_last_audit(
    state_path: Path, *, field: str, mode: str, flagged: int, ts: str
) -> None:
    """Set state.json `last_audit`, preserving all other keys."""
    update_state(
        state_path,
        {"last_audit": {"field": field, "mode": mode, "flagged": flagged, "ts": ts}},
    )


def _now_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit duplicate/near-identical synonyms in a meaning field. "
        "Default: report only. --ai judges (no writes). --fix removes strict "
        "duplicates. --apply-tsv applies a reviewed TSV."
    )
    parser.add_argument(
        "--field",
        choices=["ru_meaning", "ru_meaning_raw", "ta_meaning"],
        default="ru_meaning_raw",
        help="meaning field to audit (default: ru_meaning_raw)",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="max rows to audit (default: all)"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="apply safe fixes to the DB (strict duplicates only; brackets are kept)",
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="judge flagged entries with the model chain (judge only, no DB writes)",
    )
    parser.add_argument(
        "--apply-tsv",
        type=Path,
        default=None,
        metavar="PATH",
        help="apply a reviewed review.tsv to the DB (no AI, no cache)",
    )
    parser.add_argument(
        "--allow-peak",
        action="store_true",
        help="run --ai during DeepSeek peak hours (full price)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="difflib.SequenceMatcher ratio for the lexical near-dup flag (default: 0.85)",
    )
    parser.add_argument(
        "--provider",
        help="explicit AI provider (must be given together with --model; "
        "default: the default_models chain)",
    )
    parser.add_argument(
        "--model",
        help="explicit AI model (must be given together with --provider)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="flagged entries judged per AI request (default: 10)",
    )
    parser.add_argument(
        "--max-judgments",
        type=int,
        default=0,
        help="stop after N new AI judgments this run (default: 0 = unlimited)",
    )
    return parser


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """Reject invalid flag combinations via parser.error (exit code 2)."""
    if bool(args.provider) != bool(args.model):
        parser.error(
            "--provider and --model must be given together (or neither) — a lone "
            "--provider silently falls back to the default model chain, which is "
            "the exact behavior this flag exists to override."
        )
    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")
    if args.max_judgments < 0:
        parser.error("--max-judgments must be 0 or greater")
    if args.apply_tsv is not None and (args.ai or args.fix or args.limit is not None):
        parser.error("--apply-tsv cannot be combined with --ai, --fix or --limit")
    if args.ai and args.field == "ta_meaning":
        parser.error("Tamil judge not supported")


def run_apply_tsv(args: argparse.Namespace) -> tuple[int, int]:
    """Apply a reviewed TSV. Returns (rows read, rows applied)."""
    model_cls = FIELD_MODEL[args.field]
    pth = ProjectPaths(base_dir=PROJECT_ROOT)
    db_session: Session = get_db_session(pth.dpd_db_path)
    timestamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S")
    applied_path = REPORT_DIR / f"{timestamp}_applied.tsv"
    try:
        totals = apply_review_tsv(
            db_session, model_cls, args.field, args.apply_tsv, applied_path
        )
    except TsvFieldMismatchError as exc:
        db_session.close()
        pr.red(str(exc))
        sys.exit(1)
    db_session.close()
    pr.white(
        f"Applied: {totals['applied']}, rejected: {totals['rejected']}, "
        f"unchanged: {totals['unchanged']}, stale: {totals['stale']}"
    )
    if totals["applied"]:
        pr.white(f"Undo record: {applied_path}")
    return sum(totals.values()), totals["applied"]


def run_audit(args: argparse.Namespace) -> tuple[int, int]:
    """Report / judge / strict-fix run. Returns (rows flagged, rows fixed)."""
    use_ai = args.ai
    ai_manager: "AIManager | None" = None  # noqa: UP037 (local import below shadows the name)
    chain: list[tuple[str, str]] = []
    if use_ai:
        from tools.ai_manager import AIManager

        ai_manager = AIManager()
        if args.provider and args.provider not in ai_manager.providers:
            pr.red(
                f"--provider {args.provider!r} is not initialized in AIManager.providers "
                f"({sorted(ai_manager.providers)}); check API keys/config before re-running."
            )
            sys.exit(1)
        chain = resolve_chain(ai_manager, args.provider, args.model)
        if not chain:
            pr.red("No initialised provider in default_models; check API keys/config.")
            sys.exit(1)

    model_cls = FIELD_MODEL[args.field]
    pth = ProjectPaths(base_dir=PROJECT_ROOT)
    db_session: Session = get_db_session(pth.dpd_db_path)

    field_column = getattr(model_cls, args.field)
    query = (
        db_session.query(DpdHeadword, model_cls)
        .join(model_cls, DpdHeadword.id == model_cls.id)
        .filter(field_column.isnot(None), field_column != "")
        .order_by(DpdHeadword.id)
    )
    if args.limit:
        query = query.limit(args.limit)
    rows = query.all()

    cache = load_judgment_cache(CACHE_PATH) if use_ai else {}

    # --- Phase A: lexical scan ---
    flagged: list[dict] = []
    for headword, record in rows:
        field_value = getattr(record, args.field)
        parts = split_meanings(field_value)
        if len(parts) < 2:
            continue
        exact_dups = find_exact_dups(parts)
        near_dups = find_near_dups(parts, args.threshold)
        if not exact_dups and not near_dups:
            continue
        flagged.append(
            {
                "headword": headword,
                "record": record,
                "field_value": field_value,
                "parts": parts,
                "exact_dups": exact_dups,
                "near_dups": near_dups,
            }
        )

    n_rows_flagged = len(flagged)
    n_exact = sum(len(item["exact_dups"]) for item in flagged)
    n_near = sum(len(item["near_dups"]) for item in flagged)

    # --- Phase B: AI judging (per-entry, batched, cached) ---
    n_ai_trim = 0
    n_ai_keep = 0
    n_ai_failed = 0
    n_ai_cached = 0
    n_ai_skipped = 0

    if use_ai:
        assert ai_manager is not None
        to_judge: list[JudgeEntry] = []
        for item in flagged:
            if not item["near_dups"]:
                continue
            entry = JudgeEntry(
                id=item["headword"].id,
                field=args.field,
                lemma_1=item["headword"].lemma_1,
                english=item["headword"].meaning_1 or item["headword"].meaning_2 or "",
                parts=item["parts"],
            )
            item["judge_entry"] = entry
            cached = find_cached_judgment(
                cache, entry.id, entry.field, variants_hash(entry.parts)
            )
            if cached is not None:
                item["verdict"] = set(cached.drop_indexes or [])
                item["judge_model"] = cached.model
                n_ai_cached += 1
                continue
            to_judge.append(entry)

        limited_to_judge = to_judge
        if args.max_judgments and len(to_judge) > args.max_judgments:
            limited_to_judge = to_judge[: args.max_judgments]
            n_ai_skipped = len(to_judge) - args.max_judgments

        batches = [
            limited_to_judge[i : i + args.batch_size]
            for i in range(0, len(limited_to_judge), args.batch_size)
        ]

        entry_by_id = {
            item["judge_entry"].id: item for item in flagged if "judge_entry" in item
        }

        failure_streak = 0
        for batch_index, batch in enumerate(batches):
            result = judge_with_chain(ai_manager, batch, chain)
            failure_streak = update_failure_streak(
                failure_streak, result.request_failures, result.any_success
            )
            for entry in batch:
                drop = result.verdicts.get(entry.id)
                entry_by_id[entry.id]["verdict"] = drop
                entry_by_id[entry.id]["judge_model"] = result.model
                append_judgment(
                    CACHE_PATH, make_cache_record(entry, drop, result.model)
                )

            if failure_streak >= MAX_CONSECUTIVE_FAILURES:
                pr.red(
                    f"{failure_streak} consecutive AI request failures — "
                    "aborting AI judging for this run (provider may be down or "
                    "quota exhausted). Already-judged entries are cached; re-run "
                    "to resume."
                )
                n_ai_skipped += sum(len(b) for b in batches[batch_index + 1 :])
                break

        for item in flagged:
            if "judge_entry" not in item or "verdict" not in item:
                continue
            verdict = item["verdict"]
            if verdict is None:
                n_ai_failed += 1
            elif verdict:
                n_ai_trim += 1
            else:
                n_ai_keep += 1

    # --- Phase C+D: apply fixes and build reports ---
    report_lines: list[str] = []
    tsv_rows: list[list[str]] = []
    n_fixed = 0

    for item in flagged:
        headword = item["headword"]
        record = item["record"]
        field_value = item["field_value"]
        parts = item["parts"]
        exact_dups = item["exact_dups"]
        near_dups = item["near_dups"]
        verdict = item.get("verdict")
        has_judge_entry = "judge_entry" in item

        ai_drop = verdict if isinstance(verdict, set) else set()
        proposed_drop = set(exact_dups) | ai_drop
        proposed_value = rebuild_field(parts, proposed_drop)

        row_reasons = [f"exact duplicate: '{parts[i]}'" for i in exact_dups]
        for i, j, ratio in near_dups:
            row_reasons.append(
                f"near-duplicate candidate ({ratio:.2f}): '{parts[i]}' ~ '{parts[j]}'"
            )

        if use_ai and has_judge_entry:
            if "verdict" not in item:
                row_reasons.append(
                    "AI judgment skipped (--max-judgments limit reached)"
                )
                verdict_label = "skipped"
            elif verdict is None:
                row_reasons.append(
                    "AI judging FAILED for this entry (see judgments.jsonl)"
                )
                verdict_label = "failed"
            elif verdict:
                for i in sorted(verdict):
                    row_reasons.append(f"AI-dropped variant {i}: '{parts[i]}'")
                verdict_label = "trim"
            else:
                row_reasons.append("AI judged all variants distinct (kept)")
                verdict_label = "keep"
        elif exact_dups and not near_dups:
            verdict_label = "exact_only"
        else:
            verdict_label = "not_ai_judged"

        if args.fix and exact_dups:
            new_value = rebuild_field(parts, set(exact_dups))
            setattr(record, args.field, new_value)
            db_session.commit()
            n_fixed += 1
            pr.green(f"Fixed ID {headword.id}: '{field_value}' -> '{new_value}'")

        report_lines.append(f"ID: {headword.id}")
        report_lines.append(f"Lemma: {headword.lemma_1}")
        report_lines.append(f"Original: {field_value}")
        report_lines.append(f"Proposed: {proposed_value}")
        report_lines.append("Reasons:")
        report_lines.extend(f"  - {reason}" for reason in row_reasons)
        report_lines.append("")

        max_ratio = max((ratio for _, _, ratio in near_dups), default=0.0)
        tsv_rows.append(
            build_tsv_row(
                entry_id=headword.id,
                field=args.field,
                lemma=headword.lemma_1,
                english=headword.meaning_1 or headword.meaning_2 or "",
                current_value=field_value,
                proposed_value=proposed_value,
                parts=parts,
                drop=proposed_drop,
                max_ratio=max_ratio,
                verdict=verdict_label,
                judge_model=str(item.get("judge_model", "")),
            )
        )

    db_session.close()

    ratio_col = TSV_HEADER.index("max_ratio")
    tsv_rows.sort(key=lambda r: float(r[ratio_col]), reverse=True)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = REPORT_DIR / f"{timestamp}_report.txt"
    tsv_path = REPORT_DIR / f"{timestamp}_review.tsv"

    header = [
        f"SYNONYM AUDIT REPORT — field={args.field}\n",
        "=" * 50 + "\n\n",
        f"Rows audited: {len(rows)}\n",
        f"Rows flagged: {n_rows_flagged}\n",
        f"Exact duplicates found: {n_exact}\n",
        f"Near-duplicate pairs found: {n_near}\n",
    ]
    if use_ai:
        header.append(f"AI entries trimmed: {n_ai_trim}\n")
        header.append(f"AI entries kept: {n_ai_keep}\n")
        header.append(f"AI entries failed: {n_ai_failed}\n")
        header.append(f"AI judgments served from cache: {n_ai_cached}\n")
        if n_ai_skipped:
            header.append(
                f"AI judgments skipped (--max-judgments limit): {n_ai_skipped}\n"
            )
    header.append(f"Rows fixed: {n_fixed}\n\n")

    report_path.write_text("".join(header) + "\n".join(report_lines), encoding="utf-8")

    with tsv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(TSV_HEADER)
        writer.writerows(tsv_rows)

    pr.white(f"Report saved to {report_path}")
    pr.white(f"Review TSV saved to {tsv_path}")
    pr.white(f"Rows audited: {len(rows)}, rows flagged: {n_rows_flagged}")
    pr.white(f"Exact duplicates: {n_exact}, near-duplicate pairs: {n_near}")
    if use_ai:
        pr.white(
            f"AI trimmed: {n_ai_trim}, kept: {n_ai_keep}, failed: {n_ai_failed}, "
            f"cached: {n_ai_cached}, skipped: {n_ai_skipped}"
        )
    pr.white(f"Rows fixed: {n_fixed}")
    return n_rows_flagged, n_fixed


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    validate_args(parser, args)

    if args.ai:
        require_offpeak(args.allow_peak)

    if args.apply_tsv is not None:
        mode = "apply-tsv"
    elif args.ai:
        mode = "ai-fix" if args.fix else "ai"
    elif args.fix:
        mode = "fix"
    else:
        mode = "report"

    start = _now_iso()
    exit_code = 0
    flagged = 0
    changed = 0
    try:
        if args.apply_tsv is not None:
            flagged, changed = run_apply_tsv(args)
        else:
            flagged, changed = run_audit(args)
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 1
        raise
    except Exception:
        exit_code = 1
        raise
    finally:
        end = _now_iso()
        append_audit_log(
            LOG_PATH,
            start=start,
            end=end,
            mode=mode,
            field=args.field,
            flagged=flagged,
            changed=changed,
            exit_code=exit_code,
        )
        record_last_audit(
            STATE_PATH, field=args.field, mode=mode, flagged=flagged, ts=end
        )


if __name__ == "__main__":
    main()
