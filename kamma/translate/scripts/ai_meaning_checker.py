"""
Russian Meaning Checker - Validates Russian translations against English meanings using AI.

This module provides the RussianMeaningChecker class for analyzing and validating
Russian translations in the DPD database. It supports multiple checking modes:
- meaning: Regular meanings (meaning_1 vs ru_meaning)
- meaning_raw: AI-generated raw meanings (meaning_1 vs ru_meaning_raw)
- meaning_lit: Literal meanings (meaning_lit vs ru_meaning_lit)
- notes: Notes translations (notes vs ru_notes)

The checker uses AI models to identify mismatches and generates detailed reports.
"""

import datetime
import json
from pathlib import Path

from sqlalchemy import and_
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from tools.ai_batch_processor import BatchProcessor, ComparisonResult, WordComparison
from tools.ai_related import replace_abbreviations
from tools.meaning_snapshot_ru import (
    compose_english_content,
    compute_field_hash,
    invalidate_changed,
    load_snapshot,
    save_snapshot,
)
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr


# Extension of WordComparison with additional functionality
def create_word_comparison(
    headword_id: int,
    lemma_1: str,
    english_meaning: str,
    russian_meaning: str,
    grammar: str,
    russian_meaning_alt: str | None = None,
) -> WordComparison:
    """Create a WordComparison with all required fields"""
    return WordComparison(
        headword_id=headword_id,
        lemma_1=lemma_1,
        english_meaning=english_meaning,
        russian_meaning=russian_meaning,
        russian_meaning_alt=russian_meaning_alt,
        grammar=grammar,
    )


def word_comparison_to_ai_prompt_text(comp: WordComparison) -> str:
    """Convert WordComparison to readable text for AI prompt"""
    return f"""ID: {comp.headword_id}
Lemma: {comp.lemma_1}
English: {comp.english_meaning}
Russian: {comp.russian_meaning}
Grammar: {comp.grammar}"""


