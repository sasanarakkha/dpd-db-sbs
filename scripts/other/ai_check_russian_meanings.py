#!/usr/bin/env python3
"""Analyze Russian translations against English meanings using AI to find mismatches."""

from tools.ai_meaning_checker import RussianMeaningChecker
import argparse
import sys

from tools.paths import ProjectPaths
from db.db_helpers import get_db_session
from tools.printer import printer as pr

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def main():
    pr.tic()
    parser = argparse.ArgumentParser(
        description="Check Russian meaning mismatches using AI"
    )
    parser.add_argument(
        "--mode",
        choices=[
            "meaning",
            "meaning_raw",
            "meaning_ru_raw",
            "meaning_raw_list",
            "meaning_lit",
            "meaning_lit_list",
            "notes",
            "notes_raw",
        ],
        default="meaning",
        help="Checking mode: meaning (default), meaning_raw, meaning_ru_raw, meaning_raw_list, meaning_lit, meaning_lit_list, notes, or notes_raw",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Use batch processing (default: individual)",
    )
    parser.add_argument(
        "--individual",
        action="store_true",
        help="Use individual processing (the default; flag kept for compatibility)",
    )
    parser.add_argument(
        "--limit", type=int, help="Limit number of words to analyze (for testing)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output report filename (auto-generated if not specified)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the checked-IDs snapshot for the given mode and exit",
    )
    parser.add_argument(
        "--no-auto-invalidate",
        action="store_true",
        help="Skip invalidation of checked IDs whose English content changed",
    )

    args = parser.parse_args()

    # Determine processing mode (default: individual; batch is opt-in)
    use_batch = args.batch and not args.individual

    # Create checker with specified mode
    checker = RussianMeaningChecker(mode=args.mode)

    if args.reset:
        checker.checked_ids_file.unlink(missing_ok=True)
        pr.yes(f"checked-IDs snapshot reset for mode '{args.mode}'")
        pr.toc()
        return

    if not args.no_auto_invalidate:
        n_invalidated, n_seeded = checker.apply_invalidation(db_session)
        pr.white(
            f"Invalidated {n_invalidated} IDs (English changed), "
            f"seeded {n_seeded} baseline hashes"
        )

    total_count = checker.get_total_count_with_session(db_session)

    pr.yellow_title(f"RUSSIAN {args.mode.upper()} MISMATCH ANALYSIS")
    pr.white(f"Checking mode: {args.mode}")
    pr.white(f"Processing mode: {'Batch' if use_batch else 'Individual'}")
    pr.white(f"Total words which need check: {total_count}")
    if args.limit:
        pr.white(f"Limit: {args.limit} words")

    try:
        # Run the analysis
        pr.green_tmr("running analysis")
        checker.run_analysis(
            db_session=db_session,
            use_batch=use_batch,
            limit=args.limit,
            auto_invalidate=False,
        )
        pr.yes("ok")

        pr.green_title("ANALYSIS COMPLETE!")

        # Display appropriate message based on mode
        if args.mode == "meaning_raw":
            pr.white(
                "Note: For meaning_raw mode, mismatched entries had their meaning_raw cleared."
            )
        elif args.mode == "meaning_ru_raw":
            pr.white(
                "Note: For meaning_ru_raw mode, checking only Russian grammar without clearing meanings."
            )
        elif args.mode == "meaning_raw_list":
            pr.white(
                "Note: For meaning_raw_list mode, processing only IDs from ai_processed_ids_json file."
            )
        elif args.mode == "meaning_lit":
            pr.white(
                "Note: For meaning_lit mode, checking literal meanings against English meanings."
            )
        elif args.mode == "meaning_lit_list":
            pr.white(
                "Note: For meaning_lit_list mode, processing only IDs from ai_processed_ids_json file for literal meanings."
            )
        elif args.mode == "notes":
            pr.white(
                "Note: For notes mode, checking English notes vs Russian notes (excluding AI translations)."
            )
        elif args.mode == "notes_raw":
            pr.white(
                "Note: For notes_raw mode, mismatched entries had their ru_notes cleared."
            )

    except KeyboardInterrupt:
        pr.red("\nAnalysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        pr.red(f"\nError during analysis: {e}")
        sys.exit(1)

    pr.toc()


if __name__ == "__main__":
    main()
