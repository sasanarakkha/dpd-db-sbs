"""Shared prompt-building and analysis utilities for Pāḷi AI translation."""

import copy
import json
import re
from typing import Any

from sqlalchemy.orm import Session

from exporter.mcp.analyzer import analyze_sentence
from tools.ai_manager import AIManager


def _normalize_ai_response(ai_data: dict[str, Any]) -> dict[str, Any]:
    """Fix malformed AI responses with nested 'scores' keys.

    Some AI models return scores in a nested structure like {"scores": {"scores": {...}}}.
    This function flattens that to the expected {"scores": {...}} format.
    """
    scores = ai_data.get("scores", {})
    if (
        isinstance(scores, dict)
        and "scores" in scores
        and not any(
            k.startswith(("decon_", "digits")) or "_" in k
            for k in scores.keys()
            if isinstance(k, str)
        )
    ):
        # The outer "scores" key only contains another "scores" key → nested structure
        ai_data["scores"] = scores["scores"]
    return ai_data


def _clean_meaning(meaning: str) -> str:
    """Strip trailing grammar parentheticals that duplicate the Grammar column.

    Removes patterns like '(masculine nominative plural of 'X')' and
    '(component of compound 'X')' that the AI inherits from DPD meaning_combo.
    """
    return re.sub(r"\s*\([^)]*'[^']+'\)\s*$", "", meaning).strip()


def pre_match_db_examples(
    analysis: list[dict[str, Any]],
    verse_source: str,
) -> None:
    """Mutate analysis in-place: mark options whose source_1/source_2 matches verse_source.

    Sets ai_score=10 and db_example_match=True so the AI and post-processing strongly prefer them.
    """
    for token_data in analysis:
        for option in token_data.get("data", []):
            s1 = option.get("source_1", "")
            s2 = option.get("source_2", "")
            if (s1 and s1 == verse_source) or (s2 and s2 == verse_source):
                option["ai_score"] = 10
                option["db_example_match"] = True


def _extract_partial_response(response_text: str) -> dict[str, Any]:
    """Extract translation/literal_translation from a malformed JSON response.

    When the AI returns incomplete JSON (e.g., with template placeholders),
    extract what we can and construct a fallback response.
    """
    fallback: dict[str, Any] = {
        "translation": "",
        "literal_translation": "",
        "scores": {},
    }

    # Try to extract translation using regex
    trans_match = re.search(
        r'"translation"\s*:\s*"([^"]*(?:\\"[^"]*)*)"', response_text
    )
    if trans_match:
        fallback["translation"] = trans_match.group(1).replace('\\"', '"')

    # Try to extract literal_translation
    lit_match = re.search(
        r'"literal_translation"\s*:\s*"([^"]*(?:\\"[^"]*)*)"', response_text
    )
    if lit_match:
        fallback["literal_translation"] = lit_match.group(1).replace('\\"', '"')

    # Try to extract valid score entries (those with numeric scores)
    score_matches = re.finditer(
        r'"([^"]+?)"\s*:\s*\{\s*"score"\s*:\s*(\d+)', response_text
    )
    for match in score_matches:
        key = match.group(1)
        score = int(match.group(2))
        fallback["scores"][key] = {"score": score}

    return fallback


