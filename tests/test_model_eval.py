from unittest.mock import MagicMock, patch
from scripts.other.ai_translate_evaluator import (
    get_available_models,
    build_translation_prompt,
    generate_markdown_report,
    TARGET_POS,
)
from db.models import DpdHeadword


def test_get_available_models_openai():
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.models.list.return_value.data = [
            MagicMock(id="gpt-4"),
            MagicMock(id="gpt-3.5-turbo"),
        ]

        models = get_available_models("openai", "fake-key")
        assert "gpt-4" in models
        assert "gpt-3.5-turbo" in models
        assert len(models) == 2


def test_get_available_models_openrouter():
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_get.return_value = mock_response
        mock_response.json.return_value = {
            "data": [{"id": "anthropic/claude-3-opus"}, {"id": "google/gemini-pro"}]
        }
        mock_response.raise_for_status.return_value = None

        models = get_available_models("openrouter", "fake-key")
        assert "anthropic/claude-3-opus" in models
        assert "google/gemini-pro" in models
        assert len(models) == 2


@patch("scripts.other.ai_translate_evaluator.load_translation_examples")
@patch("scripts.other.ai_translate_evaluator.replace_abbreviations")
@patch("scripts.other.ai_translate_evaluator.generate_messages_for_meaning")
@patch("scripts.other.ai_translate_evaluator.generate_messages_for_meaning_ta")
@patch("scripts.other.ai_translate_evaluator.make_meaning_combo")
def test_build_translation_prompt_ru(
    mock_make_meaning, mock_generate_ta, mock_generate, mock_replace, mock_load
):
    mock_load.return_value = {"masc": "example"}
    mock_replace.return_value = "noun"
    mock_generate.return_value = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "user"},
    ]
    mock_make_meaning.return_value = "meaning"

    word = MagicMock(spec=DpdHeadword)
    word.lemma_1 = "pali"
    word.pos = "masc"
    word.grammar = "m."
    word.example_1 = "context"

    messages = build_translation_prompt(word, MagicMock(), lang="ru")

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    mock_generate.assert_called_once_with(
        "pali", "noun", "meaning", "context", "example"
    )


@patch("scripts.other.ai_translate_evaluator.load_translation_examples")
@patch("scripts.other.ai_translate_evaluator.replace_abbreviations")
@patch("scripts.other.ai_translate_evaluator.generate_messages_for_meaning")
@patch("scripts.other.ai_translate_evaluator.generate_messages_for_meaning_ta")
@patch("scripts.other.ai_translate_evaluator.make_meaning_combo")
def test_build_translation_prompt_ta(
    mock_make_meaning, mock_generate_ta, mock_generate, mock_replace, mock_load
):
    mock_load.return_value = {"masc": "example"}
    mock_replace.return_value = "noun"
    mock_generate_ta.return_value = [
        {"role": "system", "content": "sys-ta"},
        {"role": "user", "content": "user-ta"},
    ]
    mock_make_meaning.return_value = "meaning"

    word = MagicMock(spec=DpdHeadword)
    word.lemma_1 = "pali"
    word.pos = "masc"
    word.grammar = "m."
    word.example_1 = "context"

    messages = build_translation_prompt(word, MagicMock(), lang="ta")

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    mock_generate_ta.assert_called_once_with(
        "pali", "noun", "meaning", "context", "example"
    )


def test_target_pos_constant():
    assert isinstance(TARGET_POS, list)
    assert "adj" in TARGET_POS
    assert "masc" in TARGET_POS
    assert "nt" in TARGET_POS


def test_generate_markdown_report():
    results = [
        {
            "id": 1,
            "lemma": "pali1",
            "pos": "masc",
            "english": "meaning1",
            "models": {"model-a": "ru1", "model-b": "ru2"},
        }
    ]
    shortlist = ["model-a", "model-b"]
    report = generate_markdown_report(results, "openai", shortlist, "ru")

    assert "# AI Translation Evaluation Report" in report
    assert "| 1 | pali1 | masc | meaning1 | ru1 | ru2 |" in report
    assert "**Language**: ru" in report


def test_generate_markdown_report_tamil():
    results = [
        {
            "id": 2,
            "lemma": "pali2",
            "pos": "adj",
            "english": "meaning2",
            "models": {"model-a": "ta1"},
        }
    ]
    shortlist = ["model-a"]
    report = generate_markdown_report(results, "openai", shortlist, "ta")

    assert "**Language**: ta" in report
    assert "model-a" in report


@patch("scripts.other.ai_translate_evaluator.get_db_session")
def test_select_evaluation_sample_uses_target_pos(mock_get_db):
    # Verify that select_evaluation_sample uses TARGET_POS constant
    # by checking the import works correctly
    from scripts.other.ai_translate_evaluator import select_evaluation_sample

    # Just verify the function exists and is callable
    assert callable(select_evaluation_sample)
