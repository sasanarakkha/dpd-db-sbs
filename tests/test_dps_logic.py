import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, DpdHeadword, Russian, DpdRoot, FamilyCompound, Lookup

# Import functions
from db.families.family_compound_ru import create_comp_fam_dict, compile_cf_html_ru, add_cf_to_db as update_cf_db
from db.families.family_idiom_ru import create_idioms_dict, compile_idioms_html_ru
from db.families.family_root_ru import make_roots_family_dict_and_bases_dict as make_roots_family_dict, compile_rf_html_ru
from db.families.family_set_ru import make_sets_dict, compile_sf_html_ru
from db.families.family_word_ru import make_word_fam_dict, compile_wf_html_ru
from db.rpd.rpd_to_lookup import make_clean_meaning_list, make_meaning_plus_case

@pytest.fixture
def in_memory_db():
    """Sets up an in-memory SQLite database with the DPD schema for safe testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

class TestDPSLogic:
    """
    Tests the functional logic of core DPS components.
    Uses an in-memory database for write operations to protect the actual dpd.db.
    """

    def _create_mock_word(self, lemma="test_word", meaning="test meaning"):
        """Helper to create a mock DpdHeadword with Russian data."""
        mock_ru = MagicMock(spec=Russian)
        mock_ru.ru_meaning = "русское значение"
        
        mock_word = MagicMock(spec=DpdHeadword)
        mock_word.lemma_1 = lemma
        mock_word.lemma_clean = lemma
        mock_word.meaning_1 = meaning
        mock_word.pos = "noun"
        mock_word.ru = mock_ru
        # Defaults for families
        mock_word.family_compound_list = []
        mock_word.family_idioms_list = []
        mock_word.family_root = ""
        mock_word.root_family_key = ""
        mock_word.family_set_list = []
        mock_word.family_word = ""
        mock_word.root_base = ""
        
        return mock_word

    def test_family_compound_full_flow(self, in_memory_db):
        """Test Family Compound Logic from extraction to (mocked) DB update."""
        mock_word = self._create_mock_word()
        mock_word.family_compound_list = ["comp_fam"]
        mock_word.grammar = "comp"
        
        dpd_db = [mock_word]
        
        # 1. Extraction
        cf_dict = create_comp_fam_dict(dpd_db)
        assert "comp_fam" in cf_dict
        
        # 2. Compilation
        res_dict = compile_cf_html_ru(dpd_db, cf_dict)
        assert "test_word" in res_dict["comp_fam"]["html_ru"]
        
        # 3. Safe DB Update (using in-memory DB)
        # Pre-seed the in-memory DB with the family entry
        new_fam = FamilyCompound(compound_family="comp_fam")
        in_memory_db.add(new_fam)
        in_memory_db.commit()
        
        update_cf_db(in_memory_db, res_dict)
        
        # Verify update
        updated = in_memory_db.query(FamilyCompound).filter_by(compound_family="comp_fam").first()
        assert updated.html_ru == res_dict["comp_fam"]["html_ru"]
        assert "test_word" in updated.html_ru

    def test_family_root_logic(self):
        """Test Family Root Logic extraction and compilation."""
        mock_word = self._create_mock_word()
        mock_word.family_root = "root_fam"
        mock_word.root_key = "root_key"
        mock_word.root_family_key = "root_key root_fam"
        
        mock_root = MagicMock(spec=DpdRoot)
        mock_root.root_ru_meaning = "корень"
        mock_word.rt = mock_root
        
        dpd_db = [mock_word]
        
        rf_dict, bases_dict = make_roots_family_dict(dpd_db)
        key = "root_key root_fam"
        assert rf_dict[key]["meaning_ru"] == "корень"
        
        res_dict = compile_rf_html_ru(dpd_db, rf_dict)
        assert "корень" in res_dict[key]["html_ru"]

    def test_rpd_logic(self):
        """Test logic for Russian to Pali Dictionary cleaning and formatting."""
        mock_ru = MagicMock(spec=Russian)
        mock_ru.ru_meaning = "значение 1; значение 2 (в скобках) ??"
        mock_word = MagicMock(spec=DpdHeadword)
        mock_word.ru = mock_ru
        
        cleaned = make_clean_meaning_list(mock_word)
        assert "значение 1" in cleaned
        assert "значение 2" in cleaned
        assert "??" not in str(cleaned)
        
        mock_word.plus_case = "+dat"
        mock_word.ru.ru_meaning = "значение"
        
        with patch('db.rpd.rpd_to_lookup.ru_replace_abbreviations') as mock_replace:
            mock_replace.return_value = "Дат"
            result = make_meaning_plus_case(mock_word)
            assert "значение (Дат)" in result

    def test_lookup_safe_update(self, in_memory_db):
        """Test Lookup table update logic using in-memory DB."""
        # This tests the logic similar to add_help_ru or add_to_lookup_table
        # but in a simplified, safe way.
        key = "test_key"
        meaning = "test help text"
        
        # Simulate add_help_ru logic
        existing = in_memory_db.query(Lookup).filter_by(lookup_key=key).first()
        if not existing:
            lkp = Lookup(lookup_key=key)
            lkp.help_pack(meaning)
            in_memory_db.add(lkp)
        
        in_memory_db.commit()
        
        # Verify
        result = in_memory_db.query(Lookup).filter_by(lookup_key=key).first()
        assert result.lookup_key == key
        assert result.help_unpack == meaning
