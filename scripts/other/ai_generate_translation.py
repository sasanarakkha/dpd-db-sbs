#!/usr/bin/env python3

"""Generate AI translations for Pāḷi headwords in multiple languages (Russian, Tamil, etc.) and persist to database or export as JSONL batch prompts."""

import os
import json
import glob
import re

from typing import List, Dict

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Russian, Tamil

from tools.paths import ProjectPaths
from tools.meaning_construction import make_meaning_combo
from tools.date_and_time import year_month_day_hour_minute_dash

from tools.ai_related import (
    load_translation_examples,
    replace_abbreviations,
    generate_messages_for_meaning,
    generate_messages_for_notes,
    generate_messages_for_meaning_lit,
    generate_messages_for_meaning_ta,
    load_ai_config,
)
from tools.ai_manager import AIManager
from tools.printer import printer as pr

from tools.paths_dps import DPSPaths

from sqlalchemy import and_, or_, null
from sqlalchemy.orm import joinedload


pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)
date = year_month_day_hour_minute_dash()

ai_manager = AIManager()
api_key, provider, model = load_ai_config()

# Language routing configuration for meaning mode
LANG_CONFIG = {
    "ru": {
        "orm_model": Russian,
        "rel_name": "ru",
        "field_name": "ru_meaning_raw",
        "prompt_builder": generate_messages_for_meaning,
    },
    "ta": {
        "orm_model": Tamil,
        "rel_name": "ta",
        "field_name": "ta_meaning",
        "prompt_builder": generate_messages_for_meaning_ta,
    },
}


def remove_irrelevant(limit: int, lang: str = "ru"):
    # Query the database to fetch words based on language
    if lang == "ru":
        db = (
            db_session.query(DpdHeadword)
            .join(Russian)
            .filter(
                or_(
                    and_(
                        Russian.id != "",
                        Russian.ru_meaning_raw == "",
                        Russian.ru_meaning == "",
                    ),
                    and_(
                        Russian.id != "",
                        Russian.ru_meaning == "",
                        Russian.ru_meaning_raw == "",
                    ),
                )
            )
            .all()
        )
    elif lang == "ta":
        db = (
            db_session.query(DpdHeadword)
            .join(Tamil)
            .filter(Tamil.ta_meaning != "")
            .all()
        )
        # Filter for those containing Roman characters in ta_meaning
        db = [word for word in db if re.search(r"[a-zA-Z]", word.ta.ta_meaning)]
    else:
        raise ValueError(f"Unsupported language: {lang}")

    total_row_count = len(db)
    db = db[:limit]

    print(f"Rows filtered for the process ({lang}): {len(db)} / {total_row_count}")

    # Remove the filtered rows from the respective table
    for word in db:
        if lang == "ru":
            db_session.delete(word.ru)
        elif lang == "ta":
            db_session.delete(word.ta)

    # Commit the changes
    db_session.commit()


