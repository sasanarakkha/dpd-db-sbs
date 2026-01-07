import importlib
import pytest
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestDPSImports:
    """
    Verifies that all critical DPS/RU specific modules can be imported.
    This checks for syntax errors, missing dependencies, and incorrect paths.
    """

    @pytest.mark.parametrize("module_name", [
        "db.families.family_compound_ru",
        "db.families.family_idiom_ru",
        "db.families.family_root_ru",
        "db.families.family_set_ru",
        "db.families.family_word_ru",
        "db.rpd.rpd_to_lookup",
        "db.lookup.help_abbrev_add_to_lookup_ru",
        "exporter.goldendict.main_ru",
        "exporter.goldendict.main_sbs",
        "exporter.grammar_dict.grammar_dict_ru",
        "exporter.kindle.kindle_exporter_ru",
        "exporter.tpr.tpr_exporter_ru",
        "exporter.webapp.main_ru",
        "gui2.main",
        "scripts.build.db_rebuild_from_tsv_ru_sbs",
    ])
    def test_import_module(self, module_name):
        """Test that the module can be imported successfully."""
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")
        except Exception as e:
            pytest.fail(f"An error occurred while importing {module_name}: {e}")
