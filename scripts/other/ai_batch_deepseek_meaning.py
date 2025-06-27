#!/usr/bin/env python3

"""making ai generated translation into Russian and saving to db using batch requests"""

import os
import json
import pandas as pd
import glob

from typing import List, Dict, Any

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Russian

from tools.paths import ProjectPaths
from tools.meaning_construction import make_meaning_combo
from tools.date_and_time import year_month_day_hour_minute_dash

from tools.ai_related import (
    load_translation_examples,
    replace_abbreviations,
    get_ai_client,
    # These are not directly used in batch_processing, but their logic is integrated
    # generate_messages_for_meaning,
    # generate_messages_for_notes
)

from tools.ai_llm_factory import LLMFactory
from tools.configger import config_read

from tools.paths_dps import DPSPaths

from sqlalchemy import and_, or_, null
from sqlalchemy.orm import joinedload


pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)
date = year_month_day_hour_minute_dash()

# --- Configuration ---
provider = "deepseek"
model = "deepseek-chat" # or "deepseek-reasoner"

# --- LLM Initialization (from ai_sentences_extracting.py) ---
DEEPSEEK_CACHE_DIR = "shared_data/deepseek_cache"
os.makedirs(DEEPSEEK_CACHE_DIR, exist_ok=True)

if config_read("apis", "deepseek"):
    DEEPSEEK_API_KEY = config_read("apis", "deepseek")
else:
    raise ValueError("SBS_DEEPSEEK_API_KEY not found in environment variables.")

deepseek_llm_instance = LLMFactory("deepseek", "langchain", "deepseek-chat", DEEPSEEK_API_KEY, 0.7).get_llm() # type: ignore

# --- Prompt Definitions for Batch API ---
# System prompt for meaning translation
SYSTEM_PROMPT_RU_MEANING = """
You are an AI assistant specialized in Pali language processing and Russian translation.
Your task is to translate the provided Pali word's meaning, grammar, and an example sentence into natural and accurate Russian.

Output MUST be a JSON object with the following structure:
{
    "id": "<Original word ID>",
    "pali": "<Original Pali word>",
    "ru_meaning_raw": "<Translated Russian meaning>",
    "ru_example_raw": "<Translated Russian example sentence>"
}

Instructions:
1. Translate the 'meaning' and 'grammar' into a concise Russian meaning.
2. Translate the 'example_sentence' into Russian. If 'example_sentence' is empty, set "ru_example_raw" to an empty string.
3. Ensure the translation is contextually appropriate for a Russian speaker.
4. Do NOT include any additional text or markdown outside the JSON object.
"""

# User prompt template for meaning translation
USER_PROMPT_RU_MEANING_BATCH_TEMPLATE = """
Translate the following:
Pali word: "{pali_word}"
Grammar: "{grammar}"
Meaning: "{meaning}"
Example sentence: "{example_sentence}"

Output in JSON format.
"""

# System prompt for notes translation
SYSTEM_PROMPT_RU_NOTES = """
You are an AI assistant specialized in Pali language processing and Russian translation.
Your task is to translate the provided Pali word's notes into natural and accurate Russian.

Output MUST be a JSON object with the following structure:
{
    "id": "<Original word ID>",
    "pali": "<Original Pali word>",
    "ru_notes": "<Translated Russian notes>"
}

Instructions:
1. Translate the 'notes' into Russian.
2. Prefix the translated notes with "[пер. ИИ] ".
3. Ensure the translation is contextually appropriate for a Russian speaker.
4. Do NOT include any additional text or markdown outside the JSON object.
"""

# User prompt template for notes translation
USER_PROMPT_RU_NOTES_BATCH_TEMPLATE = """
Translate the following notes:
Pali word: "{pali_word}"
Notes: "{notes}"

Output in JSON format.
"""


def filter_words_for_translation(mode: str, limit: int) -> List[DpdHeadword]:
    """Filter words that need translation based on mode (meaning or notes)."""
    if mode == "meaning":
        db_query = db_session.query(DpdHeadword).outerjoin(
            Russian, DpdHeadword.id == Russian.id
        ).filter(
            DpdHeadword.meaning_1 != '',
            or_(
                Russian.ru_meaning_raw.is_(None),
                Russian.ru_meaning_raw == '',
                Russian.id.is_(null())
            )
        ).order_by(DpdHeadword.ebt_count.desc())
    elif mode == "note":
        db_query = db_session.query(DpdHeadword).outerjoin(
            Russian, DpdHeadword.id == Russian.id
        ).options(
            joinedload(DpdHeadword.ru)
        ).filter(
            DpdHeadword.notes != '',
            Russian.ru_notes.is_(None) | (Russian.ru_notes == ''),
            Russian.id.isnot(null()) # Ensure Russian table entry exists for notes
        ).order_by(DpdHeadword.ebt_count.desc())
    else:
        raise ValueError(f"Invalid mode: {mode}. Choose 'meaning' or 'note'.")

    words = db_query.limit(limit).all()
    total_row_count = db_query.count() # Get total count before limiting
    print(f"Rows filtered for the process: {len(words)} / {total_row_count}")
    return words


