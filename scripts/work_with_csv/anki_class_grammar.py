#!/usr/bin/env python3

# Generate csvs for grammar anki deck for all classes from the database.
# https://sasanarakkha.github.io/study-tools/pali-class/pali-class.html

import pandas as pd
from datetime import datetime
from pathlib import Path
from tools.paths_dps import DPSPaths
from tools.paths import ProjectPaths

from tools.printer import printer as pr

dpspth = DPSPaths()
pth = ProjectPaths()

current_date = datetime.now().strftime("%m-%d")


def main():
    pr.tic()
    pr.title("Extracting grammar csvs...")
    excel_file_dir = pth.temp_dir / "grammar.xlsx"
    # moving_grammar(excel_file_dir)
    make_grammar_csvs(excel_file_dir)
    check_duplicate_ids(excel_file_dir)
    pr.toc()


def check_duplicate_ids(excel_file_dir):
    # Load the Excel file into a pandas ExcelFile object
    with pd.ExcelFile(excel_file_dir) as excel_file:
        # Dictionary to store [id] values from each sheet
        id_dict = {}

        # Loop through each sheet in the Excel file
        for sheet_name in excel_file.sheet_names:
            # Read the current sheet into a DataFrame
            df = excel_file.parse(sheet_name)

            # Check if df is a DataFrame
            if isinstance(df, pd.DataFrame):
                # Check if the first column exists and is named 'id'
                if df.columns[0] == "id":
                    # Iterate through each [id] value in the first column
                    for id_value in df[df.columns[0]]:
                        # Check if the [id] value is already in the dictionary
                        if id_value in id_dict:
                            # If it is, print the [id] value in red
                            pr.red(f"{id_value}")
                        else:
                            # If not, add the [id] value to the dictionary
                            id_dict[id_value] = True
                else:
                    print(
                        f"Sheet {sheet_name} does not have an 'id' column as the first column."
                    )
            else:
                print(
                    f"Sheet {sheet_name} did not load as a DataFrame. It is a {type(df)}."
                )


