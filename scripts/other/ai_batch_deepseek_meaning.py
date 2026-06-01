#!/usr/bin/env python3
"""Generate AI translations into Russian using DeepSeek Batch requests and update the database."""

from pathlib import Path
from typing import List, Dict, Any

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Russian

from tools.paths import ProjectPaths
from tools.meaning_construction import make_meaning_combo
from tools.date_and_time import year_month_day_hour_minute_dash
from tools.printer import printer as pr

from tools.ai_related import replace_abbreviations

from tools.ai_llm_factory import LLMFactory
from tools.configger import config_read

from tools.paths_dps import DPSPaths

from sqlalchemy import or_, null
from sqlalchemy.orm import joinedload


pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)
date = year_month_day_hour_minute_dash()

# --- Configuration ---
provider = "deepseek"
model = "deepseek-chat"  # or "deepseek-reasoner"

# --- LLM Initialization ---
DEEPSEEK_CACHE_DIR = Path("shared_data/deepseek_cache")
DEEPSEEK_CACHE_DIR.mkdir(parents=True, exist_ok=True)

api_key = config_read("apis", "deepseek")
if api_key:
    DEEPSEEK_API_KEY = api_key
else:
    raise ValueError("SBS_DEEPSEEK_API_KEY not found in environment variables.")

deepseek_llm_instance = LLMFactory(
    "deepseek", "langchain", "deepseek-chat", DEEPSEEK_API_KEY, 0.7
).get_llm()  # type: ignore

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
        db_query = (
            db_session.query(DpdHeadword)
            .outerjoin(Russian, DpdHeadword.id == Russian.id)
            .filter(
                DpdHeadword.meaning_1 != "",
                or_(
                    Russian.ru_meaning_raw.is_(None),
                    Russian.ru_meaning_raw == "",
                    Russian.id.is_(null()),
                ),
            )
            .order_by(DpdHeadword.ebt_count.desc())
        )
    elif mode == "note":
        db_query = (
            db_session.query(DpdHeadword)
            .outerjoin(Russian, DpdHeadword.id == Russian.id)
            .options(joinedload(DpdHeadword.ru))
            .filter(
                DpdHeadword.notes != "",
                Russian.ru_notes.is_(None) | (Russian.ru_notes == ""),
                Russian.id.isnot(null()),  # Ensure Russian table entry exists for notes
            )
            .order_by(DpdHeadword.ebt_count.desc())
        )
    else:
        raise ValueError(f"Invalid mode: {mode}. Choose 'meaning' or 'note'.")

    words = db_query.limit(limit).all()
    total_row_count = db_query.count()  # Get total count before limiting
    pr.white(f"Rows filtered for the process: {len(words)} / {total_row_count}")
    return words


def prepare_batch_input(words: List[DpdHeadword], mode: str) -> List[Dict[str, Any]]:
    """Prepare input dictionaries for the batch API call."""
    batch_input_for_llm = []

    for word in words:
        grammar = replace_abbreviations(word.grammar)
        pali_word = word.lemma_1
        word_id = str(word.id)

        if mode == "meaning":
            meaning = make_meaning_combo(word)
            example = word.example_1 if word.example_1 else ""
            batch_input_for_llm.append(
                {
                    "id": word_id,
                    "pali_word": pali_word,
                    "grammar": grammar,
                    "meaning": meaning,
                    "example_sentence": example,
                }
            )
        elif mode == "note":
            notes = word.notes if word.notes else ""
            batch_input_for_llm.append(
                {"id": word_id, "pali_word": pali_word, "notes": notes}
            )
    return batch_input_for_llm


def run_batch_translation(mode: str, limit: int):
    """Runs batch translation using DeepSeek and updates the database."""
    pr.tic()
    pr.green_title(f"Batch DeepSeek Inference for {mode}")

    words_to_translate = filter_words_for_translation(mode, limit)
    if not words_to_translate:
        pr.amber(f"No words found needing {mode} translation.")
        pr.toc()
        return

    batch_inputs = prepare_batch_input(words_to_translate, mode)

    if mode == "meaning":
        system_prompt = SYSTEM_PROMPT_RU_MEANING
        user_prompt_template = USER_PROMPT_RU_MEANING_BATCH_TEMPLATE
    elif mode == "note":
        system_prompt = SYSTEM_PROMPT_RU_NOTES
        user_prompt_template = USER_PROMPT_RU_NOTES_BATCH_TEMPLATE

    pr.white(f"Prepared {len(batch_inputs)} items for DeepSeek batch processing.")

    try:
        pr.green_tmr("batch processing with DeepSeek")
        batch_results_raw = deepseek_llm_instance.batch_processing(
            system_prompt, user_prompt_template, batch_inputs
        )
        pr.yes(len(batch_results_raw))

        for result_dict in batch_results_raw:
            word_id = result_dict.get("id")
            pali_word = result_dict.get("pali")

            word_obj = next(
                (w for w in words_to_translate if str(w.id) == word_id), None
            )

            if word_obj:
                if mode == "meaning":
                    ru_meaning_raw = result_dict.get("ru_meaning_raw", "")

                    existing_russian = (
                        db_session.query(Russian)
                        .filter(Russian.id == word_obj.id)
                        .first()
                    )
                    if not existing_russian:
                        new_russian = Russian(
                            id=word_obj.id, ru_meaning_raw=ru_meaning_raw
                        )
                        db_session.add(new_russian)
                    else:
                        existing_russian.ru_meaning_raw = ru_meaning_raw

                    pr.white(f"Translated meaning for {pali_word} (ID: {word_id})")
                    output_path = (
                        Path(dpspth.ai_translated_dir) / f"{model}_meaning.tsv"
                    )
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "a", encoding="utf-8") as f:
                        f.write(f"{word_id}\t{pali_word}\t{ru_meaning_raw}\t\n")

                elif mode == "note":
                    ru_notes = result_dict.get("ru_notes", "")
                    if word_obj.ru:  # Ensure the Russian object exists
                        word_obj.ru.ru_notes = ru_notes
                        pr.white(f"Translated notes for {pali_word} (ID: {word_id})")
                        output_path = (
                            Path(dpspth.ai_translated_dir) / f"{model}_notes.tsv"
                        )
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, "a", encoding="utf-8") as f:
                            f.write(f"{word_id}\t{pali_word}\t{ru_notes}\n")
                    else:
                        pr.amber(
                            f"Skipping notes for {pali_word} (ID: {word_id}): No existing Russian entry."
                        )

            db_session.commit()

    except Exception as e:
        pr.red(f"An error occurred during batch processing: {e}")
        db_session.rollback()
    finally:
        db_session.close()

    pr.toc()


if __name__ == "__main__":
    limit: int = 10  # Adjust this limit based on your needs and API rate limits

    # Run for meaning translation
    run_batch_translation("meaning", limit)

    # Run for notes translation (uncomment to enable)
    # run_batch_translation("note", limit)
