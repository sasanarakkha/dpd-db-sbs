#!/usr/bin/env python3
"""AI service for DPS GUI - uses subprocess to avoid signal errors"""

from gui2.dps_ai_cli_wrapper import run_ai_via_subprocess


def translate_with_ai_from_gui(dps_fields, mode: str, synonyms: bool = False):
    """
    Uses subprocess to run AI translation in separate process to avoid signal conflicts.
    
    Args:
        dps_fields: DpsFields instance containing GUI field values
        mode: "meaning" or "note" 
        provider: AI provider ("openai" or "deepseek")
        synonyms: Whether to generate synonyms (for meaning mode)
    
    Returns:
        AI-generated suggestion or error message
    """
    try:
        # Get headword ID from GUI field
        headword_id_field = dps_fields.fields.get("dps_dpd_id")
        if not headword_id_field or not headword_id_field.value:
            return "Error: No headword ID found in GUI"
        
        try:
            headword_id = int(headword_id_field.value)
        except ValueError:
            return f"Error: Invalid headword ID: {headword_id_field.value}"
        
        # Use subprocess to run AI in separate process (avoids signal errors)
        result = run_ai_via_subprocess(headword_id, mode, synonyms)
        
        # Check if result contains error
        if "Error:" in result or "Timeout" in result:
            return result
        else:
            # Success - return the AI-generated suggestion
            return result
            
    except Exception as e:
        return f"Error in AI service: {str(e)}"
