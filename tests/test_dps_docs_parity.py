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
                    
        unique_file = Path("dpd_rus.md")
        
        # 1. Verify unique file exists in docs_rus
        assert unique_file in docs_rus_files, "docs_rus/dpd_rus.md is missing!"
        
        # 2. Verify parity
        # Remove unique file from comparison
        docs_rus_files.remove(unique_file)
        
        missing_in_rus = docs_files - docs_rus_files
        extra_in_rus = docs_rus_files - docs_files
        
        error_msg = ""
        if missing_in_rus:
            error_msg += f"\n[MISSING] The following files exist in 'docs/' but NOT in 'docs_rus/':\n"
            error_msg += "\n".join([f"  - {f}" for f in sorted(missing_in_rus)])
            
        if extra_in_rus:
            error_msg += f"\n\n[EXTRA] The following files exist in 'docs_rus/' but NOT in 'docs/':\n"
            error_msg += "\n".join([f"  - {f}" for f in sorted(extra_in_rus)])
            error_msg += "\n(Only 'dpd_rus.md' is allowed to be unique in docs_rus/)"
            
        assert not missing_in_rus and not extra_in_rus, error_msg
