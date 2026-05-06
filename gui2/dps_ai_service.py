#!/usr/bin/env python3
"""AI service for DPS GUI - uses AIManager for provider-agnostic AI requests"""

from tools.ai_related import load_translation_examples, replace_abbreviations
from tools.paths_dps import DPSPaths


def translate_with_ai_from_gui(dps_fields, mode: str, synonyms: bool = False):
    """
    Uses AIManager to generate AI suggestions for meaning or notes.

    Args:
        dps_fields: DpsFields instance containing GUI field values and toolkit
        mode: "meaning" or "note"
        synonyms: Whether to generate synonyms (for meaning mode)

    Returns:
        AI-generated suggestion or error message
    """
    try:
        # Get headword ID from GUI field
        headword_id_field = dps_fields.fields.get("dps_id")
        if not headword_id_field or not headword_id_field.value:
            return "Error: No headword ID found in GUI"

        try:
            headword_id = int(headword_id_field.value)
        except ValueError:
            return f"Error: Invalid headword ID: {headword_id_field.value}"

        # Fetch headword from database
        headword = dps_fields.toolkit.db_manager.get_headword_by_id(headword_id)
        if not headword:
            return f"Error: Headword with ID {headword_id} not found"

        # Get language-specific paths and data
        dpspth = DPSPaths()

        # Build the appropriate prompt based on mode
        if mode == "meaning":
            prompt_sys, prompt = _build_meaning_prompt(headword, dpspth, synonyms)
        elif mode == "note":
            prompt_sys, prompt = _build_notes_prompt(headword)
        else:
            return f"Error: Unknown mode '{mode}'. Use 'meaning' or 'note'."

        # Call AI manager
        ai_response = dps_fields.toolkit.ai_manager.request(
            prompt=prompt,
            prompt_sys=prompt_sys,
        )

        # Check result
        if ai_response.content:
            return ai_response.content.strip()
        else:
            return f"Error: {ai_response.status_message}"

    except Exception as e:
        return f"Error in AI service: {str(e)}"


def _build_meaning_prompt(
    headword, dpspth: DPSPaths, synonyms: bool = False
) -> tuple[str, str]:
    """Build system and user prompts for meaning translation."""

    system_content = "You are a skilled assistant that translates English text to Russian with grammatical accuracy, contextual relevance, and strict adherence to rules."

    # Get grammar and meaning data
    lemma_1 = headword.lemma_1
    grammar = headword.grammar or ""
    meaning = headword.meaning_1 or ""
    sentence = headword.example_1 or ""
    pos = headword.pos or ""

    # Expand abbreviations in grammar
    grammar = replace_abbreviations(grammar)

    # Load translation examples for this POS
    pos_examples_map = load_translation_examples(dpspth, lang="ru")
    translation_example = pos_examples_map.get(pos, "")

    user_content = f"""
	Translate the English definition of the Pali term into Russian, following these rules:

	- Translate all bracketed text (e.g., "(gram)" → "(грам)", "(comm)" → "(комм)", "(vinaya)" → "(виная)", "(of weather)" → "(о погоде)").
	- Separate synonyms with `;`.
	- Match the grammatical structure of the Pali term (noun, verb, etc.).
	- Use lowercase unless it's a proper noun.
	- Translate "lit." as "досл.".
	- Retain clarifications if any (e.g., "(of trap) laid down" → "(о капкане) установленный").
	- Translate idioms to Russian equivalents.
	- Ensure no English remains untranslated, including within brackets.
	- Output only the translation of the Definition, without labels like "Перевод" etc, without any comments, without translation of the Grammar and in one line.

	**Pali Term**: {lemma_1}
	**Grammar**: {grammar}
	**Definition**: {meaning}
"""

    if sentence:
        user_content += f"\n- Consider Pali context: {sentence}"

    if translation_example:
        user_content += f"\n- Match this example format: {translation_example}"

    if synonyms:
        user_content = user_content.replace(
            "Translate the English definition of the Pali term into Russian",
            "Provide at least nine (9) distinct Russian synonyms for the English definition of Pali term",
        )

    return system_content, user_content


def _build_notes_prompt(headword) -> tuple[str, str]:
    """Build system and user prompts for notes translation."""

    system_content = "You are a helpful assistant that translates English text to Russian considering the context."

    lemma_1 = headword.lemma_1
    grammar = headword.grammar or ""
    notes = headword.notes or ""

    # Expand abbreviations in grammar
    grammar = replace_abbreviations(grammar)

    user_content = f"""
	Translate the English notes into Russian, following these rules:
	- Keep Pali or Sanskrit terms in roman script.
	- Output only the translation of the Notes, without labels like "Перевод" etc, without any comments, without translation of the Grammar and in one line.

	**Pali Term**: {lemma_1}
	**Grammar**: {grammar}
	**Notes**: {notes}
"""

    return system_content, user_content
