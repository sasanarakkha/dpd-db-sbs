import os
import re

import pandas as pd

from tools.paths_dps import DPSPaths


def get_pali_sentences_from_txt(filepath: str) -> set[str]:
    """
    Reads a text file and extracts all Pali sentences, including multi-line sentences.

    Args:
        filepath: The path to the text file.

    Returns:
        A set of Pali sentences for efficient lookup.
    """
    sentences = set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("Pali:"):
                # Start collecting lines for this Pali sentence
                sentence = line.split(":", 1)[1].strip()
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    # Stop if we hit a blank line or a new section
                    if not next_line or next_line.startswith(
                        ("English Translation:", "Sutta Number:", "Pali:")
                    ):
                        break
                    sentence += " " + next_line
                    i += 1
                sentences.add(sentence)
            else:
                i += 1
    except FileNotFoundError:
        print(f"Error: Exercises file not found at {filepath}")
        return set()
    return sentences


def txt_contains_sentence(txt_path: str, sentence: str) -> bool:
    """Check if the cleaned sentence exists anywhere in the txt file."""
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            txt_content = f.read()
        return sentence in txt_content
    except FileNotFoundError:
        print(f"Error: Exercises file not found at {txt_path}")
        return False


def find_mismatched_examples(mode: str, source: str, dpspth: DPSPaths):
    """
    Finds examples in a CSV file that, after cleaning, do not exist
    in a corresponding text file and prints their IDs.

    Args:
        mode: The type of data to check ("pali_class" or "discourses").
        source: The class number or sutta name to process.
    """
    if mode == "pali_class":
        base_path = dpspth.pali_class_output_dir
        csv_path = os.path.join(base_path, "done", f"class_{source}_output done.csv")
        txt_path = os.path.join(base_path, "exercises", f"exercises_class_{source}.txt")
    elif mode == "discourses":
        base_path = dpspth.discourses_output_dir
        csv_path = os.path.join(base_path, "done", f"{source} done.csv")
        txt_path = os.path.join(base_path, "suttas", "combined.txt")
    else:
        print(f"Unknown mode: {mode}")
        return

    print(f"Checking CSV: {csv_path}")
    print(f"Against TXT: {txt_path}\n")

    if mode == "pali_class":
        pali_sentences = get_pali_sentences_from_txt(txt_path)
        if not pali_sentences:
            print("No sentences found in the exercises file. Exiting.")
            return

    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_path}")
        return

    required_columns = ["id", "class_example"]
    if not all(col in df.columns for col in required_columns):
        print(f"Error: CSV file must contain all of {required_columns} columns.")
        return

    mismatched_ids = []
    for _, row in df.iterrows():
        # Skip rows where 'class_source' column contains "Class Doc"
        if (
            "class_source" in df.columns
            and pd.notna(row["class_source"])  # pyright: ignore
            and "Class Doc" in str(row["class_source"])
        ):
            continue

        example = row["class_example"]

        # Print ID if class_example is empty or NaN
        if pd.isna(example) or str(example).strip() == "":  # pyright: ignore
            print(f"Empty class_example for ID: {row['id']}")
            continue

        cleaned_example = re.sub(r"</?b>", "", str(example)).strip()
        # Normalize whitespace in the example
        cleaned_example_norm = re.sub(r"\s+", " ", cleaned_example)

        # Check if the cleaned example exists anywhere in the txt file
        if mode == "pali_class":
            found = False
            for sent in pali_sentences:
                # Normalize whitespace in the txt sentence
                sent_norm = re.sub(r"\s+", " ", sent)
                if cleaned_example_norm in sent_norm:
                    found = True
                    break
            if not found:
                mismatched_ids.append(row["id"])

        elif mode == "discourses":
            if not txt_contains_sentence(txt_path, cleaned_example):
                mismatched_ids.append(row["id"])

    if mismatched_ids:
        print("Mismatched IDs (example from CSV not found in TXT):")
        for an_id in mismatched_ids:
            print(an_id)
    else:
        print(
            "All examples in the CSV were found in the exercises text file. No mismatches detected."
        )


def main():
    """Main function to run the check"""
    # --- SET THE MODE and CLASS NUMBER or SUTTA TO CHECK HERE ---
    # source = "29"
    source = "rest"
    # mode = "pali_class"
    mode = "discourses"
    # -----------------------------------------

    dpspth = DPSPaths()
    print(f"--> Checking data for {mode} : {source}\n")
    find_mismatched_examples(mode, source, dpspth)


if __name__ == "__main__":
    main()
