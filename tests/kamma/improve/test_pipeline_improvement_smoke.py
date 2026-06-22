"""Whole-skill smoke test for pipeline-improvement rewrite."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

BANNED_TERMS = ["subagent", "Haiku", "delegate"]
BANNED_PATTERNS = ["model:"]  # treated as substring (case-insensitive already covered)
SCRIPT_COMMANDS = [
    "archive_check.py",
    "second_opinion.py",
    "precommit_gate.py",
]


@pytest.fixture
def claude_redirect() -> str:
    return (REPO_ROOT / ".claude/commands/pipeline-improvement.md").read_text(
        encoding="utf-8"
    )


@pytest.fixture
def opencode_redirect() -> str:
    return (REPO_ROOT / ".opencode/commands/pipeline-improvement.md").read_text(
        encoding="utf-8"
    )


@pytest.fixture
def pipeline_content() -> str:
    return (REPO_ROOT / "kamma/improve/pipeline.md").read_text(encoding="utf-8")


class TestThinRedirects:
    def test_claude_redirect_points_to_pipeline(self, claude_redirect: str) -> None:
        assert "kamma/improve/pipeline.md" in claude_redirect

    def test_claude_redirect_is_thin(self, claude_redirect: str) -> None:
        assert len(claude_redirect.splitlines()) <= 10

    def test_claude_redirect_no_old_paths(self, claude_redirect: str) -> None:
        assert "pipeline-improvement-queue.md" not in claude_redirect
        assert "pipeline-improvement-log.md" not in claude_redirect

    def test_opencode_redirect_points_to_pipeline(self, opencode_redirect: str) -> None:
        assert "kamma/improve/pipeline.md" in opencode_redirect

    def test_opencode_redirect_is_thin(self, opencode_redirect: str) -> None:
        assert len(opencode_redirect.splitlines()) <= 10

    def test_opencode_redirect_no_old_paths(self, opencode_redirect: str) -> None:
        assert "pipeline-improvement-queue.md" not in opencode_redirect
        assert "pipeline-improvement-log.md" not in opencode_redirect


class TestCanonicalPathsExist:
    def test_queue_exists(self) -> None:
        assert (REPO_ROOT / "kamma/improve/queue.md").exists()

    def test_log_exists(self) -> None:
        assert (REPO_ROOT / "kamma/improve/log.md").exists()

    def test_pipeline_exists(self) -> None:
        assert (REPO_ROOT / "kamma/improve/pipeline.md").exists()


class TestPipelineReferences:
    def test_references_queue_path(self, pipeline_content: str) -> None:
        assert "kamma/improve/queue.md" in pipeline_content

    def test_references_log_path(self, pipeline_content: str) -> None:
        assert "kamma/improve/log.md" in pipeline_content

    def test_references_archive_check(self, pipeline_content: str) -> None:
        assert "archive_check.py" in pipeline_content

    def test_references_second_opinion(self, pipeline_content: str) -> None:
        assert "second_opinion.py" in pipeline_content

    def test_references_precommit_gate(self, pipeline_content: str) -> None:
        assert "precommit_gate.py" in pipeline_content


class TestNoBannedTerms:
    def test_no_subagent(self, pipeline_content: str) -> None:
        assert "subagent" not in pipeline_content.lower()

    def test_no_haiku(self, pipeline_content: str) -> None:
        assert "haiku" not in pipeline_content.lower()

    def test_no_model_colon(self, pipeline_content: str) -> None:
        assert "model:" not in pipeline_content.lower()

    def test_no_delegate(self, pipeline_content: str) -> None:
        assert "delegate" not in pipeline_content.lower()


class TestNoOldPaths:
    def test_pipeline_no_old_queue_path(self, pipeline_content: str) -> None:
        assert ".claude/pipeline-improvement-queue.md" not in pipeline_content

    def test_pipeline_no_old_log_path(self, pipeline_content: str) -> None:
        assert ".claude/pipeline-improvement-log.md" not in pipeline_content
