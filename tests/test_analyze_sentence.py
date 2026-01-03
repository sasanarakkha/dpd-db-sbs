from exporter.mcp.analyzer import analyze_sentence
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths
import json


def test_analyze_sentence():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    sentence = "yo'dha koci manussesu"

    analysis = analyze_sentence(sentence, db_session)

    # Dump full analysis to file
    with open("temp/debug_analysis_dump.json", "w") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print("Full analysis dump saved to debug_analysis_dump.json")
    db_session.close()


if __name__ == "__main__":
    test_analyze_sentence()
