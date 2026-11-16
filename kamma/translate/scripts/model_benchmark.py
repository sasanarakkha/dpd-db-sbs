"""Benchmark candidate AI models on the translate skill's judge, generate and check roles (read-only, no DB writes)."""

import argparse
import csv
import json
import statistics
import time
from typing import cast
from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Callable, Sequence

from sqlalchemy import Row
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Russian, Tamil
from kamma.translate.scripts.ai_generate_translation import create_translation_prompt
from kamma.translate.scripts.offpeak import require_offpeak
from kamma.translate.scripts.synonym_audit import (
    DEFAULT_THRESHOLD,
    JUDGE_SYSTEM_PROMPT,
    JudgeEntry,
    _is_literal_gloss,
    _strip_fences,
    build_judge_prompt,
    parse_judge_response,
    scan_lexical,
)
from tools.ai_batch_processor import BatchProcessor, WordComparison
from tools.ai_manager import AIManager
from tools.meaning_snapshot_ru import compose_english_content
from tools.paths import ProjectPaths
from tools.printer import printer as pr

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "temp" / "translate_overhaul"

ROLES = ("judge", "generate", "check")
YARDSTICK = ("deepseek", "deepseek-v4-pro")
JUDGE_SAMPLE = 30
JUDGE_BATCH = 10
GENERATE_SAMPLE = 20
CHECK_TRUE_PAIRS = 10
CHARS_PER_TOKEN = 4
REQUEST_TIMEOUT_SECONDS = 60.0
MAX_CONSECUTIVE_FAILURES = 3
CALLS_FILE = "bench_calls.jsonl"


@dataclass
class Call:
    """One request's outcome: reply text (None = failed), latency, and sizes for costing."""

    content: str | None
    seconds: float
    chars_in: int
    chars_out: int


@dataclass
class ModelStats:
    """Per-model accumulation across one role."""

    calls: list[Call] = field(default_factory=list)

    @property
    def invalid(self) -> int:
        return sum(1 for call in self.calls if call.content is None)


def parse_candidate(text: str) -> tuple[str, str]:
    """`provider:model` -> (provider, model); splits at the first colon only."""
    provider, sep, model = text.partition(":")
    if not sep or not provider or not model:
        raise ValueError(f"candidate must be provider:model, got {text!r}")
    return provider, model


def parse_price(text: str) -> tuple[str, tuple[float, float]]:
    """`model=in,out` (USD per 1M tokens) -> (model, (in, out))."""
    model, sep, prices = text.rpartition("=")
    price_in, comma, price_out = prices.partition(",")
    if not sep or not model or not comma:
        raise ValueError(f"price must be model=in,out, got {text!r}")
    return model, (float(price_in), float(price_out))


def estimate_cost_per_100(
    stats: ModelStats, price: tuple[float, float] | None
) -> float | None:
    """Estimated USD per 100 requests from mean chars/4 token counts; None without a price."""
    if price is None or not stats.calls:
        return None
    mean_in = statistics.fmean(c.chars_in for c in stats.calls) / CHARS_PER_TOKEN
    mean_out = statistics.fmean(c.chars_out for c in stats.calls) / CHARS_PER_TOKEN
    return 100 * (mean_in * price[0] + mean_out * price[1]) / 1_000_000


def spread_pick[T](items: list[T], n: int) -> list[T]:
    """Deterministic, evenly spaced sample of up to n items (input order kept)."""
    if n >= len(items):
        return list(items)
    step = len(items) / n
    return [items[int(i * step)] for i in range(n)]


