#!/usr/bin/env python3

"""making ai generated translation into Russian of one given word"""

import csv

from typing import Optional

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.paths import ProjectPaths
from tools.date_and_time import year_month_day_hour_minute_dash

from tools.ai_related import (
    load_translation_examples,
    replace_abbreviations,
    handle_ai_response,
    get_ai_client,
    generate_messages_for_meaning,
    generate_messages_for_notes,
    generate_messages_for_english_meaning
)

from tools.paths_dps import DPSPaths    


pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)
date = year_month_day_hour_minute_dash()


# models openai
# model="gpt-5"
# model="gpt-5-mini"
# model="gpt-4.1"
model="gpt-4o-mini" #cheapest
# model="gpt-4.1-mini"
# hight_model=""

# models deepseek
# model = "deepseek-reasoner"
# model ="deepseek-chat"


def fetch_id(db_session, id_to_check: int) -> Optional[DpdHeadword]:
    """Get id from db."""

    if not id_to_check:  # Check if id_or_lemma_1 is empty
        print("no id to check")
        return None
        
    query = db_session.query(DpdHeadword).filter(
        DpdHeadword.id == id_to_check).first()
    if query:
        return query


# ai related
def translate_with_ai(dpspth, id_to_check, mode, provider, synonyms=False):
    # Get the content of window "meaning_in"
    pali_word = fetch_id(db_session, id_to_check)
    if pali_word:
        lemma_1 = pali_word.lemma_1
        meaning = pali_word.meaning_1
        pos = pali_word.pos
        grammar = pali_word.grammar
        sentence = pali_word.example_1
        notes = pali_word.notes

    pos_example_map = load_translation_examples(dpspth)
    translation_example = pos_example_map.get(pos, "")

    if provider == "openai":
        model = "gpt-4o-mini" 
    elif provider == "deepseek":
        model = "deepseek-chat"
    grammar_orig = grammar
    grammar = replace_abbreviations(grammar)

    if mode == "meaning":
        messages = generate_messages_for_meaning(lemma_1, grammar, meaning, sentence, translation_example, synonyms)
    elif mode == "note":
        messages = generate_messages_for_notes(lemma_1, grammar, notes)
    elif mode == "english":
        messages = generate_messages_for_english_meaning(lemma_1, grammar, sentence)
    else:
        raise ValueError(f"Invalid mode: {mode}")
    # print(f"messages {messages}")


    # Get appropriate client and handle response
    client = get_ai_client(provider)
    suggestion, error_string = handle_ai_response(client, messages, model, provider)

    if error_string:
        print(error_string)
    elif suggestion:
        suggestion_str = suggestion.get("content", "") if suggestion is not None else ""
        print(suggestion_str)
        # writing history
        if mode == "meaning":
            write_suggestions_to_csv(dpspth.ai_ru_suggestion_history_path, lemma_1, grammar_orig, grammar, meaning, suggestion_str)
        elif mode == "note":
            write_suggestions_to_csv(dpspth.ai_ru_notes_suggestion_history_path, lemma_1, grammar_orig, grammar, notes, suggestion_str)
        elif mode == "english":
            write_suggestions_to_csv(dpspth.ai_en_suggestion_history_path, lemma_1, grammar_orig, grammar, sentence, suggestion_str)
        else:
            raise ValueError(f"Invalid mode: {mode}")



def write_suggestions_to_csv(file_name, lemma_1, grammar_orig, grammar, original, suggestion):
    with open(file_name, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([lemma_1, grammar_orig, grammar, original, suggestion])



if __name__ == "__main__":

    # Configuration
    # provider = "deepseek"
    provider = "openai"

    print("Translationg word the help of AI")

    id_to_check = input("please provide id")

    #! for russian meaning
    translate_with_ai(dpspth, id_to_check, "meaning", provider)

    #! for russian synonyms
    # translate_with_ai(dpspth, id_to_check, "meaning", provider, True)

    #! for russian notes
    # translate_with_ai(dpspth, id_to_check, "note", provider)

    #! for english meaning
    # translate_with_ai(dpspth, id_to_check, "english", provider)





