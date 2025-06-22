import os
import re
import pandas as pd
from tools.paths_dps import DPSPaths



def get_pali_sentences_from_txt(filepath: str) -> set[str]:
    """
    Reads a text file and extracts all Pali sentences.

    Args:
        filepath: The path to the text file.

    Returns:
        A set of Pali sentences for efficient lookup.
    """
    sentences = set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("Pali:"):
                    # Extract the sentence part, which is after "Pali: "
                    sentence = line.split(":", 1)[1].strip()
                    sentences.add(sentence)
    except FileNotFoundError:
        print(f"Error: Exercises file not found at {filepath}")
        return set()
    return sentences


def find_mismatched_examples(class_number: int, dpspth: DPSPaths):
    """
    Finds examples in a CSV file that, after cleaning, do not exist
    in a corresponding text file and prints their IDs.

    Args:
        class_number: The class number to process.
    """
    # Assuming the script is run from a directory where this path is valid.
    # You can adjust this base_path if needed.
    base_path = dpspth.pali_class_output_dir
    csv_path = os.path.join(base_path, "output", f"class_{class_number}_output.csv")
    txt_path = os.path.join(base_path, "exercises", f"exercises_class_{class_number}.txt")

    print(f"Checking CSV: {csv_path}")
    print(f"Against TXT: {txt_path}\n")

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
        if "class_source" in df.columns and pd.notna(row["class_source"]) and "Class Doc" in str(row["class_source"]):
            continue

        example = row["class_example"]

        if pd.isna(example):
            continue

        cleaned_example = re.sub(r"</?b>", "", str(example)).strip()

        if cleaned_example not in pali_sentences:
            mismatched_ids.append(row["id"])

    if mismatched_ids:
        print("Mismatched IDs (example from CSV not found in TXT):")
        for an_id in mismatched_ids:
            print(an_id)
    else:
        print("All examples in the CSV were found in the exercises text file. No mismatches detected.")


def main():
    """Main function to run the check for a specific class."""
    # --- SET THE CLASS NUMBER TO CHECK HERE ---
    class_to_check = 15
    # -----------------------------------------

    dpspth = DPSPaths()
    print(f"--> Checking data for class: {class_to_check}\n")
    find_mismatched_examples(class_to_check, dpspth)


if __name__ == "__main__":
    main()