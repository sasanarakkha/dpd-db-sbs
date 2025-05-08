#!/usr/bin/env python3

# Generate csvs for grammar anki deck for all classes from the database. 
# https://sasanarakkha.github.io/study-tools/pali-class/pali-class.html

import pandas as pd
from datetime import datetime
from pathlib import Path
from tools.paths_dps import DPSPaths

from tools.printer import Printer as pr

from rich.console import Console

dpspth = DPSPaths()

project_dir: Path = Path.cwd()  # e.g., /Users/deva/Documents/dpd-db
deva_dir: Path = project_dir.parent.parent  # e.g., /Users/deva


current_date = datetime.now().strftime('%d-%m')

console = Console()

def main():
    pr.tic()
    excel_file_dir = deva_dir / 'Downloads' / 'grammar.xlsx'
    # moving_grammar(excel_file_dir)
    make_grammar_csvs(excel_file_dir)
    check_duplicate_ids(excel_file_dir)
    pr.toc()


# def moving_grammar():
#     # Print completion message in green color
#     print("\033[1;33m moving grammar.xlsx from Downloads/ \033[0m")

#     # Assuming the script is in the 'Documents//dps/utilites' directory
#     script_dir = os.path.dirname(os.path.realpath(__file__))
#     deva_dir = os.path.abspath(os.path.join(script_dir, '..', '..', '..'))

#     downloads_dir = os.path.join(deva_dir, 'Downloads')

#     pali_course_dir = os.path.join(
#     deva_dir,
#     'Documents', 
#     'pali_resources', 
#     'pāli-course', 
#     )

#     grammar_src = os.path.join(downloads_dir, 'grammar.xlsx')
#     grammar_dest = os.path.join(pali_course_dir, 'grammar.xlsx')

#     # Move dpd-kindle.mobi to the specified directory
#     if os.path.exists(grammar_src):
#         shutil.move(grammar_src, grammar_dest)
#         print("\033[1;32m grammar.xlsx moved to pāli-course folder \033[0m")
#     else:
#         print("\033[1;31m grammar.xlsx is missing.\033[0m")


def check_duplicate_ids(excel_file_dir):
    # Load the Excel file into a pandas ExcelFile object
    excel_file = pd.ExcelFile(excel_file_dir)
    
    # Dictionary to store [id] values from each sheet
    id_dict = {}
    
    # Loop through each sheet in the Excel file
    for sheet_name in excel_file.sheet_names:
        # Read the current sheet into a DataFrame
        df = excel_file.parse(sheet_name)
        
        # Check if df is a DataFrame
        if isinstance(df, pd.DataFrame):
            # Check if the first column exists and is named 'id'
            if df.columns[0] == 'id':
                # Iterate through each [id] value in the first column
                for id_value in df[df.columns[0]]:
                    # Check if the [id] value is already in the dictionary
                    if id_value in id_dict:
                        # If it is, print the [id] value in red
                        console.print(f"[red]{id_value}[/red]", end=" ")
                    else:
                        # If not, add the [id] value to the dictionary
                        id_dict[id_value] = True
            else:
                print(f"Sheet {sheet_name} does not have an 'id' column as the first column.")
        else:
            print(f"Sheet {sheet_name} did not load as a DataFrame. It is a {type(df)}.")