def prepare_batch_input(words: List[DpdHeadword], mode: str) -> List[Dict[str, Any]]:
    """Prepare input dictionaries for the batch API call."""
    batch_input_for_llm = []
    pos_example_map = load_translation_examples(dpspth)

    for word in words:
        grammar = replace_abbreviations(word.grammar)
        pali_word = word.lemma_1
        word_id = str(word.id)

        if mode == "meaning":
            meaning = make_meaning_combo(word)
            example = word.example_1 if word.example_1 else ""
            translation_example = pos_example_map.get(word.pos, "") # Not directly used in the prompt template
            batch_input_for_llm.append({
                "id": word_id,
                "pali_word": pali_word,
                "grammar": grammar,
                "meaning": meaning,
                "example_sentence": example
            })
        elif mode == "note":
            notes = word.notes if word.notes else ""
            batch_input_for_llm.append({
                "id": word_id,
                "pali_word": pali_word,
                "notes": notes
            })
    return batch_input_for_llm


def run_batch_translation(mode: str, limit: int):
    """Runs batch translation using DeepSeek and updates the database."""
    print(f"\n--- Running Batch DeepSeek Inference for {mode} ---")

    words_to_translate = filter_words_for_translation(mode, limit)
    if not words_to_translate:
        print(f"No words found needing {mode} translation.")
        return

    batch_inputs = prepare_batch_input(words_to_translate, mode)

    if mode == "meaning":
        system_prompt = SYSTEM_PROMPT_RU_MEANING
        user_prompt_template = USER_PROMPT_RU_MEANING_BATCH_TEMPLATE
    elif mode == "note":
        system_prompt = SYSTEM_PROMPT_RU_NOTES
        user_prompt_template = USER_PROMPT_RU_NOTES_BATCH_TEMPLATE

    print(f"Prepared {len(batch_inputs)} items for DeepSeek batch processing.")

    try:
        batch_results_raw = deepseek_llm_instance.batch_processing(
            system_prompt,
            user_prompt_template,
            batch_inputs
        )

        for i, result_dict in enumerate(batch_results_raw):
            word_id = result_dict.get("id")
            pali_word = result_dict.get("pali")

            word_obj = next((w for w in words_to_translate if str(w.id) == word_id), None)

            if word_obj:
                if mode == "meaning":
                    ru_meaning_raw = result_dict.get("ru_meaning_raw", "")

                    existing_russian = db_session.query(Russian).filter(Russian.id == word_obj.id).first()
                    if not existing_russian:
                        new_russian = Russian(id=word_obj.id, ru_meaning_raw=ru_meaning_raw)
                        db_session.add(new_russian)
                    else:
                        existing_russian.ru_meaning_raw = ru_meaning_raw

                    print(f"Translated meaning for {pali_word} (ID: {word_id})")
                    with open(f'{dpspth.ai_translated_dir}/{model}_meaning.tsv', 'a', encoding='utf-8') as f:
                        f.write(f"{word_id}\t{pali_word}\t{ru_meaning_raw}\t\n")

                elif mode == "note":
                    ru_notes = result_dict.get("ru_notes", "")
                    if word_obj.ru: # Ensure the Russian object exists
                        word_obj.ru.ru_notes = ru_notes
                        print(f"Translated notes for {pali_word} (ID: {word_id})")
                        with open(f'{dpspth.ai_translated_dir}/{model}_notes.tsv', 'a', encoding='utf-8') as f:
                            f.write(f"{word_id}\t{pali_word}\t{ru_notes}\n")
                    else:
                        print(f"Skipping notes for {pali_word} (ID: {word_id}): No existing Russian entry.")

            db_session.commit()

    except Exception as e:
        print(f"\nAn error occurred during batch processing: {e}")
        db_session.rollback()
    finally:
        db_session.close()

    print("\n--- Batch Translation Finished ---")


if __name__ == "__main__":
    # --- Script Usage Guide ---
    # Set the limit for how many words to process in a batch.
    # Choose the mode: "meaning" to translate meanings and examples,
    # or "note" to translate notes.
    # --- End Script Usage Guide ---

    limit: int = 10  # Adjust this limit based on your needs and API rate limits

    # Run for meaning translation
    run_batch_translation("meaning", limit)

    # Run for notes translation (uncomment to enable)
    # run_batch_translation("note", limit)