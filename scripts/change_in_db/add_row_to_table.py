#!/usr/bin/env python3

"""
Provides a function to add or update a row in SBS or Russian tables for a given DpdHeadword ID.
If the target is SBS, a specified column is populated/updated with a given value.
If the target is Russian, an empty row (ID only) is added if it doesn't exist.
The function handles cases where the DpdHeadword ID does not exist or the related row already exists.
"""

from sqlalchemy.orm import Session

# Assuming models are in db.models
from db.models import DpdHeadword, SBS, Russian
from tools.paths import ProjectPaths # For example usage
from db.db_helpers import get_db_session # For example usage
from rich.console import Console # For rich printing


def add_new_row(
    db_session: Session,
    console: Console,
    table_name: str,
    column_to_update: str, # Relevant for SBS
    value_to_update: str,  # Relevant for SBS
    id_to_add_str: str
):
    """
    Adds or updates a related row in the specified table (SBS or Russian) for a given DpdHeadword ID.

    - Checks if DpdHeadword with id_to_add_str exists.
    - If table_name is "SBS":
        - Checks if 'column_to_update' is a valid attribute of the SBS model.
        - If an SBS row with this ID already exists, it updates the 'column_to_update'
          with 'value_to_update' if they are different.
        - If no SBS row exists, it creates a new one, setting 'column_to_update'
          to 'value_to_update'.
    - If table_name is "Russian":
        - If a Russian row with this ID already exists, no action is taken.
        - If no Russian row exists, a new "empty" row (with ID only) is created.
          'column_to_update' and 'value_to_update' are ignored for new Russian rows.
    - Commits changes to the database if an action (add/update) was performed.
    """
    try:
        id_val = int(id_to_add_str)
    except ValueError:
        console.print(f"[red]Error: ID '{id_to_add_str}' is not a valid integer.[/red]")
        return

    # 1. Check DpdHeadword existence
    dpd_headword = db_session.query(DpdHeadword).filter_by(id=id_val).first()
    if not dpd_headword:
        console.print(f"[red]Error: DpdHeadword with ID {id_val} not found. Cannot add/update related row for table '{table_name}'.[/red]")
        return

    action_taken = False

    # 2. Determine target model and process
    if table_name.upper() == "SBS":
        # Check if column_to_update is a valid attribute of SBS model before proceeding
        if not hasattr(SBS, column_to_update):
            console.print(f"[red]Error: Column '{column_to_update}' does not exist in SBS model. Operation for ID {id_val} aborted.[/red]")
            return
            
        existing_row = db_session.query(SBS).filter_by(id=id_val).first()
        if existing_row:
            current_sbs_val = getattr(existing_row, column_to_update, None)
            if current_sbs_val != value_to_update:
                setattr(existing_row, column_to_update, value_to_update)
                console.print(f"[green]Updated existing SBS row (ID: {id_val}): set '{column_to_update}' to '{value_to_update}'.[/green]")
                action_taken = True
            else:
                console.print(f"[cyan]SBS row (ID: {id_val}) already exists and '{column_to_update}' is already '{value_to_update}'. No change.[/cyan]")
        else:
            new_row = SBS(id=id_val)
            setattr(new_row, column_to_update, value_to_update)
            db_session.add(new_row)
            console.print(f"[green]Added new SBS row (ID: {id_val}): set '{column_to_update}' to '{value_to_update}'.[/green]")
            action_taken = True
    
    elif table_name.upper() == "RUSSIAN":
        existing_row = db_session.query(Russian).filter_by(id=id_val).first()
        if existing_row:
            console.print(f"[cyan]Russian row with ID {id_val} already exists. No changes made as per requirement for Russian table.[/cyan]")
        else:
            new_row = Russian(id=id_val)
            db_session.add(new_row)
            console.print(f"[green]Added new empty Russian row (ID: {id_val}).[/green]")
            action_taken = True
            # column_to_update and value_to_update are ignored for adding new Russian row.
    
    else:
        console.print(f"[red]Error: Unknown table name '{table_name}'. Must be 'SBS' or 'Russian'. Operation for ID {id_val} aborted.[/red]")
        return

    # 3. Commit changes if an action was taken
    if action_taken:
        try:
            db_session.commit()
            console.print(f"[bold green]Changes for ID {id_val} (Table: {table_name}) committed.[/bold green]")
        except Exception as e:
            db_session.rollback()
            console.print(f"[bold red]Error during commit for ID {id_val} (Table: {table_name}): {e}. Changes rolled back.[/bold red]")
    elif not (table_name.upper() == "SBS" or table_name.upper() == "RUSSIAN"): 
        # Error for invalid table name already printed, no commit needed.
        pass
    else: 
        # No action taken, but table name was valid (e.g., row existed and matched criteria for no change).
        console.print(f"[dim]No database changes to commit for ID {id_val} (Table: {table_name}).[/dim]")


if __name__ == "__main__":
    console = Console()
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    table_name = "SBS"
    # table_name = "Russian"
    column_to_update = "sbs_patimokkha"
    value_to_update = "vib"
    id_to_add = "31318"

    console.print(f"[bold yellow]Adding new row to the table '{table_name}' for ID '{id_to_add}'...[/bold yellow]")
    
    try:
        add_new_row(db_session, 
                    console, 
                    table_name, 
                    column_to_update, 
                    value_to_update, 
                    id_to_add)


    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred in the main block: {e}[/bold red]")
        # The function add_new_row handles its own commit/rollback per operation.
        # No global rollback needed here unless the session setup itself failed.
    finally:
        if db_session:
            db_session.close()
            console.print("\nDB session closed.")

