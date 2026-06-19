#!/usr/bin/env python3

"""
Converts a specific sheet from an XLSX file to a CSV file,
preserving bold formatting as HTML <b> tags and saving cell values (not formulas).
"""

import argparse
import csv
from pathlib import Path
from typing import Any, cast

import openpyxl
from openpyxl.cell.cell import Cell
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.styles.fonts import Font

from tools.printer import printer as pr


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert an XLSX sheet to CSV, preserving bold as HTML <b> tags."
    )
    parser.add_argument(
        "input_doc_path", type=Path, help="Path to the input XLSX file."
    )
    parser.add_argument(
        "output_csv_path", type=Path, help="Path to the output CSV file."
    )
    parser.add_argument("sheet_name", type=str, help="Name of the sheet to convert.")
    return parser.parse_args()


def format_cell_value(cell: Cell) -> str:
    """
    Formats the cell value, converting bold text to HTML <b> tags.
    Handles both entirely bold cells and rich text with mixed formatting.
    Converts whole number floats (e.g., 1.0) to integer strings (e.g., "1").
    """
    value: Any = cell.value  # calculated value, since data_only=True
    font: Font | None = cast("Font | None", cell.font)

    if value is None:
        return ""

    if isinstance(value, CellRichText):
        formatted_parts: list[str] = []
        for part in value:
            if isinstance(part, TextBlock):
                text_content: str = part.text if part.text is not None else ""
                if hasattr(part, "font") and part.font and part.font.b:
                    formatted_parts.append(f"<b>{text_content}</b>")
                else:
                    formatted_parts.append(text_content)
            elif isinstance(part, str):
                formatted_parts.append(part)
        return "".join(formatted_parts)

    processed_value: str
    if isinstance(value, float) and value.is_integer():
        processed_value = str(int(value))
    else:
        processed_value = str(value)

    if font and font.b:
        return f"<b>{processed_value}</b>"

    return processed_value


def convert_xlsx_to_csv(input_path: Path, output_path: Path, sheet_name: str) -> None:
    """
    Reads an XLSX sheet, formats cell content for bold text, and writes to a CSV file.
    Loads cell values, not formulas.
    """
    try:
        workbook = openpyxl.load_workbook(input_path, rich_text=True, data_only=True)
    except FileNotFoundError:
        pr.red(f"Error: Input file not found at '{input_path}'")
        return
    except (OSError, KeyError, ValueError) as e:
        pr.red(f"Error loading workbook '{input_path}': {e}")
        return

    if sheet_name not in workbook.sheetnames:
        pr.red(f"Error: Sheet '{sheet_name}' not found in the workbook.")
        pr.green(f"Available sheets: {', '.join(workbook.sheetnames)}")
        return

    sheet = workbook[sheet_name]

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", newline="", encoding="utf-8") as csvfile:
            csv_writer = csv.writer(csvfile, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
            for row_idx, row_cells in enumerate(sheet.iter_rows()):
                try:
                    csv_writer.writerow(
                        [format_cell_value(cast(Cell, cell)) for cell in row_cells]
                    )
                except (ValueError, AttributeError) as e_row:
                    pr.red(
                        f"Error processing row {row_idx + 1} in sheet '{sheet_name}': {e_row}"
                    )
        pr.green(
            f"Successfully converted sheet '{sheet_name}' from '{input_path}' "
            f"to '{output_path}' (values only)."
        )

    except OSError as e:
        pr.red(f"Error writing CSV file to '{output_path}': {e}")


if __name__ == "__main__":
    pr.tic()
    pr.amber("Converting XLSX to CSV...")
    pr.amber("This script preserves bold formatting as HTML <b> tags.")
    args = parse_arguments()
    convert_xlsx_to_csv(args.input_doc_path, args.output_csv_path, args.sheet_name)
    pr.toc()
