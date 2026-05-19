# -*- coding: utf-8 -*-
"""Read and display records from a DBF database file."""

import dbf
from tools.printer import printer as pr


def main():
    pr.tic()
    # Open the table
    pr.green_tmr("opening table")
    try:
        table = dbf.Table("/media/bodhirasa/123gb/Tipitaka/Dbf1/wordat.dbf")
        table.open()
        pr.yes("ok")

        # Print field names first
        pr.white(f"Fields in the database: {table.field_names}")

        # Read records
        pr.green_title("reading records")
        for record in table:
            # Print each field separately to avoid encoding issues
            for field_name in table.field_names:
                try:
                    value = record[field_name]
                    pr.white(f"{field_name}: {value}")
                except UnicodeDecodeError as e:
                    pr.red(f"Encoding error in field {field_name}: {e}")
            pr.white("-" * 50)  # Separator between records

        pr.yes("ok")
        table.close()

    except FileNotFoundError:
        pr.red("Error: database file not found")
    except Exception as e:
        pr.red(f"Error: {e}")

    pr.toc()


if __name__ == "__main__":
    main()
