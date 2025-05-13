import os

anki_db_path = "/Users/deva/Library/Application Support/Anki2/deva/collection.anki2"

print(f"Attempting to read: {anki_db_path}")

if not os.path.exists(anki_db_path):
    print(f"Error: Path does not exist: {anki_db_path}")
else:
    print(f"Path exists: {anki_db_path}")
    if not os.access(anki_db_path, os.R_OK):
        print(f"Error: No read permission for: {anki_db_path}")
    else:
        print(f"Read permission confirmed for: {anki_db_path}")
        try:
            with open(anki_db_path, 'rb') as f:
                header = f.read(100) # Read first 100 bytes
            print(f"Successfully read first 100 bytes: {header}")
        except Exception as e:
            print(f"Error reading file: {e}")
