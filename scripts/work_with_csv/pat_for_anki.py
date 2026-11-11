#!/usr/bin/env python3

"""
Processes the local Patimokkha word-by-word TSV (dpspth.pat_source_path, in the
study-tools repo) for Anki: keeps the first occurrence of each word, selects
columns, adds new computed columns, and saves the result to
anki_patimokkha.csv in anki_csvs_dir.
"""

import csv  # For csv.QUOTE_MINIMAL
import re
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd

from tools.paths_dps import DPSPaths
from tools.printer import printer as pr

dpspth = DPSPaths()

COLUMNS_TO_KEEP: list[str] = [
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

_FEEDBACK_FORM_URL = (
    "https://docs.google.com/forms/d/e/1FAIpQLSdG6zKDtlwibtrX-cbKVn4WmIs8miH4VnuJvb7f94plCDKJyA/viewform"
    "?usp=pp_url&entry.438735500={pali_word}&entry.1433863141=Anki-{date_long}"
)


_BOLD_TAG = re.compile(r"</?b>")


def _filter_input_rows(df: pd.DataFrame, input_path: Path) -> pd.DataFrame:
    """Keep first occurrences of each word (rows with a pos) that have a meaning.

    The key is the pali cell without <b> tags and surrounding whitespace.
    """
    has_pos = df["pos"].str.strip() != ""
    key = df["pali"].map(lambda v: _BOLD_TAG.sub("", v).strip())
    first_idx = key.loc[has_pos].drop_duplicates().index
    condition = df.index.isin(first_idx)
    if "meaning" in df.columns:
        condition &= (df["meaning"].str.strip() != "").to_numpy()
    else:
        pr.amber(
            f"'meaning' column not found in '{input_path}'. Not filtering on meaning."
        )

    df_filtered = df.loc[condition].copy()
    if df_filtered.empty:
        pr.amber(
            f"No rows found in '{input_path}' matching the filter criteria "
            "(first occurrence of a word with a pos AND 'meaning' is not empty). "
            "Output will be an empty file with headers."
        )
    return df_filtered


def _build_feedback_column(df_processed: pd.DataFrame, date_long: str) -> pd.Series:
    if "pali" in df_processed.columns and not df_processed["pali"].empty:
        return cast(
            pd.Series,
            df_processed["pali"].apply(
                lambda pali_word: (
                    'Spot a mistake? <a class="link" href="'
                    + _FEEDBACK_FORM_URL.format(
                        pali_word=pali_word if pd.notna(pali_word) else "",
                        date_long=date_long,
                    )
                    + '">Fix it here</a>.'
                )
            ),
        )
    feedback = (
        'Spot a mistake? <a class="link" href="'
        + _FEEDBACK_FORM_URL.format(pali_word="", date_long=date_long)
        + '">Fix it here</a>.'
    )
    return pd.Series([feedback] * len(df_processed), index=df_processed.index)


def _build_web_link_column(
    df_processed: pd.DataFrame, sources_links_path: Path
) -> pd.Series:
    empty_links = pd.Series([""] * len(df_processed), index=df_processed.index)

    if not sources_links_path.exists():
        pr.amber(
            f"Source links file '{sources_links_path}' not found. 'web_link' column will be empty."
        )
        return empty_links

    try:
        sources_links_df = pd.read_csv(sources_links_path, sep="\t")
        source_to_link: dict[str, str] = dict(
            zip(sources_links_df["source"], sources_links_df["web_link"])
        )

        if "source" not in df_processed.columns or df_processed["source"].empty:
            return empty_links

        df_processed["source"] = df_processed["source"].astype(str)
        web_links = df_processed["source"].map(cast(Any, source_to_link))
        return cast(
            pd.Series,
            web_links.apply(
                lambda x: (
                    f'Check out the web analysis of rule <a class="link" href="{x}">here</a>.'
                    if pd.notna(x) and x
                    else ""
                )
            ),
        )
    except (pd.errors.ParserError, OSError, KeyError) as e_sl:
        pr.amber(
            f"Could not process '{sources_links_path}': {e_sl}. 'web_link' column may be incomplete or empty."
        )
        return empty_links


def _write_field_list(df_processed: pd.DataFrame, sbs_anki_style_dir: Path) -> None:
    if not sbs_anki_style_dir.exists():
        return

    pr.green("Saving field list to sbs directory.")
    field_list_path = sbs_anki_style_dir / "field-list-pat.md"
    columns_with_notez = list(df_processed.columns) + ["notez"]
    with open(field_list_path, "w", encoding="utf-8") as file:
        file.write("# Field List: Patimokkha\n\n```\n")
        file.write("\n".join(columns_with_notez))
        file.write("\n```\n")


def process_patimokkha_csv() -> None:
    """
    Main processing function.
    Reads the source TSV, applies transformations, and writes the output CSV.
    """
    input_csv_path = dpspth.pat_source_path
    output_csv_path = dpspth.anki_csvs_dir / "anki_patimokkha.csv"
    sources_links_path = dpspth.pat_links_path  # formerly sources_links.tsv

    try:
        # dtype=str + keep_default_na=False: every cell stays a string ("" when blank).
        df = pd.read_csv(input_csv_path, sep="\t", dtype=str, keep_default_na=False)
    except FileNotFoundError:
        pr.red(f"Input TSV file not found at '{input_csv_path}'")
        return
    except (pd.errors.ParserError, OSError, UnicodeDecodeError) as e:
        pr.red(f"Error reading TSV '{input_csv_path}': {e}")
        return

    if df.empty:
        pr.amber(
            f"Input TSV '{input_csv_path}' is empty. Output will be an empty file with headers."
        )
        df_filtered = pd.DataFrame()
    else:
        df_filtered = _filter_input_rows(df, input_csv_path)

    df_processed = df_filtered.reindex(columns=COLUMNS_TO_KEEP, fill_value="")

    now = datetime.now().astimezone()
    date_short = now.strftime("%m-%d")
    date_long = now.strftime("%y-%m-%d")

    df_processed["test"] = date_short
    df_processed["order"] = range(1, len(df_processed) + 1)
    df_processed["feedback"] = _build_feedback_column(df_processed, date_long)
    df_processed["web_link"] = _build_web_link_column(df_processed, sources_links_path)

    try:
        # Ensure output directory exists
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        # Save as tab-separated CSV
        df_processed.to_csv(
            output_csv_path, index=False, sep="\t", quoting=csv.QUOTE_MINIMAL
        )
        pr.green(f"Successfully processed CSV and saved to '{output_csv_path}'")
    except OSError as e:
        pr.red(f"Error writing processed CSV to '{output_csv_path}': {e}")

    _write_field_list(df_processed, dpspth.sbs_anki_style_dir)


if __name__ == "__main__":
    pr.tic()
    pr.green_title("Processing patimokkha CSV for Anki...")
    process_patimokkha_csv()
    pr.toc()
