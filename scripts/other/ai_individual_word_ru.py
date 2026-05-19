#!/usr/bin/env python3
"""Generate AI translations into Russian for a given Pali word."""

import csv
from pathlib import Path
from typing import Optional

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.paths import ProjectPaths
from tools.date_and_time import year_month_day_hour_minute_dash
from tools.printer import printer as pr

from tools.ai_related import (
    load_translation_examples,
    replace_abbreviations,
    handle_ai_response,
    get_ai_client,
    print_ai_config,
    generate_messages_for_meaning,
    generate_messages_for_notes,
    generate_messages_for_english_meaning,
)

from tools.paths_dps import DPSPaths


pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)
date = year_month_day_hour_minute_dash()


def fetch_id(db_session, id_to_check: int) -> Optional[DpdHeadword]:
    """Get id from db."""

    if not id_to_check:  # Check if id_or_lemma_1 is empty
        pr.red("no id to check")
        return None

    query = db_session.query(DpdHeadword).filter(DpdHeadword.id == id_to_check).first()
    if query:
        return query


# ai related
def translate_with_ai(dpspth, id_to_check, mode, synonyms=False):
    # Get the content of window "meaning_in"
    pali_word = fetch_id(db_session, id_to_check)
    if not pali_word:
        pr.red(f"ID {id_to_check} not found")
        return

    lemma_1 = pali_word.lemma_1
    meaning = pali_word.meaning_1
    pos = pali_word.pos
    grammar = pali_word.grammar
    sentence = pali_word.example_1
    notes = pali_word.notes

    pr.green_tmr(f"translating {lemma_1} ({pos})")

    pos_example_map = load_translation_examples(dpspth)
    translation_example = pos_example_map.get(pos, "")

    grammar_orig = grammar
    grammar = replace_abbreviations(grammar)

    if mode == "meaning":
        messages = generate_messages_for_meaning(
            lemma_1, grammar, meaning, sentence, translation_example, synonyms
        )
    elif mode == "note":
        messages = generate_messages_for_notes(lemma_1, grammar, notes)
    elif mode == "english":
        messages = generate_messages_for_english_meaning(lemma_1, grammar, sentence)
    else:
        pr.no("invalid mode")
        raise ValueError(f"Invalid mode: {mode}")

    # Get appropriate client and handle response
    client = get_ai_client()
    print_ai_config()
    suggestion, error_string = handle_ai_response(client, messages)

    if error_string:
        pr.red(error_string)
    elif suggestion:
        suggestion_str = suggestion.get("content", "") if suggestion is not None else ""
        pr.white(suggestion_str)
        pr.yes("ok")

        # writing history
        if mode == "meaning":
            write_suggestions_to_csv(
                dpspth.ai_ru_suggestion_history_path,
                lemma_1,
                grammar_orig,
                grammar,
                meaning,
                suggestion_str,
            )
        elif mode == "note":
            write_suggestions_to_csv(
                dpspth.ai_ru_notes_suggestion_history_path,
                lemma_1,
                grammar_orig,
                grammar,
                notes,
                suggestion_str,
            )
        elif mode == "english":
            write_suggestions_to_csv(
                dpspth.ai_en_suggestion_history_path,
                lemma_1,
                grammar_orig,
                grammar,
                sentence,
                suggestion_str,
            )
        else:
            raise ValueError(f"Invalid mode: {mode}")


def write_suggestions_to_csv(
    file_name, lemma_1, grammar_orig, grammar, original, suggestion
):
    file_path = Path(file_name)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow([lemma_1, grammar_orig, grammar, original, suggestion])


if __name__ == "__main__":
    pr.tic()
    pr.yellow_title("Translating word with the help of AI")

    id_input = input("please provide id: ")
    if id_input:
        id_to_check = int(id_input)

        #! for russian meaning
        translate_with_ai(dpspth, id_to_check, "meaning")

        #! for russian synonyms
        # translate_with_ai(dpspth, id_to_check, "meaning", True)

        #! for russian notes
        # translate_with_ai(dpspth, id_to_check, "note")

        #! for english meaning
        # translate_with_ai(dpspth, id_to_check, "english")

    pr.toc()
