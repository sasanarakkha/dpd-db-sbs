#!/usr/bin/env python3
"""
Russian Meaning Mismatch Checker - Usage Script

This script provides easy access to the RussianMeaningChecker tool.
You can run this to analyze Russian translations against English meanings.
"""

from tools.russian_meaning_checker import RussianMeaningChecker
import argparse
import sys

from tools.paths import ProjectPaths
from db.db_helpers import get_db_session 

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def main():
    parser = argparse.ArgumentParser(description='Check Russian meaning mismatches using AI')
    parser.add_argument('--batch', action='store_true', help='Use batch processing (default: True)')
    parser.add_argument('--individual', action='store_true', help='Use individual processing (slower but more precise)')
    parser.add_argument('--limit', type=int, help='Limit number of words to analyze (for testing)')
    parser.add_argument('--output', type=str, default='temp/ai_meaning_check/mismatches.txt', help='Output report filename')
    
    args = parser.parse_args()
    
    # Determine processing mode
    use_batch = True
    if args.individual:
        use_batch = False
    elif args.batch:
        use_batch = True
    
    # Create checker and run analysis
    checker = RussianMeaningChecker()

    total_count = checker.get_total_count_with_session(db_session)
    
    print("="*60)
    print("RUSSIAN MEANING MISMATCH ANALYSIS")
    print("="*60)
    print(f"Processing mode: {'Batch' if use_batch else 'Individual'}")
    print(f"Total words which need check: {total_count}")
    if args.limit:
        print(f"Limit: {args.limit} words")
    print("="*60)
    
    try:
        # Run the analysis
        checker.run_analysis(
            db_session=db_session,
            use_batch=use_batch,
            limit=args.limit
        )
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE!")
        print("="*60)
        print(f"Check the report file: {args.output}")
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()