"""Normalize SBS gāthā examples into one pāda per line."""

import argparse
import csv
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import SBS
from tools.paths import ProjectPaths
from tools.printer import printer as pr


EXAMPLE_SOURCE_FIELDS: tuple[tuple[str, str], ...] = (
    ("sbs_example_1", "sbs_source_1"),
    ("sbs_example_2", "sbs_source_2"),
    ("dhp_example", "dhp_source"),
    ("pat_example", "pat_source"),
    ("vib_example", "vib_source"),
    ("class_example", "class_source"),
    ("discourses_example", "discourses_source"),
    ("extra_example", "extra_source"),
)
REVIEW_PATH = Path("temp/sbs_gatha_review.tsv")
CONCERN_PATH = Path("temp/sbs_gatha_concerns.tsv")
EXPECTED_LINE_COUNTS = {4, 6}
SHORT_PHRASE_MAX_CHARS = 10
SHORT_PHRASE_MAX_TOKENS = 2
PERIOD_BOUNDARY_RE = re.compile(r"\. +(?=\S)")
TAG_RE = re.compile(r"<[^>]+>")
WORD_EDGE_RE = re.compile(r"^[^\w]+|[^\w]+$")
# Compiled from distinct SBS source values: TH/THI are this DB's
# Theragāthā/Therīgāthā abbreviations. Commentaries and local chants are excluded.
VERSE_SOURCE_PREFIXES: tuple[str, ...] = (
    "DHP",
    "SNP",
    "TH",
    "THI",
    "THAG",
    "THIG",
    "VV",
    "PV",
    "APA",
    "BV",
)


@dataclass(frozen=True)
class ReviewRow:
    """One unusual line-count result for human review."""

    entry_id: int
    field: str
    source: str
    before: str
    after: str


@dataclass(frozen=True)
class ConcernRow:
    """One high-risk transform result for focused review."""

    entry_id: int
    field: str
    source: str
    before_lines: int
    after_lines: int
    line_number: int
    line: str
    before: str
    after: str


@dataclass
class MigrationSummary:
    """Counters and review rows from one migration run."""

    rows_seen: int = 0
    rows_changed: int = 0
    targeted_by_field: Counter[str] = field(default_factory=Counter)
    changed_by_field: Counter[str] = field(default_factory=Counter)
    review_rows: list[ReviewRow] = field(default_factory=list)
    concern_rows: list[ConcernRow] = field(default_factory=list)


def split_gatha_lines(text: str) -> str:
    """Split pādas without joining existing lines."""
    if not text:
        return ""

    lines: list[str] = []
    for existing_line in text.split("\n"):
        existing_line = existing_line.rstrip()
        for period_part in PERIOD_BOUNDARY_RE.sub(".\n", existing_line).split("\n"):
            lines.extend(split_comma_boundaries(period_part))
    return "\n".join(merge_short_one_word_lines(lines))


def split_comma_boundaries(text: str) -> list[str]:
    """Split comma-space boundaries."""
    parts = text.split(", ")
    if len(parts) == 1:
        return [text]
    return [f"{part}," for part in parts[:-1]] + [parts[-1]]


def merge_short_one_word_lines(lines: list[str]) -> list[str]:
    """Merge short phrase lines when comma splitting overproduces lines."""
    merged = list(lines)
    while len(merged) > 4:
        short_line_index = next(
            (index for index, line in enumerate(merged) if is_short_phrase(line)),
            None,
        )
        if short_line_index is None:
            break

        if short_line_index + 1 < len(merged):
            merged[short_line_index] = (
                f"{merged[short_line_index]} {merged[short_line_index + 1]}"
            )
            del merged[short_line_index + 1]
        elif short_line_index > 0:
            merged[short_line_index - 1] = (
                f"{merged[short_line_index - 1]} {merged[short_line_index]}"
            )
            del merged[short_line_index]
        else:
            break
    return merged


def is_short_phrase(text: str) -> bool:
    """Return whether text is a short phrase after markup is stripped."""
    plain = TAG_RE.sub("", text)
    words = [WORD_EDGE_RE.sub("", word) for word in plain.split()]
    words = [word for word in words if word]
    if not words or len(words) > SHORT_PHRASE_MAX_TOKENS:
        return False
    normalized = "".join(words).replace("'", "").replace("’", "")
    return len(normalized) <= SHORT_PHRASE_MAX_CHARS


def is_verse_source(source: str) -> bool:
    """Return whether an SBS source belongs to a verse-only text."""
    source_upper = source.strip().upper()
    if not source_upper:
        return False

    match = re.match(r"^([A-Z]+)", source_upper)
    if match is None:
        return False

    return match.group(1) in VERSE_SOURCE_PREFIXES


def line_count(text: str) -> int:
    """Return the number of rendered lines in non-empty text."""
    if not text:
        return 0
    return len(text.splitlines())


def tsv_cell(text: str) -> str:
    """Serialize text for one physical TSV row."""
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")


def write_review_tsv(rows: list[ReviewRow], review_path: Path) -> None:
    """Write unusual line-count results to a TSV review file."""
    review_path.parent.mkdir(parents=True, exist_ok=True)
    with review_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["id", "field", "source", "before", "after"])
        for row in rows:
            writer.writerow(
                [
                    row.entry_id,
                    row.field,
                    row.source,
                    tsv_cell(row.before),
                    tsv_cell(row.after),
                ]
            )


