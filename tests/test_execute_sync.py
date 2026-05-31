"""Verify automated upstream sync execution refuses unsafe repository states."""

import unittest
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from kamma.upstream_sync.scripts.execute_sync import (
    GitContext,
    execute_sync,
    get_permanent_exclusions,
    get_run_specific_exclusions,
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

    @patch("kamma.upstream_sync.scripts.execute_sync.GitContext")
    def test_execute_sync_requires_thread_dir(self, mock_context_class):
        result = execute_sync(None)

        self.assertEqual(result, 1)
        mock_context_class.assert_not_called()

    @patch("kamma.upstream_sync.scripts.execute_sync.GitContext")
    def test_execute_sync_rejects_dirty_working_tree(self, mock_context_class):
        context = MagicMock()
        context.is_dirty = True
        context.original_branch = "sbs-ru"
        mock_context_class.return_value = context

        result = execute_sync(str(self.thread_dir))

        self.assertEqual(result, 1)
        context.restore_original_state.assert_not_called()

    @patch("kamma.upstream_sync.scripts.execute_sync.verify_manifest", return_value=1)
    @patch("kamma.upstream_sync.scripts.execute_sync.load_accepted_sync_state")
    @patch("kamma.upstream_sync.scripts.execute_sync.run_git")
    @patch("kamma.upstream_sync.scripts.execute_sync.GitContext")
    def test_execute_sync_rejects_invalid_manifest(
        self,
        mock_context_class,
        mock_run_git,
        mock_load_state,
        mock_verify_manifest,
    ):
        context = MagicMock()
        context.is_dirty = False
        context.original_branch = "sbs-ru"
        mock_context_class.return_value = context
        mock_load_state.return_value = {"last_accepted_upstream_ref": "upstream/main"}
        mock_run_git.side_effect = [
            MagicMock(stdout=""),  # git fetch upstream
            MagicMock(stdout="newsha456\n"),  # rev-parse upstream/main
        ]

        result = execute_sync(str(self.thread_dir))

        self.assertEqual(result, 1)
        mock_verify_manifest.assert_called_once_with(
            str(self.thread_dir),
            accepted_sync_state={"last_accepted_upstream_ref": "upstream/main"},
            target_sha="newsha456",
            allow_discuss=False,
            allow_blockers=False,
        )
        mock_run_git.assert_any_call(["git", "fetch", "upstream"])

    @patch("kamma.upstream_sync.scripts.execute_sync.GitContext")
    def test_execute_sync_rejects_wrong_starting_branch(self, mock_context_class):
        context = MagicMock()
        context.is_dirty = False
        context.original_branch = "feature-work"
        mock_context_class.return_value = context

        result = execute_sync(str(self.thread_dir))

        self.assertEqual(result, 1)

    @patch("kamma.upstream_sync.scripts.execute_sync.load_registry")
    @patch("kamma.upstream_sync.scripts.execute_sync.verify_manifest", return_value=0)
    @patch("kamma.upstream_sync.scripts.execute_sync.load_accepted_sync_state")
    @patch("kamma.upstream_sync.scripts.execute_sync.run_git")
    @patch("kamma.upstream_sync.scripts.execute_sync.Path.exists", return_value=False)
    @patch("kamma.upstream_sync.scripts.execute_sync.GitContext")
    def test_execute_sync_updates_as_upstream_ref_to_manifest_sha(
        self,
        mock_context_class,
        mock_path_exists,
        mock_run_git,
        mock_load_state,
        mock_verify_manifest,
        mock_load_registry,
    ):
        context = MagicMock()
        context.is_dirty = False
        context.original_branch = "sbs-ru"
        mock_context_class.return_value = context
        mock_load_state.return_value = {"last_accepted_upstream_ref": "upstream/main"}
        mock_load_registry.return_value = {
            "modified_upstream_files": [],
            "no_sync_files": [],
        }

        mock_run_git.side_effect = [
            MagicMock(stdout=""),  # git fetch upstream
            MagicMock(stdout="newsha456\n"),  # rev-parse upstream/main
            MagicMock(stdout="localsha789\n"),  # rev-parse HEAD
            MagicMock(stdout=""),  # update-ref refs/heads/as_upstream newsha456
            MagicMock(stdout=""),  # checkout as_upstream -- .
            MagicMock(stdout=""),  # git add .
        ]

        result = execute_sync(str(self.thread_dir))

        self.assertEqual(result, 0)
        mock_verify_manifest.assert_called_once_with(
            str(self.thread_dir),
            accepted_sync_state={"last_accepted_upstream_ref": "upstream/main"},
            target_sha="newsha456",
            allow_discuss=False,
            allow_blockers=False,
        )
        mock_run_git.assert_any_call(
            ["git", "update-ref", "refs/heads/as_upstream", "newsha456"]
        )
        self.assertNotIn(
            (["git", "reset", "--hard", "newsha456"],),
            [call.args for call in mock_run_git.call_args_list],
        )

    @patch("kamma.upstream_sync.scripts.execute_sync.subprocess.run")
    @patch("kamma.upstream_sync.scripts.execute_sync.Path.exists", return_value=True)
    @patch("kamma.upstream_sync.scripts.execute_sync.load_registry")
    @patch("kamma.upstream_sync.scripts.execute_sync.verify_manifest", return_value=0)
    @patch("kamma.upstream_sync.scripts.execute_sync.load_accepted_sync_state")
    @patch("kamma.upstream_sync.scripts.execute_sync.run_git")
    @patch("kamma.upstream_sync.scripts.execute_sync.GitContext")
    def test_execute_sync_fails_when_assertions_fail(
        self,
        mock_context_class,
        mock_run_git,
        mock_load_state,
        mock_verify_manifest,
        mock_load_registry,
        mock_path_exists,
        mock_subprocess_run,
    ):
        context = MagicMock()
        context.is_dirty = False
        context.original_branch = "sbs-ru"
        mock_context_class.return_value = context
        mock_load_state.return_value = {"last_accepted_upstream_ref": "upstream/main"}
        mock_load_registry.return_value = {
            "modified_upstream_files": [],
            "no_sync_files": [],
        }
        mock_run_git.side_effect = [
            MagicMock(stdout=""),
            MagicMock(stdout="newsha456\n"),
            MagicMock(stdout="localsha789\n"),
            MagicMock(stdout=""),
            MagicMock(stdout=""),
            MagicMock(stdout=""),
        ]
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            1, ["bash", "scripts/bash/dpd-sync-assertions.sh", "localsha789"]
        )

        result = execute_sync(str(self.thread_dir))

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
