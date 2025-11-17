from sqlalchemy import and_
from typing import List, Optional
from dataclasses import dataclass
from tools.ai_manager import AIManager
import os

from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from db.db_helpers import get_db_session

from tools.ai_related import replace_abbreviations

pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)

checked_id_pth = dpspth.ai_meaning_checked
output_txt_folder = dpspth.ai_meaning_report_dir

@dataclass
class WordComparison:
    """Represents a word entry for AI comparison"""
    headword_id: int
    lemma_1: str
    english_meaning: str
    russian_meaning: str
    grammar: str
    
    def to_ai_prompt_text(self) -> str:
        """Convert to readable text for AI prompt"""
        return f"""ID: {self.headword_id}
Lemma: {self.lemma_1}
English: {self.english_meaning}
Russian: {self.russian_meaning}
Grammar: {self.grammar}"""


@dataclass
class ComparisonResult:
    """Result of AI comparison"""
    headword_id: int
    lemma_1: str
    match_status: str  # "MATCH", "PARTIAL_MATCH", "MISMATCH"
    confidence: float  # 0.0 to 1.0
    reasoning: str
    suggested_fix: Optional[str] = None


class RussianMeaningChecker:
    """Checks if Russian meanings match English meanings using AI"""
    
    def __init__(self, db_path: str = "dpd.db"):
        self.db_path = db_path
        self.ai_manager = AIManager()
        self.checked_ids_file = checked_id_pth
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
        
        # Query for entries with both meaning_1 and ru_meaning not empty, and not already checked
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
        
        comparisons = []
        for headword, russian in results:
            comparison = WordComparison(
                headword_id=headword.id,
                lemma_1=headword.lemma_1,
                english_meaning=headword.meaning_1,
                russian_meaning=russian.ru_meaning,
                grammar=replace_abbreviations(headword.grammar),
            )
            comparisons.append(comparison)
        
        return comparisons
    
    def get_total_count_with_session(self, db_session) -> int:
        """Get total count of words that need comparison using provided session"""
        if db_session is None:
            raise Exception("No db_session")
        
        from db.models import DpdHeadword, Russian
        
        count = (
            db_session.query(DpdHeadword)
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
            .count()
        )
        return count
    
    def create_comparison_prompt(self, comparisons: List[WordComparison], batch_size: int = 10) -> str:
        """Create AI prompt for comparing meanings"""
        
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

KEY RULE: If English and Russian express the same concept (even with different wording), it's a MATCH.

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

Here are the word comparisons to analyze (focus ONLY on English vs Russian meanings):

"""
        
        # Add simplified word data - focus on core meanings only
        for i, comp in enumerate(comparisons[:batch_size]):
            # Simplified format - focus on core meanings only
            prompt += f"{i+1}. ID: {comp.headword_id}\n"
            prompt += f"Pali Lemma: {comp.lemma_1}\n"
            prompt += f"Grammar: {comp.grammar}\n" 
            prompt += f"English: {comp.english_meaning}\n"
            prompt += f"Russian: {comp.russian_meaning}\n"
        
        prompt += """🚨 BE EXTREMELY CONSERVATIVE 🚨
