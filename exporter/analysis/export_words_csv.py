"""Interactive Stage 2: read an edited study report markdown and write a vocabulary CSV for Anki."""

import csv
import re

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from exporter.analysis.column_options import CUSTOM, PRESETS, REGISTRY
from exporter.analysis.example_bolding import (
    bold_word_in_verse,
    find_token_in_apos_verse,
)
from exporter.analysis.paths import ensure_analysis_dirs
from exporter.analysis.passage_by_code import get_passage_by_code
from tools.paths import ProjectPaths
from tools.printer import printer as pr


_ANALYSIS_DIRS = ensure_analysis_dirs()
_REPORTS_DIR = _ANALYSIS_DIRS.reports_dir
_OUTPUT_DIR = _ANALYSIS_DIRS.output_dir


def _normalize_export_source(source: str) -> str:
    """Return the base source code without Stage 1 passage-selection suffixes."""
    base = re.sub(r"_[vp]\d+(?:-\d+)*$", "", source)
    if base == source:
        return source
    try:
        get_passage_by_code(base)
    except ValueError:
        return source
    return base


def _parse_report(content: str) -> tuple[str, list[tuple[int, str, str]]]:
    """Extract passage plus (id, surface_word, parent_token) report rows."""
    passage = ""
    if "### English Translation" in content:
        header_part = content.split("### English Translation")[0]
        passage_lines = [
            line for line in header_part.splitlines() if not line.startswith("#")
        ]
        passage = "\n".join(passage_lines).strip()

    rows: list[tuple[int, str, str]] = []
    current_parent = ""
    if "### Word-by-Word Analysis" in content:
        table_part = content.split("### Word-by-Word Analysis")[1]
        for line in table_part.splitlines():
            if not line.startswith("| "):
                continue
            cells = line.split("|")
            if len(cells) < 3:
                continue
            raw_id = cells[1].strip()
            raw_word = cells[2].strip()
            if raw_id.isdigit():
                is_component = raw_word.startswith("-")
                surface = raw_word.lstrip("- ").strip()
                if not is_component:
                    current_parent = surface
                parent_token = current_parent or surface
                rows.append((int(raw_id), surface, parent_token))

    return passage, rows


def _build_example(
    passage: str,
    surface: str,
    parent_token: str,
    hw_id: int,
    db_session: Session,
) -> str:
    """Return the passage with a top-level row or compound component bolded."""
    is_top_level = parent_token == surface
    token = surface if is_top_level else parent_token
    apos = find_token_in_apos_verse(token, passage)
    return bold_word_in_verse(
        passage,
        apos,
        surface,
        hw_id,
        db_session,
        is_top_level=is_top_level,
    )


def _get_vagga(source: str) -> str:
    """Return the vagga/sutta name for a sutta code (e.g. DHP1), or '' for file sources."""
    try:
        return get_passage_by_code(_normalize_export_source(source)).vagga
    except ValueError:
        return ""


def _prompt_profile() -> list[str]:
    """Prompt the user to select basic / advanced / custom and return the column list."""
    pr.green("Column profiles:")
    pr.green(
        "  basic    — id, lemma_1, grammar, meaning_combo, source, sutta, example (7 cols)"
    )
    pr.green(
        f"  advanced — full DHP deck columns minus audio/feedback/marks/native/test/link ({len(PRESETS['advanced'])} cols)"
    )
    pr.green("  custom   — edit CUSTOM list in exporter/analysis/column_options.py")
    choice = input("Profile [basic/advanced/custom]: ").strip().lower()
    if choice == "advanced":
        return PRESETS["advanced"]
    if choice == "custom":
        return CUSTOM
    return PRESETS["basic"]


def main() -> None:
    paths = ProjectPaths()
    if not paths.dpd_db_path.exists():
        pr.red(f"Database not found: {paths.dpd_db_path}")
        raise SystemExit(1)

    pr.green("=" * 50)
    pr.green("Pāḷi Word Exporter — Stage 2")
    pr.green("=" * 50)

    source = input(
        "\nEnter source (code or filename stem, e.g. DHP1, SN12.3_p2, my_text): "
    ).strip()
    if not source:
        pr.red("No source entered.")
        raise SystemExit(1)
    export_source = _normalize_export_source(source)

    report_path = _REPORTS_DIR / f"{source}_study.md"
    if not report_path.exists():
        pr.red(f"Report not found: {report_path}")
        raise SystemExit(1)

    columns = _prompt_profile()

    content = report_path.read_text(encoding="utf-8")
    passage, id_surface_pairs = _parse_report(content)

    if not passage:
        pr.red("Could not extract passage from report.")
        raise SystemExit(1)
    if not id_surface_pairs:
        pr.red("No valid (id, word) rows found in report table.")
        raise SystemExit(1)

    pr.cyan_tmr("Retrieving vagga")
    vagga = _get_vagga(source)
    pr.yes("ok")

    db_session = get_db_session(paths.dpd_db_path)

    output_path = _OUTPUT_DIR / f"{export_source}_words.csv"
    seen_ids: set[int] = set()
    skipped = 0
    written = 0

    pr.green_tmr("Building rows")
    try:
        with output_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=columns, delimiter="\t")
            writer.writeheader()

            for hw_id, surface, parent_token in id_surface_pairs:
                if hw_id in seen_ids:
                    skipped += 1
                    continue
                seen_ids.add(hw_id)

                hw = db_session.query(DpdHeadword).filter_by(id=hw_id).first()
                if hw is None:
                    pr.amber(f"ID {hw_id} not found in DB — skipping.")
                    skipped += 1
                    continue

                example = _build_example(
                    passage=passage,
                    surface=surface,
                    parent_token=parent_token,
                    hw_id=hw_id,
                    db_session=db_session,
                )

                row: dict[str, str] = {}
                for col in columns:
                    if col == "source":
                        row[col] = export_source
                    elif col == "sutta":
                        row[col] = vagga
                    elif col == "example":
                        row[col] = example
                    else:
                        extractor = REGISTRY.get(col)
                        row[col] = extractor(hw) if extractor else ""

                writer.writerow(row)
                written += 1
    finally:
        db_session.close()
    pr.yes(f"{written} rows")

    if skipped:
        pr.amber(f"{skipped} rows skipped (duplicates or missing IDs).")

    pr.green(f"\nSaved: {output_path}")
    pr.green("Import into Anki or your preferred flashcard tool.")


if __name__ == "__main__":
    main()
