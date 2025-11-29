"""
AI Batch Processor - Handles batch processing of AI meaning comparisons.

This module provides the BatchProcessor class for comparing English and Russian meanings
using AI models. It processes comparisons in batches for efficiency and delegates JSON
parsing to the JSONParser class.

Main components:
- WordComparison: Data class for word entries to compare
- ComparisonResult: Data class for AI comparison results
- BatchProcessor: Main class for batch processing AI comparisons
"""

from typing import List, Optional
import json
from dataclasses import dataclass

from tools.ai_manager import AIManager
from tools.ai_json_parser import JSONParser


@dataclass
class WordComparison:
    """Represents a word entry for AI comparison"""
    headword_id: int
    lemma_1: str
    english_meaning: str
    russian_meaning: str
    russian_meaning_alt: Optional[str] = None  # For literal meaning modes - holds ru_meaning
    grammar: str = ""


@dataclass
class ComparisonResult:
    """Result of AI comparison"""
    headword_id: int
    lemma_1: str
    match_status: str  # "MATCH", "PARTIAL_MATCH", "MISMATCH"
    confidence: float  # 0.0 to 1.0
    reasoning: str
    suggested_fix: Optional[str] = None


class BatchProcessor:
    """Handles batch processing of AI meaning comparisons"""
    
    def __init__(self):
        self.ai_manager = AIManager()
        self.json_parser = JSONParser()
    
    def mark_as_checked_safe(self, checked_ids: set[int], headword_id: int) -> bool:
        """Safely mark an ID as checked"""
        try:
            checked_ids.add(headword_id)
            return True
        except Exception as e:
            print(f"⚠ Failed to mark ID {headword_id} as checked: {e}")
            return False
    
    def extract_headword_id(self, result_dict: dict) -> Optional[int]:
        """Safely extract headword_id from result dictionary"""
        headword_id_raw = result_dict.get("id")
        if isinstance(headword_id_raw, list):
            headword_id = headword_id_raw[0] if headword_id_raw else None
        elif isinstance(headword_id_raw, (int, str)):
            headword_id = int(headword_id_raw)
        else:
            print(f"⚠ Invalid ID format: {headword_id_raw}, skipping entry")
            return None
            
        if headword_id is None:
            print("⚠ Missing ID in result, skipping entry")
            return None
        
        return headword_id
    
    def create_comparison_prompt(self, comparisons: List[WordComparison], batch_size: int = 10, mode: str = "meaning") -> str:
        """Create AI prompt for comparing meanings"""
        
        # Check if this is literal meaning mode based on mode parameter
        has_lit_mode = mode in ["meaning_lit", "meaning_lit_list"]
        
        # Check if this is Russian grammar checking mode (meaning_ru_raw)
        is_ru_raw_mode = (mode == "meaning_ru_raw")
        
        if is_ru_raw_mode:
            # Russian grammar-only checking mode - NO English meaning comparison
            prompt = """You are an expert Russian language grammarian. Your task is to check ONLY Russian grammar and language correctness.

🎯 TASK: Identify Russian language errors in the given Russian text.

FOCUS ONLY ON:
1. TYPOS in Russian text
2. CASE ENDING ERRORS - do they match the given grammar details?
3. GRAMMAR CORRECTNESS - proper Russian grammar rules
4. SPELLING MISTAKES
5. PUNCTUATION ERRORS

GRAMMAR CHECKING RULES:
- Check if nouns have correct case endings based on grammar
- Verify adjective-noun agreement in case, number, gender
- Check preposition + case combinations
- Verify verb conjugations and aspects
- Look for common Russian typos and misspellings

EXAMPLES OF MISMATCHES (flag these):
- "книга читаю" → MISMATCH (wrong case ending - should be "книгу читаю")
- "в хороший дому" → MISMATCH (wrong preposition case - should be "в хорошем доме")
- "они идёт" → MISMATCH (verb conjugation error - should be "они идут")

EXAMPLES OF MATCHES (don't flag these):
- "книга читается" ✓ (correct grammar)
- "в красивом саду" ✓ (correct case endings)
- "мы читаем книги" ✓ (correct grammar)

FORMAT YOUR RESPONSE AS JSON:
{
    "comparisons": [
        {
            "id": [headword_id],
            "lemma": "[lemma_1]",
            "match_status": "MATCH|PARTIAL_MATCH|MISMATCH",
            "confidence": [0.0-1.0],
            "reasoning": "[detailed grammar explanation]",
            "suggested_fix": "[corrected Russian text if needed]"
        }
    ]
}

Here are the Russian texts to analyze for grammar only:

"""
        else:
            # Standard English-Russian meaning comparison mode
            prompt = """You are an expert in English-Russian translation comparison. Focus ONLY on comparing the English and Russian MEANINGS, considering grammatical information.

🎯 TASK: Identify ONLY extreme cases where Russian translations are COMPLETELY WRONG or have OPPOSITE MEANING.

🚨 BE EXTREMELY LENIENT 🚨
1. If English and Russian meanings express similar concepts, it's a MATCH
2. If Russian uses different but related words, it's still a MATCH
3. If Russian translates the concept accurately, that's a MATCH
4. Only flag as MISMATCH if meanings are COMPLETELY OPPOSITE or NONSENSICAL

EXAMPLES OF MATCHES (definitely DON'T flag these):
- "nothing; lit. not something" vs "ничто; досл. не что-то" ✓
- "smooth; tender; not harsh; not rough" vs "delicate; tactful; polite; not sharp; not coarse" ✓
- "abbreviation of Aṅguttara (Nikāya)" vs "сокращение от Ангуттара (Никая)" ✓
- "Buddha" vs "Будда" ✓
- "monk" vs "монах" ✓
- "forest meditation" vs "медитация в лесу" ✓
- "good" vs "хороший; добрый; благоприятный" ✓
- "birth" vs "рождение; появление; начало" ✓

EXAMPLES OF TRUE MISMATCHES (only flag these):
- "good" vs "плохой" (good vs bad - OPPOSITE)
- "birth" vs "смерть" (birth vs death - OPPOSITE)
- "north" vs "юг" (north vs south - OPPOSITE)
- "hot" vs "холодный" (hot vs cold - OPPOSITE)

"""
            if has_lit_mode:
                prompt += """🔥 LITERAL MEANING CHECK ADDITIONAL RULES:
If Literal Russian Meaning is TOO SIMILAR to Russian Regular Meaning, flag as MISMATCH.
Literal meanings should be DISTINCT from regular meanings, not just word-for-word duplicates.
For example: "good" vs "хороший" (literal) and "хороший" (regular) = MISMATCH (too similar)

"""
            prompt += """KEY RULES:
- If English and Russian express the same concept (even with different wording), it's a MATCH
"""
            if has_lit_mode:
                prompt += """
- Also ensure that Russian meaning is actually different from regular Russian meanings
"""
            prompt += """
FORMAT YOUR RESPONSE AS JSON:
{
    "comparisons": [
        {
            "id": [headword_id],
            "lemma": "[lemma_1]",
            "match_status": "MATCH|PARTIAL_MATCH|MISMATCH",
            "confidence": [0.0-1.0],
            "reasoning": "[detailed explanation]",
            "suggested_fix": "[what Russian should be, if applicable]"
        }
    ]
}

Here are the word comparisons to analyze:

"""
        
        # Add word data
        for i, comp in enumerate(comparisons[:batch_size]):
            if is_ru_raw_mode:
                prompt += f"{i+1}. ID: {comp.headword_id}\n"
                prompt += f"Grammar Details: {comp.grammar}\n"
                prompt += f"Russian Text: {comp.russian_meaning}\n\n"
            else:
                prompt += f"{i+1}. ID: {comp.headword_id}\n"
                prompt += f"Pali Lemma: {comp.lemma_1}\n"
                prompt += f"Grammar: {comp.grammar}\n"
                if has_lit_mode:
                    prompt += "Literal "
                prompt += f"English: {comp.english_meaning}\n"
                if has_lit_mode:
                    prompt += "Literal "
                prompt += f"Russian: {comp.russian_meaning}\n"
                
                # Add alternative Russian meaning for literal modes
                if comp.russian_meaning_alt:
                    prompt += f"Regular Russian: {comp.russian_meaning_alt}\n"
                
                prompt += "\n"
        
        if is_ru_raw_mode:
            prompt += """🚨 GRAMMAR CHECKING FOCUS 🚨
ONLY flag as MISMATCH if:
1. Russian text contains typos or spelling mistakes
2. Case endings don't match the grammar details provided
3. Grammar rules are violated (wrong prepositions, verb forms, etc.)
4. Text is grammatically incorrect in Russian
"""
        else:
            prompt += """🚨 BE EXTREMELY CONSERVATIVE 🚨
ONLY flag as MISMATCH if:
1. English and Russian meanings are completely opposite or nonsensical, Focus ONLY on whether English and Russian express the same concept.
"""
            if has_lit_mode:
                prompt += """OR
2. For literal meanings: if Literal Russian is too similar to Russian Regular meaning
"""
        print(prompt) # debug
        return prompt
    
    def process_batch_results(self, batch_results: List[dict], batch_size: int) -> List[ComparisonResult]:
        """Process batch results into ComparisonResult objects"""
        comparison_objects = []
        
        for result_dict in batch_results:
            # Ensure headword_id is properly extracted as integer
            headword_id = self.extract_headword_id(result_dict)
            if headword_id is None:
                continue
                
            result = ComparisonResult(
                headword_id=headword_id,
                lemma_1=result_dict.get("lemma", ""),
                match_status=result_dict.get("match_status", "MATCH"),
                confidence=float(result_dict.get("confidence", 0.0)),
                reasoning=result_dict.get("reasoning", ""),
                suggested_fix=result_dict.get("suggested_fix")
            )
            comparison_objects.append(result)
        
        return comparison_objects
    
    def compare_meanings_batch(self, comparisons: List[WordComparison], checked_ids: set[int], batch_size: int = 50, mode: str = "meaning") -> List[ComparisonResult]:
        """Compare meanings in batches using AI with simple interrupt handling"""
        import signal
        
        # Simple flag to track interruption
        interrupted = False
        
        def interrupt_handler(sig, frame):
            nonlocal interrupted
            print("\n⚠ INTERRUPT DETECTED - Will stop after current batch...")
            interrupted = True
        
        # Set up interrupt handler
        signal.signal(signal.SIGINT, interrupt_handler)
        
        all_results = []
        total_batches = (len(comparisons) + batch_size - 1) // batch_size
        
        try:
            for i in range(0, len(comparisons), batch_size):
                # Check for interruption
                if interrupted:
                    print("⏹ Processing stopped by user request")
                    break
                    
                batch = comparisons[i:i+batch_size]
                batch_num = i//batch_size + 1
                print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} words)")
                
                try:
                    # Create prompt for this batch
                    prompt = self.create_comparison_prompt(batch, batch_size, mode)
                    
                    # Make AI request (use default models which includes working fallbacks)
                    ai_response = self.ai_manager.request(prompt=prompt)
                    
                    if ai_response.content is not None:
                        # Try to parse response as JSON first
                        try:
                            # Extract JSON from response using JSONParser
                            json_content = self.json_parser.extract_json_from_response(ai_response.content)
                            
                            if json_content:
                                # Parse the JSON content
                                data = json.loads(json_content)
                                batch_results = data.get("comparisons", [])
                                
                                if len(batch_results) == len(batch):
                                    # Perfect! Got results for all words in batch
                                    comparison_objects = self.process_batch_results(batch_results, len(batch))
                                    all_results.extend(comparison_objects)
                                    
                                    # Mark all as checked since they were successfully processed
                                    for comp in batch:
                                        self.mark_as_checked_safe(checked_ids, comp.headword_id)
                                    
                                    print(f"✓ Batch {batch_num} completed: {len(batch_results)} results")
                                else:
                                    comparison_objects = self.process_batch_results(batch_results, len(batch))
                                    all_results.extend(comparison_objects)
                                    
                                    # Mark as checked only the ones we got results for
                                    for result_dict in batch_results:
                                        headword_id = self.extract_headword_id(result_dict)
                                        if headword_id:
                                            self.mark_as_checked_safe(checked_ids, headword_id)
                                    
                                    print(f"✓ Batch {batch_num} completed: {len(batch_results)} / {len(batch)}")
                            else:
                                # No JSON found
                                print(f"⚠ No valid JSON found for batch {batch_num}")
                                # Debug: Print the content for analysis
                                print("\n=== DEBUG: Enhanced Brace Matching Failed ===")
                                print(f"Response length: {len(ai_response.content)}")
                                print(f"First 1000 chars: {ai_response.content[:1000]}")
                                print(".........")
                                print(f"Last 500 chars: {ai_response.content[-500:]}")
                                print("=== DEBUG: End Enhanced Brace Matching Debug ===\n")
                                
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            print(f"⚠ JSON processing failed for batch {batch_num}: {e}")
                            # Debug: Print the content for analysis
                            print("\n=== DEBUG: Enhanced Brace Matching Failed ===")
                            print(f"Response length: {len(ai_response.content)}")
                            print(f"First 1000 chars: {ai_response.content[:1000]}")
                            print(".........")
                            print(f"Last 500 chars: {ai_response.content[-500:]}")
                            print("=== DEBUG: End Enhanced Brace Matching Debug ===\n")
                            continue
                            
                    else:
                        # AI request failed - just show the error
                        print(f"❌ AI request failed for batch {batch_num}: {ai_response.status_message}")
                        continue
                        
                except Exception as e:
                    print(f"⚠ Unexpected error in batch {batch_num}: {e}")
                    print("Continuing with next batch...")
                    continue
                    
        finally:
            # Reset signal handler
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            print("\n📊 BATCH PROCESSING SUMMARY:")
            print(f"   ✅ Successfully processed: {len(all_results)} words")
            if i < len(comparisons):
                print(f"   📋 Processed batches: {i//batch_size + 1}")
            else:
                print(f"   📋 Total batches: {total_batches}")
            print("   💾 Progress saved (checked IDs tracked)")
            if interrupted:
                print(f"   ⏹ Stopped early at batch {batch_num}")
        
        return all_results
    
    def compare_meanings_individual(self, comparisons: List[WordComparison], checked_ids: set[int], mode: str = "meaning") -> List[ComparisonResult]:
        """Compare meanings individually using AI (more precise but slower)"""
        all_results = []
        
        for i, comp in enumerate(comparisons):
            print(f"Processing {i+1}/{len(comparisons)}: {comp.lemma_1}")
            
            # Create prompt for single comparison
            prompt = self.create_comparison_prompt([comp], 1, mode)
            
            # Make AI request (use default models which includes working fallbacks)
            ai_response = self.ai_manager.request(prompt=prompt)
            
            if ai_response.content is not None:
                # Parse response (individual mode - pass the specific word comparison)
                batch_results = self.parse_ai_response(ai_response.content, comp)
                if batch_results:
                    all_results.extend(batch_results)
                    # Only mark as checked when we have a successful AI response
                    # Ensure we have valid results before marking as checked
                    for result in batch_results:
                        if result and result.headword_id is not None:
                            self.mark_as_checked_safe(checked_ids, result.headword_id)
                    print(f"✓ Completed: {comp.lemma_1} - {batch_results[0].match_status}")
                else:
                    print(f"⚠ No result for: {comp.lemma_1}")
            else:
                print(f"✗ AI request failed for {comp.lemma_1}: {ai_response.status_message}")
        
        return all_results
    
    def parse_ai_response(self, response_content: str, word_comparison: Optional[WordComparison] = None) -> List[ComparisonResult]:
        """Parse AI response into ComparisonResult objects"""
        import re
        
        # Clean up the response content
        response_content = response_content.strip()
        
        try:
            # Try to parse as JSON first
            data = json.loads(response_content)
            comparisons = data.get("comparisons", [])
            
            results = []
            for comp in comparisons:
                # Ensure headword_id is properly extracted as integer
                headword_id_raw = comp.get("id")
                if isinstance(headword_id_raw, list):
                    headword_id = headword_id_raw[0] if headword_id_raw else None
                elif isinstance(headword_id_raw, (int, str)):
                    headword_id = int(headword_id_raw)
                else:
                    print(f"⚠ Invalid ID format in JSON response: {headword_id_raw}")
                    continue
                
                # Skip if we couldn't get a valid headword_id
                if headword_id is None:
                    print("⚠ Missing or invalid headword_id, skipping entry")
                    continue
                    
                result = ComparisonResult(
                    headword_id=headword_id,
                    lemma_1=comp.get("lemma", ""),
                    match_status=comp.get("match_status", "MATCH"),
                    confidence=float(comp.get("confidence", 0.0)),
                    reasoning=comp.get("reasoning", ""),
                    suggested_fix=comp.get("suggested_fix")
                )
                results.append(result)
            
            print("✓ Successfully parsed JSON response")
            return results
            
        except (json.JSONDecodeError, KeyError, ValueError):
            # If JSON parsing fails, try to extract information manually
            print("⚠ AI response not in JSON format, trying manual parsing...")
            
            results = []
            
            # If we have a word comparison, create a basic result
            if word_comparison:
                # Try to determine match status from text
                content_lower = response_content.lower()
                if any(word in content_lower for word in ['mismatch', 'wrong', 'incorrect', 'opposite']):
                    match_status = "MISMATCH"
                    confidence = 0.8
                elif any(word in content_lower for word in ['partial', 'somewhat', 'mostly', 'slightly']):
                    match_status = "PARTIAL_MATCH"
                    confidence = 0.6
                elif any(word in content_lower for word in ['match', 'correct', 'accurate', 'good']):
                    match_status = "MATCH"
                    confidence = 0.9
                else:
                    match_status = "MATCH"
                    confidence = 0.5
                
                # Extract reasoning if possible
                reasoning_match = re.search(r'(?:reason|explanation|because)[:\s]+([^.]+)', response_content, re.IGNORECASE)
                reasoning = reasoning_match.group(1).strip() if reasoning_match else "AI provided response but couldn't determine specific reasoning"
                
                result = ComparisonResult(
                    headword_id=word_comparison.headword_id,
                    lemma_1=word_comparison.lemma_1,
                    match_status=match_status,
                    confidence=confidence,
                    reasoning=reasoning,
                    suggested_fix=None
                )
                results.append(result)
                
                print(f"✓ Manually parsed response for {word_comparison.lemma_1}: {match_status}")
            else:
                print("✗ Could not parse AI response and no word comparison provided")
            
            return results