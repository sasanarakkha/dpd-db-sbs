from typing import List, Optional
import json
import re
from dataclasses import dataclass

from tools.ai_manager import AIManager


@dataclass
class WordComparison:
    """Represents a word entry for AI comparison"""
    headword_id: int
    lemma_1: str
    english_meaning: str
    russian_meaning: str
    grammar: str


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
    
    def extract_json_from_response(self, ai_response_content: str) -> Optional[str]:
        """Extract JSON from AI response using multiple methods"""
        
        # Clean up the response content first
        ai_response_content = ai_response_content.strip()
        
        # Method 1: Try direct JSON parsing
        try:
            import json
            # Try to parse the entire response as JSON
            data = json.loads(ai_response_content)
            if "comparisons" in data:
                print("✓ Successfully parsed pure JSON response")
                return ai_response_content
        except json.JSONDecodeError:
            pass  # Not pure JSON, continue with other methods
        
        # Method 2: Simple brace matching - find first { and last }
        try:
            first_brace = ai_response_content.find('{')
            last_brace = ai_response_content.rfind('}')
            
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                potential_json = ai_response_content[first_brace:last_brace+1]
                
                # Check if it contains "comparisons" and is valid JSON
                if '"comparisons"' in potential_json:
                    try:
                        json.loads(potential_json)
                        print("✓ Successfully extracted JSON using brace matching")
                        return potential_json
                    except json.JSONDecodeError:
                        pass  # Try next method
        except Exception:
            pass  # Continue to next method
        
        # Method 3: Comprehensive patterns matching (UPDATED for markdown code blocks)
        json_patterns = [
            # Pattern 1: ```json code blocks with multi-line JSON content
            r'```json\s*(\{[\s\S]*?\})\s*```',
            # Pattern 2: Generic ``` code blocks with JSON content
            r'```\s*(\{[\s\S]*?\})\s*```',
            # Pattern 3: Direct JSON starting with { and containing "comparisons"
            r'(\{[\s\S]*?"comparisons"[\s\S]*?\})',
            # Pattern 4: More flexible - look for complete comparisons arrays
            r'(\{[\s\S]*?"comparisons"\s*:\s*\[[\s\S]*?\][\s\S]*?\})',
            # Pattern 5: Find any JSON-like object containing comparisons
            r'(\{[\s\S]*?comparisons[\s\S]*?\})',
            # Pattern 6: Simple extraction - find first { and last } containing comparisons
            r'(\{[^}]*comparisons[^}]*\})',
            # Pattern 7: Ultra-flexible - capture from { to last } if it contains comparisons
            r'(\{[^{]*?comparisons[^{]*?\})',
        ]
        
        for pattern_idx, pattern in enumerate(json_patterns):
            match = re.search(pattern, ai_response_content, re.DOTALL)
            if match:
                potential_json = match.group(1)
                
                # Clean the extracted content - remove markdown artifacts
                potential_json = potential_json.strip()
                
                # Additional validation: ensure we have a complete JSON object
                try:
                    # Quick validation to see if it's parseable
                    json.loads(potential_json)
                    print(f"✓ Pattern {pattern_idx + 1} successfully extracted JSON")
                    return potential_json  # Success - return the JSON
                except json.JSONDecodeError:
                    # Try to clean and fix the JSON
                    cleaned_content = self.clean_json_content(potential_json)
                    if cleaned_content:
                        print(f"✓ Pattern {pattern_idx + 1} extracted and cleaned JSON")
                        return cleaned_content
                    continue
        
        # Method 4: Enhanced brace matching with string handling
        try:
            # Find the start of JSON object - look for the first {
            start_pos = -1
            in_string = False
            escape_next = False
            
            for pos, char in enumerate(ai_response_content):
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                elif not in_string and char == '{':
                    start_pos = pos
                    break
            
            if start_pos == -1:
                return None
            
            # Find the matching closing brace for the JSON object
            brace_count = 0
            in_string = False
            escape_next = False
            json_end = -1
            
            for pos, char in enumerate(ai_response_content[start_pos:], start_pos):
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
            
            if json_end > start_pos:
                potential_json = ai_response_content[start_pos:json_end]
                
                # Validate it's actually JSON and contains comparisons
                if '"comparisons"' in potential_json:
                    try:
                        json.loads(potential_json)
                        print("✓ Successfully extracted JSON using enhanced brace matching")
                        return potential_json
                    except json.JSONDecodeError:
                        pass
                        
        except Exception as e:
            print(f"⚠ Enhanced brace matching failed: {e}")
        
        # Method 5: Final comprehensive fallback - any JSON-like content with comparisons
        try:
            # Look for any content that starts with { and contains comparisons
            json_match = re.search(r'(\{.*?comparisons.*?\})', ai_response_content, re.DOTALL)
            if json_match:
                potential_json = json_match.group(1)
                
                # Try to fix and validate
                cleaned_json = self.clean_json_content(potential_json)
                if cleaned_json:
                    try:
                        json.loads(cleaned_json)
                        print("✓ Successfully extracted JSON using final fallback method")
                        return cleaned_json
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"⚠ Final fallback method failed: {e}")
        
        return None
    
    def clean_json_content(self, json_content: str) -> Optional[str]:
        """Clean malformed JSON content"""
        try:
            import re
            
            # Remove markdown code block artifacts
            cleaned_content = json_content.strip()
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content[7:].strip()
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3].strip()
            if cleaned_content.startswith('```'):
                cleaned_content = cleaned_content[3:].strip()
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3].strip()
            
            # Fix malformed fields like "observable": "" (malformed fields)
            cleaned_content = re.sub(r'"[^"]*":\s*"\s*"\s*"\s*([,}])', r'""\1', cleaned_content)
            
            # Fix unescaped quotes in reasoning fields specifically (this is the main issue)
            cleaned_content = re.sub(
                r'(reasoning.*?:.*?)"([^"]*?)("|\'|–|-)([^"]*?)("|\'|")',
                r'\1"\2\4\5',
                cleaned_content
            )
            
            # Fix unescaped quotes in all string fields
            string_fields = ['reasoning', 'lemma', 'match_status', 'suggested_fix']
            for field in string_fields:
                pattern = rf'"{field}":\s*"([^"]*(?:\\.[^"]*)*)"'
                def fix_string_field(match):
                    field_text = match.group(1)
                    field_text = field_text.replace('\\', '\\\\').replace('"', '\\"')
                    return f'"{field}": "{field_text}"'
                
                cleaned_content = re.sub(pattern, fix_string_field, cleaned_content)
            
            # Fix trailing commas before closing brackets/braces
            cleaned_content = re.sub(r',\s*}', '}', cleaned_content)
            cleaned_content = re.sub(r',\s*]', ']', cleaned_content)
            
            # Fix missing required fields by adding default values
            cleaned_content = re.sub(
                r'("id":\s*\d+,\s*"match_status":\s*"[^"]*",\s*"confidence":\s*[\d.]+,\s*"reasoning":\s*"[^"]*",\s*"suggested_fix":\s*[^,\}]*)',
                r'\1, "lemma": ""',
                cleaned_content
            )
            
            # Fix entries missing "lemma" field
            cleaned_content = re.sub(
                r'(\{"id":\s*\d+,\s*"match_status":\s*"[^"]*",\s*"confidence":\s*[\d.]+,\s*"reasoning":\s*"[^"]*",\s*"suggested_fix":\s*null)(\s*\})',
                r'\1, "lemma": ""\2',
                cleaned_content
            )
            
            cleaned_content = re.sub(
                r'(\{"id":\s*\d+,\s*"match_status":\s*"[^"]*",\s*"confidence":\s*[\d.]+,\s*"reasoning":\s*"[^"]*",\s*"suggested_fix":\s*")(\})',
                r'\1", "lemma": ""\2',
                cleaned_content
            )
            
            # Fix missing commas before closing braces
            cleaned_content = re.sub(r'(\}\s*")(\{)', r'\1,\2', cleaned_content)
            
            # Ensure proper comma placement in arrays
            cleaned_content = re.sub(r'(\]\s*\})(\s*)(\{)', r'\1,\3', cleaned_content)
            
            # Fix brackets around numeric values
            cleaned_content = re.sub(r'"id":\s*\[(\d+)\]', r'"id": \1', cleaned_content)
            cleaned_content = re.sub(r'"confidence":\s*\[([0-9.]+)\]', r'"confidence": \1', cleaned_content)
            
            # Try to parse the cleaned content
            json.loads(cleaned_content)
            return cleaned_content
            
        except (json.JSONDecodeError, re.error):
            return None
    
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
    
    def compare_meanings_batch(self, comparisons: List[WordComparison], checked_ids: set[int], batch_size: int = 25) -> List[ComparisonResult]:
        """Compare meanings in batches using AI"""
        all_results = []
        
        for i in range(0, len(comparisons), batch_size):
            batch = comparisons[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(comparisons) + batch_size - 1)//batch_size}")
            
            # Create prompt for this batch
            prompt = self.create_comparison_prompt(batch, batch_size)
            
            # Make AI request (use default models which includes working fallbacks)
            ai_response = self.ai_manager.request(prompt=prompt)
            
            if ai_response.content is not None:
                # Try to parse response as JSON first
                try:
                    # Extract JSON from response
                    json_content = self.extract_json_from_response(ai_response.content)
                    
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
                            
                            print(f"✓ Batch {i//batch_size + 1} completed: {len(batch_results)} results")
                        else:
                            
                            comparison_objects = self.process_batch_results(batch_results, len(batch))
                            all_results.extend(comparison_objects)
                            
                            # Mark as checked only the ones we got results for
                            for result_dict in batch_results:
                                headword_id = self.extract_headword_id(result_dict)
                                if headword_id:
                                    self.mark_as_checked_safe(checked_ids, headword_id)
                            
                            print(f"✓ Batch {i//batch_size + 1} completed: {len(batch_results)} / {len(batch)}")
                    else:
                        # No JSON found
                        print(f"⚠ No valid JSON found for batch {i//batch_size + 1}")
                        # Debug: Print the content for analysis
                        print("\n=== DEBUG: Enhanced Brace Matching Failed ===")
                        print(f"Response length: {len(ai_response.content)}")
                        print(f"First 1000 chars: {ai_response.content[:1000]}")
                        print(".........")
                        print(f"Last 500 chars: {ai_response.content[-500:]}")
                        print("=== DEBUG: End Enhanced Brace Matching Debug ===\n")
                        
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"⚠ JSON processing failed for batch {i//batch_size + 1}: {e}")
                    # Debug: Print the content for analysis
                    print("\n=== DEBUG: Enhanced Brace Matching Failed ===")
                    print(f"Response length: {len(ai_response.content)}")
                    print(f"First 1000 chars: {ai_response.content[:1000]}")
                    print(".........")
                    print(f"Last 500 chars: {ai_response.content[-500:]}")
                    print("=== DEBUG: End Enhanced Brace Matching Debug ===\n")
                    continue
                    
            else:
                print(f"AI request failed for batch {i//batch_size + 1}: {ai_response.status_message}")
        
        return all_results
    
    def compare_meanings_individual(self, comparisons: List[WordComparison], checked_ids: set[int]) -> List[ComparisonResult]:
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