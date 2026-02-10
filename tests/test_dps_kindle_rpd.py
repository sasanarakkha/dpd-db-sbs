"""Tests for RPD (Russian to Pāḷi Dictionary) functionality in Kindle exporter."""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from tools.paths_ru import RuPaths
from tools.paths import ProjectPaths


class TestRenderRpdEntry:
    """Tests for render_rpd_entry function."""

    def test_render_rpd_entry_basic(self):
        """Test basic RPD entry rendering with single Pāḷi equivalent."""
        from exporter.kindle.kindle_exporter_ru import render_rpd_entry

        rupth = Mock(spec=RuPaths)
        rupth.ebook_rpd_entry_templ_path = Path("/mock/template.html")

        with patch("exporter.kindle.kindle_exporter_ru.Template") as MockTemplate:
            mock_template_instance = MagicMock()
            mock_template_instance.render.return_value = "<idx:entry>test</idx:entry>"
            MockTemplate.return_value = mock_template_instance

            result = render_rpd_entry(
                rupth, 1, "любовь", "<b class='epd'>mettā</b> f. любовь"
            )

            MockTemplate.assert_called_once_with(
                filename=str(rupth.ebook_rpd_entry_templ_path)
            )
            mock_template_instance.render.assert_called_once_with(
                counter=1,
                english_headword="любовь",
                pali_equivalents="<b class='epd'>mettā</b> f. любовь",
            )
            assert result == "<idx:entry>test</idx:entry>"


class TestRenderRpdLetterTempl:
    """Tests for render_rpd_letter_templ function."""

    def test_render_letter_a_with_header(self):
        """Test Russian letter 'а' rendering."""
        from exporter.kindle.kindle_exporter_ru import render_rpd_letter_templ

        rupth = Mock(spec=RuPaths)
        rupth.ebook_rpd_letter_templ_path = Path("/mock/letter.html")

        with patch("exporter.kindle.kindle_exporter_ru.Template") as MockTemplate:
            mock_template_instance = MagicMock()
            mock_template_instance.render.return_value = "<html>letter_a</html>"
            MockTemplate.return_value = mock_template_instance

            entries = "<idx:entry>entry1</idx:entry>"
            result = render_rpd_letter_templ(rupth, "а", entries)

            MockTemplate.assert_called_once_with(
                filename=str(rupth.ebook_rpd_letter_templ_path)
            )
            mock_template_instance.render.assert_called_once_with(
                letter="а", entries=entries
            )
            assert result == "<html>letter_a</html>"


class TestRenderRpdXhtml:
    """Tests for render_rpd_xhtml function."""

    @patch("exporter.kindle.kindle_exporter_ru.get_db_session")
    @patch("exporter.kindle.kindle_exporter_ru.Template")
    def test_render_rpd_xhtml_queries_lookup_table(
        self, mock_template, mock_get_session
    ):
        """Test that RPD data is queried from Lookup table where rpd != ''."""
        from exporter.kindle.kindle_exporter_ru import render_rpd_xhtml

        # Setup mock session and query
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Create mock lookup entries
        mock_entry1 = MagicMock()
        mock_entry1.lookup_key = "любовь"
        mock_entry1.rpd_unpack = [("mettā", "f", "любовь")]

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_entry1,
        ]

        # Setup mock template
        mock_template_instance = MagicMock()
        mock_template_instance.render.return_value = "<html>content</html>"
        mock_template.return_value = mock_template_instance

        # Setup mock paths
        pth = MagicMock(spec=ProjectPaths)
        pth.dpd_db_path = Path("/mock/db.sqlite")
        rupth = Mock(spec=RuPaths)
        rupth.epub_text_dir = Path("/mock/epub/text")
        rupth.ebook_rpd_entry_templ_path = Path("/mock/entry.html")
        rupth.ebook_rpd_letter_templ_path = Path("/mock/letter.html")

        with patch("builtins.open", MagicMock()):
            result = render_rpd_xhtml(pth, rupth, 1)

        # Verify counter was incremented
        assert result > 1

    @patch("exporter.kindle.kindle_exporter_ru.get_db_session")
    def test_group_by_russian_letter(self, mock_get_session):
        """Test that entries are grouped by first letter of Russian headword."""
        from exporter.kindle.kindle_exporter_ru import render_rpd_xhtml

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_love = MagicMock()
        mock_love.lookup_key = "любовь"
        mock_love.rpd_unpack = [("mettā", "f", "любовь")]

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_love,
        ]

        pth = MagicMock(spec=ProjectPaths)
        pth.dpd_db_path = Path("/mock/db.sqlite")
        rupth = Mock(spec=RuPaths)
        rupth.epub_text_dir = Path("/mock/epub/text")
        rupth.ebook_rpd_entry_templ_path = Path("/mock/entry.html")
        rupth.ebook_rpd_letter_templ_path = Path("/mock/letter.html")

        mock_open = MagicMock()
        with patch("builtins.open", mock_open):
            with patch("exporter.kindle.kindle_exporter_ru.Template") as mock_template:
                mock_template_instance = MagicMock()
                mock_template_instance.render.return_value = "<html></html>"
                mock_template.return_value = mock_template_instance

                render_rpd_xhtml(pth, rupth, 1)

        # Check that files were created for letter 'л'
        calls = mock_open.call_args_list
        file_paths = [str(call[0][0]) for call in calls]

        assert any("rpd_12_л.xhtml" in fp for fp in file_paths)
