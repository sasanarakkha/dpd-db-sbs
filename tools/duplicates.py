import csv
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from collections import Counter

def has_duplicate_values_in_column(
    tsv_path: Path,
    column_name: Optional[str] = None,
    column_index: Optional[int] = 0
) -> Tuple[bool, List[str], Dict[str, List[int]]]:
    """
    Checks a TSV file for duplicate values in a specified column.

    Args:
        tsv_path: Path to the TSV file.
        column_name: Name of the column to check. Takes precedence over column_index.
        column_index: Index of the column to check (default is 0 for the first column).
                      Used if column_name is None.

    Returns:
        A tuple: (has_duplicates, list_of_duplicate_values, dict_of_duplicates_with_line_numbers)
        - bool: True if duplicates are found, False otherwise.
        - List[str]: A list of the values that were found to be duplicates.
        - Dict[str, List[int]]: A dictionary where keys are duplicate values and
                                values are lists of line numbers (1-based, including header)
                                where these duplicates occur.
    
    Raises:
        FileNotFoundError: If tsv_path does not exist.
        ValueError: If column_name is provided but not found in headers,
                    or if column_index is out of bounds.
    """
    if not tsv_path.exists():
        raise FileNotFoundError(f"TSV file not found at: {tsv_path}")

    values_seen: Counter = Counter()
    line_numbers_for_values: Dict[str, List[int]] = {}
    target_col_idx: int = -1

    with open(tsv_path, "r", newline="", encoding="utf-8") as tsvfile:
        reader = csv.reader(tsvfile, delimiter="\t")
        
        try:
            header = next(reader)
        except StopIteration: # Empty file
            return False, [], {}

        if column_name:
            try:
                target_col_idx = header.index(column_name)
            except ValueError:
                raise ValueError(
                    f"Column name '{column_name}' not found in TSV header: {header}"
                )
        elif column_index is not None:
            if not (0 <= column_index < len(header)):
                raise ValueError(
                    f"Column index {column_index} is out of bounds for TSV with {len(header)} columns."
                )
            target_col_idx = column_index
        else: # Should not happen if defaults are set, but as a safeguard
            raise ValueError("Either column_name or column_index must be specified.")

        for line_num, row in enumerate(reader, start=2): # start=2 because header is line 1
            if target_col_idx >= len(row): # Handle short rows
                continue 
            
            value = row[target_col_idx]
            values_seen[value] += 1
            if value not in line_numbers_for_values:
                line_numbers_for_values[value] = []
            line_numbers_for_values[value].append(line_num)

    duplicate_values = [val for val, count in values_seen.items() if count > 1]
    
    if not duplicate_values:
        return False, [], {}
    else:
        # Filter line_numbers_for_values to only include duplicates
        duplicate_lines = {
            val: line_numbers_for_values[val] 
            for val in duplicate_values
        }
        return True, duplicate_values, duplicate_lines
