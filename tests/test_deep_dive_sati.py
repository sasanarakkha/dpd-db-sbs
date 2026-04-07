
from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.paths import ProjectPaths
from exporter.mcp.analyzer import get_word_details

def deep_dive_sati():
    paths = ProjectPaths()
    db_session = get_db_session(paths.dpd_db_path)
    
    token = "sati"
    
    print(f"\n--- 1. DB Lookup for '{token}' ---")
    lookup = db_session.query(Lookup).filter(Lookup.lookup_key == token).first()
    if not lookup:
        print("No lookup found!")
        return

    grammar_list = lookup.grammar_unpack
    print(f"Lookup Grammar List ({len(grammar_list)} entries):")
    for g in grammar_list:
        print(f"  {g}")

    headword_ids = lookup.headwords_unpack
    print(f"\nAssociated Headwords ({len(headword_ids)}): {headword_ids}")
    
    headwords = db_session.query(DpdHeadword).filter(DpdHeadword.id.in_(headword_ids)).all()
    
    print("\n--- 2. Headword Analysis ---")
    for hw in headwords:
        print(f"\nID: {hw.id} | Lemma: {hw.lemma_1} | Clean: {hw.lemma_clean} | Stem: {hw.stem}")
        
        # Test our Logic manually
        is_stem = False
        print("  checking grammar list matches:")
        for g_lemma, g_pos, g_gram in grammar_list:
            if g_lemma == hw.lemma_clean:
                 print(f"    - Matches lemma clean: {g_gram}")
                 # Check strict compatibility
                 if "in comp" in g_gram.lower():
                     print("      -> STEM COMPATIBLE (in comp)")
                     is_stem = True
                 
                 has_case = False
                 for kw in ["nom", "acc", "gen", "dat", "instr", "ins", "abl", "loc", "voc", "sg", "pl"]:
                     if kw in g_gram.lower().split():
                         has_case = True
                 if not has_case:
                      print("      -> STEM COMPATIBLE (no case)")
                      is_stem = True
        
        if hw.lemma_clean == token:
            print("  -> STEM COMPATIBLE (Lemma == Token)")
            is_stem = True
            
        print(f"  => FINAL VERDICT: Is valid stem? {is_stem}")

    print("\n--- 3. Actual Analyzer Output (is_inflected_part=False) ---")
    details = get_word_details(token, db_session, is_inflected_part=False)
    for d in details:
        print(f"  Included: {d['key']} | Lemma: {d['lemma']}")
        
    db_session.close()

if __name__ == "__main__":
    deep_dive_sati()