def filter_words_for_translation(
    mode, limit: int, lang: str = "ru"
) -> List[DpdHeadword]:
    """Filter words that need translation for specified language."""

    # Get language-specific configuration
    if lang not in LANG_CONFIG:
        raise ValueError(f"Unsupported language: {lang}")

    lang_cfg = LANG_CONFIG[lang]
    orm_model = lang_cfg["orm_model"]

    if mode == "meaning":
        #! for filling those which does not have language table and fill the conditions

        db = (
            db_session.query(DpdHeadword)
            .outerjoin(orm_model, DpdHeadword.id == orm_model.id)
            .filter(
                and_(
                    # DpdHeadword.meaning_1 != "",
                    or_(DpdHeadword.meaning_1 != "", DpdHeadword.meaning_2 != ""),
                    or_(
                        orm_model.id.is_(null()),
                        getattr(orm_model, lang_cfg["field_name"]).is_(None),
                    ),
                )
            )
            .order_by(DpdHeadword.ebt_count.desc())
            .all()
        )

        #! for filling empty rows in Russian table

        # db = db_session.query(DpdHeadword).outerjoin(
        #     Russian, DpdHeadword.id == Russian.id
        #         ).filter(
        #                 Russian.id != '',
        #                 Russian.ru_meaning == '',
        #                 Russian.ru_meaning_raw == '',
        #                 ).order_by(DpdHeadword.ebt_count.desc()).all()

        #! for filling those which have lower model of gpt:

        # # Call the functions to read IDs from the TSV and json files to exclude
        # exclude_ids_tsv: set[str] = read_exclude_ids_from_tsv(f"{dpspth.ai_translated_dir}/{hight_model}.tsv")
        # exclude_ids_json: set[str] = read_exclude_ids_from_json(dpspth.ai_from_batch_api_dir)
        # exclude_ids = exclude_ids_tsv | exclude_ids_json
        # print(f"excluded words {len(exclude_ids)}")

        # # Add the conditions to the query
        # db = db_session.query(DpdHeadword).outerjoin(
        #     Russian, DpdHeadword.id == Russian.id
        #     ).filter(
        #         and_(
        #             DpdHeadword.meaning_1 != '',
        #             # DpdHeadword.example_1 != '',
        #             Russian.ru_meaning_raw != '',
        #             # func.length(Russian.ru_meaning_raw) > 20,
        #             Russian.ru_meaning == '',
        #             ~DpdHeadword.id.in_(exclude_ids)
        #         )
        #     ).order_by(DpdHeadword.ebt_count.desc()).all()

    if mode == "lit":
        #! filter for lit meaning
        db = (
            db_session.query(DpdHeadword)
            .outerjoin(Russian, DpdHeadword.id == Russian.id)
            .filter(
                and_(
                    DpdHeadword.meaning_lit != "",
                    Russian.ru_meaning != "",
                    Russian.ru_meaning_lit == "",
                )
            )
            .order_by(DpdHeadword.ebt_count.desc())
            .all()
        )

    if mode == "note":
        #! for filling notes those which has Russian table and does not have ru_notes
        db = (
            db_session.query(DpdHeadword)
            .outerjoin(Russian, DpdHeadword.id == Russian.id)
            .options(joinedload(DpdHeadword.ru))
            .filter(
                and_(
                    # DpdHeadword.meaning_1 != '',
                    # DpdHeadword.example_1 != '',
                    DpdHeadword.notes != "",
                    Russian.ru_notes == "",
                ),
                or_(
                    Russian.ru_meaning != "",
                    Russian.ru_meaning_raw != "",
                ),
            )
            .order_by(DpdHeadword.ebt_count.desc())
            .all()
        )

    total_row_count = len(db)
    db = db[:limit]

    print(f"Rows filtered for the process: {len(db)} / {total_row_count}")

    return db


def create_translation_prompt(word: DpdHeadword, mode, lang: str = "ru") -> Dict:
    """Create a translation prompt for a given word."""
    pos_example_map = load_translation_examples(dpspth, lang=lang)
    meaning = make_meaning_combo(word)
    example = word.example_1 if word.example_1 else ""
    translation_example = pos_example_map.get(word.pos, "")
    grammar = replace_abbreviations(word.grammar)

    if mode == "meaning":
        if lang not in LANG_CONFIG:
            raise ValueError(f"Unsupported language: {lang}")
        prompt_builder = LANG_CONFIG[lang]["prompt_builder"]
        messages = prompt_builder(
            word.lemma_1, grammar, meaning, example, translation_example
        )
    elif mode == "lit":
        messages = generate_messages_for_meaning_lit(
            word.lemma_1,
            grammar,
            word.meaning_lit,
            word.ru.ru_meaning if word.ru else "",
        )
    elif mode == "note":
        messages = generate_messages_for_notes(word.lemma_1, grammar, word.notes)

    return {
        "custom_id": f"request-{word.id}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {"model": model, "messages": messages},
    }


def translate(
    lemma_1, grammar, pos, meaning, sentence, notes, mode, lang: str = "ru"
) -> str | None:
    pos_example_map = load_translation_examples(dpspth, lang=lang)
    translation_example = pos_example_map.get(pos, "")
    grammar = replace_abbreviations(grammar)

    if mode == "meaning":
        if lang not in LANG_CONFIG:
            raise ValueError(f"Unsupported language: {lang}")
        prompt_builder = LANG_CONFIG[lang]["prompt_builder"]
        messages = prompt_builder(
            lemma_1, grammar, meaning, sentence, translation_example
        )

    elif mode == "lit":
        # For lit mode, we need the ru_meaning to check if translation is already present
        messages = generate_messages_for_meaning_lit(
            lemma_1, grammar, meaning, sentence
        )

    elif mode == "note":
        messages = generate_messages_for_notes(lemma_1, grammar, notes)
    else:
        raise ValueError(f"Invalid mode: {mode}")

    sys_content = messages[0]["content"]
    user_content = messages[1]["content"]
    response = ai_manager.request(prompt=user_content, prompt_sys=sys_content)
    if response.content is None:
        pr.red(response.status_message)
        return None
    if mode == "meaning":
        return response.content
    elif mode == "lit":
        return response.content
    elif mode == "note":
        return f"[пер. ИИ] {response.content}"
    else:
        raise ValueError(f"Invalid mode: {mode}")


