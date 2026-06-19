"""Verify the HTML structure of records in the Tipitaka Pali Reader (TPR) database."""

import csv
import sqlite3
from pathlib import Path

from lxml import etree  # type: ignore

from tools.configger import config_read
from tools.printer import printer as pr


def main():
    pr.tic()
    tpr_db_path_str: str | None = config_read("tpr", "db_path")

    if not tpr_db_path_str:
        pr.red("Error: tpr db_path not found in configuration.")
        return

    # Use Path for filepath handling
    tpr_db_path: Path = Path(tpr_db_path_str)

    if not tpr_db_path.exists():
        # Check if the path relative to the CWD exists if the absolute/configured one doesn't
        tpr_db_path = Path.cwd() / tpr_db_path_str
        if not tpr_db_path.exists():
            pr.red(
                f"Error: Database file not found at {tpr_db_path_str} or {tpr_db_path}"
            )
            return
        else:
            pr.white(f"Info: Found database at relative path: {tpr_db_path}")

    # Create output directory
    output_dir = Path("shared_data")
    output_dir.mkdir(parents=True, exist_ok=True)
    errors_tsv_path = output_dir / "tpr_parsing_errors.tsv"

    pr.green_tmr(f"connecting to database: {tpr_db_path.name}")
    try:
        conn: sqlite3.Connection = sqlite3.connect(tpr_db_path)
        cursor: sqlite3.Cursor = conn.cursor()
        pr.yes("ok")
    except sqlite3.DatabaseError as e:
        pr.no("failed")
        pr.red(f"Error connecting to database: {e}")
        return

    # Fetch all rows
    pr.green_tmr("fetching pages")
    cursor.execute("SELECT rowid, content FROM pages")
    rows: list[tuple[int, str | None]] = cursor.fetchall()
    pr.yes(len(rows))

    # Store rows with parsing issues
    invalid_html_rows: list[tuple[int, str]] = []

    # Explicitly create a parser
    html_parser = etree.HTMLParser(recover=False)

    pr.green_title(f"Processing {len(rows)} rows")
    for rowid, content in rows:
        if content is None or not content.strip():
            continue  # Skip empty content without tracking

        try:
            # Try parsing with the explicit HTMLParser
            content_bytes: bytes
            if isinstance(content, str):
                content_bytes = content.encode("utf-8")
            elif isinstance(content, bytes):
                content_bytes = content
            else:
                invalid_html_rows.append(
                    (rowid, f"Unexpected content type: {type(content)}")
                )
                continue

            if not content_bytes.strip().lower().startswith((b"<html", b"<!doctype")):
                content_bytes = b"<div>" + content_bytes + b"</div>"

            etree.fromstring(content_bytes, parser=html_parser)

        except (etree.XMLSyntaxError, etree.ParserError, ValueError) as e:
            invalid_html_rows.append((rowid, str(e)))

    conn.close()

    # Write Invalid HTML Rows to TSV
    pr.green_tmr(f"writing errors to {errors_tsv_path.name}")
    with open(errors_tsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["rowid", "error"])
        writer.writerows(invalid_html_rows)
    pr.yes(len(invalid_html_rows))

    # Report Invalid HTML
    if invalid_html_rows:
        pr.amber(
            f"Found {len(invalid_html_rows)} rows with invalid HTML structure. Full list saved to {errors_tsv_path}"
        )
        pr.white("First 5 examples:")
        for rowid, error in invalid_html_rows[:5]:
            pr.white(f"  Row {rowid}: {error}")
    else:
        pr.green("No invalid HTML rows found.")

    pr.toc()


if __name__ == "__main__":
    main()