def collect_concern_rows(
    *,
    entry_id: int,
    field_name: str,
    source: str,
    before: str,
    after: str,
) -> list[ConcernRow]:
    """Return focused concern rows for short phrase over-splits."""
    before_lines = line_count(before)
    after_lines = line_count(after)
    if after_lines <= 4:
        return []

    concern_rows: list[ConcernRow] = []
    for line_number, line in enumerate(after.splitlines(), start=1):
        if is_short_phrase(line):
            concern_rows.append(
                ConcernRow(
                    entry_id=entry_id,
                    field=field_name,
                    source=source,
                    before_lines=before_lines,
                    after_lines=after_lines,
                    line_number=line_number,
                    line=line,
                    before=before,
                    after=after,
                )
            )
    return concern_rows


def write_concern_tsv(rows: list[ConcernRow], concern_path: Path) -> None:
    """Write focused high-risk results to a TSV review file."""
    concern_path.parent.mkdir(parents=True, exist_ok=True)
    with concern_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(
            [
                "id",
                "field",
                "source",
                "before_lines",
                "after_lines",
                "line_number",
                "line",
                "before",
                "after",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.entry_id,
                    row.field,
                    row.source,
                    row.before_lines,
                    row.after_lines,
                    row.line_number,
                    tsv_cell(row.line),
                    tsv_cell(row.before),
                    tsv_cell(row.after),
                ]
            )


def migrate_sbs_gatha_lines(
    db_session: Session,
    *,
    apply_changes: bool,
    review_path: Path = REVIEW_PATH,
    concern_path: Path = CONCERN_PATH,
) -> MigrationSummary:
    """Calculate or apply SBS gāthā line normalization."""
    summary = MigrationSummary()
    changed_entry_ids: set[int] = set()
    sbs_rows = db_session.query(SBS).order_by(SBS.id).all()
    summary.rows_seen = len(sbs_rows)

    for sbs in sbs_rows:
        for example_field, source_field in EXAMPLE_SOURCE_FIELDS:
            before = str(getattr(sbs, example_field) or "")
            source = str(getattr(sbs, source_field) or "")
            if not before:
                continue
            if "\n" not in before and not is_verse_source(source):
                continue

            summary.targeted_by_field[example_field] += 1
            after = split_gatha_lines(before)
            if line_count(after) not in EXPECTED_LINE_COUNTS:
                summary.review_rows.append(
                    ReviewRow(
                        entry_id=sbs.id,
                        field=example_field,
                        source=source,
                        before=before,
                        after=after,
                    )
                )
            if after == before:
                continue

            summary.changed_by_field[example_field] += 1
            changed_entry_ids.add(sbs.id)
            summary.concern_rows.extend(
                collect_concern_rows(
                    entry_id=sbs.id,
                    field_name=example_field,
                    source=source,
                    before=before,
                    after=after,
                )
            )
            if apply_changes:
                setattr(sbs, example_field, after)

    summary.rows_changed = len(changed_entry_ids)
    write_review_tsv(summary.review_rows, review_path)
    write_concern_tsv(summary.concern_rows, concern_path)
    if apply_changes:
        db_session.commit()
    else:
        db_session.rollback()
    return summary


def print_summary(
    summary: MigrationSummary,
    *,
    apply_changes: bool,
    review_path: Path,
    concern_path: Path,
) -> None:
    """Print migration counters with the project printer."""
    pr.summary("mode", "apply" if apply_changes else "dry-run")
    pr.summary("rows seen", summary.rows_seen)
    pr.summary("rows changed", summary.rows_changed)
    for example_field, _source_field in EXAMPLE_SOURCE_FIELDS:
        targets = summary.targeted_by_field[example_field]
        changes = summary.changed_by_field[example_field]
        pr.summary(f"{example_field} targets", targets)
        pr.summary(f"{example_field} changes", changes)
    pr.summary("review rows", len(summary.review_rows))
    pr.summary("review path", str(review_path))
    pr.summary("concern rows", len(summary.concern_rows))
    pr.summary("concern path", str(concern_path))


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Normalize SBS gāthā examples into one pāda per line."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate changes and write review TSV without DB writes (default).",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Write normalized examples to the DB and commit.",
    )
    parser.add_argument(
        "--review-path",
        type=Path,
        default=REVIEW_PATH,
        help="Path for the unusual line-count TSV.",
    )
    parser.add_argument(
        "--concern-path",
        type=Path,
        default=CONCERN_PATH,
        help="Path for the focused high-risk TSV.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the SBS gāthā normalization script."""
    args = parse_args()
    apply_changes = bool(args.apply)

    pr.green_title("Rearrange SBS gāthā lines")
    pr.summary("db writes", "enabled" if apply_changes else "disabled")
    pr.summary("verse prefixes", ", ".join(VERSE_SOURCE_PREFIXES))
    pr.bip()

    paths = ProjectPaths()
    db_session = get_db_session(paths.dpd_db_path)
    try:
        summary = migrate_sbs_gatha_lines(
            db_session,
            apply_changes=apply_changes,
            review_path=cast(Path, args.review_path),
            concern_path=cast(Path, args.concern_path),
        )
        print_summary(
            summary,
            apply_changes=apply_changes,
            review_path=cast(Path, args.review_path),
            concern_path=cast(Path, args.concern_path),
        )
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
