#!/usr/bin/env python3

"""Update DPS Anki deck with latest data directly from the DB."""

import copy
import sys
import traceback
from datetime import date
from pathlib import Path

from anki.collection import Collection
from anki.errors import DBError
from anki.notes import Note

from anki.cards import Card  # isort:skip — must follow Collection (avoids upstream circular import)
from sqlalchemy.orm import joinedload

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.configger import config_read
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pr.tic()
    pr.amber("updating dps anki")

    update_test_field = "test" in sys.argv
    current_date = date.today().strftime("%m-%d")  # noqa: DTZ011

    pr.green("setup dbs")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.sbs), joinedload(DpdHeadword.ru))
        .all()
    )
    pr.yes(len(db))

    calculate_index(db, db_session)

    decks = ["Pali"]
    col, data_dict, deck_dict, model_dict, carry_on = setup_anki_updater(decks)

    if carry_on:
        update_from_db(
            db, col, data_dict, deck_dict, model_dict, current_date, update_test_field
        )

    pr.cyan(f"test {current_date}")

    pr.toc()


def setup_anki_updater(decks: list[str]) -> tuple:
    col = get_anki_collection()
    if col:
        backup_anki_db(col)
        notes = get_notes(col, decks)
        cards = get_cards(col, decks)
        deck_dict = get_decks(col)
        model_dict = get_models(col)
        data_dict = make_data_dict(notes, cards)
        return col, data_dict, deck_dict, model_dict, True
    return col, {}, {}, {}, False


def get_anki_collection() -> Collection | None:
    pr.green("get anki collection")
    anki_db_path = config_read("anki", "db_path")
    if anki_db_path:
        try:
            col = Collection(anki_db_path)
            pr.yes("ok")
            return col
        except DBError as e:
            pr.no("error")
            pr.red(f"Anki DBError: {e}")
            pr.red("Full traceback:")
            traceback.print_exc()
            pr.red("Anki is currently open, close and try again.")
            return None
    return None


def backup_anki_db(col: Collection) -> None:
    pr.green("backup anki db")
    anki_backup_path = config_read("anki", "backup_path")
    if anki_backup_path:
        Path(anki_backup_path).mkdir(parents=True, exist_ok=True)
        is_backed_up = col.create_backup(
            backup_folder=anki_backup_path, force=False, wait_for_completion=False
        )
        if not is_backed_up:
            pr.no("no")
        else:
            pr.yes("ok")
    else:
        pr.no("no path")


def make_search_query(decks: list[str]) -> str:
    return " or ".join(f'deck:"{deck}"' for deck in decks)


def get_notes(col: Collection, decks: list[str]) -> list[Note]:
    pr.green("get notes")
    search_query = make_search_query(decks)
    note_ids = col.find_notes(search_query)
    notes = [col.get_note(note_id) for note_id in note_ids]
    pr.yes(len(notes))
    return notes


def get_cards(col: Collection, decks: list[str]) -> list[Card]:
    pr.green("get cards")
    search_query = make_search_query(decks)
    card_ids = col.find_cards(search_query)
    cards = [col.get_card(card_id) for card_id in card_ids]
    pr.yes(len(cards))
    return cards


def get_decks(col: Collection) -> dict:
    pr.green("get decks")
    decks = col.decks.all()
    deck_dict: dict = {deck["name"]: deck["id"] for deck in decks}
    deck_dict.update({did: name for name, did in deck_dict.items()})
    pr.yes(len(deck_dict))
    return deck_dict


def get_models(col: Collection) -> dict:
    pr.green("get models")
    models = col.models.all()
    model_dict = {model["name"]: model["id"] for model in models}
    pr.yes(len(model_dict))
    return model_dict


def make_data_dict(notes: list[Note], cards: list[Card]) -> dict[str, dict]:
    pr.green("make data dict")
    data_dict: dict[str, dict] = {}
    nid_to_dpd_id: dict[int, str] = {}

    for note in notes:
        dpd_id = note.fields[0]
        data_dict[dpd_id] = {
            "nid": note.id,
            "dpd_id": dpd_id,
            "mid": note.mid,
            "guid": note.guid,
            "note": note,
            "cid": None,
            "did": None,
            "card": None,
        }
        nid_to_dpd_id[note.id] = dpd_id

    for card in cards:
        dpd_id = nid_to_dpd_id.get(card.nid)
        if dpd_id:
            data_dict[dpd_id]["cid"] = card.id
            data_dict[dpd_id]["did"] = card.did
            data_dict[dpd_id]["card"] = card

    pr.yes(len(data_dict))
    return data_dict