ONLY flag as MISMATCH if English and Russian meanings are completely opposite or nonsensical.
Focus ONLY on whether English and Russian express the same concept."""
        
        return prompt
    
    def parse_ai_response(self, response_content: str, word_comparison: Optional[WordComparison] = None) -> List[ComparisonResult]:
        """Parse AI response into ComparisonResult objects"""
        import json
        import re
        
        # Clean up the response content
        response_content = response_content.strip()
        
        try:
            # Try to parse as JSON first
            data = json.loads(response_content)
            comparisons = data.get("comparisons", [])
            
            results = []
            for comp in comparisons:
                result = ComparisonResult(
                    headword_id=comp.get("id"),
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
    
    def compare_meanings_batch(self, comparisons: List[WordComparison], batch_size: int = 10) -> List[ComparisonResult]:
        """Compare meanings in batches using AI"""
        all_results = []
        
        for i in range(0, len(comparisons), batch_size):
            batch = comparisons[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(comparisons) + batch_size - 1)//batch_size}")
            
            # Create prompt for this batch
            prompt = self.create_comparison_prompt(batch, len(batch))
            
            # Make AI request (use default models which includes working fallbacks)
            ai_response = self.ai_manager.request(prompt=prompt)
            
            if ai_response.content is not None:
                # Try to parse response as JSON first
                try:
                    import json
                    import re
                    
                    # Check if response contains JSON wrapped in text (common with some AI models)
                    json_content = ai_response.content
                    
                    # Look for JSON content within code blocks or text
                    json_patterns = [
                        r'```(?:json)?\s*(\{.*?\})\s*```',  # Code blocks
                        r'(\{[\s\S]*?"comparisons"\s*:\s*\[[\s\S]*?\][\s\S]*?\})',  # Complete comparisons object
                        r'(\{.*?"comparisons".*?\})',  # Direct JSON content
                        r'(\{[\s\S]*?"comparisons"[\s\S]*?\})',  # More robust direct JSON
                        r'(?s)\{(\s*"comparisons":\s*\[[^}]*(?:\{[^}]*\}[^}]*)*\])\s*\}',  # Balanced JSON pattern
                    ]
                    
                    # Try pattern matching first
                    for pattern_idx, pattern in enumerate(json_patterns):
                        match = re.search(pattern, ai_response.content, re.DOTALL)
                        if match:
                            potential_json = match.group(1)
                            
                            # Validate that the extracted JSON is complete by checking for balanced braces
                            if potential_json.strip().startswith('{'):
                                # If the pattern starts with {, then we got the whole object
                                json_content = potential_json
                            else:
                                # We need to add the braces back
                                json_content = '{' + potential_json + '}'
                            
                            # Additional validation: ensure we have a complete JSON object
                            try:
                                # Quick validation to see if it's parseable
                                json.loads(json_content)
                                print(f"✓ Extracted JSON from text wrapper pattern {pattern_idx + 1} for batch {i//batch_size + 1}")
                                break
                            except json.JSONDecodeError as e:
                                # Check if it's just missing closing braces
                                if json_content.strip().endswith(']}'):
                                    # The JSON is missing the final closing brace
                                    fixed_json = json_content.rstrip() + '\n}'
                                    try:
                                        json.loads(fixed_json)
                                        json_content = fixed_json
                                        print(f"✓ Fixed missing closing brace for pattern {pattern_idx + 1} for batch {i//batch_size + 1}")
                                        break
                                    except json.JSONDecodeError:
                                        pass
                                
                                # Try to extend incomplete JSON
                                print(f"⚠ Pattern {pattern_idx + 1} extracted incomplete JSON, trying to extend...")
                                
                                # Use the original content after our successful extraction as fallback
                                fallback_start = ai_response.content.find('{"comparisons":')
                                if fallback_start != -1:
                                    # Use enhanced brace matching to find complete JSON
                                    brace_count = 0
                                    in_string = False
                                    escape_next = False
                                    json_end = fallback_start
                                    
                                    for pos, char in enumerate(ai_response.content[fallback_start:], fallback_start):
                                        if escape_next:
                                            escape_next = False
                                            continue
                                        
                                        if char == '\\' and in_string:
                                            escape_next = True
                                            continue
                                        
                                        if char == '"' and not escape_next:
                                            in_string = not in_string
                                        elif not in_string:
                                            if char == '{':
                                                brace_count += 1
                                            elif char == '}':
                                                brace_count -= 1
                                                if brace_count == 0:
                                                    json_end = pos + 1
                                                    break
                                    
                                    if brace_count == 0:
                                        json_content = ai_response.content[fallback_start:json_end]
                                        print(f"✓ Found complete JSON by extending pattern {pattern_idx + 1} for batch {i//batch_size + 1}")
                                        break
                                
                                # If we couldn't fix or extend it, continue to next pattern
                                continue
                    
                    # If pattern matching failed, try brace matching approach (original method)
                    if not json_content or json_content == ai_response.content:
                        # Find JSON object by matching braces
                        start_pos = ai_response.content.find('{"comparisons":')
                        if start_pos != -1:
                            brace_count = 0
                            in_string = False
                            escape_next = False
                            json_end = start_pos
                            
                            for pos, char in enumerate(ai_response.content[start_pos:], start_pos):
                                if escape_next:
                                    escape_next = False
                                    continue
                                
                                if char == '\\' and in_string:
                                    escape_next = True
                                    continue
                                
                                if char == '"' and not escape_next:
                                    in_string = not in_string
                                elif not in_string:
                                    if char == '{':
                                        brace_count += 1
                                    elif char == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            json_end = pos + 1
                                            break
                            
                            if brace_count == 0:
                                json_content = ai_response.content[start_pos:json_end]
                                print(f"✓ Found complete JSON using brace matching for batch {i//batch_size + 1}")
                    
                    # Additional fallback: Try enhanced brace matching for problematic cases
                    if json_content == ai_response.content:
                        try:
                            # Try more robust brace matching with better escape handling
                            start_pos = ai_response.content.find('{"comparisons":')
                            if start_pos != -1:
                                brace_count = 0
                                in_string = False
                                json_end = start_pos
                                
                                pos = start_pos
                                while pos < len(ai_response.content):
                                    char = ai_response.content[pos]
                                    
                                    if in_string:
                                        if char == '\\':
                                            # Skip the next character (escaped character)
                                            pos += 1
                                            if pos >= len(ai_response.content):
                                                break
                                        elif char == '"':
                                            # End of string
                                            in_string = False
                                    else:
                                        if char == '"':
                                            # Start of string
                                            in_string = True
                                        elif char == '{':
                                            brace_count += 1
                                        elif char == '}':
                                            brace_count -= 1
                                            if brace_count == 0:
                                                json_end = pos + 1
                                                break
                                    
                                    pos += 1
                                
                                if brace_count == 0:
                                    json_content = ai_response.content[start_pos:json_end]
                                    print(f"✓ Found complete JSON using enhanced brace matching for batch {i//batch_size + 1}")
                        except Exception as e:
                            print(f"⚠ Enhanced brace matching failed: {e}")
                            # Debug: Print the content for analysis
                            print("\n=== DEBUG: Enhanced Brace Matching Failed ===")
                            print(f"DEBUG: Response length: {len(ai_response.content)}")
                            print(f"DEBUG: First 1000 chars: {ai_response.content[:1000]}")
                            print(".........")
                            print(f"DEBUG: Last 500 chars: {ai_response.content[-500:]}")
                            print("=== End Enhanced Brace Matching Debug ===\n")
                            # Continue with original logic
                    
                    # Final fallback: Try JSON cleaning and lenient parsing
                    if json_content == ai_response.content:
                        try:
                            print(f"⚠ Attempting JSON cleaning for batch {i//batch_size + 1}")
                            
                            # Try to find and clean JSON content
                            cleaned_content = ai_response.content.strip()
                            
                            # Remove potential BOM or hidden characters
                            if cleaned_content.startswith('\ufeff'):
                                cleaned_content = cleaned_content[1:]
                            
                            # Fix common AI formatting errors: remove brackets around numeric values
                            import re
                            # Replace "id": [number] with "id": number
                            cleaned_content = re.sub(r'"id":\s*\[(\d+)\]', r'"id": \1', cleaned_content)
                            # Replace "headword_id": [number] with "headword_id": number
                            cleaned_content = re.sub(r'"headword_id":\s*\[(\d+)\]', r'"headword_id": \1', cleaned_content)
                            # Replace "confidence": [0.x] with "confidence": 0.x
                            cleaned_content = re.sub(r'"confidence":\s*\[([0-9.]+)\]', r'"confidence": \1', cleaned_content)
                            # Fix trailing commas before closing brackets
                            cleaned_content = re.sub(r',\s*}', '}', cleaned_content)
                            cleaned_content = re.sub(r',\s*]', ']', cleaned_content)
                            
                            # Find JSON boundaries more precisely using brace matching
                            start_brace = cleaned_content.find('{"comparisons":')
                            if start_brace == -1:
                                start_brace = cleaned_content.find('{')
                            
                            if start_brace != -1:
                                # Use precise brace matching to find the correct end
                                brace_count = 0
                                in_string = False
                                escape_next = False
                                json_end = start_brace
                                
                                for pos, char in enumerate(cleaned_content[start_brace:], start_brace):
                                    if escape_next:
                                        escape_next = False
                                        continue
                                    
                                    if char == '\\' and in_string:
                                        escape_next = True
                                        continue
                                    
                                    if char == '"' and not escape_next:
                                        in_string = not in_string
                                    elif not in_string:
                                        if char == '{':
                                            brace_count += 1
                                        elif char == '}':
                                            brace_count -= 1
                                            if brace_count == 0:
                                                json_end = pos + 1
                                                break
                                
                                if brace_count == 0:
                                    potential_json = cleaned_content[start_brace:json_end]
                                    
                                    # Validate JSON completeness before attempting to parse
                                    try:
                                        # First validate that essential JSON structure exists
                                        if '"comparisons"' not in potential_json:
                                            print("⚠ Missing 'comparisons' key in JSON")
                                        
                                        # Try to parse the cleaned JSON
                                        data = json.loads(potential_json)
                                        json_content = potential_json
                                        print(f"✓ Successfully cleaned and parsed JSON for batch {i//batch_size + 1}")
                                    except json.JSONDecodeError as clean_error:
                                        print(f"⚠ JSON cleaning failed: {clean_error}")
                                else:
                                    print(f"⚠ Could not find complete JSON structure (brace_count: {brace_count})")
                            else:
                                print("⚠ Could not find valid JSON boundaries")
                                
                        except Exception as e:
                            print(f"⚠ JSON cleaning fallback failed: {e}")
                            # Debug the cleaning failure
                            print("\n=== DEBUG: JSON Cleaning Failed ===")
                            print(f"DEBUG: Response length: {len(ai_response.content)}")
                            print(f"DEBUG: First 1000 chars: {repr(ai_response.content[:1000])}")
                            print(".........")
                            print(f"DEBUG: Last 500 chars: {repr(ai_response.content[-500:])}")
                            print("=== End JSON Cleaning Debug ===\n")
                    
                    # If still no JSON found, try direct parsing (pure JSON responses)
                    if json_content == ai_response.content:
                        try:
                            # Test if the response is actually pure JSON
                            json.loads(ai_response.content)
                            json_content = ai_response.content  # Use as-is
                            print(f"✓ Using pure JSON response for batch {i//batch_size + 1}")
                        except json.JSONDecodeError as e:
                            # Not pure JSON, print debug
                            print(f"⚠ All JSON extraction methods failed for batch {i//batch_size + 1}: {e}")
                            # debug
                            print("\n=== DEBUG: Non-JSON AI Response Content ===")
                            print(f"DEBUG: Response length: {len(ai_response.content)}")
                            print(f"DEBUG: First 1000 chars: {ai_response.content[:1000]}")
                            print(".........")
                            print(f"Last 500 chars: {ai_response.content[-500:]}")
                            print("=== End Debug Info ===\n")

                            break
                    
                    # Parse the JSON content
                    data = json.loads(json_content)
                    batch_results = data.get("comparisons", [])
                    
                    if len(batch_results) == len(batch):
                        # Perfect! Got results for all words in batch
                        # Convert dicts to ComparisonResult objects
                        comparison_objects = []
                        for result_dict in batch_results:
                            result = ComparisonResult(
                                headword_id=result_dict.get("id"),
                                lemma_1=result_dict.get("lemma", ""),
                                match_status=result_dict.get("match_status", "MATCH"),
                                confidence=float(result_dict.get("confidence", 0.0)),
                                reasoning=result_dict.get("reasoning", ""),
                                suggested_fix=result_dict.get("suggested_fix")
                            )
                            comparison_objects.append(result)
                        
                        all_results.extend(comparison_objects)
                        # Mark all as checked since they were successfully processed
                        for comp in batch:
                            self.mark_as_checked(comp.headword_id)
                        print(f"Batch {i//batch_size + 1} completed: {len(batch_results)} results")
                    else:
                        # Got incomplete JSON results - only track the ones we successfully processed
                        print(f"⚠ Got only {len(batch_results)} results from batch, unprocessed words will be picked up in next run...")
                        
                        # Convert dicts to ComparisonResult objects for partial batch
                        comparison_objects = []
                        for result_dict in batch_results:
                            result = ComparisonResult(
                                headword_id=result_dict.get("id"),
                                lemma_1=result_dict.get("lemma", ""),
                                match_status=result_dict.get("match_status", "MATCH"),
                                confidence=float(result_dict.get("confidence", 0.0)),
                                reasoning=result_dict.get("reasoning", ""),
                                suggested_fix=result_dict.get("suggested_fix")
                            )
                            comparison_objects.append(result)
                        
                        all_results.extend(comparison_objects)
                        
                        # Mark as checked only the ones we got results for
                        for result_dict in batch_results:
                            result_id = result_dict.get("id")
                            if result_id:
                                self.mark_as_checked(result_id)
                        
                        print(f"Batch {i//batch_size + 1} completed: {len(batch_results)} results (next batch will handle remaining)")
                        
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    # Check if we had already successfully extracted JSON
                    if 'json_content' in locals() and json_content != ai_response.content:
                        # We had extracted JSON but something failed during processing
                        print(f"⚠ JSON extraction worked but processing failed: {e}")
                        
                        # Debug: Print the extracted JSON to see what's wrong
                        print("\n=== DEBUG: Non-JSON AI Response Content ===")
                        print(f"DEBUG: Extracted JSON length: {len(json_content)}")
                        print(f"DEBUG: First 1000 chars: {json_content[:1000]}")
                        print(".........")
                        print(f"DEBUG: Last 500 chars: {json_content[-500:]}")
                        print("=== End Debug Info ===\n")
                        
                        break
                    else:
                        # Genuine non-JSON response - try manual extraction
                        print(f"⚠ AI response not in JSON format, attempting manual extraction from batch {i//batch_size + 1}")
                        
                        # debug: Print the actual AI response content
                        print("\n=== DEBUG: Non-JSON AI Response Content ===")
                        print(f"Response length: {len(ai_response.content)} characters")
                        print(f"First 1000 chars: {ai_response.content[:1000]}")
                        print(".........")
                        print(f"Last 500 chars: {ai_response.content[-500:]}")
                        print("=== End Debug Info ===\n")
                        
                        break
                    
            else:
                print(f"AI request failed for batch {i//batch_size + 1}: {ai_response.status_message}")
        
        return all_results
    
    def compare_meanings_individual(self, comparisons: List[WordComparison]) -> List[ComparisonResult]:
        """Compare meanings individually using AI (more precise but slower)"""
        all_results = []
        
        for i, comp in enumerate(comparisons):
            print(f"Processing {i+1}/{len(comparisons)}: {comp.lemma_1}")
            
            # Create prompt for single comparison
            prompt = self.create_comparison_prompt([comp], 1)
            
            # Make AI request (use default models which includes working fallbacks)
            ai_response = self.ai_manager.request(prompt=prompt)
            
            if ai_response.content is not None:
                # Parse response (individual mode - pass the specific word comparison)
                batch_results = self.parse_ai_response(ai_response.content, comp)
                if batch_results:
                    all_results.extend(batch_results)
                    # Only mark as checked when we have a successful AI response
                    self.mark_as_checked(comp.headword_id)
                    print(f"✓ Completed: {comp.lemma_1} - {batch_results[0].match_status}")
                else:
                    print(f"⚠ No result for: {comp.lemma_1}")
            else:
                print(f"✗ AI request failed for {comp.lemma_1}: {ai_response.status_message}")
        
        return all_results
    
    def generate_report(self, results: List[ComparisonResult], output_txt_folder):
        """Generate a human-readable report of mismatches"""
        import datetime
        
        # Create directory if it doesn't exist
        os.makedirs(output_txt_folder, exist_ok=True)
        
        # Generate timestamp-based filename
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = os.path.join(output_txt_folder, f"{timestamp}_mismatches.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("RUSSIAN MEANING MISMATCH ANALYSIS REPORT\n")
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
                results = self.compare_meanings_batch(comparisons, batch_size=10)
                # IDs are now marked as checked within the batch method only on success
            else:
                print("Using individual processing...")
                results = self.compare_meanings_individual(comparisons)
            
            # Generate report
            self.generate_report(results, globals()['output_txt_folder'])
            
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
            print(comp.to_ai_prompt_text())
            print("-" * 50)
            
    finally:
        db_session.close()