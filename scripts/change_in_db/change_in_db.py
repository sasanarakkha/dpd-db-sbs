#!/usr/bin/env python3

"""
Filter the database on a specified column by a given value, then update another specified column with a provided value.
"""

import re
from typing import Any

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import aliased
from sqlalchemy import and_

from db.models import DpdHeadword, SBS, Russian
from tools.paths import ProjectPaths
from db.db_helpers import get_db_session
from tools.printer import printer as pr

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def filter_and_update(
    column_to_filter: InstrumentedAttribute,
    filter_value: str,
    related_table: type[Any],
    related_column_to_update: str,
    update_value: str,
) -> None:
    related_alias = aliased(related_table)
    words_to_update = (
        db_session.query(DpdHeadword, related_alias)
        .join(related_alias, related_alias.id == DpdHeadword.id)
        .filter(getattr(related_alias, column_to_filter.key) == filter_value)
        .all()
    )

    pr.green(f"words_to_update = {len(words_to_update)}")

    for word, related in words_to_update:
        old_value = getattr(related, related_column_to_update)
        if old_value or update_value:
            setattr(related, related_column_to_update, update_value)
            pr.amber(f"{word.id} {related_column_to_update}:")
            pr.white("")
            pr.white(str(old_value))
            pr.white("")
            pr.white(update_value)
            pr.white("")

    # db_session.commit()


def filter_and_add(
    column_to_filter: InstrumentedAttribute,
    filter_value: str,
    related_table: type[Any],
    related_column_to_update: str,
    update_value: str,
) -> None:
    related_alias = aliased(related_table)
    words_to_update = (
        db_session.query(DpdHeadword, related_alias)
        .join(related_alias, related_alias.id == DpdHeadword.id)
        .filter(
            and_(
                column_to_filter.contains(filter_value),
                related_alias.ru_meaning_raw != "",
                related_alias.ru_meaning_raw.notlike(f"%{update_value}%"),
            )
        )
        .all()
    )

    for word, related in words_to_update:
        old_value = getattr(related, related_column_to_update)
        if old_value or update_value:
            new_value = "(грам) " + old_value if old_value else update_value
            setattr(related, related_column_to_update, new_value)
            pr.amber(f"{word.id} {related_column_to_update}:")
            pr.white("")
            pr.white(str(old_value))
            pr.white("")
            pr.white(new_value)
            pr.white("")

    # db_session.commit()


def update_notes() -> None:
    db = (
        db_session.query(DpdHeadword)
        .outerjoin(Russian, DpdHeadword.id == Russian.id)
        .filter(
            DpdHeadword.notes.like("agent noun used verbally see Perniola §292"),
        )
        .order_by(DpdHeadword.ebt_count.desc())
        .all()
    )

    for word in db:
        new_value = re.sub(
            "agent noun used verbally see Perniola §292",
            "существительное деятель, используемое глагольно, см. Перниола §292",
            word.notes,
        )

        existing_russian = (
            db_session.query(Russian).filter(Russian.id == word.id).first()
        )
        if not existing_russian:
            new_russian = Russian(id=word.id, ru_notes=new_value)
            db_session.add(new_russian)
            pr.amber(f"{word.id} {Russian.ru_notes}:")
            pr.white("")
            pr.white(new_value)
            pr.white("")
        else:
            old_value = getattr(word.ru, "ru_notes")
            if not old_value or "ИИ" in old_value:
                existing_russian.ru_notes = new_value
                pr.amber(f"{word.id} {Russian.ru_notes}:")
                pr.white("")
                pr.white(str(old_value))
                pr.white("")
                pr.white(new_value)
                pr.white("")

        # db_session.commit()


if __name__ == "__main__":
    column_to_filter = SBS.class_extra
    filter_value = "yes"
    related_table = SBS
    related_column_to_update = "class_extra"
    value_to_update = "extra"

    print("1. filter_and_update")
    print("2. filter_and_add")
    print("3. update_notes")
    choice = input("Choose (1-3): ").strip()
    if choice == "1":
        filter_and_update(
            column_to_filter,
            filter_value,
            related_table,
            related_column_to_update,
            value_to_update,
        )
    elif choice == "2":
        filter_and_add(
            column_to_filter,
            filter_value,
            related_table,
            related_column_to_update,
            value_to_update,
        )
    elif choice == "3":
        update_notes()
