from sqlalchemy import and_
from typing import List, Optional
import os

from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths

from db.db_helpers import get_db_session

from tools.ai_batch_processor import BatchProcessor, WordComparison, ComparisonResult
from tools.ai_related import replace_abbreviations

pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)


# Extension of WordComparison with additional functionality
def create_word_comparison(headword_id: int, lemma_1: str, english_meaning: str, russian_meaning: str, grammar: str) -> WordComparison:
    """Create a WordComparison with all required fields"""
    return WordComparison(
        headword_id=headword_id,
        lemma_1=lemma_1,
        english_meaning=english_meaning,
        russian_meaning=russian_meaning,
        grammar=grammar
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
    
    def __init__(self, db_path: str = "dpd.db", mode: str = "meaning"):
        self.db_path = db_path
        self.mode = mode
        self.batch_processor = BatchProcessor()
        
        # Use different checked IDs files for different modes
        if mode == "meaning_raw":
            self.checked_ids_file = dpspth.ai_meaning_raw_checked
            self.output_txt_folder = dpspth.ai_meaning_raw_report_dir
        elif mode == "notes":
            self.checked_ids_file = dpspth.ai_notes_checked
            self.output_txt_folder = dpspth.ai_notes_report_dir
        elif mode == "notes_raw":
            self.checked_ids_file = dpspth.ai_notes_raw_checked
            self.output_txt_folder = dpspth.ai_notes_raw_report_dir
        else:
            self.checked_ids_file = dpspth.ai_meaning_checked
            self.output_txt_folder = dpspth.ai_meaning_report_dir
            
        self.checked_ids = self.load_checked_ids()
        
    def load_checked_ids(self) -> set[int]:
        """Load previously checked IDs from file"""
        try:
            import json
            if os.path.exists(self.checked_ids_file):
                with open(self.checked_ids_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            else:
                return set()
        except (json.JSONDecodeError, FileNotFoundError):
            return set()
    
    def save_checked_ids(self):
        """Save checked IDs to file"""
        try:
            import json
            with open(self.checked_ids_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.checked_ids), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save checked IDs: {e}")
    
    def mark_as_checked(self, headword_id: int):
        """Mark a word as checked"""
        self.checked_ids.add(headword_id)
        
    def get_words_for_comparison_with_session(self, db_session) -> List[WordComparison]:
        """Get all words that have both English and Russian meanings using provided session"""
        if db_session is None:
            raise Exception("No db_session")
        
        from db.models import DpdHeadword, Russian
        
        if self.mode == "meaning":
            # Original mode: check meaning_1 vs ru_meaning
            results = (
                db_session.query(DpdHeadword, Russian)
                .join(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        DpdHeadword.meaning_1.isnot(None),
                        DpdHeadword.meaning_1 != "",
                        Russian.ru_meaning.isnot(None),
                        Russian.ru_meaning != "",
                        ~DpdHeadword.id.in_(list(self.checked_ids))  # Exclude already checked IDs
                    )
                )
                .all()
            )
            russian_field = "ru_meaning"
            
        elif self.mode == "meaning_raw":
            # Raw mode: check meaning_1 vs ru_meaning_raw
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
                        ~DpdHeadword.id.in_(list(self.checked_ids))  # Exclude already checked IDs
                    )
                )
                .all()
            )
            russian_field = "ru_meaning_raw"
            
        elif self.mode == "notes":
            # Notes mode: check notes vs ru_notes (excluding AI translations)
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
                        ~DpdHeadword.id.in_(list(self.checked_ids)),  # Exclude already checked IDs
                        ~Russian.ru_notes.contains("[пер. ИИ]")  # Exclude AI translations
                    )
                )
                .all()
            )
            russian_field = "ru_notes"
        elif self.mode == "notes_raw":
            # Notes raw mode: check notes vs ru_notes (AI translations only)
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
                        ~DpdHeadword.id.in_(list(self.checked_ids)),  # Exclude already checked IDs
                        Russian.ru_notes.contains("[пер. ИИ]")  # Only AI translations
                    )
                )
                .all()
            )
            russian_field = "ru_notes"
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
        
        comparisons = []
        for headword, russian in results:
            # For notes modes, use notes as the English content
            if self.mode in ["notes", "notes_raw"]:
                english_content = headword.notes
            else:
                english_content = headword.meaning_1
                
            comparison = create_word_comparison(
                headword_id=headword.id,
                lemma_1=headword.lemma_1,
                english_meaning=english_content,
                russian_meaning=getattr(russian, russian_field),
                grammar=replace_abbreviations(headword.grammar),
            )
            comparisons.append(comparison)
        
        return comparisons
    
    def get_total_count_with_session(self, db_session) -> int:
        """Get total count of words that need comparison using provided session"""
        # Use the same query logic as get_words_for_comparison_with_session
        comparisons = self.get_words_for_comparison_with_session(db_session)
        return len(comparisons)
    
    def compare_meanings_batch(self, comparisons: List[WordComparison], batch_size: int = 25) -> List[ComparisonResult]:
        """Compare meanings in batches using AI - delegates to BatchProcessor"""
        return self.batch_processor.compare_meanings_batch(comparisons, self.checked_ids, batch_size)
    
    def compare_meanings_individual(self, comparisons: List[WordComparison]) -> List[ComparisonResult]:
        """Compare meanings individually using AI - delegates to BatchProcessor"""
        return self.batch_processor.compare_meanings_individual(comparisons, self.checked_ids)
    
    def clean_ru_meaning_raw_for_mismatches(self, results: List[ComparisonResult]):
        """Clean ru_meaning_raw for mismatched entries"""
        from db.models import Russian
        
        mismatches = [r for r in results if r.match_status == "MISMATCH"]
        if not mismatches:
            return
            
        print(f"Cleaning ru_meaning_raw for {len(mismatches)} mismatched entries...")
        
        try:
            from db.db_helpers import get_db_session
            from tools.paths import ProjectPaths
            
            pth = ProjectPaths()
            clean_session = get_db_session(pth.dpd_db_path)
            
            for result in mismatches:
                try:
                    # Find the Russian record and clear ru_meaning_raw
                    russian_record = clean_session.query(Russian).filter(Russian.id == result.headword_id).first()
                    if russian_record:
                        russian_record.ru_meaning_raw = ""
                        clean_session.commit()
                        print(f"✓ Cleared ru_meaning_raw for ID {result.headword_id}")
                except Exception as e:
                    print(f"⚠ Failed to clear ru_meaning_raw for ID {result.headword_id}: {e}")
                    clean_session.rollback()
            
            clean_session.close()
            print("✓ Completed cleaning ru_meaning_raw for mismatched entries")
            
        except Exception as e:
            print(f"⚠ Failed to clean ru_meaning_raw: {e}")

    def clean_ru_notes_for_mismatches(self, results: List[ComparisonResult]):
        """Clean ru_notes for mismatched entries"""
        from db.models import Russian
        
        mismatches = [r for r in results if r.match_status == "MISMATCH"]
        if not mismatches:
            return
            
        print(f"Cleaning ru_notes for {len(mismatches)} mismatched entries...")
        
        try:
            from db.db_helpers import get_db_session
            from tools.paths import ProjectPaths
            
            pth = ProjectPaths()
            clean_session = get_db_session(pth.dpd_db_path)
            
            for result in mismatches:
                try:
                    # Find the Russian record and clear ru_notes
                    russian_record = clean_session.query(Russian).filter(Russian.id == result.headword_id).first()
                    if russian_record:
                        russian_record.ru_notes = ""
                        clean_session.commit()
                        print(f"✓ Cleared ru_notes for ID {result.headword_id}")
                except Exception as e:
                    print(f"⚠ Failed to clear ru_notes for ID {result.headword_id}: {e}")
                    clean_session.rollback()
            
            clean_session.close()
            print("✓ Completed cleaning ru_notes for mismatched entries")
            
        except Exception as e:
            print(f"⚠ Failed to clean ru_notes: {e}")
    
    def generate_report(self, results: List[ComparisonResult], output_txt_folder: str | None = None):
        """Generate a human-readable report of mismatches"""
        import datetime
        
        # Use instance output folder if not provided
        output_folder = output_txt_folder or self.output_txt_folder
        
        # Create directory if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Generate timestamp-based filename
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = os.path.join(output_folder, f"{timestamp}_mismatches.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"RUSSIAN {self.mode.upper()} MISMATCH ANALYSIS REPORT\n")
            f.write("="*50 + "\n\n")
            
            # Filter for problematic entries - ONLY COMPLETE MISMATCHES (no partial matches)
            mismatches = [r for r in results if r.match_status == "MISMATCH"]
            matches = [r for r in results if r.match_status == "MATCH"]
            
            f.write(f"Total entries analyzed: {len(results)}\n")
            f.write(f"Complete mismatches: {len(mismatches)}\n")
            f.write(f"Correct matches: {len(matches)}\n\n")
            
            if mismatches:
                f.write("COMPLETE MISMATCHES (Require Russian Translation Review):\n")
                f.write("-" * 50 + "\n\n")
                for result in mismatches:
                    f.write(f"ID: {result.headword_id}\n")
                    f.write(f"Lemma: {result.lemma_1}\n")
                    f.write(f"Confidence: {result.confidence:.2f}\n")
                    f.write(f"Reasoning: {result.reasoning}\n")
                    if result.suggested_fix:
                        f.write(f"Suggested fix: {result.suggested_fix}\n")
                    f.write("\n" + "-" * 40 + "\n\n")
            else:
                f.write("No complete mismatches found! All translations appear accurate.\n")
        
        print(f"Report saved to {output_file}")
        print(f"Total entries analyzed: {len(results)}")
        print(f"Total problematic entries requiring review: {len(mismatches)}")
        
        # Special handling for raw mode
        if self.mode == "meaning_raw" and mismatches:
            self.clean_ru_meaning_raw_for_mismatches(results)
        elif self.mode == "notes_raw" and mismatches:
            self.clean_ru_notes_for_mismatches(results)
        
        # Save checked IDs after analysis
        self.save_checked_ids()
    
    
    def run_analysis(self, db_session=None, use_batch: bool = True, limit: Optional[int] = None):
        """Run the complete analysis"""
        print("Starting Russian meaning mismatch analysis...")
        
        # Use provided session or the global one
        session = db_session or globals()['db_session']
        
        try:
            # Get words for comparison
            comparisons = self.get_words_for_comparison_with_session(session)
            
            if limit:
                comparisons = comparisons[:limit]
            
            print(f"Found {len(comparisons)} words to analyze")
            
            if not comparisons:
                print("No words found with both English and Russian meanings")
                return
            
            # Run comparison
            if use_batch:
                print("Using batch processing...")
                results = self.compare_meanings_batch(comparisons, batch_size=25)
                # IDs are now marked as checked within the batch method only on success
            else:
                print("Using individual processing...")
                results = self.compare_meanings_individual(comparisons)
            
            # Generate report
            self.generate_report(results)
            
            print(f"Analysis complete. Found {len([r for r in results if r.match_status == 'MISMATCH'])} problematic entries.")
            
        finally:
            # Only close if we created our own session
            if db_session is None:
                session.close()


if __name__ == "__main__":
    # Test the functionality
    checker = RussianMeaningChecker()
    
    print("Testing RussianMeaningChecker...")
    
    try:
        total_count = checker.get_total_count_with_session(db_session)
        print(f"Total words with both meanings: {total_count}")
        
        # Test with small sample
        comparisons = checker.get_words_for_comparison_with_session(db_session)
        sample = comparisons[:3]  # Get first 3 for testing
        
        print("\n--- Sample Data ---")
        for comp in sample:
            print(word_comparison_to_ai_prompt_text(comp))
            print("-" * 50)
            
    finally:
        db_session.close()