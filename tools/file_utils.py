# file_utils.py
import os
import re
import pandas as pd


def search_pali_in_csv(keyword, vocab_folder_path):
    """Search for a Pali word in all CSV files in the folder."""
    result = {
        "id": -1,
        "pali": "",
        "meaning": "",
        "pos": "",
        "exercise_number": "",
        "prdc": []
    }
    found_match = False
    for filename in os.listdir(vocab_folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(vocab_folder_path, filename)
            try:
                df = pd.read_csv(file_path, dtype=str)
                if "pali" not in df.columns:
                    continue
                
                example_columns = [col for col in df.columns if "example" in col.lower()]
                match = df[df["pali"] == keyword]

                if not match.empty:
                    result["id"] = match["id"].values[0]
                    result["pali"] = match["pali"].values[0]
                    result["meaning"] = match["meaning"].values[0] if "meaning" in match.columns and pd.notna(match["meaning"].values[0]) else ""
                    result["pos"] = match["pos"].values[0] if "pos" in match.columns and pd.notna(match["pos"].values[0]) else ""

                    for col in example_columns:
                        if col in match.columns: # Check if the example column exists for this row
                            sentence = match[col].values[0]
                            if isinstance(sentence, str):
                                extracted = re.findall(r"<b>(.*?)</b>", sentence)
                                for ext in extracted:
                                    if ext not in result['prdc']:
                                        result['prdc'].append(ext)
                    
                    print(f"Match found for '{keyword}' in file: {filename}")
                    
                    number_match = re.search(r'_(\d+)(?:\.csv)', filename)
                    if number_match:
                        result["exercise_number"] = number_match.group(1)
                    else:
                        result["exercise_number"] = ""
                    
                    found_match = True
                    break 
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                continue

    if not found_match:
        print(f"No matches found for '{keyword}' in {vocab_folder_path}")
        result["pali"] = keyword
        result["id"] = result.get("id", -1) 
    return result


def load_exercise_data_from_file(exercise_file_path):
    """Loads exercise data from a .txt file."""
    try:
        with open(exercise_file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: Exercise file not found at {exercise_file_path}")
        return ""
    except Exception as e:
        print(f"Error reading exercise file {exercise_file_path}: {e}")
        return ""


def load_discourse_sutta_data(file_path):
    """
    Loads and parses a discourse sutta text file.
    The file is expected to have entries like:
    SUTTA: sn12.1 paṭiccasamuppādasuttaṃ
    <Pali sentence 1>
    <Pali sentence 2>
    ...
    SUTTA: sn12.10 gotamasuttaṃ
    ...

    Returns:
        list: A list of dictionaries, where each dictionary represents a sutta
              and has "sutta_ref", "sutta_title", and "sentences" (a list of strings).
    """
    suttas_data = []
    current_sutta = None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("SUTTA:"):
                    if current_sutta: # Save previous sutta
                        suttas_data.append(current_sutta)
                    parts = line.split(" ", 2) # Split "SUTTA:" "sn12.1" "name"
                    current_sutta = {"sutta_ref": parts[1], "sutta_title": parts[2] if len(parts) > 2 else "", "sentences": []}
                elif line and current_sutta: # Non-empty line and we are inside a sutta
                    current_sutta["sentences"].append(line)
            if current_sutta: # Save the last sutta
                suttas_data.append(current_sutta)
    except FileNotFoundError:
        print(f"Error: Discourse Sutta file not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading Discourse Sutta file {file_path}: {e}")
        return []
    return suttas_data