def build_check_pairs(
    pairs: list[tuple[int, str, str]], n_true: int
) -> list[tuple[int, str, str, bool]]:
    """n_true real (id, english, russian) pairs plus the same number mismatched by rotation.

    Each shuffled pair keeps its English but takes the Russian of a different,
    non-identical entry. Returns (id, english, russian, is_true).
    """
    picked = spread_pick(pairs, n_true)
    out: list[tuple[int, str, str, bool]] = [(i, e, r, True) for i, e, r in picked]
    count = len(picked)
    shift = max(1, count // 2)
    for index, (pair_id, english, russian) in enumerate(picked):
        for offset in range(shift, shift + count):
            other = picked[(index + offset) % count][2]
            if other.strip().lower() != russian.strip().lower():
                out.append((pair_id, english, other, False))
                break
    return out


def score_check(verdicts: list[str | None], truth: list[bool]) -> float:
    """Share of pairs judged correctly; MISMATCH = not true, MATCH/PARTIAL_MATCH = true, None = wrong."""
    if not truth:
        return 0.0
    correct = 0
    for verdict, is_true in zip(verdicts, truth, strict=True):
        if verdict is None:
            continue
        if (verdict != "MISMATCH") == is_true:
            correct += 1
    return correct / len(truth)


def count_guard_hits(content: str | None, entries: list[JudgeEntry]) -> int:
    """How many proposed drops pointed at a `досл.` variant (the code guard strips these)."""
    if content is None:
        return 0
    try:
        parsed = json.loads(_strip_fences(content))
    except json.JSONDecodeError:
        return 0
    if not isinstance(parsed, dict):
        return 0
    hits = 0
    for entry in entries:
        raw = parsed.get(str(entry.id))
        if not isinstance(raw, list):
            continue
        hits += sum(
            1
            for i in raw
            if isinstance(i, int)
            and not isinstance(i, bool)
            and 0 <= i < len(entry.parts)
            and _is_literal_gloss(entry.parts[i])
        )
    return hits


def judge_agreement(
    verdicts: dict[int, set[int] | None], reference: dict[int, set[int] | None]
) -> float:
    """Share of entries whose drop set equals the reference model's (FAILED never agrees)."""
    if not reference:
        return 0.0
    same = sum(
        1
        for entry_id, ref in reference.items()
        if ref is not None and verdicts.get(entry_id) == ref
    )
    return same / len(reference)


def judge_sample(session: Session, n: int = JUDGE_SAMPLE) -> list[JudgeEntry]:
    """First n flagged `ru_meaning_raw` entries that have a near-duplicate pair (by id)."""
    rows = (
        session.query(DpdHeadword, Russian)
        .join(Russian, DpdHeadword.id == Russian.id)
        .filter(Russian.ru_meaning_raw.isnot(None), Russian.ru_meaning_raw != "")
        .order_by(DpdHeadword.id)
        .all()
    )
    scan_rows = cast(Sequence[Row[tuple[DpdHeadword, Russian | Tamil]]], rows)
    entries: list[JudgeEntry] = []
    for item in scan_lexical(scan_rows, "ru_meaning_raw", DEFAULT_THRESHOLD):
        if not item["near_dups"]:
            continue
        headword = item["headword"]
        entries.append(
            JudgeEntry(
                id=headword.id,
                field="ru_meaning_raw",
                lemma_1=headword.lemma_1,
                english=headword.meaning_1 or headword.meaning_2 or "",
                parts=item["parts"],
            )
        )
        if len(entries) >= n:
            break
    return entries


def human_headwords(session: Session) -> list[tuple[DpdHeadword, Russian]]:
    """All headwords with a human `ru_meaning`, ordered by id."""
    rows = (
        session.query(DpdHeadword, Russian)
        .join(Russian, DpdHeadword.id == Russian.id)
        .filter(Russian.ru_meaning.isnot(None), Russian.ru_meaning != "")
        .order_by(DpdHeadword.id)
        .all()
    )
    return [(headword, russian) for headword, russian in rows]


def generate_sample(
    session: Session, n: int = GENERATE_SAMPLE
) -> list[tuple[DpdHeadword, str]]:
    """n evenly spaced headwords with a human ru_meaning, paired with that human value."""
    picked = spread_pick(human_headwords(session), n)
    return [(headword, russian.ru_meaning) for headword, russian in picked]


def check_sample(
    session: Session, n_true: int = CHECK_TRUE_PAIRS
) -> list[tuple[int, str, str, bool]]:
    """True and shuffled (id, english, russian, is_true) pairs from human ru_meaning rows."""
    pairs = [
        (headword.id, compose_english_content(headword, "meaning"), russian.ru_meaning)
        for headword, russian in human_headwords(session)
    ]
    return build_check_pairs(pairs, n_true)


def timed_request(
    ai_manager: AIManager,
    prompt: str,
    prompt_sys: str | None,
    pair: tuple[str, str],
) -> Call:
    """One request pinned to `pair`; any exception or empty reply counts as a failed call."""
    start = time.monotonic()
    content: str | None
    try:
        response = ai_manager.request(
            prompt,
            prompt_sys=prompt_sys,
            provider_preference=pair[0],
            model=pair[1],
        )
        content = response.content
    except Exception as exc:  # noqa: BLE001 - a provider failure is a data point here.
        pr.red(f"{pair[0]}:{pair[1]} request failed: {exc}")
        content = None
    seconds = time.monotonic() - start
    return Call(
        content, seconds, len(prompt) + len(prompt_sys or ""), len(content or "")
    )


class CallStore:
    """Append-only JSONL of every call, flushed per call; successful calls resume a rerun."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.done: dict[tuple[str, str, str], Call] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                if record["content"] is None:
                    continue
                self.done[(record["role"], record["model"], record["key"])] = Call(
                    record["content"],
                    record["seconds"],
                    record["chars_in"],
                    record["chars_out"],
                )

    def add(self, role: str, pair: tuple[str, str], key: str, call: Call) -> None:
        """Append one call record and flush it to disk immediately."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "role": role,
            "model": f"{pair[0]}:{pair[1]}",
            "key": key,
            "seconds": round(call.seconds, 2),
            "chars_in": call.chars_in,
            "chars_out": call.chars_out,
            "content": call.content,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
        if call.content is not None:
            self.done[(role, record["model"], key)] = call


@dataclass
class Runner:
    """Shared request context: store, timeout-aware manager and per-(role, model) circuit breaker."""

    ai_manager: AIManager
    store: CallStore
    max_failures: int = MAX_CONSECUTIVE_FAILURES
    streaks: dict[tuple[str, str], int] = field(default_factory=dict)

    def call(
        self,
        role: str,
        pair: tuple[str, str],
        key: str,
        prompt: str,
        prompt_sys: str | None,
        position: str,
    ) -> Call:
        """Cached call if done; skipped (failed, not stored) if the breaker tripped; else request."""
        model = f"{pair[0]}:{pair[1]}"
        cached = self.store.done.get((role, model, key))
        if cached is not None:
            pr.white(f"[{role} {model} {position}] cached")
            return cached
        if self.streaks.get((role, model), 0) >= self.max_failures:
            pr.amber(f"[{role} {model} {position}] skipped (breaker tripped)")
            return Call(None, 0.0, len(prompt) + len(prompt_sys or ""), 0)
        call = timed_request(self.ai_manager, prompt, prompt_sys, pair)
        self.store.add(role, pair, key, call)
        if call.content is None:
            self.streaks[(role, model)] = self.streaks.get((role, model), 0) + 1
            pr.red(f"[{role} {model} {position}] FAILED after {call.seconds:.1f}s")
        else:
            self.streaks[(role, model)] = 0
            pr.green(f"[{role} {model} {position}] {call.seconds:.1f}s")
        return call


def check_prompt_and_parser(
    processor: BatchProcessor, pair_id: int, english: str, russian: str
) -> tuple[str, Callable[[str], str | None]]:
    """The checker's own single-word prompt and strict parser for (english, russian)."""
    comparison = WordComparison(
        headword_id=pair_id,
        lemma_1="",
        english_meaning=english,
        russian_meaning=russian,
    )
    prompt = processor.create_comparison_prompt([comparison], 1, "meaning")

    def parse(content: str) -> str | None:
        results = processor.parse_ai_response(content, comparison)
        return results[0].match_status if results else None

    return prompt, parse


def write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    """Write a TSV with embedded tabs/newlines flattened."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(header)
        for row in rows:
            writer.writerow(
                [cell.replace("\t", " ").replace("\n", " ") for cell in row]
            )


def summary_line(
    role: str,
    pair: tuple[str, str],
    stats: ModelStats,
    price: tuple[float, float] | None,
    extra: str,
) -> str:
    """One summary row: model, invalid replies, median latency, est. cost, role-specific extra."""
    latencies = [c.seconds for c in stats.calls if c.content is not None]
    median = f"{statistics.median(latencies):.1f}s" if latencies else "n/a"
    cost = estimate_cost_per_100(stats, price)
    cost_text = f"${cost:.4f}/100req" if cost is not None else "price n/a"
    return (
        f"{role:8} {pair[0]}:{pair[1]} | invalid {stats.invalid}/{len(stats.calls)} | "
        f"median {median} | {cost_text}{' | ' + extra if extra else ''}"
    )


def run_judge(
    runner: Runner,
    entries: list[JudgeEntry],
    pairs: list[tuple[str, str]],
    prices: dict[str, tuple[float, float]],
    out_dir: Path,
) -> list[str]:
    """Judge the same sample with every pair; compare each with the yardstick's drops."""
    batches = [
        entries[i : i + JUDGE_BATCH] for i in range(0, len(entries), JUDGE_BATCH)
    ]
    verdicts: dict[tuple[str, str], dict[int, set[int] | None]] = {}
    stats: dict[tuple[str, str], ModelStats] = {}
    guard: dict[tuple[str, str], int] = {}
    try:
        for pair in pairs:
            stats[pair] = ModelStats()
            verdicts[pair] = {}
            guard[pair] = 0
            for n, batch in enumerate(batches, 1):
                call = runner.call(
                    "judge",
                    pair,
                    str(batch[0].id),
                    build_judge_prompt(batch),
                    JUDGE_SYSTEM_PROMPT,
                    f"{n}/{len(batches)}",
                )
                stats[pair].calls.append(call)
                guard[pair] += count_guard_hits(call.content, batch)
                parsed = parse_judge_response(call.content, batch)
                if parsed is None:
                    verdicts[pair].update({e.id: None for e in batch})
                else:
                    verdicts[pair].update(parsed)
    finally:
        done = [p for p in pairs if p in verdicts]
        reference = verdicts.get(YARDSTICK, {})
        rows: list[list[str]] = []
        for entry in entries:
            row = [str(entry.id), entry.lemma_1, " | ".join(entry.parts)]
            for pair in done:
                drop = verdicts[pair].get(entry.id)
                row.append("FAILED" if drop is None else str(sorted(drop)))
            rows.append(row)
        write_tsv(
            out_dir / "bench_judge.tsv",
            ["id", "lemma", "variants", *[f"{p[0]}:{p[1]}" for p in done]],
            rows,
        )
    lines: list[str] = []
    for pair in pairs:
        trimmed = sum(1 for d in verdicts[pair].values() if d)
        agreement = judge_agreement(verdicts[pair], reference)
        extra = (
            f"trimmed {trimmed}/{len(entries)} | agreement with pro {agreement:.0%} | "
            f"guard hits {guard[pair]}"
        )
        lines.append(
            summary_line("judge", pair, stats[pair], prices.get(pair[1]), extra)
        )
    return lines


def run_generate(
    runner: Runner,
    sample: list[tuple[DpdHeadword, str]],
    pairs: list[tuple[str, str]],
    prices: dict[str, tuple[float, float]],
    out_dir: Path,
) -> list[str]:
    """Generate ru_meaning drafts with every pair; written beside the human value."""
    messages = [
        create_translation_prompt(headword, "meaning", "ru")["body"]["messages"]
        for headword, _ in sample
    ]
    outputs: dict[tuple[str, str], list[str]] = {}
    all_stats: dict[tuple[str, str], ModelStats] = {}
    try:
        for pair in pairs:
            all_stats[pair] = ModelStats()
            outputs[pair] = []
            for n, ((headword, _), message) in enumerate(zip(sample, messages), 1):
                call = runner.call(
                    "generate",
                    pair,
                    str(headword.id),
                    message[1]["content"],
                    message[0]["content"],
                    f"{n}/{len(sample)}",
                )
                all_stats[pair].calls.append(call)
                outputs[pair].append((call.content or "FAILED").strip())
    finally:
        done = [p for p in pairs if p in outputs]
        rows = [
            [
                str(headword.id),
                headword.lemma_1,
                human,
                *[outputs[p][i] if i < len(outputs[p]) else "" for p in done],
            ]
            for i, (headword, human) in enumerate(sample)
        ]
        write_tsv(
            out_dir / "bench_generate.tsv",
            ["id", "lemma", "human_ru_meaning", *[f"{p[0]}:{p[1]}" for p in done]],
            rows,
        )
    return [
        summary_line("generate", pair, all_stats[pair], prices.get(pair[1]), "")
        for pair in pairs
    ]


def run_check(
    runner: Runner,
    processor: BatchProcessor,
    sample: list[tuple[int, str, str, bool]],
    pairs: list[tuple[str, str]],
    prices: dict[str, tuple[float, float]],
    out_dir: Path,
) -> list[str]:
    """Run the checker prompt over true and shuffled pairs; accuracy against ground truth."""
    prompts = [check_prompt_and_parser(processor, i, e, r) for i, e, r, _ in sample]
    truth = [item[3] for item in sample]
    verdicts: dict[tuple[str, str], list[str | None]] = {}
    all_stats: dict[tuple[str, str], ModelStats] = {}
    try:
        for pair in pairs:
            all_stats[pair] = ModelStats()
            verdicts[pair] = []
            for n, ((prompt, parse), item) in enumerate(zip(prompts, sample), 1):
                call = runner.call(
                    "check",
                    pair,
                    f"{item[0]}:{item[3]}",
                    prompt,
                    None,
                    f"{n}/{len(sample)}",
                )
                all_stats[pair].calls.append(call)
                verdicts[pair].append(parse(call.content) if call.content else None)
    finally:
        done = [p for p in pairs if p in verdicts]
        rows = [
            [
                str(i),
                e,
                r,
                str(t),
                *[str(verdicts[p][n]) if n < len(verdicts[p]) else "" for p in done],
            ]
            for n, (i, e, r, t) in enumerate(sample)
        ]
        write_tsv(
            out_dir / "bench_check.tsv",
            ["id", "english", "russian", "is_true", *[f"{p[0]}:{p[1]}" for p in done]],
            rows,
        )
    return [
        summary_line(
            "check",
            pair,
            all_stats[pair],
            prices.get(pair[1]),
            f"accuracy {score_check(verdicts[pair], truth) if len(verdicts[pair]) == len(truth) else float('nan'):.0%}",
        )
        for pair in pairs
    ]


def build_parser() -> argparse.ArgumentParser:
    """CLI: roles, candidates, prices, peak override."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--roles", default=",".join(ROLES), help="comma list of judge,generate,check"
    )
    parser.add_argument(
        "--candidates",
        nargs="+",
        default=[],
        metavar="PROVIDER:MODEL",
        help="models to benchmark in addition to the default_models[0] reference",
    )
    parser.add_argument(
        "--price",
        nargs="+",
        default=[],
        metavar="MODEL=IN,OUT",
        help="USD per 1M tokens, for the cost estimate",
    )
    parser.add_argument(
        "--allow-peak", action="store_true", help="run in DeepSeek peak hours"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=REQUEST_TIMEOUT_SECONDS,
        help="seconds before one request is abandoned (default: 60)",
    )
    parser.add_argument(
        "--max-failures",
        type=int,
        default=MAX_CONSECUTIVE_FAILURES,
        help="consecutive failures after which a model is skipped for the rest of a role",
    )
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    return parser


def main() -> None:
    """Run the selected roles for the yardstick, the default chain head and candidates."""
    parser = build_parser()
    args = parser.parse_args()
    roles = [r for r in args.roles.split(",") if r]
    unknown = [r for r in roles if r not in ROLES]
    if unknown:
        parser.error(f"unknown roles: {unknown}")
    try:
        candidates = [parse_candidate(c) for c in args.candidates]
        prices = dict(parse_price(p) for p in args.price)
    except ValueError as exc:
        parser.error(str(exc))
    require_offpeak(args.allow_peak)

    processor = BatchProcessor(strict_parse=True)
    ai_manager = processor.ai_manager
    # Benchmark-only per-request timeout, set on this instance (the shared 150 s default is untouched).
    ai_manager.__dict__["_get_model_timeout"] = lambda provider, model: args.timeout
    head = ai_manager.DEFAULT_MODELS[0]
    flash = (head[0], head[1])
    pairs = list(dict.fromkeys([YARDSTICK, flash, *candidates]))
    pr.green(f"Benchmark models: {[f'{p}:{m}' for p, m in pairs]}")
    pr.white(
        f"timeout {args.timeout:.0f}s per request, skip a model after "
        f"{args.max_failures} consecutive failures; calls saved to {args.out_dir / CALLS_FILE}"
    )

    runner = Runner(ai_manager, CallStore(args.out_dir / CALLS_FILE), args.max_failures)
    session = get_db_session(ProjectPaths().dpd_db_path)
    summary: list[str] = []

    def save_summary() -> None:
        (args.out_dir / "bench_summary.txt").write_text(
            "\n".join(summary) + "\n", encoding="utf-8"
        )

    if "judge" in roles:
        summary += run_judge(runner, judge_sample(session), pairs, prices, args.out_dir)
        save_summary()
    if "generate" in roles:
        summary += run_generate(
            runner, generate_sample(session), pairs, prices, args.out_dir
        )
        save_summary()
    if "check" in roles:
        summary += run_check(
            runner, processor, check_sample(session), pairs, prices, args.out_dir
        )
        save_summary()
    session.close()
    for line in summary:
        pr.white(line)


if __name__ == "__main__":
    main()
