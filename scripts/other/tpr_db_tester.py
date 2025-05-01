#!/usr/bin/env python3

import sqlite3
import csv
from lxml import etree
from tools.configger import config_read
from pathlib import Path
from typing import Optional, List, Tuple

tpr_db_path_str: Optional[str] = config_read("tpr", "db_path")

if not tpr_db_path_str:
    print("Error: tpr db_path not found in configuration.")
    exit(1)

# Use Path for filepath handling
tpr_db_path: Path = Path(tpr_db_path_str)

if not tpr_db_path.exists():
    # Check if the path relative to the CWD exists if the absolute/configured one doesn't
    tpr_db_path = Path.cwd() / tpr_db_path_str
    if not tpr_db_path.exists():
        print(f"Error: Database file not found at {tpr_db_path_str} or {tpr_db_path}")
        exit(1)
    else:
        print(f"Info: Found database at relative path: {tpr_db_path}")

# Create output directory
output_dir = Path("temp")
output_dir.mkdir(parents=True, exist_ok=True)
errors_tsv_path = output_dir / "tpr_parsing_errors.tsv"

print(f"Info: Connecting to database: {tpr_db_path}")
conn: sqlite3.Connection = sqlite3.connect(tpr_db_path)
cursor: sqlite3.Cursor = conn.cursor()

# Fetch all rows
cursor.execute("SELECT rowid, content FROM pages")
rows: List[Tuple[int, Optional[str]]] = cursor.fetchall()

# Store rows with parsing issues
invalid_html_rows: List[Tuple[int, str]] = []

# Explicitly create a parser
html_parser = etree.HTMLParser(recover=False)

print(f"Info: Processing {len(rows)} rows...")

for rowid, content in rows:
    if content is None or not content.strip():
        continue  # Skip empty content without tracking

    try:
        # Try parsing with the explicit HTMLParser
        content_bytes: bytes
        if isinstance(content, str):
            content_bytes = content.encode('utf-8')
        elif isinstance(content, bytes):
            content_bytes = content
        else:
            invalid_html_rows.append((rowid, f"Unexpected content type: {type(content)}"))
            continue
            
        if not content_bytes.strip().lower().startswith((b'<html', b'<!doctype')):
            content_bytes = b'<div>' + content_bytes + b'</div>'

        etree.fromstring(content_bytes, parser=html_parser)

    except (etree.XMLSyntaxError, etree.ParserError, ValueError) as e:
        invalid_html_rows.append((rowid, str(e)))

conn.close()
print("Info: Database connection closed.")

# Write Invalid HTML Rows to TSV
print(f"Info: Writing {len(invalid_html_rows)} rows with parsing errors to {errors_tsv_path}...")
with open(errors_tsv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerow(['rowid', 'error'])
    writer.writerows(invalid_html_rows)

# Report Invalid HTML
print("-" * 30)
print(f"Found {len(invalid_html_rows)} rows with invalid HTML structure. Full list saved to {errors_tsv_path}")
print("First 5 examples:")
if invalid_html_rows:
    for rowid, error in invalid_html_rows[:5]:
        print(f"  Row {rowid}: {error}")
else:
    print("  None found.")

print("-" * 30)
print("Info: Script finished.")
