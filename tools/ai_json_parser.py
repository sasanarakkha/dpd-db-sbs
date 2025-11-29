"""
JSON Parser - Extracts and cleans JSON from AI responses.

Handles malformed JSON including: markdown blocks, JavaScript trailing code,
unicode artifacts, truncated strings, incomplete arrays, and syntax issues.
"""

from typing import Optional
import json
import re


class JSONParser:
    """Handles extraction and cleaning of JSON from AI responses"""
    
    def _preprocess_response(self, content: str) -> str:
        """Pre-process AI response to remove common garbage patterns"""
        content = content.strip()
        
        # Remove JavaScript-like trailing code
        content = re.sub(r'\}\s*\.map\(.*$', '}', content, flags=re.DOTALL)
        content = re.sub(r'\}\s*\.filter\(.*$', '}', content, flags=re.DOTALL)
        
        # Find last valid JSON closing brace before garbage
        last_valid_brace = -1
        for match in re.finditer(r'\}', content):
            if '"comparisons"' in content[:match.end()]:
                last_valid_brace = match.end()
        
        if last_valid_brace > 0:
            content = content[:last_valid_brace]
        
        return content
    
    def _try_direct_parse(self, content: str) -> Optional[str]:
        """Try to parse content directly as JSON"""
        try:
            data = json.loads(content)
            if "comparisons" in data:
                print("✓ Successfully parsed pure JSON response")
                return content
        except json.JSONDecodeError:
            pass
        return None
    
    def _try_brace_matching(self, content: str) -> Optional[str]:
        """Try simple brace matching extraction"""
        try:
            first_brace = content.find('{')
            last_brace = content.rfind('}')
            
            if first_brace != -1 and last_brace > first_brace:
                potential_json = content[first_brace:last_brace+1]
                if '"comparisons"' in potential_json:
                    json.loads(potential_json)
                    print("✓ Successfully extracted JSON using brace matching")
                    return potential_json
        except (json.JSONDecodeError, Exception):
            pass
        return None
    
    def _try_pattern_matching(self, content: str) -> Optional[str]:
        """Try regex pattern matching extraction"""
        patterns = [
            r'```json\s*(\{[\s\S]*?\})\s*```',
            r'```\s*(\{[\s\S]*?\})\s*```',
            r'(\{[\s\S]*?"comparisons"[\s\S]*?\})',
            r'(\{[\s\S]*?"comparisons"\s*:\s*\[[\s\S]*?\][\s\S]*?\})',
            r'(\{[\s\S]*?comparisons[\s\S]*?\})',
        ]
        
        for idx, pattern in enumerate(patterns):
            match = re.search(pattern, content, re.DOTALL)
            if match:
                potential_json = match.group(1).strip()
                try:
                    json.loads(potential_json)
                    print(f"✓ Pattern {idx + 1} successfully extracted JSON")
                    return potential_json
                except json.JSONDecodeError:
                    cleaned = self.clean_json_content(potential_json)
                    if cleaned:
                        print(f"✓ Pattern {idx + 1} extracted and cleaned JSON")
                        return cleaned
        return None
    
    def _try_enhanced_brace_matching(self, content: str) -> Optional[str]:
        """Try enhanced brace matching with string handling"""
        try:
            # Find first { outside of strings
            start_pos = -1
            in_string = False
            escape_next = False
            
            for pos, char in enumerate(content):
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
            
            # Find matching closing brace
            brace_count = 0
            in_string = False
            escape_next = False
            
            for pos, char in enumerate(content[start_pos:], start_pos):
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
                            potential_json = content[start_pos:pos+1]
                            if '"comparisons"' in potential_json:
                                json.loads(potential_json)
                                print("✓ Successfully extracted JSON using enhanced brace matching")
                                return potential_json
                            break
        except Exception:
            pass
        return None
    
    def extract_json_from_response(self, ai_response_content: str) -> Optional[str]:
        """Extract JSON from AI response using multiple methods"""
        content = self._preprocess_response(ai_response_content)
        
        # Try each extraction method in order
        result = self._try_direct_parse(content)
        if result:
            return result
        
        result = self._try_brace_matching(content)
        if result:
            return result
        
        result = self._try_pattern_matching(content)
        if result:
            return result
        
        result = self._try_enhanced_brace_matching(content)
        if result:
            return result
        
        # Final fallback
        try:
            match = re.search(r'(\{.*?comparisons.*?\})', content, re.DOTALL)
            if match:
                cleaned = self.clean_json_content(match.group(1))
                if cleaned:
                    json.loads(cleaned)
                    print("✓ Successfully extracted JSON using final fallback")
                    return cleaned
        except Exception:
            pass
        
        return None
    
    def _strip_markdown_blocks(self, content: str) -> str:
        """Remove markdown code block artifacts"""
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:].strip()
        if content.endswith('```'):
            content = content[:-3].strip()
        if content.startswith('```'):
            content = content[3:].strip()
            if content.endswith('```'):
                content = content[:-3].strip()
        return content
    
    def _fix_string_fields(self, content: str) -> str:
        """Fix unescaped quotes in string fields"""
        content = re.sub(r'"[^"]*":\s*"\s*"\s*"\s*([,}])', r'""\1', content)
        content = re.sub(
            r'(reasoning.*?:.*?)"([^"]*?)("|\'|–|-)([^"]*?)("|\'|")',
            r'\1"\2\4\5',
            content
        )
        
        for field in ['reasoning', 'lemma', 'match_status', 'suggested_fix']:
            pattern = rf'"{field}":\s*"([^"]*(?:\\.[^"]*)*)"'
            def fix_field(match, f=field):
                text = match.group(1).replace('\\', '\\\\').replace('"', '\\"')
                return f'"{f}": "{text}"'
            content = re.sub(pattern, fix_field, content)
        
        return content
    
    def _fix_truncated_strings(self, content: str) -> str:
        """Fix truncated reasoning fields with unclosed strings"""
        if '"reasoning"' not in content:
            return content
        
        matches = list(re.finditer(r'"reasoning"\s*:\s*"', content))
        if not matches:
            return content
        
        last_match = matches[-1]
        after = content[last_match.end():]
        
        escape_next = False
        for char in after:
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"':
                return content
        
        delimiter = re.search(r'[,}]', after)
        if delimiter:
            pos = last_match.end() + delimiter.start()
            content = content[:pos] + '"' + content[pos:]
        
        return content
    
    def _fix_syntax_issues(self, content: str) -> str:
        """Fix common JSON syntax issues"""
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        content = re.sub(r'(\}\s*")(\{)', r'\1,\2', content)
        content = re.sub(r'(\]\s*\})(\s*)(\{)', r'\1,\3', content)
        content = re.sub(r'"id":\s*\[(\d+)\]', r'"id": \1', content)
        content = re.sub(r'"confidence":\s*\[([0-9.]+)\]', r'"confidence": \1', content)
        return content
    
    def _fix_missing_fields(self, content: str) -> str:
        """Fix entries missing required fields"""
        content = re.sub(
            r'("id":\s*\d+,\s*"match_status":\s*"[^"]*",\s*"confidence":\s*[\d.]+,\s*"reasoning":\s*"[^"]*",\s*"suggested_fix":\s*[^,\}]*)',
            r'\1, "lemma": ""',
            content
        )
        content = re.sub(
            r'(\{"id":\s*\d+,\s*"match_status":\s*"[^"]*",\s*"confidence":\s*[\d.]+,\s*"reasoning":\s*"[^"]*",\s*"suggested_fix":\s*null)(\s*\})',
            r'\1, "lemma": ""\2',
            content
        )
        content = re.sub(
            r'(\{"id":\s*\d+,\s*"match_status":\s*"[^"]*",\s*"confidence":\s*[\d.]+,\s*"reasoning":\s*"[^"]*",\s*"suggested_fix":\s*")(\})',
            r'\1", "lemma": ""\2',
            content
        )
        return content
    
    def _fix_incomplete_array(self, content: str) -> str:
        """Fix incomplete comparisons array"""
        if '"comparisons"' not in content:
            return content
        if re.search(r'"comparisons"\s*:\s*\[.*?\]', content, re.DOTALL):
            return content
        
        array_start = re.search(r'"comparisons"\s*:\s*\[', content)
        if not array_start or '{' not in content[array_start.end():]:
            return content
        
        after = content[array_start.end():]
        last_obj_end = -1
        brace_count = 0
        in_string = False
        escape_next = False
        
        for i, char in enumerate(after):
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
                        last_obj_end = i + 1
        
        if last_obj_end > 0:
            pos = array_start.end() + last_obj_end
            content = content[:pos] + ']}'
        
        return content
    
    def clean_json_content(self, json_content: str) -> Optional[str]:
        """Clean malformed JSON content"""
        try:
            content = self._strip_markdown_blocks(json_content)
            content = self._fix_string_fields(content)
            content = self._fix_truncated_strings(content)
            content = self._fix_syntax_issues(content)
            content = self._fix_missing_fields(content)
            content = self._fix_incomplete_array(content)
            
            json.loads(content)
            return content
        except (json.JSONDecodeError, re.error):
            return None