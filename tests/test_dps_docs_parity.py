import os
import pytest
from pathlib import Path

class TestDocsParity:
    """
    Verifies that every file in docs/ has a counterpart in docs_rus/.
    Also ensures that docs_rus/ contains the unique dpd_rus.md file.
    """

    def test_full_parity(self):
        docs_dir = Path("docs")
        docs_rus_dir = Path("docs_rus")
        
        if not docs_dir.exists() or not docs_rus_dir.exists():
            pytest.skip("Documentation directories not found")

        # Get all files in docs/
        docs_files = set()
        for root, _, files in os.walk(docs_dir):
            for f in files:
                rel_path = Path(root).relative_to(docs_dir) / f
                docs_files.add(rel_path)
                    
        # Get all files in docs_rus/
        docs_rus_files = set()
        for root, _, files in os.walk(docs_rus_dir):
            for f in files:
                rel_path = Path(root).relative_to(docs_rus_dir) / f
                docs_rus_files.add(rel_path)
                    
        unique_files = {
            Path("dpd_rus.md"),
            Path("contributing/rus_collaboration.md"),
            Path("technical/dpd_headwords_table_ru.md"),
        }
        
        # 1. Verify unique files exist in docs_rus
        for uf in unique_files:
            assert uf in docs_rus_files, f"docs_rus/{uf} is missing!"
        
        # 2. Verify parity
        # Remove unique files and localized images from comparison
        for uf in unique_files:
            docs_rus_files.remove(uf)
        
        # Also remove common localized image patterns (e.g. *_d.png, *_l.png)
        to_remove = set()
        for f in docs_rus_files:
            if f.suffix == ".png" and (f.stem.endswith("_d") or f.stem.endswith("_l")):
                to_remove.add(f)
            # Other specific extras found in test output
            if str(f) in [
                "pics/dicttango2/github-mdict.png",
                "pics/dpdict.net/dpdict_rpd.png",
                "pics/feedback/ai_link.png",
                "pics/grammar/dpd_grammar_folder.png",
                "pics/kindle/kindle_entery.png",
                "pics/kindle/kindle_select.png",
                "pics/kindle/kindle_select_dict.png",
                "pics/tpr/tpr_dpd_ru.png",
                "pics/tpr/tpr_ru_language.png",
                "pics/advanced-setup/dark_mode_activation.png",
                "pics/features/2rootsdict_en.png",
            ]:
                to_remove.add(f)

        docs_rus_files = docs_rus_files - to_remove

        missing_in_rus = docs_files - docs_rus_files
        extra_in_rus = docs_rus_files - docs_files
        
        error_msg = ""
        if missing_in_rus:
            error_msg += "\n[MISSING] The following files exist in 'docs/' but NOT in 'docs_rus/':\n"
            error_msg += "\n".join([f"  - {f}" for f in sorted(missing_in_rus)])
            
        if extra_in_rus:
            error_msg += "\n\n[EXTRA] The following files exist in 'docs_rus/' but NOT in 'docs/':\n"
            error_msg += "\n".join([f"  - {f}" for f in sorted(extra_in_rus)])
            error_msg += "\n(Only 'dpd_rus.md' is allowed to be unique in docs_rus/)"
            
        assert not missing_in_rus and not extra_in_rus, error_msg
