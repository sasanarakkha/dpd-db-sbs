#!/usr/bin/env python3

"""Generate AI translations for Pāḷi headwords in multiple languages (Russian, Tamil, etc.) and persist to database or export as JSONL batch prompts."""

import argparse
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict

from sqlalchemy import and_, case, null, or_

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Russian, Tamil
from tools.ai_manager import AIManager
from tools.ai_manager import load_models_from_json as load_ai_models_by_kind
from tools.ai_related import (
    generate_messages_for_meaning,
    generate_messages_for_meaning_lit,
    generate_messages_for_meaning_ta,
    generate_messages_for_notes,
    load_translation_examples,
    replace_abbreviations,
)
from tools.date_and_time import year_month_day_hour_minute_dash
from tools.meaning_construction import make_meaning_combo
from tools.meaning_snapshot_ru import remove_ids_from_snapshot
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr

pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)
date = year_month_day_hour_minute_dash()

ai_manager: AIManager | None = None


def get_ai_manager() -> AIManager:
    """Lazily initialize and return AIManager."""
    global ai_manager
    if ai_manager is None:
        ai_manager = AIManager()
    return ai_manager


def load_models_from_json() -> list[tuple[str, str, int, float]]:
    """Flat provider/model list from tools/ai_models.json, sourced from AIManager."""
    models = load_ai_models_by_kind()
    return models["default"] + models["grounded"]


def default_model_name() -> str:
    """First model in the AIManager fallback list, used as a default model id."""
    all_models = load_models_from_json()
    return all_models[0][1] if all_models else "unknown-model"


# Language routing configuration for meaning mode
class LangConfig(TypedDict):
    """Configuration for language-specific translation generation."""

    orm_model: Any
    rel_name: str
    field_name: str
    prompt_builder: Callable[..., list[dict[str, str]]]