def update_from_db(
    db,
    col,
    data_dict,
    deck_dict,
    model_dict,
    current_date: str,
    update_test_field: bool,
) -> None:
    pr.green("updating")
    added_list: list[int] = []
    updated_list: list[int] = []
    deleted_list: list[int] = []
    changed_deck_list: list[int] = []
    for counter, i in enumerate(db):
        id = str(i.id)
        deck = deck_selector(i)
        if deck:
            if id in data_dict:
                note = data_dict[id]["note"]
                note, is_updated = update_note_values(
                    note, i, current_date, update_test_field
                )
                if is_updated:
                    updated_list.append(i.id)
                    col.update_note(note)
                if update_deck(col, note, i, data_dict[id], deck_dict, model_dict):
                    changed_deck_list.append(i.id)
            else:
                added_list.append(i.id)
                make_new_note(
                    col, deck, model_dict, deck_dict, i, current_date, update_test_field
                )
            if counter % 5000 == 0:
                pr.counter(counter, len(db), i.lemma_1)
        else:
            if i.id in data_dict:
                pr.cyan(str(data_dict[id]))
                deleted_list.append(i.id)

    pr.summary("added", len(added_list))
    pr.summary("updated", len(updated_list))
    pr.summary("changed deck", len(changed_deck_list))
    pr.summary("deleted", len(deleted_list))

    pr.cyan(f"{added_list=}")
    pr.cyan(f"{updated_list=}")
    pr.cyan(f"{changed_deck_list=}")
    pr.cyan(f"{deleted_list=}")


def update_note_values(note, i, current_date: str, update_test_field: bool):
    old_fields = copy.copy(note.fields)

    note["id"] = str(i.id)
    note["pali"] = str(i.lemma_1)
    if i.ru:
        if i.ru.ru_meaning:
            note["ru_meaning"] = str(i.ru.ru_meaning)
        elif i.ru.ru_meaning_raw:
            note["ru_meaning"] = f"пер ИИ: {i.ru.ru_meaning_raw}"

        note["ru_meaning_lit"] = str(i.ru.ru_meaning_lit)
        note["ru_notes"] = str(i.ru.ru_notes).replace("\n", "<br>")
        note["ru_cognate"] = str(i.ru.ru_cognate)
    else:
        pr.cyan(f"no ru {i.lemma_1}")

    if i.sbs:
        note["sbs_meaning"] = str(i.sbs.sbs_meaning)
        note["class_anki"] = str(i.sbs.class_anki)
        note["sbs_source_1"] = str(i.sbs.sbs_source_1)
        note["sbs_sutta_1"] = str(i.sbs.sbs_sutta_1).replace("\n", "<br>")
        note["sbs_example_1"] = str(i.sbs.sbs_example_1).replace("\n", "<br>")
        note["sbs_chant_pali_1"] = str(i.sbs.sbs_chant_pali_1)
        note["sbs_chant_eng_1"] = str(i.sbs.sbs_chant_eng_1)
        note["sbs_chapter_1"] = str(i.sbs.sbs_chapter_1)
        note["sbs_source_2"] = str(i.sbs.sbs_source_2)
        note["sbs_sutta_2"] = str(i.sbs.sbs_sutta_2).replace("\n", "<br>")
        note["sbs_example_2"] = str(i.sbs.sbs_example_2).replace("\n", "<br>")
        note["sbs_chant_pali_2"] = str(i.sbs.sbs_chant_pali_2)
        note["sbs_chant_eng_2"] = str(i.sbs.sbs_chant_eng_2)
        note["sbs_chapter_2"] = str(i.sbs.sbs_chapter_2)
        note["dhp_source"] = str(i.sbs.dhp_source)
        note["dhp_sutta"] = str(i.sbs.dhp_sutta).replace("\n", "<br>")
        note["dhp_example"] = str(i.sbs.dhp_example).replace("\n", "<br>")
        note["pat_source"] = str(i.sbs.pat_source)
        note["pat_sutta"] = str(i.sbs.pat_sutta).replace("\n", "<br>")
        note["pat_example"] = str(i.sbs.pat_example).replace("\n", "<br>")
        note["vib_source"] = str(i.sbs.vib_source)
        note["vib_sutta"] = str(i.sbs.vib_sutta).replace("\n", "<br>")
        note["vib_example"] = str(i.sbs.vib_example).replace("\n", "<br>")
        note["class_source"] = str(i.sbs.class_source)
        note["class_sutta"] = str(i.sbs.class_sutta).replace("\n", "<br>")
        note["class_example"] = str(i.sbs.class_example).replace("\n", "<br>")
        note["class_example_translation"] = str(
            i.sbs.class_example_translation
        ).replace("\n", "<br>")
        note["class_extra"] = str(i.sbs.class_extra).replace("\n", "<br>")
        note["discourses_source"] = str(i.sbs.discourses_source)
        note["discourses_sutta"] = str(i.sbs.discourses_sutta).replace("\n", "<br>")
        note["discourses_example"] = str(i.sbs.discourses_example).replace("\n", "<br>")
        note["sbs_notes"] = str(i.sbs.sbs_notes).replace("\n", "<br>")
        note["sbs_index"] = str(i.sbs.sbs_index)

    note["grammar"] = str(i.grammar)
    note["neg"] = str(i.neg)
    note["verb"] = str(i.verb)
    note["trans"] = str(i.trans)
    note["plus_case"] = str(i.plus_case)

    if i.ru:
        if not i.meaning_1 and i.meaning_lit and " lit." in i.meaning_2:
            note["meaning"] = i.meaning_2.split("; lit.")[0]
        elif (
            not i.meaning_1
            and i.meaning_lit
            and i.meaning_2
            or not i.meaning_1
            and not i.meaning_lit
            and i.meaning_2
        ):
            note["meaning"] = i.meaning_2
        elif i.meaning_1:
            note["meaning"] = i.meaning_1
        else:
            pr.amber(f"no meaning {i.lemma_1}")

    note["meaning_lit"] = str(i.meaning_lit)
    note["sanskrit"] = str(i.sanskrit)
    note["root"] = str(i.root_clean)
    note["root_sign"] = str(i.root_sign)
    note["root_base"] = str(i.root_base)
    if i.root_key:
        note["sanskrit_root"] = str(i.rt.sanskrit_root)
        note["sanskrit_root_meaning"] = str(i.rt.sanskrit_root_meaning)
        note["sanskrit_root_ru_meaning"] = str(i.rt.sanskrit_root_ru_meaning)
        note["sanskrit_root_class"] = str(i.rt.sanskrit_root_class)
        note["root_meaning"] = str(i.rt.root_meaning)
        note["root_ru_meaning"] = str(i.rt.root_ru_meaning)
        note["root_has_verb"] = str(i.rt.root_has_verb)
        note["root_group"] = str(i.rt.root_group)
    note["construction"] = str(i.construction).replace("\n", "<br>")
    note["derivative"] = str(i.derivative)
    note["suffix"] = str(i.suffix)
    note["phonetic"] = str(i.phonetic).replace("\n", "<br>")
    note["compound_type"] = str(i.compound_type)
    note["compound_construction"] = str(i.compound_construction)
    note["antonym"] = str(i.antonym)
    note["synonym"] = str(i.synonym)
    note["commentary"] = str(i.commentary).replace("\n", "<br>")
    note["notes"] = str(i.notes).replace("\n", "<br>")
    if update_test_field:
        note["test"] = current_date

    if i.link:
        note["link"] = f'<a class="link" href="{i.link}">Wiki link</a>'
    else:
        note["link"] = ""

    anki_media_dir_path = config_read("anki", "media_dir")
    if anki_media_dir_path:
        audio_path = Path(anki_media_dir_path) / f"{i.lemma_clean}.mp3"
        if audio_path.exists():
            sbs_audio = f"[sound:{i.lemma_clean}.mp3]"
        else:
            sbs_audio = ""
    else:
        pr.red("no path to anki media")
        sbs_audio = ""

    note["audio"] = sbs_audio

    feedback_url = (
        f'Нашли ошибку? <a class="link" '
        f'href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/'
        f'viewform?usp=pp_url&entry.438735500={i.lemma_1}&entry.1433863141=Anki-{current_date}">'
        f"Пожалуйста сообщите</a>."
    )
    if update_test_field:
        note["feedback"] = feedback_url

    is_updated = note.fields != old_fields

    return note, is_updated


