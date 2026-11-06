"""Tests for RPD (Russian to Pāḷi Dictionary) functionality in Kindle exporter."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from tools.paths import ProjectPaths
from tools.paths_ru import RuPaths


class TestRenderRpdEntry:
    """Tests for render_rpd_entry_ru function."""

    def test_render_rpd_entry_basic(self):
        """Test basic RPD entry rendering with single Pāḷi equivalent."""
        from exporter.kindle.kindle_exporter_ru import render_rpd_entry_ru

        jinja_env = MagicMock()
        template = jinja_env.get_template.return_value
        template.render.return_value = "<idx:entry>test</idx:entry>"

        result = render_rpd_entry_ru(
            jinja_env, 1, "любовь", "<b class='epd'>mettā</b> f. любовь"
        )

        jinja_env.get_template.assert_called_once_with("ebook_ru_rpd_entry.jinja")
        template.render.assert_called_once_with(
            counter=1,
            english_headword="любовь",
            pali_equivalents="<b class='epd'>mettā</b> f. любовь",
        )
        assert result == "<idx:entry>test</idx:entry>"


class TestRenderRpdLetterTempl:
    """Tests for render_rpd_letter_templ_ru function."""

    def test_render_letter_a_with_header(self):
        """Test Russian letter 'а' rendering."""
        from exporter.kindle.kindle_exporter_ru import render_rpd_letter_templ_ru

        jinja_env = MagicMock()
        template = jinja_env.get_template.return_value
        template.render.return_value = "<html>letter_a</html>"

        entries = "<idx:entry>entry1</idx:entry>"
        result = render_rpd_letter_templ_ru(jinja_env, "а", entries)

        jinja_env.get_template.assert_called_once_with("ebook_ru_rpd_letter.jinja")
        template.render.assert_called_once_with(letter="а", entries=entries)
        assert result == "<html>letter_a</html>"


class TestRenderRpdXhtml:
    """Tests for render_rpd_xhtml_ru function."""

    @staticmethod
    def _love_session() -> MagicMock:
        """A fake db session whose Lookup query yields one RPD entry."""
        mock_session = MagicMock()
        mock_love = MagicMock()
        mock_love.lookup_key = "любовь"
        mock_love.rpd_unpack = [("mettā", "f", "любовь")]
        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_love,
        ]
        return mock_session

    @staticmethod
    def _paths(epub_text_dir: Path) -> tuple[MagicMock, Mock]:
        pth = MagicMock(spec=ProjectPaths)
        pth.dpd_db_path = Path("/mock/db.sqlite")
        rupth = Mock(spec=RuPaths)
        rupth.epub_text_dir = epub_text_dir
        return pth, rupth

    @patch("exporter.kindle.kindle_exporter_ru.get_jinja2_env")
    @patch("exporter.kindle.kindle_exporter_ru.get_db_session")
    def test_render_rpd_xhtml_queries_lookup_table(
        self, mock_get_session, mock_get_env, tmp_path
    ):
        """Test that RPD data is queried from Lookup table where rpd != ''."""
        from exporter.kindle.kindle_exporter_ru import render_rpd_xhtml_ru

        mock_session = self._love_session()
        mock_get_session.return_value = mock_session
        mock_get_env.return_value.get_template.return_value.render.return_value = (
            "<html>content</html>"
        )
        pth, rupth = self._paths(tmp_path)

        result = render_rpd_xhtml_ru(pth, rupth, 1)

        mock_get_env.assert_called_once_with("exporter/kindle/ru_components/templates")
        mock_get_session.assert_called_once_with(pth.dpd_db_path)
        mock_session.query.return_value.filter.assert_called_once()
        mock_session.close.assert_called_once()
        # Verify counter was incremented
        assert result > 1

    @patch("exporter.kindle.kindle_exporter_ru.get_jinja2_env")
    @patch("exporter.kindle.kindle_exporter_ru.get_db_session")
    def test_group_by_russian_letter(self, mock_get_session, mock_get_env, tmp_path):
        """Test that entries are grouped by first letter of Russian headword."""
        from exporter.kindle.kindle_exporter_ru import render_rpd_xhtml_ru

        mock_get_session.return_value = self._love_session()
        template = mock_get_env.return_value.get_template.return_value
        template.render.return_value = "<html></html>"
        pth, rupth = self._paths(tmp_path)

        render_rpd_xhtml_ru(pth, rupth, 1)

        # Check that files were created for every letter, with the entry on 'л'
        written = {path.name for path in tmp_path.iterdir()}
        assert "rpd_12.xhtml" in written
        assert len(written) == 33
        letter_calls = [
            call.kwargs
            for call in template.render.call_args_list
            if "letter" in call.kwargs
        ]
        by_letter = {c["letter"]: c["entries"] for c in letter_calls}
        assert by_letter["л"] == "<html></html>"
        assert by_letter["а"] == ""
