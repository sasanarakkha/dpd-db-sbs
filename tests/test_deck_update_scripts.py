"""Tests for deck update shell helper behavior."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UPDATE_DECKS = REPO_ROOT / "scripts" / "bash" / "update_decks.sh"


def test_update_decks_uses_pali_course_push_helper() -> None:
    """The vocab branch must push courses changes without leaving dpd-db."""
    script = UPDATE_DECKS.read_text()
    helper_call = 'bash "$PROJECT_DIR/scripts/bash/pali_vocab_push.sh"'
    vocab_prompt = '"need to push vocab for classes?"'
    grammar_prompt = '"need to make updated grammar.csv?"'

    assert "git-push" not in script
    assert helper_call in script
    assert script.index(vocab_prompt) < script.index(helper_call)
    assert script.index(helper_call) < script.index(grammar_prompt)
    assert (
        'cd "$PROJECT_DIR"'
        in script[script.index(helper_call) : script.index(grammar_prompt)]
    )


def test_patimokkha_download_clears_inherited_virtual_env() -> None:
    """Cross-project uv runs should not warn about the dpd-db virtualenv."""
    script = UPDATE_DECKS.read_text()
    assert "env -u VIRTUAL_ENV uv run bash scripts/download_patimokkha.sh" in script
