#!/usr/bin/env python3
"""Extract Pali and English sentences for Pali words from SuttaCentral data."""

import csv
import re
from pathlib import Path

from tools.printer import printer as pr


def clean_text(text):
    """Removes curly quotes, unwanted characters, and replaces ṁ with ṃ."""
    text = re.sub(r"[“”]", "", text)  # Remove curly quotes
    text = re.sub(r"ṁ", "ṃ", text)
    return text


def search_word_in_folder(word, folder: Path):
    """Searches for a word in a given folder and returns the first match found."""
    word = clean_text(word)  # Normalize search term

    if not folder.exists():
        return None, None

    for file_path in folder.rglob("*.json"):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if re.search(rf"\b{word}\b", clean_text(line), re.IGNORECASE):
                    return file_path.name, line.strip()  # Return first match found
    return None, None


def extract_id(line):
    """Extracts Source ID from a matched line."""
    match = re.search(r'"(pli-tv-kd[^\"]+)":', line)
    return match.group(1) if match else None


def extract_pali_sentence(line):
    """Extracts the actual Pali sentence from JSON line."""
    match = re.search(r'":\s*"([^"]+)"', line)
    return clean_text(match.group(1)) if match else ""


def find_translation(id, translation_folder: Path):
    """Finds the English translation corresponding to a given ID."""
    if not translation_folder.exists():
        return "No translation found"

    for file_path in translation_folder.rglob("*.json"):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if id and id in line:
                    return extract_pali_sentence(line)  # Extract cleaned translation
    return "No translation found"


def process_csv(
    input_csv: Path,
    output_found_csv: Path,
    output_not_found_csv: Path,
    primary_pali_folder: Path,
    variant_folder: Path,
    translation_folder: Path,
):
    """Processes the input CSV, searches for words, and writes output into two CSVs."""
    pr.tic()

    if not input_csv.exists():
        pr.red(f"Error: {input_csv} does not exist")
        pr.toc()
        return

    pr.green_tmr("processing CSV")
    found_count = 0
    not_found_count = 0

    # Ensure output directories exist
    output_found_csv.parent.mkdir(parents=True, exist_ok=True)

    with (
        open(input_csv, "r", encoding="utf-8") as infile,
        open(output_found_csv, "w", encoding="utf-8", newline="") as found_file,
        open(output_not_found_csv, "w", encoding="utf-8", newline="") as not_found_file,
    ):
        reader = csv.reader(infile)
        found_writer = csv.writer(found_file, delimiter=";")
        not_found_writer = csv.writer(not_found_file, delimiter=";")

        # Write headers
        found_writer.writerow(
            ["Pali Word", "Source ID", "Pali Sentence", "English Translation"]
        )
        not_found_writer.writerow(["Pali Word"])

        for row in reader:
            if not row:
                continue
            word = row[0].strip()
            _, pali_line = search_word_in_folder(word, primary_pali_folder)

            if not pali_line:
                # If not found in primary, check in variant
                _, pali_line = search_word_in_folder(word, variant_folder)
                if pali_line:
                    # Try to find corresponding primary sentence
                    id = extract_id(pali_line)
                    if id:
                        _, primary_pali_line = search_word_in_folder(
                            id, primary_pali_folder
                        )
                        if primary_pali_line:
                            pali_line = (
                                primary_pali_line  # Use primary version if available
                            )

            if not pali_line:
                not_found_writer.writerow([word])  # Save word in "not found" file
                not_found_count += 1
                continue

            id = extract_id(pali_line)
            pali_sentence = extract_pali_sentence(pali_line)
            translation = (
                find_translation(id, translation_folder)
                if id
                else "No translation found"
            )

            # Write output with 4 columns
            found_writer.writerow([word, id, pali_sentence, translation])
            found_count += 1

    pr.yes("ok")
    pr.summary("Found", found_count)
    pr.summary("Not Found", not_found_count)
    pr.toc()


if __name__ == "__main__":
    input_csv = Path("temp/input.csv")
    output_found_csv = Path("temp/output_found.csv")
    output_not_found_csv = Path("temp/output_not_found.csv")

    base_dir = Path("resources/sc-data/sc_bilara_data")
    primary_pali_folder = base_dir / "root/pli/ms/vinaya/pli-tv-kd"
    variant_folder = base_dir / "variant"
    translation_folder = base_dir / "translation/en/brahmali/vinaya/pli-tv-kd"

    process_csv(
        input_csv,
        output_found_csv,
        output_not_found_csv,
        primary_pali_folder,
        variant_folder,
        translation_folder,
    )