def calculate_index(db, db_session):
    pr.green("calculating sbs_index")
    try:
        for i in db:
            if i.sbs:
                sbs_index_old = i.sbs.sbs_index
                sbs_index_value = i.sbs.calculate_index()
                if sbs_index_old != sbs_index_value:
                    i.sbs.sbs_index = sbs_index_value
                    pr.cyan(
                        f"{i.lemma_1} old index {sbs_index_old} changed to {sbs_index_value}"
                    )

        db_session.commit()

    except Exception as e:  # noqa: BLE001
        pr.red(str(e))


def deck_selector(i):
    if i.sbs and (
        i.sbs.sbs_chapter_1
        or i.sbs.sbs_chapter_2
        or i.sbs.dhp_example
        or i.sbs.pat_example
        or i.sbs.vib_example
        or i.sbs.class_anki
        or i.sbs.discourses_example
    ):
        return "Pali"
    return None


def update_deck(col, note, i, data, deck_dict, model_dict):
    new_deck = deck_selector(i)
    old_deck = deck_dict[data["did"]]

    if old_deck != new_deck:
        if new_deck in model_dict:
            note.mid = model_dict[new_deck]
            col.update_note(note)

            card = data["card"]
            card.did = deck_dict[new_deck]
            card.queue = 0
            card.lapse = 0
            card.due = 0
            col.update_card(card)

            return True
        else:
            return False

    return False


def make_new_note(
    col, deck, model_dict, deck_dict, i, current_date: str, update_test_field: bool
):
    pr.cyan(f"Creating new note for {i.lemma_1}")

    note_type_name = "Pāli"

    if note_type_name in model_dict:
        model_id = model_dict[note_type_name]
        deck_id = deck_dict[deck]
        note = col.new_note(model_id)
        note, _ = update_note_values(note, i, current_date, update_test_field)
        col.add_note(note, deck_id)

    else:
        pr.amber(
            f"Warning: Note type '{note_type_name}' not found in model_dict. for {i.lemma_1}"
        )


if __name__ == "__main__":
    main()
