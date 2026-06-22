#!/usr/bin/env python3

"""Adds or updates a row in the SBS or Russian table for a given DpdHeadword ID."""

from typing import Literal

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from db.models import DpdHeadword, Russian, SBS
from tools.printer import printer as pr


def add_new_row(
    db_session: Session,
    table_name: Literal["SBS", "Russian"],
    column_to_update: str,
    value_to_update: str,
    id_to_add: int,
) -> None:
    dpd_headword = db_session.query(DpdHeadword).filter_by(id=id_to_add).first()
    if not dpd_headword:
        pr.red(f"DpdHeadword ID {id_to_add} not found.")
        return

    action_taken = False

    if table_name == "SBS":
        valid_columns = {attr.key for attr in sa_inspect(SBS).column_attrs}
        if column_to_update not in valid_columns:
            pr.red(f"Column '{column_to_update}' does not exist in SBS model.")
            return

        existing_row = db_session.query(SBS).filter_by(id=id_to_add).first()
        if existing_row:
            if getattr(existing_row, column_to_update) != value_to_update:
                setattr(existing_row, column_to_update, value_to_update)
                pr.green(
                    f"Updated SBS row {id_to_add}: '{column_to_update}' = '{value_to_update}'."
                )
                action_taken = True
            else:
                pr.cyan(f"SBS row {id_to_add}: '{column_to_update}' unchanged.")
        else:
            new_row = SBS(id=id_to_add)
            setattr(new_row, column_to_update, value_to_update)
            db_session.add(new_row)
            pr.green(
                f"Added SBS row {id_to_add}: '{column_to_update}' = '{value_to_update}'."
            )
            action_taken = True

    elif table_name == "Russian":
        existing_row = db_session.query(Russian).filter_by(id=id_to_add).first()
        if existing_row:
            pr.cyan(f"Russian row {id_to_add} already exists.")
        else:
            db_session.add(Russian(id=id_to_add))
            pr.green(f"Added empty Russian row {id_to_add}.")
            action_taken = True

    else:
        pr.red(f"Unknown table '{table_name}'.")
        return

    if action_taken:
        try:
            db_session.commit()
            pr.green(f"Committed: ID {id_to_add}, Table {table_name}.")
        except Exception as e:
            db_session.rollback()
            pr.red(f"Commit failed for ID {id_to_add}: {e}. Rolled back.")


if __name__ == "__main__":
    from db.db_helpers import get_db_session
    from tools.paths import ProjectPaths

    pth = ProjectPaths()
    session = get_db_session(pth.dpd_db_path)

    try:
        add_new_row(session, "SBS", "class_anki", "1", 30377)
    except Exception as e:
        pr.red(f"Unexpected error: {e}")
    finally:
        session.close()
