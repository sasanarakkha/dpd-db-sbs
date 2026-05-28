from exporter.analysis.analyzer import get_word_details
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths
from db.models import Lookup
import json


def reproduce():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    token = "yodha"
    print(f"\n--- Analyzing token: {token} ---")

    # Check lookup
    lookup = db_session.query(Lookup).filter(Lookup.lookup_key == token).first()
    if lookup:
        print(f"Lookup grammar: {lookup.grammar_unpack}")
        headwords = lookup.headwords_unpack
        print(f"Headword IDs: {headwords}")

    else:
        print("No lookup entry found.")

    # Check details
    details = get_word_details(token, db_session)
    print("\n--- details output ---")
    print(json.dumps(details, indent=2, ensure_ascii=False))

    db_session.close()


if __name__ == "__main__":
    reproduce()
