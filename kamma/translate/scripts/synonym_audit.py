"""Audit Russian and Tamil meaning fields for duplicate or near-identical synonyms and optionally trim them."""

import argparse
import datetime
import difflib
import re
from pathlib import Path

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Russian, Tamil
from tools.paths import ProjectPaths
from tools.printer import printer as pr

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PROJECT_ROOT / "temp" / "synonym_audit"

FIELD_MODEL: dict[str, type[Russian] | type[Tamil]] = {
    "ru_meaning": Russian,
    "ru_meaning_raw": Russian,
    "ta_meaning": Tamil,
}

_BRACKETS_RE = re.compile(r"\([^)]*\)")
_WHITESPACE_RE = re.compile(r"\s+")


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


def _judge_pair(ai_manager, part_a: str, part_b: str, english: str) -> bool:
    """Ask the AI whether two meaning variants are duplicates of one sense."""
    prompt_sys = (
        "You are a strict linguistic judge. Given an English definition and two "
        "translated variants of it, answer with exactly one word: DUPLICATE if "
        "the two variants express the same sense, nuance, or usage, or DISTINCT "
        "if they express a genuinely different sense, nuance, or usage."
    )
    prompt = (
        f"English meaning: {english}\n"
        f"Variant A: {part_a}\n"
        f"Variant B: {part_b}\n"
        "Answer with exactly one word: DUPLICATE or DISTINCT."
    )
    response = ai_manager.request(prompt, prompt_sys=prompt_sys)
    content = (response.content or "").strip().upper()
    return content.startswith("DUPLICATE")


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
        help="additionally judge near-duplicate pairs with AIManager",
    )
    parser.add_argument(
        "--fix-ai",
        action="store_true",
        help="trim AI-confirmed near-duplicates (implies --ai)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="difflib.SequenceMatcher ratio for the lexical near-dup flag (default: 0.85)",
    )
    args = parser.parse_args()

    use_ai = args.ai or args.fix_ai

    ai_manager = None
    if use_ai:
        from tools.ai_manager import AIManager

        ai_manager = AIManager()

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

    report_lines: list[str] = []
    n_rows_flagged = 0
    n_exact = 0
    n_near = 0
    n_ai_confirmed = 0
    n_fixed = 0

    for headword, record in rows:
        field_value = getattr(record, args.field)
        parts = split_meanings(field_value)
        if len(parts) < 2:
            continue

        exact_dups = find_exact_dups(parts)
        near_dups = find_near_dups(parts, args.threshold)
        if not exact_dups and not near_dups:
            continue

        n_rows_flagged += 1
        n_exact += len(exact_dups)
        drop: set[int] = set(exact_dups)
        row_reasons = [f"exact duplicate: '{parts[i]}'" for i in exact_dups]

        if near_dups:
            n_near += len(near_dups)
            ai_confirmed: list[tuple[int, int, float]] = []
            if use_ai:
                english = headword.meaning_1 or ""
                for i, j, ratio in near_dups:
                    if _judge_pair(ai_manager, parts[i], parts[j], english):
                        ai_confirmed.append((i, j, ratio))
                        row_reasons.append(
                            f"AI-confirmed near-duplicate ({ratio:.2f}): "
                            f"'{parts[i]}' ~ '{parts[j]}'"
                        )
                    else:
                        row_reasons.append(
                            f"AI-judged distinct ({ratio:.2f}): "
                            f"'{parts[i]}' ~ '{parts[j]}'"
                        )
                n_ai_confirmed += len(ai_confirmed)
                if args.fix_ai:
                    drop.update(j for _, j, _ in ai_confirmed)
            else:
                for i, j, ratio in near_dups:
                    row_reasons.append(
                        f"near-duplicate candidate ({ratio:.2f}, not auto-fixed): "
                        f"'{parts[i]}' ~ '{parts[j]}'"
                    )

        report_lines.append(f"ID: {headword.id}")
        report_lines.append(f"Lemma: {headword.lemma_1}")
        report_lines.append(f"Original: {field_value}")
        report_lines.append(f"Proposed: {rebuild_field(parts, drop)}")
        report_lines.append("Reasons:")
        report_lines.extend(f"  - {reason}" for reason in row_reasons)
        report_lines.append("")

        if (args.fix or args.fix_ai) and drop:
            new_value = rebuild_field(parts, drop)
            setattr(record, args.field, new_value)
            db_session.commit()
            n_fixed += 1
            pr.green(f"Fixed ID {headword.id}: '{field_value}' -> '{new_value}'")

    db_session.close()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = REPORT_DIR / f"{timestamp}_report.txt"

    header = [
        f"SYNONYM AUDIT REPORT — field={args.field}\n",
        "=" * 50 + "\n\n",
        f"Rows audited: {len(rows)}\n",
        f"Rows flagged: {n_rows_flagged}\n",
        f"Exact duplicates found: {n_exact}\n",
        f"Near-duplicate pairs found: {n_near}\n",
    ]
    if use_ai:
        header.append(f"AI-confirmed duplicate pairs: {n_ai_confirmed}\n")
    header.append(f"Rows fixed: {n_fixed}\n\n")

    report_path.write_text("".join(header) + "\n".join(report_lines), encoding="utf-8")

    pr.white(f"Report saved to {report_path}")
    pr.white(f"Rows audited: {len(rows)}, rows flagged: {n_rows_flagged}")
    pr.white(f"Exact duplicates: {n_exact}, near-duplicate pairs: {n_near}")
    if use_ai:
        pr.white(f"AI-confirmed duplicates: {n_ai_confirmed}")
    pr.white(f"Rows fixed: {n_fixed}")


if __name__ == "__main__":
    main()
