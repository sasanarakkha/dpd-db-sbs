"""Generate SBS examples that can be replaced by matching DPD examples."""

import argparse
import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, SBS
from scripts.change_in_db.rearrange_sbs_gatha_lines import (
    EXAMPLE_SOURCE_FIELDS,
    line_count,
    tsv_cell,
)
from tools.paths import ProjectPaths
from tools.printer import printer as pr


DPD_EXAMPLE_SOURCE_FIELDS: tuple[tuple[str, str], ...] = (
    ("example_1", "source_1"),
    ("example_2", "source_2"),
)
TRANSFER_PATH = Path("temp/sbs_dpd_example_transfers.tsv")
TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class TransferCandidate:
    """One SBS field that can be copied from a matching DPD example."""

    entry_id: int
    sbs_field: str
    sbs_source: str
    dpd_field: str
    dpd_source: str
    sbs_lines: int
    dpd_lines: int
    sbs_example: str
    dpd_example: str


def normalize_source(source: str) -> str:
    """Normalize source text for conservative equality matching."""
    return source.strip()


def normalize_example_for_match(text: str) -> str:
    """Normalize example text by keeping only letters and numbers."""
    text_without_tags = TAG_RE.sub("", text).casefold()
    return "".join(
        char
        for char in text_without_tags
        if unicodedata.category(char)[0] in {"L", "N"}
    )


def collect_transfer_candidates_for_row(
    dpd_headword: Any,
    sbs: Any,
) -> list[TransferCandidate]:
    """Find DPD-to-SBS transfer candidates for one same-id row pair."""
    candidates: list[TransferCandidate] = []
    for sbs_field, sbs_source_field in EXAMPLE_SOURCE_FIELDS:
        sbs_example = str(getattr(sbs, sbs_field) or "")
        sbs_source = str(getattr(sbs, sbs_source_field) or "")
        if not sbs_example or not sbs_source:
            continue

        normalized_sbs_source = normalize_source(sbs_source)
        normalized_sbs_example = normalize_example_for_match(sbs_example)
        if not normalized_sbs_example:
            continue

        for dpd_field, dpd_source_field in DPD_EXAMPLE_SOURCE_FIELDS:
            dpd_example = str(getattr(dpd_headword, dpd_field) or "")
            dpd_source = str(getattr(dpd_headword, dpd_source_field) or "")
            if not dpd_example or not dpd_source:
                continue
            if normalize_source(dpd_source) != normalized_sbs_source:
                continue
            if normalize_example_for_match(dpd_example) != normalized_sbs_example:
                continue
            if dpd_example == sbs_example:
                continue

            candidates.append(
                TransferCandidate(
                    entry_id=int(getattr(sbs, "id")),
                    sbs_field=sbs_field,
                    sbs_source=sbs_source,
                    dpd_field=dpd_field,
                    dpd_source=dpd_source,
                    sbs_lines=line_count(sbs_example),
                    dpd_lines=line_count(dpd_example),
                    sbs_example=sbs_example,
                    dpd_example=dpd_example,
                )
            )
    return candidates


def collect_transfer_candidates(db_session: Session) -> list[TransferCandidate]:
    """Find all same-id DPD-to-SBS transfer candidates."""
    candidates: list[TransferCandidate] = []
    rows = (
        db_session.query(DpdHeadword, SBS)
        .join(SBS, SBS.id == DpdHeadword.id)
        .order_by(DpdHeadword.id)
        .all()
    )
    for dpd_headword, sbs in rows:
        candidates.extend(collect_transfer_candidates_for_row(dpd_headword, sbs))
    return candidates


def write_transfer_tsv(
    candidates: list[TransferCandidate],
    output_path: Path,
) -> None:
    """Write DPD-to-SBS transfer candidates to TSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(
            [
                "id",
                "sbs_field",
                "sbs_source",
                "dpd_field",
                "dpd_source",
                "sbs_lines",
                "dpd_lines",
                "sbs_example",
                "dpd_example",
            ]
        )
        for candidate in candidates:
            writer.writerow(
                [
                    candidate.entry_id,
                    candidate.sbs_field,
                    candidate.sbs_source,
                    candidate.dpd_field,
                    candidate.dpd_source,
                    candidate.sbs_lines,
                    candidate.dpd_lines,
                    tsv_cell(candidate.sbs_example),
                    tsv_cell(candidate.dpd_example),
                ]
            )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate SBS examples that can be replaced by matching DPD examples."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=TRANSFER_PATH,
        help="Path for the dry-run transfer TSV.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the dry-run DPD-to-SBS transfer generator."""
    args = parse_args()

    pr.green_title("Generate SBS DPD example transfers")
    pr.summary("db writes", "disabled")
    pr.bip()

    paths = ProjectPaths()
    db_session = get_db_session(paths.dpd_db_path)
    try:
        candidates = collect_transfer_candidates(db_session)
        write_transfer_tsv(candidates, args.output)
        pr.summary("transfer candidates", len(candidates))
        pr.summary("output path", str(args.output))
        db_session.rollback()
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
