#!/usr/bin/env python3

"""
    Filter the database on a specified column by a given value, then update another specified column with a provided value.
"""
import re

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import aliased
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from db.models import DpdHeadword, SBS, Russian
from tools.paths import ProjectPaths
from db.db_helpers import get_db_session

from rich.console import Console

console = Console()

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)

def filter_and_update(
        column_to_filter: InstrumentedAttribute, 
        filter_value: str,
        related_table,
        related_column_to_update, 
        update_value: str
    ):
    
    # Create an alias for the related class to query it directly
    related_alias = aliased(related_table)

    # Find the words that match the filter criteria
    words_to_update = db_session.query(DpdHeadword, related_alias).join(
        related_alias, related_alias.id == DpdHeadword.id
    ).filter(column_to_filter == filter_value).all()

    for __word__, related in words_to_update:
        old_value = getattr(related, related_column_to_update.key)
        if old_value or update_value:

            setattr(related, related_column_to_update.key, update_value)  

            console.print(f"[bold bright_yellow]{__word__.id} {related_column_to_update.key}:")
            print()
            print(f"{old_value}")
            print()
            print(f"{update_value}")
            print()

    # db_session.commit()



def filter_and_add(
        column_to_filter: InstrumentedAttribute,  
        filter_value: str,
        related_table,
        related_column_to_update,  
        update_value: str
    ):
    
    # Create an alias for the related class to query it directly
    related_alias = aliased(related_table)

    # Find the words that match the filter criteria
    words_to_update = db_session.query(DpdHeadword, related_alias).join(
        related_alias, related_alias.id == DpdHeadword.id
    ).filter(
        and_(
            column_to_filter.contains(filter_value),
            related_alias.ru_meaning_raw != "",
            related_alias.ru_meaning_raw.notlike(f'%{update_value}%'),
        )
    ).all()

    for __word__, related in words_to_update:
        old_value = getattr(related, related_column_to_update.key)
        if old_value or update_value:
            # Prepend (грам) to the existing value of ru_meaning_raw
            new_value = "(грам) " + old_value if old_value else update_value
            setattr(related, related_column_to_update.key, new_value)   

            console.print(f"[bold bright_yellow]{__word__.id} {related_column_to_update.key}:")
            print()
            print(f"{old_value}")
            print()
            print(f"{new_value}")
            print()

    # db_session.commit()


def update_notes():

    # "Kacc %" "see %" "or %"
    db = db_session.query(DpdHeadword).outerjoin(
    Russian, DpdHeadword.id == Russian.id
        ).filter(
            DpdHeadword.notes.like("agent noun used verbally see Perniola §292"),
        ).order_by(DpdHeadword.ebt_count.desc()).all()

    for counter, i in enumerate(db):

        # new_value = re.sub(r'\bor \b', 'или ', i.notes)
        new_value = re.sub("agent noun used verbally see Perniola §292", 'существительное деятель, используемое глагольно, см. Перниола §292', i.notes)
        # new_value = i.notes
        
        # Check if a Russian row with the same id exists
        existing_russian = db_session.query(Russian).filter(Russian.id == i.id).first()
        if not existing_russian:
            # If not, create a new Russian row
            new_russian = Russian(id=i.id, ru_notes=new_value)
            db_session.add(new_russian)
            console.print(f"[bold bright_yellow]{i.id} {Russian.ru_notes}:")
            print()
            print(f"{new_value}")
            print()

        else:
            old_value = getattr(i.ru, 'ru_notes')
            if "ИИ" in old_value or not old_value:
                # If it exists, use the existing row
                existing_russian.ru_notes = new_value

                console.print(f"[bold bright_yellow]{i.id} {Russian.ru_notes}:")
                print()
                print(f"{old_value}")
                print()
                print(f"{new_value}")
                print()

        # db_session.commit()


# def update_sbs_source_3(
#     new_source_3: str = "",
#     new_sutta_3: str = "",
#     new_example_3: str = ""
# ) -> None:
#     """
#     Filters DpdHeadword entries where SBS.sbs_source_3 is not empty,
#     replaces sbs_source_3, sbs_sutta_3, and sbs_example_3 with empty strings,
#     and saves changes to the database.
#     """
#     console.print("[bold blue]Updating SBS source 3 entries...")

#     # Query words with non-empty sbs_source_3, loading the related SBS object
#     words_to_update = db_session.query(DpdHeadword).options(
#         joinedload(DpdHeadword.sbs)
#     ).join(SBS, DpdHeadword.id == SBS.id).filter(
#         and_(
#             SBS.sbs_source_3.isnot(None),
#             SBS.sbs_source_3 != ''
#         )
#     ).all()

#     count_updated = 0
#     for word in words_to_update:
#         if word.sbs: # Ensure SBS object exists
#             old_source_3 = word.sbs.sbs_source_3
#             old_sutta_3 = word.sbs.sbs_sutta_3
#             old_example_3 = word.sbs.sbs_example_3

#             # Update the values
#             word.sbs.sbs_source_3 = new_source_3
#             word.sbs.sbs_sutta_3 = new_sutta_3
#             word.sbs.sbs_example_3 = new_example_3

#             console.print(f"[cyan]Updating word ID:[/cyan] {word.id}")
#             console.print(f"  [yellow]Old source_3:[/yellow] {old_source_3}")
#             console.print(f"  [green]New source_3:[/green] {new_source_3}")
#             console.print(f"  [yellow]Old sutta_3:[/yellow] {old_sutta_3}")
#             console.print(f"  [green]New sutta_3:[/green] {new_sutta_3}")
#             console.print(f"  [yellow]Old example_3:[/yellow] {old_example_3}")
#             console.print(f"  [green]New example_3:[/green] {new_example_3}")
#             print()
#             count_updated += 1
#         else:
#             console.print(f"[yellow]Warning:[/yellow] Word ID {word.id} matched filter but has no SBS object.")


#     if count_updated > 0:
#         console.print(f"[bold green]Committing {count_updated} changes...")
#         # db_session.commit() # Uncomment to save changes
#         console.print("[bold green]Changes committed.")
#     else:
#         console.print("[yellow]No entries found matching the criteria. No changes made.")


column_to_filter = DpdHeadword.meaning_1
filter_value = "(gram)"
related_table = Russian
related_column_to_update = "ru_meaning_raw"
value_to_update = "(грам) "

# !To use the functions:

# filter_and_update(column_to_filter, filter_value, related_table, related_column_to_update, value_to_update)

# filter_and_add(column_to_filter, filter_value, related_table, related_column_to_update, value_to_update)

# update_notes()

# update_sbs_source_3()




