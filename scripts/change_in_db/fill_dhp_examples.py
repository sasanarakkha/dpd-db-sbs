"""Fills SBS.dhp_example from AI verse analysis, bolding the matched word form."""

import argparse
import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import SBS
from exporter.analysis.example_bolding import (
    _apply_apos_fallback,
    bold_word_in_verse,
    collect_all_ids,
    find_token_in_apos_verse,
)
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.speech_marks import SpeechMarkManager


def natural_sort_key(source: str) -> list[str]:
    """Return a natural-sort key for DHP source labels."""
    return [
        text.zfill(12) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", source)
    ]


def should_overwrite_existing(
    current_source: str | None,
    new_source: str,
    *,
    force: bool,
    prefer_earlier: bool,
) -> bool:
    """Decide whether an existing DHP example should be overwritten."""
    if force:
        return True
    if not prefer_earlier or not current_source:
        return False
    return natural_sort_key(new_source) < natural_sort_key(current_source)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fill SBS.dhp_example from AI analysis."
    )
    parser.add_argument("--book", required=True, help="CST book code (e.g., kn2)")
    parser.add_argument("--verse", help="Process a specific verse only (e.g., DHP1)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show proposed changes without committing",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Process even if dhp_example already exists",
    )
    parser.add_argument(
        "--prefer-earlier",
        action="store_true",
        help="Overwrite if current verse is earlier than existing one (e.g. DHP1 > DHP10)",
    )
    parser.add_argument("--limit", type=int, help="Limit number of verses to process")
    args = parser.parse_args()

    book = args.book
    analysis_path = Path("exporter/analysis/output") / f"{book}_analysis.json"

    if not analysis_path.exists():
        pr.no(f"Analysis file not found: {analysis_path}")
        return

    with open(analysis_path, encoding="utf-8") as f:
        all_analysis: list[dict[str, Any]] = json.load(f)

    if args.verse:
        analysis_results = [v for v in all_analysis if v["num"] == args.verse]
        if not analysis_results:
            pr.no(f"Verse '{args.verse}' not found in {analysis_path}")
            return
    else:
        analysis_results = all_analysis

    # Sort results to ensure natural ordering (e.g., DHP1, DHP2... DHP10)
    analysis_results.sort(key=lambda x: natural_sort_key(x["num"]))

    if args.limit:
        analysis_results = analysis_results[: args.limit]

    paths = ProjectPaths()
    db_session: Session = get_db_session(paths.dpd_db_path)
    speech_marks_manager = SpeechMarkManager(paths)

    try:
        sbs_map: dict[int, SBS] = {sbs.id: sbs for sbs in db_session.query(SBS).all()}

        filled_count = 0
        skipped_count = 0

        for verse in analysis_results:
            dhp_source: str = verse["num"]
            dhp_sutta: str = verse["vagga"]

            # Use verse_text from analysis JSON (set by ai_batch_translate, has apostrophes);
            # fall back to applying speech_marks to the raw CST text for older analysis entries.
            verse_text: str = verse.get("verse_text") or _apply_apos_fallback(
                verse["text"], speech_marks_manager
            )

            pr.green(f"Processing {dhp_source}...")

            updated_in_verse: set[int] = set()

            for token_data in verse.get("analysis", []):
                word = token_data.get("word", "")
                options: list[dict[str, Any]] = token_data.get("data", [])
                if not options:
                    continue

                best_option = max(options, key=lambda x: int(x.get("ai_score") or 0))
                all_entries = collect_all_ids(best_option, word)

                # Locate this token's apostrophe form in the verse text
                apos_word = find_token_in_apos_verse(word, verse_text)

                for (
                    headword_id,
                    component_pali,
                    _word_in_verse,
                    is_first_component,
                    is_top_level,
                ) in all_entries:
                    if headword_id in updated_in_verse:
                        skipped_count += 1
                        continue

                    updated_in_verse.add(headword_id)

                    sbs = sbs_map.get(headword_id)
                    exists = sbs and sbs.dhp_example and sbs.dhp_example.strip()
                    if exists and not should_overwrite_existing(
                        sbs.dhp_source if sbs else None,
                        dhp_source,
                        force=args.force,
                        prefer_earlier=args.prefer_earlier,
                    ):
                        skipped_count += 1
                        continue

                    example = bold_word_in_verse(
                        verse_text,
                        apos_word,
                        component_pali,
                        headword_id,
                        db_session,
                        is_first_component,
                        is_top_level,
                    )

                    if args.dry_run:
                        label = "[DRY-RUN]"
                        if exists:
                            label = "[DRY-RUN OVERWRITING]"
                        pr.yes(f"  {label} ID {headword_id} '{component_pali}':")
                        pr.yes(f"    Source: {dhp_source}")
                        pr.yes(f"    Sutta:  {dhp_sutta}")
                        pr.yes("    Example:")
                        for line in example.splitlines():
                            pr.yes(f"      {line}")
                    else:
                        if not sbs:
                            sbs = SBS(id=headword_id)
                            db_session.add(sbs)
                            sbs_map[headword_id] = sbs

                        sbs.dhp_source = dhp_source
                        sbs.dhp_sutta = dhp_sutta
                        sbs.dhp_example = example
                        filled_count += 1

            if not args.dry_run:
                db_session.commit()

        pr.yes(f"Finished. Filled: {filled_count}, Skipped: {skipped_count}")

    except SQLAlchemyError as e:
        pr.no(f"An error occurred: {e}")
        db_session.rollback()
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