class RussianMeaningChecker:
    """Checks if Russian meanings match English meanings using AI"""

    def __init__(
        self,
        db_path: str = "dpd.db",
        mode: str = "meaning",
        provider: str | None = None,
        model: str | None = None,
    ):
        self.db_path = db_path
        self.mode = mode
        self.provider = provider
        self.model = model
        self._batch_processor: BatchProcessor | None = None
        dpspth = DPSPaths()
        self.list_ids_file: Path | None = None

        # Use different checked IDs files for different modes
        if mode == "meaning_raw":
            self.checked_ids_file = dpspth.ai_meaning_raw_checked
            self.output_txt_folder = dpspth.ai_meaning_raw_report_dir
        elif mode == "russian_grammar_meaning_raw":
            self.checked_ids_file = dpspth.ai_russian_grammar_meaning_raw_checked
            self.output_txt_folder = dpspth.ai_russian_grammar_meaning_raw_report_dir
        elif mode == "meaning_raw_list":
            self.checked_ids_file = dpspth.ai_meaning_raw_checked
            self.output_txt_folder = dpspth.ai_meaning_raw_report_dir
            self.list_ids_file = dpspth.ai_processed_ids_json
        elif mode == "meaning_lit":
            self.checked_ids_file = dpspth.ai_meaning_lit_checked
            self.output_txt_folder = dpspth.ai_meaning_lit_report_dir
        elif mode == "meaning_lit_list":
            self.checked_ids_file = dpspth.ai_meaning_lit_checked
            self.output_txt_folder = dpspth.ai_meaning_lit_report_dir
            self.list_ids_file = dpspth.ai_processed_ids_json
        elif mode == "notes":
            self.checked_ids_file = dpspth.ai_notes_checked
            self.output_txt_folder = dpspth.ai_notes_report_dir
        elif mode == "notes_raw":
            self.checked_ids_file = dpspth.ai_notes_raw_checked
            self.output_txt_folder = dpspth.ai_notes_raw_report_dir
        else:
            self.checked_ids_file = dpspth.ai_meaning_checked
            self.output_txt_folder = dpspth.ai_meaning_report_dir

        self.snapshot: dict[int, str] = {}
        self.english_by_id: dict[int, str] = {}
        self.checked_ids = self.load_checked_ids()

    @property
    def batch_processor(self) -> BatchProcessor:
        """Lazy load BatchProcessor to avoid heavy AI initialization."""
        if self._batch_processor is None:
            self._batch_processor = BatchProcessor(
                provider=self.provider, model=self.model
            )
        return self._batch_processor

    def load_checked_ids(self) -> set[int]:
        """Load the snapshot (v2, auto-migrating v1) and return its IDs."""
        self.snapshot = load_snapshot(self.checked_ids_file)
        return set(self.snapshot.keys())

    def save_checked_ids(self) -> None:
        """Reconcile newly checked IDs into the snapshot and persist it."""
        try:
            for headword_id in self.checked_ids:
                if headword_id not in self.snapshot:
                    english = self.english_by_id.get(headword_id)
                    # "" = baseline-unknown sentinel; seeded from DB next run
                    self.snapshot[headword_id] = (
                        compute_field_hash(english) if english else ""
                    )
            save_snapshot(self.checked_ids_file, self.snapshot)
        except OSError as e:
            pr.amber(f"Could not save checked IDs: {e}")

    def apply_invalidation(self, db_session: Session) -> tuple[int, int]:
        """Drop snapshot entries whose English content changed in the DB.

        Returns (n_invalidated, n_seeded). Persists immediately so an
        interrupted run loses nothing (invalidated IDs simply re-check later).
        """
        n_invalidated, n_seeded = invalidate_changed(
            self.snapshot, db_session, self.mode
        )
        self.checked_ids = set(self.snapshot.keys())
        save_snapshot(self.checked_ids_file, self.snapshot)
        return n_invalidated, n_seeded

    def load_list_ids(self) -> set[int]:
        """Load IDs from the ai_processed_ids_json file for meaning_raw_list mode"""
        if self.list_ids_file is None or not self.list_ids_file.exists():
            return set()
        try:
            return set(json.loads(self.list_ids_file.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            return set()

    def get_words_for_comparison_with_session(
        self, db_session: Session
    ) -> list[WordComparison]:
        """Get all words that have both English and Russian meanings using provided session"""
        from db.models import DpdHeadword, Russian

        if self.mode == "meaning":
            # Original mode: check ru_meaning
            results = (
                db_session.query(DpdHeadword, Russian)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_1.isnot(None),
                        DpdHeadword.meaning_1 != "",
                        Russian.ru_meaning.isnot(None),
                        Russian.ru_meaning != "",
                        ~DpdHeadword.id.in_(
                            list(self.checked_ids)
                        ),  # Exclude already checked IDs
                    )
                )
                .all()
            )
            russian_field = "ru_meaning"

        elif self.mode == "meaning_raw" or self.mode == "russian_grammar_meaning_raw":
            # Raw modes: check ru_meaning_raw
            results = (
                db_session.query(DpdHeadword, Russian)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_1.isnot(None),
                        DpdHeadword.meaning_1 != "",
                        Russian.ru_meaning == "",
                        Russian.ru_meaning_raw.isnot(None),
                        Russian.ru_meaning_raw != "",
                        ~DpdHeadword.id.in_(
                            list(self.checked_ids)
                        ),  # Exclude already checked IDs
                    )
                )
                .all()
            )
            russian_field = "ru_meaning_raw"

        elif self.mode == "meaning_raw_list":
            # List mode: check ru_meaning_raw for IDs in the list file only
            list_ids = self.load_list_ids()
            if not list_ids:
                pr.amber("No IDs found in ai_processed_ids_json file. Exiting.")
                return []

            results = (
                db_session.query(DpdHeadword, Russian)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_1.isnot(None),
                        DpdHeadword.meaning_1 != "",
                        Russian.ru_meaning == "",
                        Russian.ru_meaning_raw.isnot(None),
                        Russian.ru_meaning_raw != "",
                        DpdHeadword.id.in_(
                            list(list_ids)
                        ),  # Only IDs from the list file
                        ~DpdHeadword.id.in_(
                            list(self.checked_ids)
                        ),  # Exclude already checked IDs
                    )
                )
                .all()
            )
            russian_field = "ru_meaning_raw"

        elif self.mode == "notes":
            # Notes mode: check ru_notes (excluding AI translations)
            results = (
                db_session.query(DpdHeadword, Russian)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_1.isnot(None),
                        DpdHeadword.meaning_1 != "",
                        DpdHeadword.notes.isnot(None),
                        DpdHeadword.notes != "",
                        Russian.ru_notes.isnot(None),
                        Russian.ru_notes != "",
                        ~DpdHeadword.id.in_(
                            list(self.checked_ids)
                        ),  # Exclude already checked IDs
                        ~Russian.ru_notes.contains(
                            "[пер. ИИ]"
                        ),  # Exclude AI translations
                    )
                )
                .all()
            )
            russian_field = "ru_notes"
        elif self.mode == "notes_raw":
            # Notes raw mode: check ru_notes (AI translations only)
            results = (
                db_session.query(DpdHeadword, Russian)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_1.isnot(None),
                        DpdHeadword.meaning_1 != "",
                        DpdHeadword.notes.isnot(None),
                        DpdHeadword.notes != "",
                        Russian.ru_notes.isnot(None),
                        Russian.ru_notes != "",
                        ~DpdHeadword.id.in_(
                            list(self.checked_ids)
                        ),  # Exclude already checked IDs
                        Russian.ru_notes.contains("[пер. ИИ]"),  # Only AI translations
                    )
                )
                .all()
            )
            russian_field = "ru_notes"
        elif self.mode == "meaning_lit":
            # Literal meaning mode: check ru_meaning_lit
            results = (
                db_session.query(DpdHeadword, Russian)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_lit.isnot(None),
                        DpdHeadword.meaning_lit != "",
                        Russian.ru_meaning.isnot(None),
                        Russian.ru_meaning != "",
                        Russian.ru_meaning_lit.isnot(None),
                        Russian.ru_meaning_lit != "",
                        ~DpdHeadword.id.in_(
                            list(self.checked_ids)
                        ),  # Exclude already checked IDs
                    )
                )
                .all()
            )
            russian_field = "ru_meaning_lit"

        elif self.mode == "meaning_lit_list":
            # List mode: check ru_meaning_lit for IDs in the list file only
            list_ids = self.load_list_ids()
            if not list_ids:
                pr.amber("No IDs found in ai_processed_ids_json file. Exiting.")
                return []

            results = (
                db_session.query(DpdHeadword, Russian)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_lit.isnot(None),
                        DpdHeadword.meaning_lit != "",
                        Russian.ru_meaning.isnot(None),
                        Russian.ru_meaning != "",
                        Russian.ru_meaning_lit.isnot(None),
                        Russian.ru_meaning_lit != "",
                        DpdHeadword.id.in_(
                            list(list_ids)
                        ),  # Only IDs from the list file
                        ~DpdHeadword.id.in_(
                            list(self.checked_ids)
                        ),  # Exclude already checked IDs
                    )
                )
                .all()
            )
            russian_field = "ru_meaning_lit"
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        comparisons = []
        for headword, russian in results:
            english_content = compose_english_content(headword, self.mode)

            if self.mode in [
                "notes",
                "notes_raw",
                "meaning_lit",
                "meaning_lit_list",
                "meaning_raw",
                "meaning_raw_list",
                "russian_grammar_meaning_raw",
            ]:
                russian_meaning = getattr(russian, russian_field)
            else:
                if russian.ru_meaning_lit:
                    russian_meaning = (
                        f"{russian.ru_meaning}; досл. {russian.ru_meaning_lit}"
                    )
                else:
                    russian_meaning = russian.ru_meaning

            comparison = create_word_comparison(
                headword_id=headword.id,
                lemma_1=headword.lemma_1,
                english_meaning=english_content,
                russian_meaning=russian_meaning,
                russian_meaning_alt=russian.ru_meaning
                if self.mode in ["meaning_lit", "meaning_lit_list"]
                else None,
                grammar=replace_abbreviations(headword.grammar),
            )
            comparisons.append(comparison)

        return comparisons

    def get_total_count_with_session(self, db_session: Session) -> int:
        """Get total count of words that need comparison using provided session"""
        from db.models import DpdHeadword, Russian

        if self.mode == "meaning":
            query = (
                db_session.query(DpdHeadword.id)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_1.isnot(None),
                        DpdHeadword.meaning_1 != "",
                        Russian.ru_meaning.isnot(None),
                        Russian.ru_meaning != "",
                        ~DpdHeadword.id.in_(list(self.checked_ids)),
                    )
                )
            )
        elif self.mode in ["meaning_raw", "russian_grammar_meaning_raw"]:
            query = (
                db_session.query(DpdHeadword.id)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_1.isnot(None),
                        DpdHeadword.meaning_1 != "",
                        Russian.ru_meaning == "",
                        Russian.ru_meaning_raw.isnot(None),
                        Russian.ru_meaning_raw != "",
                        ~DpdHeadword.id.in_(list(self.checked_ids)),
                    )
                )
            )
        elif self.mode == "meaning_raw_list":
            list_ids = self.load_list_ids()
            if not list_ids:
                return 0
            query = (
                db_session.query(DpdHeadword.id)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_1.isnot(None),
                        DpdHeadword.meaning_1 != "",
                        Russian.ru_meaning == "",
                        Russian.ru_meaning_raw.isnot(None),
                        Russian.ru_meaning_raw != "",
                        DpdHeadword.id.in_(list(list_ids)),
                        ~DpdHeadword.id.in_(list(self.checked_ids)),
                    )
                )
            )
        elif self.mode == "notes":
            query = (
                db_session.query(DpdHeadword.id)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_1.isnot(None),
                        DpdHeadword.meaning_1 != "",
                        DpdHeadword.notes.isnot(None),
                        DpdHeadword.notes != "",
                        Russian.ru_notes.isnot(None),
                        Russian.ru_notes != "",
                        ~DpdHeadword.id.in_(list(self.checked_ids)),
                        ~Russian.ru_notes.contains("[пер. ИИ]"),
                    )
                )
            )
        elif self.mode == "notes_raw":
            query = (
                db_session.query(DpdHeadword.id)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_1.isnot(None),
                        DpdHeadword.meaning_1 != "",
                        DpdHeadword.notes.isnot(None),
                        DpdHeadword.notes != "",
                        Russian.ru_notes.isnot(None),
                        Russian.ru_notes != "",
                        ~DpdHeadword.id.in_(list(self.checked_ids)),
                        Russian.ru_notes.contains("[пер. ИИ]"),
                    )
                )
            )
        elif self.mode == "meaning_lit":
            query = (
                db_session.query(DpdHeadword.id)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_lit.isnot(None),
                        DpdHeadword.meaning_lit != "",
                        Russian.ru_meaning.isnot(None),
                        Russian.ru_meaning != "",
                        Russian.ru_meaning_lit.isnot(None),
                        Russian.ru_meaning_lit != "",
                        ~DpdHeadword.id.in_(list(self.checked_ids)),
                    )
                )
            )
        elif self.mode == "meaning_lit_list":
            list_ids = self.load_list_ids()
            if not list_ids:
                return 0
            query = (
                db_session.query(DpdHeadword.id)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_lit.isnot(None),
                        DpdHeadword.meaning_lit != "",
                        Russian.ru_meaning.isnot(None),
                        Russian.ru_meaning != "",
                        Russian.ru_meaning_lit.isnot(None),
                        Russian.ru_meaning_lit != "",
                        DpdHeadword.id.in_(list(list_ids)),
                        ~DpdHeadword.id.in_(list(self.checked_ids)),
                    )
                )
            )
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        return query.count()

    def compare_meanings_batch(
        self, comparisons: list[WordComparison], batch_size: int = 50
    ) -> list[ComparisonResult]:
        """Compare meanings in batches using AI - delegates to BatchProcessor"""
        return self.batch_processor.compare_meanings_batch(
            comparisons, self.checked_ids, batch_size, self.mode
        )

    def compare_meanings_individual(
        self, comparisons: list[WordComparison]
    ) -> list[ComparisonResult]:
        """Compare meanings individually using AI - delegates to BatchProcessor"""
        return self.batch_processor.compare_meanings_individual(
            comparisons, self.checked_ids, self.mode
        )

    def _clean_field_for_mismatches(
        self, results: list[ComparisonResult], field_name: str
    ) -> None:
        """Clear the given Russian field for mismatched entries"""
        from db.models import Russian

        if self.mode in ["meaning_raw", "meaning_raw_list"]:
            mismatches = [
                r for r in results if r.match_status in ["MISMATCH", "PARTIAL_MATCH"]
            ]
        else:
            mismatches = [r for r in results if r.match_status == "MISMATCH"]
        if not mismatches:
            return

        pr.white(f"Cleaning {field_name} for {len(mismatches)} mismatched entries...")

        pth = ProjectPaths()
        clean_session = get_db_session(pth.dpd_db_path)
        try:
            for result in mismatches:
                try:
                    russian_record = (
                        clean_session.query(Russian)
                        .filter(Russian.id == result.headword_id)
                        .first()
                    )
                    if russian_record:
                        setattr(russian_record, field_name, "")
                        clean_session.commit()
                        pr.green(f"Cleared {field_name} for ID {result.headword_id}")
                except OSError as e:
                    pr.amber(
                        f"Failed to clear {field_name} for ID {result.headword_id}: {e}"
                    )
                    clean_session.rollback()

            pr.green(f"Completed cleaning {field_name} for mismatched entries")
        finally:
            clean_session.close()

    def generate_report(
        self,
        results: list[ComparisonResult],
        output_txt_folder: Path | None = None,
    ) -> None:
        """Generate a human-readable report of mismatches"""
        # Use instance output folder if not provided
        output_folder = output_txt_folder or self.output_txt_folder
        output_folder.mkdir(parents=True, exist_ok=True)

        # Generate timestamp-based filename
        timestamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = output_folder / f"{timestamp}_mismatches.txt"

        lines = [
            f"RUSSIAN {self.mode.upper()} MISMATCH ANALYSIS REPORT\n",
            "=" * 50 + "\n\n",
        ]

        # Filter for problematic entries - treat PARTIAL_MATCH as mismatch in raw modes
        if self.mode in ["meaning_raw", "meaning_raw_list"]:
            mismatches = [
                r for r in results if r.match_status in ["MISMATCH", "PARTIAL_MATCH"]
            ]
        else:
            mismatches = [r for r in results if r.match_status == "MISMATCH"]
        matches = [r for r in results if r.match_status == "MATCH"]

        lines.append(f"Total entries analyzed: {len(results)}\n")
        lines.append(f"Complete mismatches: {len(mismatches)}\n")
        lines.append(f"Correct matches: {len(matches)}\n\n")

        if mismatches:
            lines.append("COMPLETE MISMATCHES (Require Russian Translation Review):\n")
            lines.append("-" * 50 + "\n\n")
            for result in mismatches:
                lines.append(f"ID: {result.headword_id}\n")
                lines.append(f"Lemma: {result.lemma_1}\n")
                lines.append(f"Confidence: {result.confidence:.2f}\n")
                lines.append(f"Reasoning: {result.reasoning}\n")
                if result.suggested_fix:
                    lines.append(f"Suggested fix: {result.suggested_fix}\n")
                lines.append("\n" + "-" * 40 + "\n\n")
        else:
            lines.append(
                "No complete mismatches found! All translations appear accurate.\n"
            )

        output_file.write_text("".join(lines), encoding="utf-8")

        pr.white(f"Report saved to {output_file}")
        pr.white(f"Total entries analyzed: {len(results)}")
        pr.white(f"Total problematic entries requiring review: {len(mismatches)}")

        # Special handling for raw mode - only clean database fields for raw modes
        if self.mode in ["meaning_raw", "meaning_raw_list"] and mismatches:
            self._clean_field_for_mismatches(results, "ru_meaning_raw")
        elif self.mode == "notes_raw" and mismatches:
            self._clean_field_for_mismatches(results, "ru_notes")
        # Note: meaning_lit and meaning_lit_list modes don't clean database fields, only report
        # Note: russian_grammar_meaning_raw mode also doesn't clean database fields - keeps Russian meanings for review

        # Save checked IDs after analysis
        self.save_checked_ids()

    def run_analysis(
        self,
        db_session: Session,
        use_batch: bool = True,
        limit: int | None = None,
        auto_invalidate: bool = True,
    ) -> None:
        """Run the complete analysis"""
        pr.white("Starting Russian meaning mismatch analysis...")

        if auto_invalidate:
            n_invalidated, n_seeded = self.apply_invalidation(db_session)
            pr.white(
                f"Invalidated {n_invalidated} IDs (English changed), "
                f"seeded {n_seeded} baseline hashes"
            )

        # Get words for comparison
        comparisons = self.get_words_for_comparison_with_session(db_session)
        self.english_by_id = {c.headword_id: c.english_meaning for c in comparisons}

        if limit:
            comparisons = comparisons[:limit]

        pr.white(f"Found {len(comparisons)} words to analyze")

        if not comparisons:
            pr.white("No words found with both English and Russian meanings")
            return

        # Run comparison
        if use_batch:
            pr.white("Using batch processing (saving after each batch)...")
            all_results: list[ComparisonResult] = []
            batch_size = 50
            total_batches = (len(comparisons) + batch_size - 1) // batch_size
            for offset in range(0, len(comparisons), batch_size):
                batch = comparisons[offset : offset + batch_size]
                batch_num = offset // batch_size + 1
                pr.cyan(f"Batch {batch_num}/{total_batches} ({len(batch)} words)")
                batch_results = self.compare_meanings_batch(
                    batch, batch_size=batch_size
                )
                all_results.extend(batch_results)
                self.save_checked_ids()
                pr.green(f"Batch {batch_num} done — checked IDs saved to disk")
            results = all_results
        else:
            pr.white("Using individual processing (saving progress every 50 words)...")
            results = []
            chunk_size = 50
            for offset in range(0, len(comparisons), chunk_size):
                chunk = comparisons[offset : offset + chunk_size]
                chunk_results = self.compare_meanings_individual(chunk)
                results.extend(chunk_results)
                self.save_checked_ids()

                # Clean database mismatches incrementally for this chunk
                if self.mode in ["meaning_raw", "meaning_raw_list"]:
                    self._clean_field_for_mismatches(chunk_results, "ru_meaning_raw")
                elif self.mode == "notes_raw":
                    self._clean_field_for_mismatches(chunk_results, "ru_notes")

                pr.green(
                    f"Checked {len(results)}/{len(comparisons)} words — progress saved and database updated"
                )

        # Generate report
        self.generate_report(results)

        n_mismatches = len([r for r in results if r.match_status == "MISMATCH"])
        pr.white(f"Analysis complete. Found {n_mismatches} problematic entries.")


if __name__ == "__main__":
    # Test the functionality
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    checker = RussianMeaningChecker()

    pr.white("Testing RussianMeaningChecker...")

    try:
        total_count = checker.get_total_count_with_session(db_session)
        pr.white(f"Total words with both meanings: {total_count}")

        # Test with small sample
        comparisons = checker.get_words_for_comparison_with_session(db_session)
        sample = comparisons[:3]  # Get first 3 for testing

        pr.white("--- Sample Data ---")
        for comp in sample:
            pr.white(word_comparison_to_ai_prompt_text(comp))
            pr.white("-" * 50)

    finally:
        db_session.close()