def translate_sentence(
    sentence: str,
    db_session: Session,
    ai_manager: AIManager | None = None,
    model: str | None = None,
    verse_source: str | None = None,
    speech_mark_options: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Full pipeline: Analyze → AI Translate → Merge. Returns the enriched analysis object."""
    if ai_manager is None:
        ai_manager = AIManager()

    analysis = analyze_sentence(sentence, db_session)

    if verse_source:
        pre_match_db_examples(analysis, verse_source)

    sys_prompt = build_system_prompt(analysis, speech_mark_options)

    response = ai_manager.request(
        prompt=f"Please translate and analyze: {sentence}",
        model=model,
        prompt_sys=sys_prompt,
    )

    if not response.content:
        raise ValueError(f"AI Request Failed: {response.status_message}")

    json_str = response.content.strip()
    if json_str.startswith("```json"):
        json_str = json_str[7:-3].strip()
    elif json_str.startswith("```"):
        json_str = json_str[3:-3].strip()

    try:
        ai_data = json.loads(json_str)
    except json.JSONDecodeError:
        # JSON is malformed; extract what we can
        ai_data = _extract_partial_response(response.content)

    ai_data = _normalize_ai_response(ai_data)
    return merge_ai_selections(analysis, ai_data)


def generate_markdown_report(
    merged_result: dict[str, Any], sentence: str, verse_id: str = ""
) -> str:
    """Render a merged analysis result as a markdown document."""
    if verse_id:
        parts: list[str] = [f"# Analysis of: {verse_id}", sentence]
    else:
        parts = [f"# Analysis of: {sentence}"]
    parts += [
        "### English Translation",
        f"**Translation:** {merged_result.get('translation', '')}",
        f"**Literal Translation:** {merged_result.get('literal_translation', '')}",
        "### Word-by-Word Analysis",
        format_markdown_table(merged_result["analysis"]),
    ]
    return "\n\n".join(parts)


def build_system_prompt(
    analysis: list[dict[str, Any]],
    speech_mark_options: dict[str, list[str]] | None = None,
) -> str:
    """Build a comprehensive system prompt with the Pāḷi dictionary context."""

    context_str = json.dumps(analysis, ensure_ascii=False, indent=2)

    disambiguation_block = ""
    verse_text_field = ""
    if speech_mark_options:
        options_lines = "\n".join(
            f"- '{word}': {variants}" for word, variants in speech_mark_options.items()
        )
        disambiguation_block = f"""
### Verse Text Disambiguation
The following words in this verse have multiple possible apostrophe/sandhi forms.
Based on your grammatical analysis, choose the correct form for each and output the full
verse text (with all chosen forms substituted) in the `verse_text` field:
{options_lines}
"""
        verse_text_field = (
            '\n  "verse_text": "full verse with resolved apostrophe forms",'
        )

    prompt = f"""You are an expert Pāḷi translator and grammarian with deep knowledge of the Tipitaka.
Your task is to analyze a Pāḷi sentence and perform word-sense disambiguation using the provided dictionary analysis.

### Dictionary Context (Word-by-Word Analysis Options)
{context_str}

### Instructions:
1. **Analyze the Sentence:** Use the context to understand grammatical relationships.
2. **Disambiguate:** For each word in the sentence, identify the correct dictionary option (`key`).
3. **Score Options:**
   - Assign a score of **10** to the correct `key` for the context.
   - Assign lower scores (0-9) to alternative options if there is ambiguity.
   - Assign **10** to the correct `key` for *components* of compounds as well.
4. **Contextualize:**
   - **`contextual_meaning`**: Adjust the dictionary `meaning_combo` to fit the grammar (e.g., "dwells" -> "I would dwell").
     - **CRITICAL:** Do this for the main word AND for any components that are **sandhi** (pos: "sandhi").
     - You do NOT need to adjust meanings for standard compound components unless necessary for clarity.
     - **CRITICAL:** Provide ONLY the core meaning. Do NOT append grammatical case notes in parentheses — never add phrases like "(masculine nominative plural of 'X')" or "(component of compound 'X')". The Grammar column already shows this information.
   - **`selected_pos`**: If `pos` is "sandhi/compound", specify "sandhi" or "compound".
5. **Handle Deconstructions (MANDATORY):** If an option key starts with `decon_` or has `meaning_combo: "[Deconstructed]"`, you **MUST** provide a full English translation of that sandhi/compound in the `contextual_meaning` field.
   - **NEVER** leave a `decon_` key with a score of 10 without providing its `contextual_meaning`.
   - **Example:** If `okassa` is deconstructed as `oka + assa`, `contextual_meaning` should be something like "to the house" or "of the dwelling".
6. **Use Existing Examples for Disambiguation:**
   - Each option includes `example_1`/`source_1` and `example_2`/`source_2` — real curated examples from the dictionary that illustrate the exact meaning of that entry.
   - Options marked `db_example_match: true` already have this exact verse as their curated example. **Strongly prefer them** — they represent the editor-validated meaning for this context. Their `ai_score` is pre-set to 10; confirm by scoring them 10 in your output as well.
   - For options without `db_example_match`, use the examples to understand which meaning best fits the verse context before assigning scores.
{disambiguation_block}
### Output Format:
Return a JSON object with translations and a flat map of **scores** keyed by the option `key`.

```json
{{
  "translation": "Fluent English translation",
  "literal_translation": "Literal English translation",{verse_text_field}
  "scores": {{
    "decon_word_0": {{
      "score": 10,
      "contextual_meaning": "Full meaning of the deconstruction",
      "selected_pos": "sandhi"
    }},
    "12345_0": {{
      "score": 10,
      "contextual_meaning": "I would dwell",
      "selected_pos": "verb"
    }}
  }}
}}
```
**CRITICAL:**
- **Keys in `scores` MUST match the `key` values in the Dictionary Context.**
- Only output the JSON object. Do not explain.
"""
    return prompt


def format_markdown_table(enriched_analysis: list[dict[str, Any]]) -> str:
    """
    Reconstruct the Markdown table using the enriched Python structure.
    We iterate through the Python data (which contains all components)
    and simply pick the highest-scored option to display.
    """

    table_rows = [
        "| ID | Word in Sentence | Grammar | Meaning | Construction | Root |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    def add_rows_recursive(option: dict[str, Any], depth: int, parent_pos: str = ""):
        if "components" in option:
            for part_options in option["components"]:
                if not part_options:
                    continue

                # Each part has multiple lookups (homonyms). Pick the best scored one.
                # If all options have the same ai_score (e.g., 0 for sub-components),
                # prefer noun forms when parent is a noun compound.
                best_part = max(
                    part_options,
                    key=lambda x: (
                        x.get("ai_score", 0),
                        # Secondary key: if parent is noun and this option is noun, boost score
                        1
                        if (
                            parent_pos == "noun"
                            and x.get("pos", "") in {"noun", "masc", "fem", "nt"}
                        )
                        else 0,
                    ),
                    default=None,
                )
                if not best_part:
                    continue

                # Format component row
                clean_comp_word = best_part.get("pali", "").replace("- ", "").strip()
                indent_prefix = "- " * depth

                comp_meaning = best_part.get("meaning_combo", "")

                # Cleanup if AI failed to provide a meaning for a deconstruction
                if not comp_meaning and best_part.get("key", "").startswith("decon_"):
                    comp_meaning = "*(AI analysis of deconstruction)*"

                comp_meaning = _clean_meaning(comp_meaning)

                # Prefer grammar (for sandhi/comp vb), fallback to POS (for pure compound parts)
                comp_grammar = best_part.get("grammar") or best_part.get("pos", "")

                if "selected_pos" in best_part and best_part["selected_pos"]:
                    if comp_grammar == "sandhi/compound":
                        comp_grammar = best_part["selected_pos"]

                # Construction Column: prefer compound_construction if available, else construction
                comp_construction = best_part.get("compound_construction", "")
                if not comp_construction:
                    comp_construction = best_part.get("construction", "")
                # Clean up formatting if needed (though analyzer usually sends clean strings for construction)
                comp_construction = comp_construction.replace("<b>", "").replace(
                    "</b>", ""
                )

                table_rows.append(
                    f"| {best_part.get('id', '')} | {indent_prefix}{clean_comp_word} | {comp_grammar} | {comp_meaning} | {comp_construction} | {best_part.get('root_key', '')} |"
                )

                # Only recurse into components of real compounds/sandhi, not etymological breakdowns
                if (
                    best_part.get("compound_type", "")
                    or best_part.get("pos", "") in {"sandhi", "sandhi/compound"}
                    or best_part.get("key", "").startswith("decon_")
                ):
                    add_rows_recursive(best_part, depth + 1, best_part.get("pos", ""))

    for token_data in enriched_analysis:
        word = token_data["word"]
        options = token_data["data"]

        if not options:
            table_rows.append(f"| | {word} | | | | |")
            continue

        # Sort options by AI score (desc), then by completeness/original score
        # We assume 'ai_score' has been merged into the options. Default to 0.
        best_option = max(options, key=lambda x: x.get("ai_score", 0))

        # Determine values to display
        hw_id = best_option.get("id", "")
        meaning = best_option.get("meaning_combo", "")

        # Cleanup if AI failed to provide a meaning for a deconstruction
        if not meaning and best_option.get("key", "").startswith("decon_"):
            meaning = "*(AI analysis of deconstruction)*"

        meaning = _clean_meaning(meaning)

        grammar = best_option.get("grammar", "")

        # Handle POS override
        if "selected_pos" in best_option and best_option["selected_pos"]:
            if grammar == "sandhi/compound":
                grammar = best_option["selected_pos"]

        # Prepend adj POS when grammar exists but doesn't already label the word class
        if (
            best_option.get("pos", "") == "adj"
            and grammar
            and not grammar.startswith("adj")
        ):
            grammar = f"adj, {grammar}"

        # Construction Column: prefer compound_construction if available
        construction = best_option.get("compound_construction", "")
        if not construction:
            construction = best_option.get("construction", "")
        construction = construction.replace("<b>", "").replace("</b>", "")

        table_rows.append(
            f"| {hw_id} | {word} | {grammar} | {meaning} | {construction} | {best_option.get('root_key', '')} |"
        )

        # Start Recursion
        add_rows_recursive(best_option, 1, best_option.get("pos", ""))

    return "\n".join(table_rows)


def merge_ai_selections(
    analysis_data: list[dict[str, Any]], ai_response: dict[str, Any]
) -> dict[str, Any]:
    """
    Merge AI scores and meanings into the analysis data structure.
    Returns a new object containing translation and the enriched analysis.
    """
    # Create a deep copy to avoid mutating the original input
    enriched_analysis = copy.deepcopy(analysis_data)
    scores_map = ai_response.get("scores", {})

    # Helper to traverse and update
    def update_entries(data_list):
        for item in data_list:
            key = item.get("key")
            if key in scores_map:
                update = scores_map[key]
                item["ai_score"] = update.get("score", 0)

                # Apply contextual info if score is positive (implying relevance)
                if update.get("score", 0) > 0:
                    if "contextual_meaning" in update:
                        item["meaning_combo"] = update["contextual_meaning"]
                    if "selected_pos" in update:
                        item["selected_pos"] = update["selected_pos"]
            else:
                item["ai_score"] = 0

            # Recursively update components
            if "components" in item:
                for comp_list in item["components"]:
                    if isinstance(comp_list, list):
                        update_entries(comp_list)

    for word_obj in enriched_analysis:
        update_entries(word_obj["data"])

    return {
        "translation": ai_response.get("translation", ""),
        "literal_translation": ai_response.get("literal_translation", ""),
        "verse_text": ai_response.get("verse_text", ""),
        "analysis": enriched_analysis,
    }
