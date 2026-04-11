import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Import functions/classes to test
# Grammar Dict
from exporter.grammar_dict.grammar_dict_ru import generate_html_from_lookup, ProgData_ru

# DB Rebuild
from scripts.build.db_rebuild_from_tsv_dps import (
    get_tsv_files,
    make_table_data_ru,
)

# GoldenDict Ru
from exporter.goldendict.main_ru import main as gd_main

# Kindle Ru
from exporter.kindle.kindle_exporter_ru import main as kindle_main

# TPR Ru
from exporter.tpr.tpr_exporter_ru import main as tpr_main

# Webapp Ru
from exporter.webapp.main_ru import app as webapp

# Gui2 Main
from gui2.main import App


@pytest.fixture
def mock_db_session():
    return MagicMock()


@pytest.fixture
def mock_project_paths():
    mock = MagicMock()
    mock.dpd_db_path = Path("fake.db")
    return mock


class TestGrammarDictRu:
    @patch("exporter.grammar_dict.grammar_dict_ru.load_abbreviations_dict")
    @patch("exporter.grammar_dict.grammar_dict_ru.get_jinja2_env")
    @patch("exporter.grammar_dict.grammar_dict_ru.GrammarData_ru")
    def test_generate_html_from_lookup(
        self,
        mock_grammar_data,
        mock_jinja,
        mock_load_abbr,
        mock_db_session,
        mock_project_paths,
    ):
        """Test generation of HTML from lookup data."""
        # Setup mocks
        g = MagicMock(spec=ProgData_ru)
        g.db_session = mock_db_session
        g.pth = mock_project_paths
        g.rupth = MagicMock()
        g.rupth.abbreviations_tsv_path = Path("fake_abbrev.tsv")
        g.html_dict = {}

        # Mock DB Query result
        mock_lookup = MagicMock()
        mock_lookup.lookup_key = "test_word"
        mock_lookup.grammar = "masc nom sg"
        mock_lookup.grammar_unpack = [("word", "noun", "masc nom sg")]

        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_lookup
        ]

        # Mock Jinja
        mock_env = mock_jinja.return_value
        mock_template = mock_env.get_template.return_value
        mock_template.render.return_value = "grammar_dict test_word"

        # Mock load_abbreviations_dict to do nothing
        mock_load_abbr.return_value = {}

        # Run function
        generate_html_from_lookup(g)

        # Verify
        assert len(g.html_dict) == 1
        assert "test_word" in g.html_dict
        assert "grammar_dict" in g.html_dict["test_word"]


