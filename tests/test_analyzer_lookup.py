import json
from db.db_helpers import get_db_session
from db.models import Lookup
from tools.paths import ProjectPaths
from exporter.analysis.analyzer import analyze_sentence


def test_analyzer_lookup():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # Get first 100 lookup entries and which has column "roots" empty
    lookups = db_session.query(Lookup).filter(Lookup.roots == "").limit(1000).all()

    print(f"Testing {len(lookups)} lookup entries...")

    for i, lookup in enumerate(lookups):
        print(f"\n--- Entry {i + 1}: {lookup.lookup_key} ---")
        try:
            # analyze_sentence expects a sentence, but here we are testing single words from lookup
            # However, analyze_sentence tokenizes the input, so passing the lookup_key works.
            result = analyze_sentence(lookup.lookup_key, db_session)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Error analyzing {lookup.lookup_key}: {e}")


if __name__ == "__main__":
    test_analyzer_lookup()
