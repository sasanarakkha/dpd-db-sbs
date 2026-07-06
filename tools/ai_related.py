"""Builds AI translation prompts (messages) and grammar-abbreviation helpers."""

import csv
import re

from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths

pth = ProjectPaths()


def load_translation_examples(dpspth: DPSPaths, lang: str = "ru") -> dict[str, str]:
    """Load the pos-examples mapping from a TSV file into a dictionary."""
    pos_examples_map: dict[str, str] = {}
    if lang == "ru":
        path = dpspth.ru_translation_example_path
    elif lang == "ta":
        path = dpspth.ta_translation_example_path
    else:
        raise ValueError(f"Unsupported language: {lang}")
    with path.open("r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter="\t")
        next(reader)  # Skip header row
        for row in reader:
            pos, examples = row[0], row[1]
            pos_examples_map[pos] = examples
    return pos_examples_map


def replace_abbreviations(grammar_string: str) -> str:
    # Clean the grammar string
    cleaned_grammar_string = re.sub(
        r" of [\w\s]+|, pp of [\w\s]+|, prp of [\w\s]+|, ptp of [\w\s]+|, from [\w\s]+|, loc abs|, gen abs|\(.*?\)",
        "",
        grammar_string,
    )

    # TODO consider noun, pp of ... remove pp or make it from pp

    replacements: dict[str, str] = {}
    multi_word_replacements: dict[str, str] = {}

    # Read abbreviations and their full forms into a dictionary
    with pth.abbreviations_tsv_path.open("r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter="\t")
        next(reader)  # skip header
        for row in reader:
            abbrev, full_form = (
                row[0],
                row[1].split(",")[0].strip(),
            )  # select only the first two columns and split by comma
            if " " in abbrev:
                multi_word_replacements[abbrev] = full_form
            else:
                replacements[abbrev] = full_form

    # First, replace multi-word abbreviations
    for abbrev, full_form in multi_word_replacements.items():
        cleaned_grammar_string = re.sub(
            r"\b" + re.escape(abbrev) + r"\b", full_form, cleaned_grammar_string
        )

    # Then, replace single-word abbreviations
    words = re.findall(r"[\w'+&]+|[.,!?;]", cleaned_grammar_string)
    for idx, word in enumerate(words):
        if word in replacements:
            words[idx] = replacements[word]

    # Join the words back into a string
    return " ".join(words)


def generate_messages_for_meaning(
    lemma_1: str,
    grammar: str,
    meaning: str,
    sentence: str,
    translation_example: str = "",
    synonyms: bool = False,
) -> list[dict[str, str]]:
    """Generate messages for translation."""

    system_content = "You are a skilled assistant that translates English text to Russian with grammatical accuracy, contextual relevance, and strict adherence to rules."

    if synonyms:
        synonym_rules = "- Separate synonyms with `;`."
    else:
        synonym_rules = (
            "- Give at most 3 Russian meanings, separated by `;`.\n"
            "        - Each meaning must be semantically distinct — a different sense, nuance, or usage, not a reworded synonym.\n"
            "        - If the English definition expresses only one sense, output exactly one translation: fewer distinct meanings is better than padded near-synonyms."
        )

    user_content = f"""
        Translate the English definition of the Pali term into Russian, following these rules:

        - Translate all bracketed text (e.g., "(gram)" → "(грам)", "(comm)" → "(комм)", "(vinaya)" → "(виная)", "(of weather)" → "(о погоде)").
        {synonym_rules}
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

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def generate_messages_for_notes(
    lemma_1: str, grammar: str, notes: str
) -> list[dict[str, str]]:
    """Generate messages for translation."""

    system_content = "You are a helpful assistant that translates English text to Russian considering the context."

    user_content = f"""
    Translate the English notes into Russian, following these rules:
    - Keep Pali or Sanskrit terms in roman script.
    - Output only the translation of the Notes, without labels like "Перевод" etc, without any comments, without translation of the Grammar and in one line.

                **Pali Term**: {lemma_1}
                **Grammar**: {grammar}
                **Notes**: {notes}
    """

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def generate_messages_for_meaning_ta(
    lemma_1: str,
    grammar: str,
    meaning: str,
    sentence: str,
    translation_example: str = "",
) -> list[dict[str, str]]:
    """Generate messages for Tamil translation of meaning."""

    system_content = "You are a skilled assistant that translates English text to Tamil with grammatical accuracy, contextual relevance, and strict adherence to rules."

    synonym_rules = (
        "- Give at most 3 Tamil meanings, separated by `;`.\n"
        "        - Each meaning must be semantically distinct — a different sense, nuance, or usage, not a reworded synonym.\n"
        "        - If the English definition expresses only one sense, output exactly one translation: fewer distinct meanings is better than padded near-synonyms."
    )

    user_content = f"""
        Translate the English definition of the Pali term into Tamil, following these rules:

        - Translate all bracketed text (e.g., "(gram)" → "(இலக்கணம்)", "(of weather)" → "(வெயிலைப் பற்றி)").
        {synonym_rules}
        - Match the grammatical structure of the Pali term (noun, verb, etc.).
        - Use lowercase unless it's a proper noun.
        - Retain clarifications if any.
        - Translate idioms to Tamil equivalents.
        - Ensure no English remains untranslated, including within brackets.
        - Output only the translation of the Definition, without labels, without any comments, without translation of the Grammar and in one line.

        **Pali Term**: {lemma_1}
        **Grammar**: {grammar}
        **Definition**: {meaning}
    """

    if sentence:
        user_content += f"\n- Consider Pali context: {sentence}"

    if translation_example:
        user_content += f"\n- Match this example format: {translation_example}"

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def generate_messages_for_meaning_lit(
    lemma_1: str, grammar: str, meaning_lit: str, ru_meaning: str = ""
) -> list[dict[str, str]]:
    """Generate messages for literal meaning translation with duplication check."""

    system_content = "You are a skilled assistant that translates English text to Russian with grammatical accuracy, contextual relevance, and strict adherence to rules."

    user_content = f"""
        Translate the English literal definition of the Pali term into Russian, following these rules:

        - Translate all bracketed text (e.g., "(of weather)" → "(о погоде)").
        - Match the grammatical structure of the Pali term (noun, verb, etc.).
        - Use lowercase unless it's a proper noun.
        - Retain clarifications if any (e.g., "(of trap) laid down" → "(о капкане) установленный").
        - Translate idioms to Russian equivalents.
        - Ensure no English remains untranslated, including within brackets.
        - Output only the translation of the literal Definition, without labels like "Перевод" etc, without any comments, without translation of the Grammar and in one line.

        **IMPORTANT**: If the literal translation is already contained in the existing Russian meaning, return only an empty string "" without any translation or comments.

        **Pali Term**: {lemma_1}
        **Grammar**: {grammar}
        **Literal Definition**: {meaning_lit}
        **Existing Russian Meaning**: {ru_meaning}
    """

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
