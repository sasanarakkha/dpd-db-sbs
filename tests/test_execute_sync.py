import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil
import tempfile

from kamma.upstream_sync.scripts.execute_sync import (
    get_run_specific_exclusions,
    get_permanent_exclusions,
    GitContext,
)


class TestExecuteSync(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.thread_dir = Path(self.test_dir) / "thread"
        self.thread_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("subprocess.run")
    def test_git_context_init(self, mock_run):
        # Mock git rev-parse --abbrev-ref HEAD
        mock_rev_parse = MagicMock()
        mock_rev_parse.stdout = "sbs-ru\n"

        # Mock git status --porcelain
        mock_status = MagicMock()
        mock_status.stdout = "M file.py\n"

        mock_run.side_effect = [mock_rev_parse, mock_status]

        context = GitContext()
        self.assertEqual(context.original_branch, "sbs-ru")
        self.assertTrue(context.is_dirty)

    @patch("subprocess.run")
    def test_git_context_restore(self, mock_run):
        # Initial state
        mock_rev_parse_init = MagicMock()
        mock_rev_parse_init.stdout = "sbs-ru\n"
        mock_status_init = MagicMock()
        mock_status_init.stdout = ""

        # State during restore
        mock_rev_parse_current = MagicMock()
        mock_rev_parse_current.stdout = "as_upstream\n"

        # Calls:
        # 1. _get_current_branch (in __init__)
        # 2. _check_if_dirty (in __init__)
        # 3. _get_current_branch (in restore_original_state)
        # 4. subprocess.run(["git", "checkout", ...])
        mock_run.side_effect = [
            mock_rev_parse_init,
            mock_status_init,
            mock_rev_parse_current,
            MagicMock(),
        ]

        context = GitContext()
        context.restore_original_state()

        mock_run.assert_any_call(["git", "checkout", "sbs-ru"], check=False)

    def test_get_run_specific_exclusions_empty(self):
        # No file exists
        exclusions = get_run_specific_exclusions(str(self.thread_dir))
        self.assertEqual(exclusions, [])

    def test_get_run_specific_exclusions_with_file(self):
        exclusions_file = self.thread_dir / "run_exclusions.txt"
        exclusions_file.write_text(
            "path/to/file1\n# comment\n  path/to/file2  \n\n", encoding="utf-8"
        )

        exclusions = get_run_specific_exclusions(str(self.thread_dir))
        self.assertEqual(exclusions, ["path/to/file1", "path/to/file2"])

    @patch("kamma.upstream_sync.scripts.execute_sync.load_registry")
    def test_get_permanent_exclusions(self, mock_load_registry):
        mock_load_registry.return_value = {
            "no_sync_files": ["infra/file1"],
            "modified_upstream_files": [
                "db/models.py",
                {"path": "exporter/goldendict/export_goldendict.py"},
            ],
        }

        exclusions = get_permanent_exclusions()
        self.assertIn("infra/file1", exclusions)
        self.assertIn("db/models.py", exclusions)
        self.assertIn("exporter/goldendict/export_goldendict.py", exclusions)
        self.assertEqual(len(exclusions), 3)


if __name__ == "__main__":
    unittest.main()