LANG_CONFIG: dict[str, LangConfig] = {
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

# generation mode -> checker snapshot files holding verdicts for the regenerated field
SNAPSHOTS_BY_MODE: dict[str, list[Path]] = {
    "meaning": [dpspth.ai_meaning_raw_checked, dpspth.ai_meaning_ru_raw_checked],
    "lit": [dpspth.ai_meaning_lit_checked],
    "note": [dpspth.ai_notes_raw_checked],
}


def remove_irrelevant(
    limit: int | None, lang: str = "ru", dry_run: bool = False
) -> None:
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

    pr.white(f"Rows filtered for the process ({lang}): {len(db)} / {total_row_count}")

    if dry_run:
        pr.amber(f"[DRY-RUN] Would remove {len(db)} rows from {lang} database:")
        for idx, word in enumerate(db, 1):
            pr.white(f"  {idx}/{len(db)} {word.id}, {word.lemma_1}")
        return

    # Remove the filtered rows from the respective table
    for word in db:
        if lang == "ru":
            db_session.delete(word.ru)
        elif lang == "ta":
            db_session.delete(word.ta)

    # Commit the changes
    db_session.commit()


def filter_words_for_translation(
    mode: str, limit: int | None, lang: str = "ru"
) -> list[DpdHeadword]:
    """Filter words that need translation for specified language."""

    # Get language-specific configuration
    if lang not in LANG_CONFIG:
        raise ValueError(f"Unsupported language: {lang}")

    filter_desc = ""

    if mode == "meaning":
        if lang == "ta":
            filter_desc = (
                f"mode: {mode} | lang: {lang} | "
                "filter: (meaning_1 != '' OR meaning_2 != '') AND (Tamil entry is missing OR ta_meaning is empty/null)"
            )
            db = (
                db_session.query(DpdHeadword)
                .outerjoin(Tamil, DpdHeadword.id == Tamil.id)
                .filter(
                    and_(
                        or_(DpdHeadword.meaning_1 != "", DpdHeadword.meaning_2 != ""),
                        or_(
                            Tamil.id.is_(null()),
                            Tamil.ta_meaning.is_(None),
                            Tamil.ta_meaning == "",
                        ),
                    )
                )
                .order_by(
                    case(
                        (
                            and_(
                                DpdHeadword.meaning_1 != "",
                                DpdHeadword.meaning_1.isnot(None),
                            ),
                            0,
                        ),
                        (
                            and_(
                                DpdHeadword.meaning_2 != "",
                                DpdHeadword.meaning_2.isnot(None),
                            ),
                            1,
                        ),
                        else_=2,
                    ),
                    DpdHeadword.ebt_count.desc(),
                )
                .all()
            )
        elif lang == "ru":
            filter_desc = (
                f"mode: {mode} | lang: {lang} | "
                "filter: (meaning_1 != '' OR meaning_2 != '') AND (Russian entry is missing OR both ru_meaning_raw and ru_meaning are empty/null)"
            )
            db = (
                db_session.query(DpdHeadword)
                .outerjoin(Russian, DpdHeadword.id == Russian.id)
                .filter(
                    and_(
                        or_(DpdHeadword.meaning_1 != "", DpdHeadword.meaning_2 != ""),
                        or_(
                            Russian.id.is_(null()),
                            and_(
                                or_(
                                    Russian.ru_meaning_raw.is_(None),
                                    Russian.ru_meaning_raw == "",
                                ),
                                or_(
                                    Russian.ru_meaning.is_(None),
                                    Russian.ru_meaning == "",
                                ),
                            ),
                        ),
                    )
                )
                .order_by(
                    case(
                        (
                            and_(
                                DpdHeadword.meaning_1 != "",
                                DpdHeadword.meaning_1.isnot(None),
                            ),
                            0,
                        ),
                        (
                            and_(
                                DpdHeadword.meaning_2 != "",
                                DpdHeadword.meaning_2.isnot(None),
                            ),
                            1,
                        ),
                        else_=2,
                    ),
                    DpdHeadword.ebt_count.desc(),
                )
                .all()
            )
        else:
            raise ValueError(f"Unsupported language: {lang}")

    elif mode == "lit":
        filter_desc = (
            f"mode: {mode} | lang: {lang} | "
            "filter: (meaning_1 != '' OR meaning_2 != '') AND meaning_lit != '' AND Russian entry exists AND ru_meaning != '' AND ru_meaning_lit is empty/null"
        )
        db = (
            db_session.query(DpdHeadword)
            .join(Russian, DpdHeadword.id == Russian.id)
            .filter(
                and_(
                    or_(DpdHeadword.meaning_1 != "", DpdHeadword.meaning_2 != ""),
                    DpdHeadword.meaning_lit != "",
                    Russian.ru_meaning != "",
                    or_(
                        Russian.ru_meaning_lit.is_(None),
                        Russian.ru_meaning_lit == "",
                    ),
                )
            )
            .order_by(
                case(
                    (
                        and_(
                            DpdHeadword.meaning_1 != "",
                            DpdHeadword.meaning_1.isnot(None),
                        ),
                        0,
                    ),
                    (
                        and_(
                            DpdHeadword.meaning_2 != "",
                            DpdHeadword.meaning_2.isnot(None),
                        ),
                        1,
                    ),
                    else_=2,
                ),
                DpdHeadword.ebt_count.desc(),
            )
            .all()
        )

    elif mode == "note":
        filter_desc = (
            f"mode: {mode} | lang: {lang} | "
            "filter: (meaning_1 != '' OR meaning_2 != '') AND notes != '' AND (Russian entry is missing OR ru_notes is empty/null)"
        )
        db = (
            db_session.query(DpdHeadword)
            .outerjoin(Russian, DpdHeadword.id == Russian.id)
            .filter(
                and_(
                    or_(DpdHeadword.meaning_1 != "", DpdHeadword.meaning_2 != ""),
                    DpdHeadword.notes != "",
                    or_(
                        Russian.id.is_(null()),
                        Russian.ru_notes.is_(None),
                        Russian.ru_notes == "",
                    ),
                )
            )
            .order_by(
                case(
                    (
                        and_(
                            DpdHeadword.meaning_1 != "",
                            DpdHeadword.meaning_1.isnot(None),
                        ),
                        0,
                    ),
                    (
                        and_(
                            DpdHeadword.meaning_2 != "",
                            DpdHeadword.meaning_2.isnot(None),
                        ),
                        1,
                    ),
                    else_=2,
                ),
                DpdHeadword.ebt_count.desc(),
            )
            .all()
        )
    else:
        raise ValueError(f"Invalid mode: {mode}")

    total_row_count = len(db)
    db = db[:limit]

    pr.white(f"Current filter: {filter_desc}")
    pr.white(f"Rows filtered for the process: {len(db)} / {total_row_count}")

    return db


def create_translation_prompt(
    word: DpdHeadword, mode: str, lang: str = "ru", model: str | None = None
) -> dict[str, Any]:
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
    else:
        raise ValueError(f"Invalid mode: {mode}")

    body_model = model if model is not None else default_model_name()
    return {
        "custom_id": f"request-{word.id}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {"model": body_model, "messages": messages},
    }


def translate(
    lemma_1: str,
    grammar: str,
    pos: str,
    meaning: str,
    sentence: str,
    notes: str,
    mode: str,
    lang: str = "ru",
    provider: str | None = None,
    model: str | None = None,
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
    response = get_ai_manager().request(
        prompt=user_content,
        prompt_sys=sys_content,
        provider_preference=provider,
        model=model,
    )
    if response.content is None:
        pr.red(response.status_message)
        return None
    if mode == "meaning" or mode == "lit":
        return response.content
    elif mode == "note":
        return f"[пер. ИИ] {response.content}"
    else:
        raise ValueError(f"Invalid mode: {mode}")


def save_prompts_to_json(prompts: list[dict[str, Any]], filename: str | Path) -> None:
    """Save prompts to a JSON file for Batch API use."""
    with Path(filename).open("w", encoding="utf-8") as f:
        for prompt in prompts:
            json.dump(prompt, f, ensure_ascii=False)
            f.write("\n")
    pr.green(f"prompts saved to {filename}")


def make_json(
    mode: str,
    limit: int | None,
    lang: str = "ru",
    dry_run: bool = False,
    model: str | None = None,
) -> None:
    words = filter_words_for_translation(mode, limit, lang=lang)
    if dry_run:
        pr.amber(f"[DRY-RUN] Would generate prompts for {len(words)} words:")
        for idx, word in enumerate(words, 1):
            pr.white(f"  {idx}/{len(words)} {word.id}, {word.lemma_1}")
        return
    prompts = [
        create_translation_prompt(word, mode, lang=lang, model=model) for word in words
    ]

    file_name = dpspth.ai_for_batch_api_dir / f"{mode}-{lang}-{date}.jsonl"
    save_prompts_to_json(prompts, file_name)


def translation_generate(
    mode: str,
    limit: int | None,
    lang: str = "ru",
    dry_run: bool = False,
    provider: str | None = None,
    model: str | None = None,
) -> None:
    words = filter_words_for_translation(mode, limit, lang=lang)
    if dry_run:
        pr.amber(f"[DRY-RUN] Would process translation for {len(words)} words:")
        for idx, word in enumerate(words, 1):
            pr.white(f"  {idx}/{len(words)} {word.id}, {word.lemma_1}")
        return
    regenerated_ids: set[int] = set()
    total = len(words)
    for idx, word in enumerate(words, 1):
        meaning_result = translate(
            word.lemma_1,
            word.grammar,
            word.pos,
            make_meaning_combo(word),
            word.example_1 or "",
            word.notes or "",
            mode,
            lang=lang,
            provider=provider,
            model=model,
        )
        if meaning_result:
            regenerated_ids.add(word.id)
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

                pr.green(
                    f"{idx}/{total} {word.id}, {word.ebt_count} {word.lemma_1} {meaning_result}"
                )

                tsv_model = model if model is not None else default_model_name()
                tsv_path = dpspth.ai_translated_dir / f"{tsv_model}-{lang}.tsv"
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
                    pr.green(
                        f"{idx}/{total} {word.id}, {word.ebt_count} {word.lemma_1} {meaning_result}"
                    )

            elif mode == "note":
                existing_russian = (
                    db_session.query(Russian).filter(Russian.id == word.id).first()
                )
                if not existing_russian:
                    existing_russian = Russian(id=word.id)
                    db_session.add(existing_russian)
                existing_russian.ru_notes = meaning_result

                db_session.commit()

                pr.green(
                    f"{idx}/{total} {word.id}, {word.ebt_count} {word.lemma_1} {meaning_result}"
                )

    if lang == "ru" and regenerated_ids:
        for snapshot_path in SNAPSHOTS_BY_MODE.get(mode, []):
            removed = remove_ids_from_snapshot(snapshot_path, regenerated_ids)
            if removed:
                pr.white(
                    f"{removed} regenerated IDs dropped from "
                    f"{snapshot_path.name} (will be re-checked)"
                )

    if regenerated_ids:
        project_root = Path(__file__).resolve().parents[3]
        temp_dir = project_root / "temp"
        temp_dir.mkdir(exist_ok=True)
        last_translated_path = temp_dir / "last_translated.json"
        try:
            with open(last_translated_path, "w", encoding="utf-8") as f:
                json.dump({"lang": lang, "ids": sorted(regenerated_ids)}, f)
        except (OSError, TypeError, ValueError) as e:
            pr.red(f"Warning: could not save last translated IDs: {e}")


def read_exclude_ids_from_tsv(file_path: str | Path) -> set[str]:
    exclude_ids = set()
    with Path(file_path).open("r", encoding="utf-8") as file:
        for line in file:
            word_id = line.split("\t")[0]
            exclude_ids.add(word_id)
    return exclude_ids


def read_exclude_ids_from_json(
    dir_path: str | Path, mode: str = "meaning", lang: str = "ru"
) -> set[int]:
    """Read queued IDs from JSONL batch files. Extracts numeric ID from custom_id field like 'request-12345'."""
    exclude_ids: set[int] = set()
    json_files = Path(dir_path).glob("*.jsonl")

    for file_path in json_files:
        with file_path.open("r", encoding="utf-8") as file:
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


def get_provider_for_model(model_name: str) -> str | None:
    for model_tuple in load_models_from_json():
        if model_tuple[1] == model_name:
            return model_tuple[0]
    return None


def get_default_model_for_provider(provider_name: str) -> str | None:
    for model_tuple in load_models_from_json():
        if model_tuple[0] == provider_name:
            return model_tuple[1]
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate AI translations for Pāḷi headwords.",
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-help",
        "-h",
        "--help",
        action="help",
        help="List all flags and exit.",
    )
    parser.add_argument(
        "-lang",
        "--lang",
        default="ru",
        choices=["ru", "ta"],
        help="Language to translate to (default: ru)",
    )
    parser.add_argument(
        "-mode",
        "--mode",
        default="meaning",
        choices=["meaning", "note", "lit"],
        help="Generation mode (default: meaning)",
    )
    parser.add_argument(
        "-remove",
        "--remove",
        action="store_true",
        help="Run remove_irrelevant instead of translation_generate/make_json",
    )
    parser.add_argument(
        "-json",
        "--json",
        action="store_true",
        help="Run make_json instead of translation_generate",
    )
    parser.add_argument(
        "-limit",
        "--limit",
        type=int,
        default=None,
        help="Limit of rows to process (default: no limit)",
    )
    parser.add_argument(
        "-dry-run",
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Simulate operations without making database modifications or AI requests.",
    )
    all_models: list[tuple[str, str, int, float]] = load_models_from_json()
    configured_providers: list[str] = sorted({m[0] for m in all_models})
    configured_models: list[str] = sorted({m[1] for m in all_models})

    provider_list: str = ", ".join(configured_providers)
    provider_help: str = (
        f"Specify the AI provider to use. Available: {provider_list}.\n"
        "Default is the sequence from ai_models.json."
    )

    provider_to_models: dict[str, list[str]] = {}
    for m in all_models:
        provider_to_models.setdefault(m[0], []).append(m[1])

    model_help_blocks: list[str] = ["Specify the AI model to use. Available models:"]
    for prov in sorted(provider_to_models.keys()):
        prov_models: list[str] = sorted(set(provider_to_models[prov]))
        prov_lines: list[str] = [f"  {prov} / {mdl}" for mdl in prov_models]
        model_help_blocks.append("\n".join(prov_lines))
    model_help: str = "\n\n".join(model_help_blocks)

    parser.add_argument(
        "-provider",
        "--provider",
        help=provider_help,
    )
    parser.add_argument(
        "-model",
        "--model",
        help=model_help,
    )

    args = parser.parse_args()

    provider_val = args.provider
    model_val = args.model

    if provider_val and provider_val not in configured_providers:
        parser.error(f"provider must be one of: {', '.join(configured_providers)}")
    if model_val and model_val not in configured_models:
        parser.error(f"model must be one of: {', '.join(configured_models)}")

    if model_val and not provider_val:
        provider_val = get_provider_for_model(model_val)
    elif provider_val and not model_val:
        model_val = get_default_model_for_provider(provider_val)

    pr.white("Translating with the help of AI")

    if args.remove:
        remove_irrelevant(args.limit, lang=args.lang, dry_run=args.dry_run)
    elif args.json:
        make_json(
            args.mode,
            args.limit,
            lang=args.lang,
            dry_run=args.dry_run,
            model=model_val,
        )
    else:
        translation_generate(
            args.mode,
            args.limit,
            lang=args.lang,
            dry_run=args.dry_run,
            provider=provider_val,
            model=model_val,
        )
        if not args.dry_run:
            check_cmd = f"uv run python3 kamma/translate/scripts/ai_translation_check.py -lang {args.lang}"
            pr.green("\n" + "=" * 60)
            pr.green("Translation run complete!")
            pr.white("To verify the generated translations, run:")
            pr.white(f"  {check_cmd}")
            pr.green("=" * 60)
