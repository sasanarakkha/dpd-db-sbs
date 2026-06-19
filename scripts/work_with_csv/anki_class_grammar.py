#!/usr/bin/env python3

# Generate csvs for grammar anki deck for all classes from the database.
# https://sasanarakkha.github.io/study-tools/pali-class/pali-class.html

from datetime import datetime
from pathlib import Path

import pandas as pd

from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr


def make_feedback_link(question_text: str, update_date: str) -> str:
    """Build the prefilled grammar feedback form link."""
    return (
        f"""Spot a mistake? <a class="link" href="https://docs.google.com/forms/d/1Z8Jjt0-E0HNX7ygABIzAcrChG23M3IOyoZGQ-EDRzXY/viewform?usp=pp_url&entry.438735500"""
        f"""={question_text}"""
        f"""&entry.957833742=Anki Deck Grammar"""
        f"""&entry.1940411063=Anki-{update_date}">Fix it here</a>"""
    )


def main() -> None:
    pr.tic()
    pr.green_title("Extracting grammar csvs...")
    dpspth = DPSPaths()
    pth = ProjectPaths()
    excel_file_dir = pth.temp_dir / "grammar.xlsx"
    make_grammar_csvs(excel_file_dir, dpspth, pth)
    check_duplicate_ids(excel_file_dir)
    pr.toc()


def _warn_invalid_sheet(sheet_name: str | int, df: pd.DataFrame) -> None:
    if df.columns[0] == "id":
        return
    pr.amber(f"Sheet {sheet_name} does not have an 'id' column as the first column.")


def check_duplicate_ids(excel_file_dir: Path) -> None:
    with pd.ExcelFile(excel_file_dir) as excel_file:
        seen_ids: set[object] = set()

        for sheet_name in excel_file.sheet_names:
            df = excel_file.parse(sheet_name)

            if not isinstance(df, pd.DataFrame):
                pr.amber(
                    f"Sheet {sheet_name} did not load as a DataFrame. It is a {type(df)}."
                )
                continue

            if df.columns[0] != "id":
                _warn_invalid_sheet(sheet_name, df)
                continue

            for id_value in df[df.columns[0]]:
                if id_value in seen_ids:
                    pr.red(f"{id_value}")
                else:
                    seen_ids.add(id_value)


def make_grammar_csvs(
    excel_file_dir: Path, dpspth: DPSPaths, pth: ProjectPaths
) -> None:
    now = datetime.now().astimezone()
    current_date = now.strftime("%m-%d")
    current_date_year = now.strftime("%y-%m-%d")

    # Create a dictionary to store the DataFrames
    dfs: dict[str | int, pd.DataFrame] = {}

    with pd.ExcelFile(excel_file_dir) as excel_file:
        sheet_names = excel_file.sheet_names

        for sheet_name in sheet_names:
            df = excel_file.parse(sheet_name)

            if not isinstance(df, pd.DataFrame):
                pr.amber(
                    f"Sheet {sheet_name} did not load as a DataFrame. It is a {type(df)}."
                )
                continue

            # Convert the 'id' column to integers
            if "id" in df.columns:
                df["id"] = df["id"].fillna(0).astype(int)
                # remove rows where id is 0 or empty
                df = df[df["id"] != 0]

            # Convert the values in the '2nd column' to strings
            df.iloc[:, 1] = df.iloc[:, 1].astype(str)

            second_column_name = df.columns[1]
            df["feedback"] = df.apply(
                lambda row, scn=second_column_name: make_feedback_link(
                    row[scn], current_date_year
                ),
                axis=1,
            )

            df.reset_index(drop=True, inplace=True)
            df["test"] = current_date

            assert isinstance(df, pd.DataFrame)
            dfs[sheet_name] = df

    pr.green("extracting df_sum_abbr for class.")

    # Load abbreviations from TSV, filter out those with capital letters, and add id/pattern columns
    abr_dir = pth.abbreviations_tsv_path
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
        lambda row: make_feedback_link(row[second_column_name], current_date_year),
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

    pr.white(f"Number of rows: {len(df_sum_abbr)}")

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

    pr.white(f"Number of rows: {len(df_sum_sandhi)}")

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
    native_dfs = [
        dfs[sheet_name][["id", "native"]]
        for sheet_name in sheets_for_gramm
        if "id" in dfs[sheet_name].columns and "native" in dfs[sheet_name].columns
    ]

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

    pr.white(f"Number of rows: {len(df_sum_gramm)}")

    if dpspth.sbs_anki_style_dir.exists():
        pr.green("Saving field list to sbs directory.")
        _write_field_list(
            dpspth.sbs_anki_style_dir / "field-list-grammar-abbr.md",
            "Grammar Abbr",
            df_sum_abbr.columns,
        )
        _write_field_list(
            dpspth.sbs_anki_style_dir / "field-list-grammar-sandhi.md",
            "Grammar Sandhi",
            df_sum_sandhi.columns,
        )
        _write_field_list(
            dpspth.sbs_anki_style_dir / "field-list-grammar-gramm.md",
            "Grammar Gramm",
            df_sum_gramm.columns,
        )
    else:
        pr.red("Study-tools/anki-style directory does not exist.")


def _write_field_list(path: Path, title: str, columns: pd.Index) -> None:
    """Write a field-list markdown file listing column names plus 'marks'."""
    columns_with_marks = [*list(columns), "marks"]
    content = (
        f"# Field List: {title}\n\n```\n" + "\n".join(columns_with_marks) + "\n```\n"
    )
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
