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
from tools.paths import ProjectPaths
from tools.printer import printer as pr

if TYPE_CHECKING:
    from tools.ai_manager import AIManager

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PROJECT_ROOT / "temp" / "synonym_audit"
CACHE_PATH = REPORT_DIR / "judgments.jsonl"

FIELD_MODEL: dict[str, type[Russian] | type[Tamil]] = {
    "ru_meaning": Russian,
    "ru_meaning_raw": Russian,
    "ta_meaning": Tamil,
}

_BRACKETS_RE = re.compile(r"\([^)]*\)")
_WHITESPACE_RE = re.compile(r"\s+")

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
    """Split a `;`-joined meaning field into stripped, non-empty parts."""
    return [part.strip() for part in field.split(";") if part.strip()]


def normalize(part: str) -> str:
    """Normalize a meaning fragment for duplicate comparison."""
    text = part.lower().replace("ё", "е")
    text = _BRACKETS_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text.rstrip(".").strip()


def find_exact_dups(parts: list[str]) -> list[int]:
    """Return indexes of parts whose normalized form already appeared earlier."""
    seen: set[str] = set()
    dup_indexes: list[int] = []
    for i, part in enumerate(parts):
        norm = normalize(part)
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
        parsed = json.loads(content)
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


def _judge_request(
    ai_manager: "AIManager",
    entries: list[JudgeEntry],
    provider: str | None,
    model: str | None,
) -> tuple[dict[int, set[int] | None] | None, bool]:
    """Make one judge request for a batch. Returns (parsed, request_ok).

    request_ok is False when the response cannot be parsed as the required
    batch JSON object. Per-entry validation failures inside a parsed batch do
    not mark the whole request failed.
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
        return None, False
    parsed = parse_judge_response(response.content, entries)
    return parsed, parsed is not None


def judge_entries(
    ai_manager: "AIManager",
    entries: list[JudgeEntry],
    provider: str | None,
    model: str | None,
) -> tuple[dict[int, set[int] | None], int]:
    """Judge a batch of entries: one retry on batch failure, then per-entry fallback.

    Returns (verdict by entry id, count of failed AI requests encountered).
    """
    request_failures = 0
    parsed, ok = _judge_request(ai_manager, entries, provider, model)
    if not ok:
        request_failures += 1
    if parsed is None:
        time.sleep(RETRY_SLEEP_SECONDS)
        parsed, ok = _judge_request(ai_manager, entries, provider, model)
        if not ok:
            request_failures += 1

    if parsed is not None:
        return parsed, request_failures

    # Batch judging failed twice — fall back to judging entries individually.
    results: dict[int, set[int] | None] = {}
    for entry in entries:
        single, ok = _judge_request(ai_manager, [entry], provider, model)
        if not ok:
            request_failures += 1
        if single is None:
            time.sleep(RETRY_SLEEP_SECONDS)
            single, ok = _judge_request(ai_manager, [entry], provider, model)
            if not ok:
                request_failures += 1
        results[entry.id] = single[entry.id] if single is not None else None
    return results, request_failures


def _tsv_safe(value: str) -> str:
    """Strip characters that would corrupt a TSV cell."""
    return value.replace("\t", " ").replace("\n", " ").replace("\r", " ")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit and optionally trim duplicate/near-identical synonyms in a meaning field."
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
        help="apply safe fixes to the DB (exact normalized duplicates only)",
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="additionally judge flagged entries with AIManager (judge only, no DB writes)",
    )
    parser.add_argument(
        "--fix-ai",
        action="store_true",
        help="judge uncached flagged entries, then trim cached AI-confirmed duplicates (implies --ai)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="difflib.SequenceMatcher ratio for the lexical near-dup flag (default: 0.85)",
    )
    parser.add_argument(
        "--provider",
        help="explicit AI provider preference (must be given together with --model; "
        "default: AIManager's default fallback chain)",
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
    args = parser.parse_args()

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

    use_ai = args.ai or args.fix_ai
    model_key = args.model or "default"

    ai_manager: "AIManager | None" = None  # noqa: UP037 (local import below shadows the name)
    if use_ai:
        from tools.ai_manager import AIManager

        ai_manager = AIManager()
        if args.provider and args.provider not in ai_manager.providers:
            pr.red(
                f"--provider {args.provider!r} is not initialized in AIManager.providers "
                f"({sorted(ai_manager.providers)}); check API keys/config before re-running."
            )
            sys.exit(1)

    model_cls = FIELD_MODEL[args.field]
    pth = ProjectPaths(base_dir=PROJECT_ROOT)
    db_session: Session = get_db_session(pth.dpd_db_path)

    field_column = getattr(model_cls, args.field)
    query = (
        db_session.query(DpdHeadword, model_cls)
        .join(model_cls, DpdHeadword.id == model_cls.id)
        .filter(field_column.isnot(None), field_column != "")
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
            cache_key = (entry.id, entry.field, variants_hash(entry.parts), model_key)
            cached = cache.get(cache_key)
            if cached is not None:
                item["verdict"] = (
                    None
                    if cached.verdict == "failed"
                    else set(cached.drop_indexes or [])
                )
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

        consecutive_failures = 0
        for batch_index, batch in enumerate(batches):
            verdicts, _request_failures = judge_entries(
                ai_manager, batch, args.provider, args.model
            )
            failed_entries = sum(1 for entry in batch if verdicts.get(entry.id) is None)
            consecutive_failures = (
                consecutive_failures + failed_entries if failed_entries else 0
            )
            for entry in batch:
                drop = verdicts.get(entry.id)
                entry_by_id[entry.id]["verdict"] = drop
                record = make_cache_record(entry, drop, model_key)
                append_judgment(CACHE_PATH, record)

            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                pr.red(
                    f"{consecutive_failures} consecutive AI request failures — "
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

        apply_drop = set(exact_dups)
        if args.fix_ai and isinstance(verdict, set):
            apply_drop |= verdict

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

        if (args.fix or args.fix_ai) and apply_drop:
            new_value = rebuild_field(parts, apply_drop)
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
            [
                str(headword.id),
                _tsv_safe(headword.lemma_1),
                _tsv_safe(headword.meaning_1 or headword.meaning_2 or ""),
                _tsv_safe(field_value),
                _tsv_safe(proposed_value),
                f"{max_ratio:.4f}",
                verdict_label,
            ]
        )

    db_session.close()

    tsv_rows.sort(key=lambda r: float(r[5]), reverse=True)

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
        writer.writerow(
            [
                "id",
                "lemma",
                "english",
                "current_value",
                "proposed_value",
                "max_ratio",
                "verdict",
            ]
        )
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


if __name__ == "__main__":
    main()