def make_grammar_csvs(excel_file_dir):
    # Load the Excel file into a pandas ExcelFile object
    # Create a dictionary to store the DataFrames
    dfs = {}

    with pd.ExcelFile(excel_file_dir) as excel_file:
        sheet_names = excel_file.sheet_names

        # Loop through each sheet in the Excel file
        for sheet_name in sheet_names:
            # Read the current sheet into a DataFrame
            df = excel_file.parse(sheet_name)

            # Check if df is a DataFrame
            if isinstance(df, pd.DataFrame):
                # Convert the 'id' column to integers
                if "id" in df.columns:
                    df["id"] = df["id"].fillna(0).astype(int)
                    # remove rows where id is 0 or empty
                    df = df[df["id"] != 0]

                # Convert the values in the '2nd column' to strings
                df.iloc[:, 1] = df.iloc[:, 1].astype(str)

                second_column_name = df.columns[1]
                df["feedback"] = df.apply(
                    lambda row: (
                        f"""Spot a mistake? <a class="link" href="https://docs.google.com/forms/d/1Z8Jjt0-E0HNX7ygABIzAcrChG23M3IOyoZGQ-EDRzXY/viewform?usp=pp_url&entry.438735500"""
                        f"""={row[second_column_name]}"""
                        f"""&entry.957833742=Anki Deck Grammar">Fix it here</a>"""
                    ),
                    axis=1,
                )

                # Reset the index and drop the old index
                df.reset_index(drop=True, inplace=True)

                # Add the current date to the DataFrame as test
                df["test"] = current_date

                # Store the DataFrame in the dictionary with the sheet name as the key
                dfs[sheet_name] = df
            else:
                print(
                    f"Sheet {sheet_name} did not load as a DataFrame. It is a {type(df)}."
                )

    # Now you can access each DataFrame using its sheet name as a key
    # For example, dfs['Sheet1'] will give you the DataFrame for 'Sheet1', and so on.

    pr.green("extracting df_sum_abbr for class.")

    # Load abbreviations from TSV, filter out those with capital letters, and add id/pattern columns
    abr_dir = pth.abbreviations_tsv_path

    # Load abbreviations from TSV, filter out capital letters, and add id/pattern columns
    df_abbr = pd.read_csv(abr_dir, sep="\t")
    assert isinstance(df_abbr, pd.DataFrame)
    df_abbr = df_abbr[
        df_abbr["abbrev"].notna() & ~df_abbr["abbrev"].str.contains("[A-Z]")
    ]
    assert isinstance(df_abbr, pd.DataFrame)
    df_abbr["id"] = range(101, 101 + len(df_abbr))
    df_abbr["type"] = "abbreviation"
    # rename column "pāli" into "pali"
    df_abbr.rename(columns={"pāli": "pali"}, inplace=True)

    # Add feedback and test columns to match other dataframes
    second_column_name = (
        df_abbr.columns[1] if len(df_abbr.columns) > 1 else df_abbr.columns[0]
    )
    df_abbr["feedback"] = df_abbr.apply(
        lambda row: (
            f"""Spot a mistake? <a class="link" href="https://docs.google.com/forms/d/1Z8Jjt0-E0HNX7ygABIzAcrChG23M3IOyoZGQ-EDRzXY/viewform?usp=pp_url&entry.438735500"""
            f"""={row[second_column_name]}"""
            f"""&entry.957833742=Anki Deck Grammar">Fix it here</a>"""
        ),
        axis=1,
    )
    df_abbr["test"] = current_date

    # Reorder columns to put 'id' first, then 'abbrev', then the rest
    columns = ["id", "abbrev"] + [
        col for col in df_abbr.columns if col not in ["id", "abbrev"]
    ]
    df_abbr = df_abbr[columns]

    # Concatenate df_abbr_class, df_alph, df_samasa, df_upasagga into df_sum_abbr
    df_abbr_class = df_abbr.drop(columns=["ru_meaning", "ru_abbrev"])
    df_upasagga_filtered = dfs["upasagga"][dfs["upasagga"]["example"].notna()]
    df_sum_abbr = pd.concat(
        [df_abbr_class, dfs["alph"], dfs["samasa"], df_upasagga_filtered, dfs["roots"]]
    )
    assert isinstance(df_sum_abbr, pd.DataFrame)

    # Convert 'id' to integer, dropping rows where 'id' is NaN
    df_sum_abbr = df_sum_abbr.dropna(subset=["id"])
    df_sum_abbr["id"] = df_sum_abbr["id"].astype(int)

    # Save df_sum_abbr to a CSV file
    sum_abbr_path = dpspth.anki_csvs_dir / "pali_class" / "grammar" / "cl_sum_abbr.csv"
    df_sum_abbr.to_csv(sum_abbr_path, sep="\t", index=False)

    row_count = len(df_sum_abbr)
    print("Number of rows:", row_count)

    pr.green("extracting df_sum_sandhi for class.")

    # Concatenate the DataFrames and store the result in df_sum_sandhi
    df_sum_sandhi = pd.concat(
        [
            dfs["v_sandhi"],
            dfs["c_sandhi"],
            dfs["m_sandhi"],
            dfs["assim"],
            dfs["mx_sandhi"],
            dfs["change_s"],
            dfs["irr_base"],
            dfs["taddhita"],
            dfs["kitaka"],
            dfs["vuddhi"],
        ]
    )

    # Convert 'id' to integer, dropping rows where 'id' is NaN
    df_sum_sandhi = df_sum_sandhi.dropna(subset=["id"])
    df_sum_sandhi["id"] = df_sum_sandhi["id"].astype(int)

    # Save df_sum_sandhi to a CSV file
    sum_sandhi_path = (
        dpspth.anki_csvs_dir / "pali_class" / "grammar" / "cl_sum_sandhi.csv"
    )
    df_sum_sandhi.to_csv(sum_sandhi_path, sep="\t", index=False)

    row_count = len(df_sum_sandhi)
    print("Number of rows:", row_count)

    pr.green("extracting cl_sum_gramm for class.")

    # Define which sheets go into the main grammar file
    sheets_for_gramm = [
        sheet_name
        for sheet_name in sheet_names
        if sheet_name
        not in [
            "abbr",
            "alph",
            "samasa",
            "upasagga",
            "roots",
            "v_sandhi",
            "c_sandhi",
            "m_sandhi",
            "assim",
            "mx_sandhi",
            "change_s",
            "irr_base",
            "taddhita",
            "kitaka",
            "vuddhi",
        ]
    ]

    # --- Create and save ru_cl_sum_gramm.csv with 'id' and 'native' ---
    native_dfs = []
    for sheet_name in sheets_for_gramm:
        if "id" in dfs[sheet_name].columns and "native" in dfs[sheet_name].columns:
            native_dfs.append(dfs[sheet_name][["id", "native"]])

    if native_dfs:
        df_sum_native = pd.concat(native_dfs, ignore_index=True)
        ru_sum_gramm_path = (
            dpspth.anki_csvs_dir / "pali_class" / "grammar" / "ru_cl_sum_gramm.csv"
        )
        df_sum_native.to_csv(ru_sum_gramm_path, sep="\t", index=False)

    # --- Create main cl_sum_gramm.csv with an empty 'native' column ---
    df_sum_gramm = pd.concat([dfs[s] for s in sheets_for_gramm])
    # Clear all values in the 'native' column
    df_sum_gramm["native"] = ""

    # Convert 'id' to integer, dropping rows where 'id' is NaN
    df_sum_gramm = df_sum_gramm.dropna(subset=["id"])
    df_sum_gramm["id"] = df_sum_gramm["id"].astype(int)

    # Save df_sum_gramm to a CSV file
    sum_gramm_path = (
        dpspth.anki_csvs_dir / "pali_class" / "grammar" / "cl_sum_gramm.csv"
    )
    df_sum_gramm.to_csv(sum_gramm_path, sep="\t", index=False)

    row_count = len(df_sum_gramm)
    print("Number of rows:", row_count)

    if dpspth.sbs_anki_style_dir.exists():
        pr.green("Saving field list to sbs directory.")

        # Save the column list of df_sum_abbr to a text file
        grammar_abbr_path = dpspth.sbs_anki_style_dir / "field-list-grammar-abbr.md"
        with open(grammar_abbr_path, "w") as file:
            columns_with_marks = list(df_sum_abbr.columns) + ["marks"]
            file.write("# Field List: Grammar Abbr\n\n```\n")
            file.write("\n".join(columns_with_marks))
            file.write("\n```\n")

        # Save the column list of df_sum_sandhi to a text file
        grammar_sandhi_path = dpspth.sbs_anki_style_dir / "field-list-grammar-sandhi.md"
        with open(grammar_sandhi_path, "w") as file:
            columns_with_marks = list(df_sum_sandhi.columns) + ["marks"]
            file.write("# Field List: Grammar Sandhi\n\n```\n")
            file.write("\n".join(columns_with_marks))
            file.write("\n```\n")

        # Save the column list of df_sum_gramm to a text file
        grammar_grammar_path = dpspth.sbs_anki_style_dir / "field-list-grammar-gramm.md"
        with open(grammar_grammar_path, "w") as file:
            columns_with_marks = list(df_sum_gramm.columns) + ["marks"]
            file.write("# Field List: Grammar Gramm\n\n```\n")
            file.write("\n".join(columns_with_marks))
            file.write("\n```\n")

    else:
        pr.red("Study-tools/anki-style directory does not exist.")


if __name__ == "__main__":
    main()