class TestDBRebuildRuSbs:
    def test_get_tsv_files_single(self):
        """Test finding a single TSV file."""
        base_path = Path("/fake/dir/file.tsv")
        with (
            patch("pathlib.Path.glob") as mock_glob,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            # Setup: No split files, single file exists
            mock_glob.return_value = []
            mock_exists.return_value = True

            files = get_tsv_files(base_path, "file")

            assert len(files) == 1
            assert files[0].name == "file.tsv"

    def test_make_russian_table_data(self, mock_db_session):
        """Test processing of Russian TSV data."""
        mock_dps_paths = MagicMock()
        mock_dps_paths.russian_path = Path("fake/russian.tsv")

        columns = ["id", "ru_meaning"]
        row = ["1", "значение"]

        with (
            patch(
                "scripts.build.db_rebuild_from_tsv_dps.get_tsv_files"
            ) as mock_get_files,
            patch(
                "scripts.build.db_rebuild_from_tsv_dps.read_tsv_files"
            ) as mock_read_files,
        ):
            mock_get_files.return_value = [Path("fake.tsv")]
            mock_read_files.return_value = [(columns, row)]

            make_table_data_ru(mock_dps_paths, mock_db_session)

            # Verify DB add was called
            mock_db_session.add.assert_called()
            # Check arguments
            args, _ = mock_db_session.add.call_args
            # Since it adds a Russian model instance, we can't easily check attributes on mock
            # but we verified add was called.


class TestGoldenDictRu:
    @patch("exporter.goldendict.main_ru.GlobalVars")
    @patch("exporter.goldendict.main_ru.generate_dpd_html")
    @patch("exporter.goldendict.main_ru.prepare_export_to_goldendict_mdict")
    @patch("exporter.goldendict.main_ru.write_size_dict")
    @patch("exporter.goldendict.main_ru.write_limited_datalist")
    @patch("exporter.goldendict.main_ru.config_test")
    def test_main_execution(
        self, mock_config, mock_limit, mock_size, mock_prep, mock_gen_dpd, mock_gv
    ):
        """Test main execution flow of GoldenDict exporter."""
        # Setup configuration to enable export
        mock_config.return_value = True

        # Setup GlobalVars mock
        mock_gv_instance = mock_gv.return_value
        mock_gv_instance.data_limit = 100  # Test limited mode to skip other generations
        mock_gv_instance.rendered_sizes = []
        mock_gv_instance.pth = MagicMock()

        # Mock generator return.
        mock_gen_dpd.return_value = ([], dict())

        # Run main
        gd_main()

        # Verify calls
        mock_gen_dpd.assert_called()
        mock_prep.assert_called()
        mock_size.assert_called()


class TestKindleExporterRu:
    @patch("exporter.kindle.kindle_exporter_ru.config_test")
    @patch("exporter.kindle.kindle_exporter_ru.ProjectPaths")
    @patch("exporter.kindle.kindle_exporter_ru.RuPaths")
    @patch("exporter.kindle.kindle_exporter_ru.render_dpd_xhtml_ru")
    @patch("exporter.kindle.kindle_exporter_ru.render_rpd_xhtml_ru")
    @patch("exporter.kindle.kindle_exporter_ru.save_abbreviations_xhtml_page")
    @patch("exporter.kindle.kindle_exporter_ru.save_title_page_xhtml")
    @patch("exporter.kindle.kindle_exporter_ru.zip_epub")
    @patch("exporter.kindle.kindle_exporter_ru.make_mobi")
    def test_main(
        self,
        mock_mobi,
        mock_zip,
        mock_title,
        mock_abbrev,
        mock_rpd,
        mock_render,
        mock_rupth,
        mock_pth,
        mock_config,
    ):
        """Test Kindle exporter main flow."""
        mock_config.return_value = True
        mock_render.return_value = 100  # id_counter
        mock_rpd.return_value = 200

        kindle_main()

        mock_render.assert_called()
        mock_zip.assert_called()
        mock_mobi.assert_called()


class TestTprExporterRu:
    @patch("exporter.tpr.tpr_exporter_ru.config_test")
    @patch("exporter.tpr.tpr_exporter_ru.GlobalVars")
    @patch("exporter.tpr.tpr_exporter_ru.generate_tpr_data")
    @patch("exporter.tpr.tpr_exporter_ru.generate_deconstructor_data")
    @patch("exporter.tpr.tpr_exporter_ru.add_spelling_mistakes")
    @patch("exporter.tpr.tpr_exporter_ru.add_roots_to_i2h")
    @patch("exporter.tpr.tpr_exporter_ru.write_tsvs")
    @patch("exporter.tpr.tpr_exporter_ru.copy_to_sqlite_db")
    @patch("exporter.tpr.tpr_exporter_ru.tpr_updater")
    @patch("exporter.tpr.tpr_exporter_ru.copy_zip_to_tpr_downloads")
    @patch("exporter.tpr.tpr_exporter_ru.make_clean_headwords_set")
    def test_main(
        self,
        mock_clean_hw,
        mock_copy_zip,
        mock_updater,
        mock_copy_db,
        mock_write_tsv,
        mock_roots,
        mock_spelling,
        mock_deconstruct,
        mock_gen_tpr,
        mock_gv,
        mock_config,
    ):
        """Test TPR exporter main flow."""
        mock_config.return_value = True
        # Mock GlobalVars instance
        gv_instance = mock_gv.return_value
        gv_instance.pth.tpr_release_path.exists.return_value = True

        tpr_main()

        mock_gen_tpr.assert_called()
        mock_copy_zip.assert_called()


class TestWebappRu:
    def test_app_initialization(self):
        """Test that the Webapp FastAPI app is initialized."""
        from fastapi import FastAPI

        assert isinstance(webapp, FastAPI)

        # Check routes exist
        routes = [route.path for route in webapp.routes]
        assert "/" in routes
        assert "/search_json" in routes
        assert "/sbs/search_json" in routes


class TestGuiMain:
    @patch("gui2.main.start_dpd_server")
    @patch("gui2.main.ft.Page")
    @patch("gui2.main.ToolKit")
    @patch("gui2.global_tab_view.GlobalTabView")
    @patch("gui2.pass1_auto_view.Pass1AutoView")
    @patch("gui2.pass1_add_view.Pass1AddView")
    @patch("gui2.pass2_pre_view.Pass2PreProcessView")
    @patch("gui2.pass2_auto_view.Pass2AutoView")
    @patch("gui2.pass2_add_view.Pass2AddView")
    @patch("gui2.tests_tab_view.TestsTabView")
    @patch("gui2.sandhi_find_replace_view.SandhiFindReplaceView")
    @patch("gui2.sandhi_view.SandhiView")
    @patch("gui2.filter_tab_view.FilterTabView")
    @patch("gui2.translations_view.TranslationsView")
    @patch("gui2.bold_search_view.BoldSearchView")
    @patch("gui2.dps_view.DpsView")
    def test_app_initialization(
        self,
        mock_dps,
        mock_bold,
        mock_transl,
        mock_filter,
        mock_sandhi2,
        mock_sandhi1,
        mock_tests,
        mock_p2add,
        mock_p2auto,
        mock_p2pre,
        mock_p1add,
        mock_p1auto,
        mock_global,
        mock_toolkit,
        mock_page,
        mock_server,
    ):
        """Test GUI App class initialization."""

        # We only care that App() can be called without erroring on instantiation
        # mocking everything it touches.

        page_instance = mock_page.return_value

        # App(page) calls build_ui which adds tabs
        App(page_instance)

        # Check that page.add was called (adding the tabs)
        page_instance.add.assert_called()
