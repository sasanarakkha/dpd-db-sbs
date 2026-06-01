#!/usr/bin/env python3

"""
Processes a specific CSV file (patimokkha_word_by_word.csv from temp_dir)
for Anki, filters rows, selects columns, adds new computed columns,
and saves the result to patimokkha_anki.csv in anki_csvs_dir.
"""

import pandas as pd
import csv  # For csv.QUOTE_MINIMAL
from datetime import datetime
from typing import Any, cast  # For type hinting with pandas
from tools.printer import printer as pr

from tools.paths_dps import DPSPaths
from tools.paths import ProjectPaths

pth = ProjectPaths()
dpspth = DPSPaths()


def process_patimokkha_csv() -> None:
    """
    Main processing function.
    Reads the input CSV, applies transformations, and writes the output CSV.
    """
    input_csv_path = pth.temp_dir / "patimokkha_word_by_word.csv"
    output_csv_path = dpspth.anki_csvs_dir / "anki_patimokkha.csv"
    sources_links_path = dpspth.pat_links_path  # formerly sources_links.tsv

    try:
        # Read with tab separator if the intermediate CSV is tab-separated
        # If xlsx2csv.py produces comma-separated, use sep=','
        df = pd.read_csv(input_csv_path, sep="\t")
    except FileNotFoundError:
        pr.red(f"Input CSV file not found at '{input_csv_path}'")
        return
    except Exception as e:
        pr.red(f"Error reading CSV '{input_csv_path}': {e}")
        return

    if df.empty:
        pr.amber(
            f"Input CSV '{input_csv_path}' is empty. Output will be an empty file with headers."
        )
        df_filtered = pd.DataFrame()
    else:
        # Ensure the first column is treated as string for comparison "1"
        df.iloc[:, 0] = df.iloc[:, 0].astype(str)

        # Define filter conditions
        condition1 = df.iloc[:, 0] == "1"

        # Check if 'meaning' column exists before trying to filter on it
        if "meaning" in df.columns:
            condition2 = df["meaning"].fillna("").astype(str).str.strip() != ""
            combined_condition = condition1 & condition2
        else:
            pr.amber(
                f"'meaning' column not found in '{input_csv_path}'. Filtering only on the first column."
            )
            combined_condition = condition1

        df_filtered = df[combined_condition].copy()

    if df_filtered.empty and not df.empty:
        pr.amber(
            f"No rows found in '{input_csv_path}' matching the filter criteria (first column is '1' AND 'meaning' is not empty). Output will be an empty file with headers."
        )

    columns_to_keep: list[str] = [
        "pali",
        "pos",
        "grammar",
        "case",
        "native",
        "meaning",
        "meaning_lit",
        "root",
        "root_gp",
        "root_sign",
        "base",
        "construction",
        "compound_type",
        "compound_construction",
        "variant",
        "abbrev",
        "source",
        "sentence",
        "commentary",
    ]

    # Create a new DataFrame with the desired columns.
    # If df_filtered is empty, this creates an empty DataFrame with these columns.
    df_processed = pd.DataFrame(columns=pd.Index(columns_to_keep))

    if not df_filtered.empty:
        for col in columns_to_keep:
            if col in df_filtered.columns:
                df_processed[col] = df_filtered[col]
            else:
                df_processed[col] = ""  # Add missing columns as empty

    df_processed.loc[:, "test"] = datetime.today().strftime("%m-%d")
    df_processed.loc[:, "order"] = range(1, len(df_processed) + 1)

    if "pali" in df_processed.columns and not df_processed["pali"].empty:
        df_processed.loc[:, "feedback"] = df_processed["pali"].apply(
            lambda pali_word: (
                f'Spot a mistake? <a class="link" href="https://docs.google.com/forms/d/e/1FAIpQLSdG6zKDtlwibtrX-cbKVn4WmIs8miH4VnuJvb7f94plCDKJyA/viewform?usp=pp_url&entry.438735500={pali_word if pd.notna(pali_word) else ""}&entry.1433863141=Anki-{datetime.today().strftime("%y-%m-%d")}">Fix it here</a>.'
            )
        )
    else:
        df_processed.loc[:, "feedback"] = (
            f'Spot a mistake? <a class="link" href="https://docs.google.com/forms/d/e/1FAIpQLSdG6zKDtlwibtrX-cbKVn4WmIs8miH4VnuJvb7f94plCDKJyA/viewform?usp=pp_url&entry.1433863141=Anki-{datetime.today().strftime("%y-%m-%d")}">Fix it here</a>.'
        )

    if sources_links_path.exists():
        try:
            sources_links_df = pd.read_csv(sources_links_path, sep="\t")
            source_to_link: dict[str, str] = cast(
                dict[str, str],
                dict(zip(sources_links_df["source"], sources_links_df["web_link"])),
            )

            if "source" in df_processed.columns and not df_processed["source"].empty:
                df_processed.loc[:, "source"] = df_processed["source"].astype(str)
                df_processed.loc[:, "web_link_temp"] = df_processed["source"].map(
                    cast(Any, source_to_link)
                )
                df_processed.loc[:, "web_link"] = df_processed["web_link_temp"].apply(
                    lambda x: (
                        f'Check out the web analysis of rule <a class="link" href="{x}">here</a>.'
                        if pd.notna(x) and x
                        else ""
                    )
                )
                df_processed.drop(columns=["web_link_temp"], inplace=True)
            else:
                df_processed.loc[:, "web_link"] = ""
        except Exception as e_sl:
            pr.amber(
                f"Could not process '{sources_links_path}': {e_sl}. 'web_link' column may be incomplete or empty."
            )
            df_processed.loc[:, "web_link"] = ""
    else:
        pr.amber(
            f"Source links file '{sources_links_path}' not found. 'web_link' column will be empty."
        )
        df_processed.loc[:, "web_link"] = ""

    try:
        # Ensure output directory exists
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        # Save as tab-separated CSV
        df_processed.to_csv(
            output_csv_path, index=False, sep="\t", quoting=csv.QUOTE_MINIMAL
        )
        pr.green(f"Successfully processed CSV and saved to '{output_csv_path}'")
    except Exception as e:
        pr.red(f"Error writing processed CSV to '{output_csv_path}': {e}")

    if dpspth.sbs_anki_style_dir.exists():
        pr.green("Saving field list to sbs directory.")

        # Save the column list of df_processed to a text file
        field_list_path = dpspth.sbs_anki_style_dir / "field-list-pat.md"
        with open(field_list_path, "w") as file:
            columns_with_notez = list(df_processed.columns) + ["notez"]
            file.write("# Field List: Patimokkha\n\n```\n")
            file.write("\n".join(columns_with_notez))
            file.write("\n```\n")


if __name__ == "__main__":
    pr.tic()
    pr.green_title("Processing patimokkha CSV for Anki...")
    process_patimokkha_csv()
    pr.toc()
