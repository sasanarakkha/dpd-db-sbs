"""A Pickle file reader and editor."""

import pickle
from pathlib import Path
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr

pth = ProjectPaths()
dpspth = DPSPaths()


def load_pickled_data(filepath: Path):
    """Load data from a pickled file."""
    with open(filepath, "rb") as file:
        data = pickle.load(file)
    return data


def print_values(data):
    """Print the values in the loaded data."""
    pr.white(str(data))


def print_values_with_row_numbers(data):
    """Print the values in the loaded data along with their row numbers."""
    for index, item in enumerate(data, start=0):
        pr.white(f"Row {index}: {item}")


def remove_row(data, index_to_remove):
    """Remove a specific row from the data."""
    if 0 <= index_to_remove < len(data):
        removed_row = data.pop(index_to_remove)
        pr.green(f"Removed row: {removed_row}")
        return True
    else:
        pr.red("Invalid index to remove")
        return False


def save_modified_data(data, filepath: Path):
    """Save the modified data back to the pickled file."""
    with open(filepath, "wb") as file:
        pickle.dump(data, file)


def main():
    pr.tic()
    filepath = dpspth.dps_save_state_path

    # pth.additions_pickle_path
    # pth.daily_record_path
    # dpspth.dps_save_state_path
    # pth.dpd_db_path

    pr.green_tmr(f"loading {filepath.name}")
    try:
        data = load_pickled_data(filepath)
        pr.yes("ok")
        print_values(data)
        # print_values_with_row_numbers(data)

        # index_to_remove = 9  # Replace this with the actual index you want to remove
        # if remove_row(data, index_to_remove):
        #     save_modified_data(data, filepath)
    except FileNotFoundError:
        pr.no("failed")
        pr.red(f"Error: {filepath} not found")
    except Exception as e:
        pr.no("failed")
        pr.red(f"Error: {e}")

    pr.toc()


if __name__ == "__main__":
    main()
