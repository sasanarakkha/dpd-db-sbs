from db.db_helpers import get_db_session
from db.models import Lookup
from tools.paths import ProjectPaths


def test_grammar_struct():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    # Check a known word with grammar info
    lookup = db_session.query(Lookup).filter(Lookup.lookup_key == "purisassa").first()
    if lookup:
        print(f"Grammar type: {type(lookup.grammar_unpack)}")
        if lookup.grammar_unpack:
            print(f"First item: {lookup.grammar_unpack[0]}")
            print(f"First item type: {type(lookup.grammar_unpack[0])}")
    else:
        print("purisassa not found")
    db_session.close()
