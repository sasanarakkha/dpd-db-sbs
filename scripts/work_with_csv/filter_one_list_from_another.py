import pandas as pd
import os

# --- Configuration ---
# Define the paths to your files
base_path = 'shared_data/discourses/'
source = "sn22"
original_vocab_path = os.path.join(base_path, f'vocab/vocab_{source}.csv')
output_path = os.path.join(base_path, f'output/{source}_output.csv')
filtered_vocab_path = os.path.join(base_path, f'vocab/vocab_{source}_filtered.csv')
filtered_output_path = os.path.join(base_path, f'output/{source}_output_filtered.csv')


# --- Main Logic ---
try:
    # 1. Load both CSV files into pandas DataFrames
    print(f"Loading original vocabulary from: {original_vocab_path}")
    vocab_df = pd.read_csv(original_vocab_path)

    print(f"Loading output data from: {output_path}")
    output_df = pd.read_csv(output_path)

    print(f"\nOriginal vocabulary has {len(vocab_df)} words.")

    # 2. Find the IDs from the output file where 'class_example' is empty/NaN
    ids_to_include = output_df[output_df['class_example'].isna()]['id'].tolist()
    print(f"Found {len(ids_to_include)} words without examples to include.")

    # 3. Filter the original vocab_df have only those IDs
    filtered_vocab_df = vocab_df[vocab_df['id'].isin(ids_to_include)]
    print(f"New filtered vocabulary will have {len(filtered_vocab_df)} words.")

    # 4. Save the resulting DataFrame to a new CSV file
    filtered_vocab_df.to_csv(filtered_vocab_path, index=False)
    print(f"\nSuccessfully saved the filtered vocabulary to:\n{filtered_vocab_path}")

    # 6. Filter from the output_df those IDs
    filtered_output_df = output_df[~output_df['id'].isin(ids_to_include)]
    print(f"New filtered output will have {len(filtered_output_df)} words.")

    # 7. Save the resulting DataFrame to a new CSV file
    filtered_output_df.to_csv(filtered_output_path, index=False)
    print(f"\nSuccessfully saved the filtered vocabulary to:\n{filtered_output_path}")

except FileNotFoundError as e:
    print("\nError: File not found. Please check your file paths.")
    print(e)
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")

