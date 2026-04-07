# Test Markdown vocabulary and abbreviation generation for dpd-pali-courses.

from unittest.mock import MagicMock
import csv

# We will need to mock these as they might not be importable in the test environment if not set up
# but since we are running in the dpd-db environment, they should be.
try:
    from db.models import DpdHeadword, SBS
except ImportError:
    class DpdHeadword: pass
    class SBS: pass

def test_generate_vocab(tmp_path):
    """Test that vocabulary files are cumulative (no deduplication)."""
    from scripts.export.vocab_abbrev_pali_course import generate_vocab
    from db.models import DpdHeadword, SBS
    from unittest.mock import MagicMock
    
    # Mock DB session
    mock_session = MagicMock()
    
    # Create some mock data
    word1 = MagicMock(spec=DpdHeadword)
    word1.lemma_1 = "word1"
    word1.pos = "pos1"
    word1.meaning_1 = "meaning1"
    word1.root_clean = "root1"
    word1.root_sign = "sign1"
    word1.root_key = "key1"
    word1.rt = None
    word1.construction_line1 = "const1"
    word1.pattern = "patt1"
    word1.sbs = MagicMock(spec=SBS)
    word1.sbs.sbs_class = 2
    
    word2 = MagicMock(spec=DpdHeadword)
    word2.lemma_1 = "word2"
    word2.pos = "pos2"
    word2.meaning_1 = "meaning2"
    word2.root_clean = "root2"
    word2.root_sign = "sign2"
    word2.root_key = "key2"
    word2.rt = None
    word2.construction_line1 = "const2"
    word2.pattern = "patt2"
    word2.sbs = MagicMock(spec=SBS)
    word2.sbs.sbs_class = 3

    # Results for filter().all()
    # class 2: [word1]
    # class 3: [word1, word2]
    mock_results = [
        [word1],        # class 2
        [word1, word2], # class 3
    ] + [[] for _ in range(26)]
    
    mock_query = mock_session.query.return_value
    mock_options = mock_query.options.return_value
    mock_join = mock_options.join.return_value
    mock_filter = mock_join.filter
    mock_filter.return_value.all.side_effect = mock_results
    
    vocab_dir = tmp_path / "vocab"
    vocab_dir.mkdir(parents=True)
    
    generate_vocab(mock_session, tmp_path)
    
    # Verify content of class-02.md
    content_02 = (vocab_dir / "class-02.md").read_text()
    assert "word1" in content_02
    assert "word2" not in content_02
    
    # Verify content of class-03.md (no deduplication)
    content_03 = (vocab_dir / "class-03.md").read_text()
    assert "word1" in content_03 # word1 should be present (cumulative)
    assert "word2" in content_03

def test_generate_vocab_index(tmp_path):
    """Test that index file is generated correctly."""
    from scripts.export.vocab_abbrev_pali_course import generate_vocab_index
    
    vocab_dir = tmp_path / "vocab"
    vocab_dir.mkdir(parents=True)
    
    # Create mock class files
    (vocab_dir / "class-02.md").write_text("class 2")
    (vocab_dir / "class-03.md").write_text("class 3")
    
    generate_vocab_index(tmp_path)
    
    index_file = vocab_dir / "index.md"
    assert index_file.exists()
    
    content = index_file.read_text()
    assert "# Vocabulary Reference" in content
    assert "[Class 2](class-02.md)" in content
    assert "[Class 3](class-03.md)" in content

def test_generate_abbreviations(tmp_path):
    """Test that abbreviations file is generated correctly."""
    from scripts.export.vocab_abbrev_pali_course import generate_abbreviations as actual_generate_abbreviations
    
    # Mock ProjectPaths
    mock_pth = MagicMock()
    tsv_path = tmp_path / "abbreviations.tsv"
    mock_pth.abbreviations_tsv_path = tsv_path
    
    # Create mock TSV data
    with open(tsv_path, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(["abbrev", "meaning", "pāli", "example", "explanation", "ru_abbrev", "ru_meaning"])
        writer.writerow(["acc", "accusative", "upayoga", "taṃ", "direct object", "вин", "винительный"])
        writer.writerow(["M", "Masculine", "pullinga", "puriso", "male gender", "М", "мужской"]) # Should be filtered out
        writer.writerow(["ca", "conjunction", "nipāta", "ca", "and", "и", "и"])
    
    actual_generate_abbreviations(mock_pth, tmp_path)
    
    abbrev_file = tmp_path / "abbreviations.md"
    assert abbrev_file.exists()
    
    content = abbrev_file.read_text()
    assert "# Abbreviations" in content
    assert "| abbrev | meaning | pāli | example | explanation |" in content
    assert "| acc | accusative | upayoga | taṃ | direct object |" in content
    assert "| ca | conjunction | nipāta | ca | and |" in content
    assert "| M |" not in content # Filtered out