def make_grammar_csvs(excel_file_dir):
    # Load the Excel file into a pandas ExcelFile object
    excel_file = pd.ExcelFile(excel_file_dir)

    # Create a dictionary to store the DataFrames
    dfs = {}

    # Loop through each sheet in the Excel file
    for sheet_name in excel_file.sheet_names:
        # Read the current sheet into a DataFrame
        df = excel_file.parse(sheet_name)

        # Check if df is a DataFrame
        if isinstance(df, pd.DataFrame):
            # Convert the 'id' column to integers
            if 'id' in df.columns:
                df['id'] = df['id'].fillna(0).astype(int)


            # Convert the values in the '2nd column' to strings
            df.iloc[:, 1] = df.iloc[:, 1].astype(str)

            second_column_name = df.columns[1]
            df['feedback'] = df.apply(lambda row: (
                f"""Spot a mistake? <a class="link" href="https://docs.google.com/forms/d/1Z8Jjt0-E0HNX7ygABIzAcrChG23M3IOyoZGQ-EDRzXY/viewform?usp=pp_url&entry.438735500"""
                f"""={row[second_column_name]}"""
                f"""&entry.957833742=Anki Deck Grammar">Fix it here</a>"""
            ), axis=1)

            # Reset the index and drop the old index
            df.reset_index(drop=True, inplace=True)

            # Add the current date to the DataFrame as test
            df['test'] = current_date

            # Store the DataFrame in the dictionary with the sheet name as the key
            dfs[sheet_name] = df
        else:
            print(f"Sheet {sheet_name} did not load as a DataFrame. It is a {type(df)}.")

    # Now you can access each DataFrame using its sheet name as a key
    # For example, dfs['Sheet1'] will give you the DataFrame for 'Sheet1', and so on.

    # TODO  add here or anywhere exporter from abbreviations.csv directley and remove it from grammar.xlsx

    # abr_dir = "../exporter/assets/abbreviations.csv"

    # if os.path.exists(abr_dir):
    #     console.print("[bold green]extracting abbreviations.csv for exporter.")
    #     # Save the DataFrame to a CSV file after dropping unnecessary columns
    #     trimmed_df = dfs['abbr'].drop(columns=['id', 'type', 'pattern', 'feedback'])
    #     trimmed_df.to_csv(abr_dir, sep="\t", index=False, header=True)

    #     # Printing the number of rows in the trimmed DataFrame
    #     row_count = len(trimmed_df)
    #     print("Number of rows:", row_count)
    # else:
    #     console.print("[bold red]abbreviations.csv does not exist.")

    console.print("[bold green]extracting df_sum_abbr for class.")

    # Filter the DataFrame to include only rows where 'type' column is not null
    filtered_df = dfs['abbr'][dfs['abbr']['type'].notna()]

    # Concatenate df_abbr_class, df_alph, df_samasa, df_upasagga into df_sum_abbr
    df_abbr_class = filtered_df.drop(columns=['ru-meaning', 'ru-abbrev', 'type'])
    df_upasagga_filtered = dfs['upasagga'][dfs['upasagga']['example'].notna()]
    df_sum_abbr = pd.concat([df_abbr_class, dfs['alph'], dfs['samasa'], df_upasagga_filtered, dfs['roots']])

    # Save df_sum_abbr to a CSV file
    sum_abbr_path = dpspth.anki_csvs_dps_dir / "pali_class" / "grammar" / "cl_sum_abbr.csv"
    df_sum_abbr.to_csv(sum_abbr_path, sep="\t", index=False)

    row_count = len(df_sum_abbr)
    print("Number of rows:", row_count)

    console.print("[bold green]extracting df_sum_sandhi for class.")

    # Concatenate the DataFrames and store the result in df_sum_sandhi
    df_sum_sandhi = pd.concat([
        dfs['v_sandhi'],
        dfs['c_sandhi'],
        dfs['m_sandhi'],
        dfs['assim'],
        dfs['mx_sandhi'],
        dfs['change_s'],
        dfs['irr_base'],
        dfs['taddhita'],
        dfs['kitaka'],
        dfs['vuddhi']
    ])

    # Save df_sum_sandhi to a CSV file
    sum_sandhi_path = dpspth.anki_csvs_dps_dir / "pali_class" / "grammar" / "cl_sum_sandhi.csv"
    df_sum_sandhi.to_csv(sum_sandhi_path, sep="\t", index=False)

    row_count = len(df_sum_sandhi)
    print("Number of rows:", row_count)

    console.print("[bold green]extracting cl_sum_gramm for class.")

    # Concatenate all DataFrames except those in df_sum_abbr and df_sum_sandhi
    dfs_to_concat = [
        dfs[sheet_name] for sheet_name in excel_file.sheet_names 
        if sheet_name not in ['abbr', 'alph', 'samasa', 'upasagga', 'roots', 'v_sandhi', 'c_sandhi', 
            'm_sandhi', 'assim', 'mx_sandhi', 'change_s', 'irr_base', 'taddhita', 'kitaka', 'vuddhi']
    ]
    df_sum_gramm = pd.concat(dfs_to_concat)

    # Save df_sum_gramm to a CSV file
    sum_gramm_path = dpspth.anki_csvs_dps_dir / "pali_class" / "grammar" / "cl_sum_gramm.csv"
    df_sum_gramm.to_csv(sum_gramm_path, sep="\t", index=False)

    row_count = len(df_sum_gramm)
    print("Number of rows:", row_count)

    sbs_dir = deva_dir / "Documents" / "sasanarakkha" / "study-tools" / "anki-style"

    if sbs_dir.exists():
        console.print("[bold green]Saving field list to sbs directory.")

        # Save the column list of df_sum_abbr to a text file
        grammar_abbr_path = sbs_dir / 'field-list-grammar-abbr.txt'
        with open(grammar_abbr_path, "w") as file:
            file.write('\n'.join(df_sum_abbr.columns))

        # Save the column list of df_sum_sandhi to a text file
        grammar_sandhi_path = sbs_dir / 'field-list-grammar-sandhi.txt'
        with open(grammar_sandhi_path, "w") as file:
            file.write('\n'.join(df_sum_sandhi.columns))

        # Save the column list of df_sum_gramm to a text file
        grammar_grammar_path = sbs_dir / 'field-list-grammar-gramm.txt'
        with open(grammar_grammar_path, "w") as file:
            file.write('\n'.join(df_sum_gramm.columns))

    else:
        console.print("[bold red]Study-tools/anki-style directory does not exist.")


if __name__ == "__main__":
    main()