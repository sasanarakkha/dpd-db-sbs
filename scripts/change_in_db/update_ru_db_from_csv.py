import csv
from rich.console import Console

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.tsv_read_write import dotdict

from sqlalchemy.orm import joinedload


console = Console()
pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)

# put in the path of the csv you want to open
csv_path = dpspth.ru_apply_path

console.print(f"[yellow]Updating db from {csv_path}")

# Detect delimiter
with open(csv_path, "r", encoding="utf-8") as f:
    sample = f.read(2048)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = "\t"  # Fallback to tab

# read the csv with detected delimiter
csv_data: list[dotdict] = []
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter=delimiter)
    for row in reader:
        csv_data.append(dotdict(row))

console.print(f"[blue]Delimiter detected: {repr(delimiter)}")
if csv_data:
    console.print(f"[blue]First entry after headings in the csv: {csv_data[0]}")
console.print(f"[blue]Total number of rows in the file: {len(csv_data)}")
input("Press enter to continue: ")

# Filter items that need review
pending_items: list[tuple[dotdict, DpdHeadword]] = []
count_auto_updated: int = 0

for i in csv_data:
    # Skip if already processed in CSV
    if i.get("processed") == "ok":
        continue

    db_entry = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.ru))
        .filter(DpdHeadword.id == i.id)
        .first()
    )
    if db_entry and db_entry.ru:
        # Auto-update if current is empty but suggestion exists
        auto_updated = False
        if (not db_entry.ru.ru_meaning or not db_entry.ru.ru_meaning.strip()) and (
            i.corrections_ru_meaning and i.corrections_ru_meaning.strip()
        ):
            db_entry.ru.ru_meaning = i.corrections_ru_meaning.strip()
            auto_updated = True

        # if (
        #     not db_entry.ru.ru_meaning_lit or not db_entry.ru.ru_meaning_lit.strip()
        # ) and (i.corrections_ru_meaning_lit and i.corrections_ru_meaning_lit.strip()):
        #     db_entry.ru.ru_meaning_lit = i.corrections_ru_meaning_lit.strip()
        #     auto_updated = True

        if auto_updated:
            count_auto_updated += 1
            # Check if there are still differences after auto-update
            has_diff_m = bool(
                i.corrections_ru_meaning
                and i.corrections_ru_meaning.strip() != db_entry.ru.ru_meaning
            )
            has_diff_l = bool(
                i.corrections_ru_meaning_lit
                and i.corrections_ru_meaning_lit.strip() != db_entry.ru.ru_meaning_lit
            )
            if not has_diff_m and not has_diff_l:
                i.processed = "ok"
                continue

        # Recalculate diffs for pending_items
        has_diff_m = bool(
            i.corrections_ru_meaning
            and i.corrections_ru_meaning.strip() != db_entry.ru.ru_meaning
        )
        has_diff_l = bool(
            i.corrections_ru_meaning_lit
            and i.corrections_ru_meaning_lit.strip() != db_entry.ru.ru_meaning_lit
        )
        if has_diff_m or has_diff_l:
            pending_items.append((i, db_entry))

# Sort by POS
pending_items.sort(key=lambda x: x[1].pos)

console.print(f"[blue]Total unique suggestions to review: {len(pending_items)}")
console.print(f"[blue]Total automatically updated: {count_auto_updated}")

count_meanings: int = 0
count_lit: int = 0

# iterate through the pending items
for idx, (i, db_entry) in enumerate(pending_items):
    console.print("-" * 20)
    console.print(f"[cyan]Suggestions left: {len(pending_items) - idx}")
    console.print(
        f"[yellow]ID: {i.id} | Pali: {db_entry.lemma_1} |  POS: {db_entry.pos} | Meaning_1: {db_entry.meaning_1}"
    )
    console.print(f"[blue]Current RU Meaning: {db_entry.ru.ru_meaning}")
    console.print(f"[blue]Current RU Meaning Lit: {db_entry.ru.ru_meaning_lit}")
    console.print(f"[green]Suggested RU Meaning: {i.corrections_ru_meaning}")
    console.print(f"[green]Suggested RU Meaning Lit: {i.corrections_ru_meaning_lit}")
    if i.get("notes"):
        console.print(f"[green]Suggested Notes: {i.notes}")

    response = (
        input("Enter (both), 1 (meaning), 2 (lit), 3 (skip), q (quit): ")
        .strip()
        .lower()
    )

    if response == "q":
        console.print("[yellow]Quitting loop...")
        break

    # All other options mark as processed
    i.processed = "ok"

    if response == "3":
        console.print("[yellow]Skipping...")
        continue
    elif response == "1":
        if i.corrections_ru_meaning and i.corrections_ru_meaning.strip():
            db_entry.ru.ru_meaning = i.corrections_ru_meaning.strip()
            count_meanings += 1
            console.print("[green]Updated ru_meaning")
        else:
            console.print("[red]Suggested ru_meaning is empty, not updating.")
    elif response == "2":
        if i.corrections_ru_meaning_lit and i.corrections_ru_meaning_lit.strip():
            db_entry.ru.ru_meaning_lit = i.corrections_ru_meaning_lit.strip()
            count_lit += 1
            console.print("[green]Updated ru_meaning_lit")
        else:
            console.print("[red]Suggested ru_meaning_lit is empty, not updating.")
    elif response == "":
        updated = False
        if i.corrections_ru_meaning and i.corrections_ru_meaning.strip():
            db_entry.ru.ru_meaning = i.corrections_ru_meaning.strip()
            count_meanings += 1
            updated = True
        if i.corrections_ru_meaning_lit and i.corrections_ru_meaning_lit.strip():
            db_entry.ru.ru_meaning_lit = i.corrections_ru_meaning_lit.strip()
            count_lit += 1
            updated = True

        if updated:
            console.print("[green]Updated (where suggested)")
        else:
            console.print("[yellow]Nothing to update (suggestions were empty)")
    else:
        console.print("[red]Invalid input, skipping...")

# check that the output is as expected, then uncomment commit
db_session.commit()

# save the updated csv/tsv
if csv_data:
    # ensure 'processed' key exists in all rows for DictWriter
    fieldnames = list(csv_data[0].keys())
    if "processed" not in fieldnames:
        fieldnames.append("processed")

    for row in csv_data:
        if "processed" not in row:
            row.processed = ""

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(csv_data)

# don't forget to always close the db session
db_session.close()

console.print("[green]Database update process completed.")
console.print(f"Number of updated ru_meanings: {count_meanings}")
console.print(f"Number of updated ru_meaning_lit: {count_lit}")
