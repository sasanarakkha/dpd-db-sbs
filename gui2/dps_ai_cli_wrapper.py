#!/usr/bin/env python3
"""CLI wrapper for AI translation - runs AI in separate process without interactive input"""

import subprocess
import sys
import os


def run_ai_via_subprocess(headword_id: int, mode: str, synonyms: bool = False, provider: str = "openai") -> str:
    """
    Run AI translation via subprocess to avoid signal conflicts.
    
    Args:
        headword_id: Headword ID to translate
        mode: "meaning" or "note"
        provider: AI provider ("openai" or "deepseek")
    
    Returns:
        AI-generated suggestion or error message
    """
    try:
        # Create a simple script that recreates the AI logic without interactive input
        script_content = f'''
import sys
import os

# Add project paths
project_root = "{os.path.dirname(os.path.dirname(__file__))}"
sys.path.insert(0, project_root)

# Import required modules
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.ai_related import (
    load_translation_examples,
    replace_abbreviations,
    handle_ai_response,
    get_ai_client,
    generate_messages_for_meaning,
    generate_messages_for_notes
)

# Initialize paths and database
pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)

# Recreate the working function logic
def fetch_id(db_session, id_to_check):
    if not id_to_check:
        return None
    query = db_session.query(DpdHeadword).filter(DpdHeadword.id == id_to_check).first()
    return query

# Get headword data
pali_word = fetch_id(db_session, {headword_id})
if pali_word:
    lemma_1 = pali_word.lemma_1
    meaning = pali_word.meaning_1
    pos = pali_word.pos
    grammar = pali_word.grammar
    sentence = pali_word.example_1
    notes = pali_word.notes

    # Load translation examples and prepare grammar
    pos_example_map = load_translation_examples(dpspth)
    translation_example = pos_example_map.get(pos, "")

    if "{provider}" == "openai":
        # model = "gpt-4.1-mini"
        model = "gpt-4.1" 
    elif "{provider}" == "deepseek":
        model = "deepseek-chat"
    grammar_orig = grammar
    grammar = replace_abbreviations(grammar)

    # Generate appropriate messages
    if "{mode}" == "meaning":
        messages = generate_messages_for_meaning(lemma_1, grammar, meaning, sentence, translation_example, {synonyms})
    elif "{mode}" == "note":
        messages = generate_messages_for_notes(lemma_1, grammar, notes)

    # Get AI client and handle response
    client = get_ai_client("{provider}")
    suggestion, error_string = handle_ai_response(client, messages, model, "{provider}")

    if error_string:
        print(f"AI Error: {{error_string}}")
    elif suggestion:
        suggestion_str = suggestion.get("content", "") if suggestion is not None else ""
        print(suggestion_str)
    else:
        print("No response from AI")
else:
    print(f"Error: Headword {{headword_id}} not found in database")
'''

        # Run the script as subprocess
        result = subprocess.run(
            [sys.executable, "-c", script_content],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            cwd=os.path.dirname(os.path.dirname(__file__))  # Run from project root
        )
        
        # Debug: Print full output for troubleshooting
        print(f"DEBUG - Subprocess return code: {result.returncode}")
        print(f"DEBUG - Subprocess stdout: {result.stdout}")
        print(f"DEBUG - Subprocess stderr: {result.stderr}")
        
        if result.returncode == 0:
            # Success - return the output
            return result.stdout.strip()
        else:
            # Error - return both stdout and stderr for debugging
            return f"AI Error (return code {result.returncode}): stdout='{result.stdout.strip()}', stderr='{result.stderr.strip()}'"
            
    except subprocess.TimeoutExpired:
        return "AI Error: Timeout - AI processing took too long"
    except Exception as e:
        return f"Subprocess Error: {str(e)}"