def save_prompts_to_json(prompts: List[Dict], filename):
    """Save prompts to a JSON file for Batch API use."""
    with open(filename, "w", encoding="utf-8") as f:
        for prompt in prompts:
            json.dump(prompt, f, ensure_ascii=False)
            f.write("\n")  # Add newline between JSON objects
    print(f"prompts saved to {filename}")


def make_json(mode, limit: int, lang: str = "ru"):
    words = filter_words_for_translation(mode, limit, lang=lang)
    prompts = [create_translation_prompt(word, mode, lang=lang) for word in words]

    file_name = os.path.join(dpspth.ai_for_batch_api_dir, f"{mode}-{lang}-{date}.jsonl")
    save_prompts_to_json(prompts, file_name)


def translation_generate(mode, limit: int, lang: str = "ru"):
    words = filter_words_for_translation(mode, limit, lang=lang)
    for word in words:
        meaning_result = translate(
            word.lemma_1,
            word.grammar,
            word.pos,
            make_meaning_combo(word),
            word.example_1 or "",
            word.notes or "",
            mode,
            lang=lang,
        )
        if meaning_result:
            if mode == "meaning":
                if lang not in LANG_CONFIG:
                    raise ValueError(f"Unsupported language: {lang}")

                lang_cfg = LANG_CONFIG[lang]
                orm_model = lang_cfg["orm_model"]
                field_name = lang_cfg["field_name"]

                existing_row = (
                    db_session.query(orm_model).filter(orm_model.id == word.id).first()
                )
                if not existing_row:
                    new_row = orm_model(id=word.id)
                    setattr(new_row, field_name, meaning_result)
                    db_session.add(new_row)
                else:
                    setattr(existing_row, field_name, meaning_result)

                db_session.commit()

                print(f"{word.id}, {word.ebt_count} {word.lemma_1} {meaning_result}")

                tsv_path = dpspth.ai_translated_dir / f"{model}-{lang}.tsv"
                tsv_path.parent.mkdir(parents=True, exist_ok=True)
                with open(tsv_path, "a", encoding="utf-8") as file:
                    file.write(f"{word.id}\t{word.lemma_1}\t{meaning_result}\n")

            elif mode == "lit":
                existing_russian = (
                    db_session.query(Russian).filter(Russian.id == word.id).first()
                )
                if existing_russian:
                    existing_russian.ru_meaning_lit = meaning_result
                    db_session.commit()
                    print(
                        f"{word.id}, {word.ebt_count} {word.lemma_1} {meaning_result}"
                    )

            if mode == "note":
                word.ru.ru_notes = meaning_result

                db_session.commit()

                print(f"{word.id}, {word.ebt_count} {word.lemma_1} {meaning_result}")


def read_exclude_ids_from_tsv(file_path) -> set[str]:
    exclude_ids = set()
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            id = line.split("\t")[0]
            exclude_ids.add(id)
    return exclude_ids


def read_exclude_ids_from_json(
    dir_path, mode: str = "meaning", lang: str = "ru"
) -> set[int]:
    """Read queued IDs from JSONL batch files. Extracts numeric ID from custom_id field like 'request-12345'."""
    exclude_ids: set[int] = set()
    # Find all JSONL files in the directory (match pattern with language for filtering if needed)
    json_files = glob.glob(f"{dir_path}/*.jsonl")

    # Read each JSONL file and extract the IDs from custom_id field
    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                try:
                    # Decode each JSON object
                    data = json.loads(line)
                    # Extract the ID from custom_id field (format: "request-{id}")
                    custom_id = data.get("custom_id", "")
                    if custom_id and custom_id.startswith("request-"):
                        try:
                            numeric_id = int(custom_id.split("-", 1)[1])
                            exclude_ids.add(numeric_id)
                        except (ValueError, IndexError):
                            # Skip malformed custom_id
                            pass
                except json.JSONDecodeError:
                    # Safely ignore malformed JSON lines
                    pass

    return exclude_ids


if __name__ == "__main__":
    print("Translating with the help of AI")

    limit: int = 1

    # lang: str = "ta"
    lang: str = "ru"

    # remove_irrelevant(limit, lang=lang)

    translation_generate("meaning", limit, lang=lang)

    # translation_generate("note", limit, lang=lang)

    # make_json("meaning", limit, lang=lang)

    # make_json("note", limit, lang=lang)

    # make_json("lit", limit, lang=lang)
