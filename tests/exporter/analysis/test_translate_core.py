"""Test Pāḷi passage variant handling in AI analysis reports."""

from typing import cast

from sqlalchemy.orm import Session

from tools.ai_manager import AIManager
from exporter.analysis.translate_core import (
    apply_variant_choices,
    build_system_prompt,
    extract_variant_options,
    format_markdown_table,
    generate_markdown_report,
    merge_ai_selections,
    pre_match_db_examples,
    sync_analysis_words_to_sentence,
    translate_sentence,
)


def test_extract_variant_options_resolves_default_text_and_options() -> None:
    text = (
        "jarāmaraṇaṃ "
        "soka-parideva-dukkha-domanass'upāyāsā//"
        "sokaparidevadukkhadomanass'upāyāsā//"
        "sokaparidevadukkhadomanassupāyāsā sambhavan'ti//sambhavanti."
    )

    resolved, options = extract_variant_options(text)

    assert resolved == (
        "jarāmaraṇaṃ soka-parideva-dukkha-domanass'upāyāsā sambhavan'ti."
    )
    assert options == {
        "soka-parideva-dukkha-domanass'upāyāsā": [
            "soka-parideva-dukkha-domanass'upāyāsā",
            "sokaparidevadukkhadomanass'upāyāsā",
            "sokaparidevadukkhadomanassupāyāsā",
        ],
        "sambhavan'ti": ["sambhavan'ti", "sambhavanti"],
    }


def test_generate_markdown_report_uses_ai_variant_choice_and_prints_options() -> None:
    merged_result = {
        "translation": "They arise.",
        "literal_translation": "They come into being.",
        "variant_choices": {"sambhavan'ti": 1},
        "analysis": [],
    }
    original_sentence = (
        "jarāmaraṇaṃ "
        "soka-parideva-dukkha-domanass'upāyāsā//"
        "sokaparidevadukkhadomanass'upāyāsā sambhavan'ti//sambhavanti."
    )
    variants = {
        "soka-parideva-dukkha-domanass'upāyāsā": [
            "soka-parideva-dukkha-domanass'upāyāsā",
            "sokaparidevadukkhadomanass'upāyāsā",
        ],
        "sambhavan'ti": ["sambhavan'ti", "sambhavanti"],
    }

    report = generate_markdown_report(
        merged_result,
        original_sentence,
        verse_id="SN12.1_p2",
        speech_mark_options=variants,
    )

    assert (
        "jarāmaraṇaṃ soka-parideva-dukkha-domanass'upāyāsā sambhavanti."
        in report
    )
    assert "### Variants" in report
    assert (
        "soka-parideva-dukkha-domanass'upāyāsā//"
        "sokaparidevadukkhadomanass'upāyāsā"
        in report
    )
    assert "sambhavan'ti//sambhavanti" in report


def test_apply_variant_choices_builds_sentence_from_indices() -> None:
    text = "a//b c//d."
    options = {"a": ["a", "b"], "c": ["c", "d"]}
    choices = {"a": 1, "c": 1}

    assert apply_variant_choices(text, options, choices) == "b d."


def test_sync_analysis_words_to_sentence_uses_selected_variant() -> None:
    analysis = [
        {"word": "sattā", "status": "found", "data": []},
        {"word": "gacchan'ti", "status": "found", "data": []},
        {"word": "duggatiṃ", "status": "found", "data": []},
    ]

    synced = sync_analysis_words_to_sentence(analysis, "sattā gacchanti duggatiṃ.")

    assert [token["word"] for token in synced] == ["sattā", "gacchanti", "duggatiṃ"]
    assert analysis[1]["word"] == "gacchan'ti"


def test_generate_markdown_report_builds_text_from_variant_choices() -> None:
    merged_result = {
        "translation": "They arise.",
        "literal_translation": "They come into being.",
        "variant_choices": {"sambhavan'ti": 1},
        "analysis": [],
    }
    sentence = "sambhavan'ti//sambhavanti."
    variants = {"sambhavan'ti": ["sambhavan'ti", "sambhavanti"]}

    report = generate_markdown_report(
        merged_result,
        sentence,
        verse_id="SN12.1_p2",
        speech_mark_options=variants,
    )

    assert "# Analysis of: SN12.1_p2\n\nsambhavanti." in report


def test_generate_markdown_report_syncs_table_word_to_selected_variant() -> None:
    merged_result = {
        "translation": "They go.",
        "literal_translation": "They go.",
        "variant_choices": {"gacchan'ti": 1},
        "analysis": [
            {
                "word": "sattā",
                "status": "found",
                "data": [
                    {
                        "key": "57676_0",
                        "id": 57676,
                        "grammar": "masc nom pl of satta",
                        "meaning_combo": "beings",
                    }
                ],
            },
            {
                "word": "gacchan'ti",
                "status": "found",
                "data": [
                    {
                        "key": "24043_0",
                        "id": 24043,
                        "grammar": "pr 3rd pl of gacchati",
                        "meaning_combo": "go",
                    }
                ],
            },
        ],
    }
    sentence = "sattā gacchan'ti//gacchanti."
    variants = {"gacchan'ti": ["gacchan'ti", "gacchanti"]}

    report = generate_markdown_report(
        merged_result,
        sentence,
        verse_id="DHP316",
        speech_mark_options=variants,
    )

    assert "# Analysis of: DHP316\n\nsattā gacchanti." in report
    assert "| 24043 | gacchanti | pr 3rd pl of gacchati | go |  |  |" in report
    assert "| 24043 | gacchan'ti |" not in report


def test_build_system_prompt_requests_variant_choices_not_full_text() -> None:
    prompt = build_system_prompt(
        [],
        {"sambhavan'ti": ["sambhavan'ti", "sambhavanti"]},
    )

    assert '"variant_choices": {"variant option key": 0}' in prompt
    assert "Do not return the\nfull passage text" in prompt
    assert '"verse_text"' not in prompt


def test_translate_sentence_reports_json_and_ai_progress(monkeypatch) -> None:
    events: list[str] = []

    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [],
    )

    class FakeAIManager:
        def request(self, **_kwargs):
            events.append("request")
            return type(
                "FakeResponse",
                (),
                {
                    "content": (
                        '{"translation": "", "literal_translation": "", "scores": {}}'
                    ),
                    "status_message": "",
                },
            )()

    translate_sentence(
        "sabbaṃ",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        progress=events.append,
    )

    assert events == [
        "json_start",
        "json_done",
        "ai_start",
        "request",
        "ai_done",
    ]


def test_merge_ai_selections_preserves_missing_scores_as_none() -> None:
    analysis = [
        {
            "word": "sammā",
            "status": "found",
            "data": [
                {"key": "60789_0", "meaning_combo": "rightly"},
                {"key": "60693_0", "meaning_combo": "cymbal"},
            ],
        }
    ]
    ai_response = {"scores": {"60693_0": {"score": 0}}}

    merged = merge_ai_selections(analysis, ai_response)
    options = merged["analysis"][0]["data"]

    assert options[0]["ai_score"] is None
    assert options[1]["ai_score"] == 0


def test_pre_match_db_examples_requires_text_overlap() -> None:
    analysis = [
        {
            "word": "dukkhakkhandhassa",
            "status": "found",
            "data": [
                {
                    "key": "1_0",
                    "example_1": (
                        "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti."
                    ),
                    "source_1": "DN1.12",
                    "example_2": "",
                    "source_2": "",
                },
                {
                    "key": "2_0",
                    "example_1": "unrelated example",
                    "source_1": "SN12.1",
                    "example_2": "",
                    "source_2": "",
                },
            ],
        }
    ]
    sentence = (
        "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti. "
        "nirodho, nirodho'ti"
    )

    pre_match_db_examples(analysis, "SN12.1", sentence)

    matched, source_only = analysis[0]["data"]
    assert matched["ai_score"] == 10
    assert matched["db_example_match"] is True
    assert matched["db_example_match_type"] == "text_overlap"
    assert "ai_score" not in source_only
    assert "db_example_match" not in source_only


def test_pre_match_db_examples_ranks_source_text_overlap_strongest() -> None:
    analysis = [
        {
            "word": "dukkhakkhandhassa",
            "status": "found",
            "data": [
                {
                    "key": "1_0",
                    "example_1": (
                        "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti."
                    ),
                    "source_1": "DN1.12",
                    "example_2": "",
                    "source_2": "",
                },
                {
                    "key": "2_0",
                    "example_1": (
                        "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti."
                    ),
                    "source_1": "SN12.1",
                    "example_2": "",
                    "source_2": "",
                },
            ],
        }
    ]
    sentence = "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti."

    pre_match_db_examples(analysis, "SN12.1", sentence)

    text_only, source_text = analysis[0]["data"]
    assert text_only["db_example_match_type"] == "text_overlap"
    assert source_text["db_example_match_type"] == "source_text_overlap"


def test_translate_sentence_retries_missing_component_scores(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "sammāsambuddhassa",
                "status": "found",
                "data": [
                    {
                        "key": "60847_0",
                        "id": 60847,
                        "pali": "sammāsambuddhassa",
                        "pos": "noun",
                        "grammar": "masc gen sg of sammāsambuddha",
                        "meaning_combo": "perfectly awakened Buddha",
                        "components": [
                            [
                                {
                                    "key": "60693_0",
                                    "id": 60693,
                                    "pali": "sammā",
                                    "pos": "nt",
                                    "meaning_1": "cymbal",
                                    "meaning_combo": "cymbal",
                                    "example_1": "example",
                                    "example_2": "",
                                },
                                {
                                    "key": "60789_0",
                                    "id": 60789,
                                    "pali": "sammā",
                                    "pos": "ind",
                                    "meaning_1": "perfectly",
                                    "meaning_combo": "perfectly; rightly",
                                    "example_1": "example",
                                    "example_2": "",
                                },
                            ]
                        ],
                    }
                ],
            }
        ],
    )

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs["prompt"])
            content = (
                '{"translation": "", "literal_translation": "", '
                '"scores": {"60847_0": {"score": 10}}}'
            )
            if len(calls) == 2:
                content = '{"scores": {"60789_0": {"score": 10}}}'
            return type(
                "FakeResponse",
                (),
                {"content": content, "status_message": "ok"},
            )()

    debug: dict = {}
    result = translate_sentence(
        "sammāsambuddhassa",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    component_options = result["analysis"][0]["data"][0]["components"][0]
    assert len(calls) == 2
    assert "missing dictionary option scores" in calls[1]
    assert component_options[0]["ai_score"] is None
    assert component_options[1]["ai_score"] == 10
    assert debug["retry_requests"][0]["missing_keys"] == ["60693_0", "60789_0"]


def test_translate_sentence_curated_example_match_overrides_ai_score(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "dukkhakkhandhassa",
                "status": "found",
                "data": [
                    {
                        "key": "1_0",
                        "id": 1,
                        "pali": "dukkhakkhandhassa",
                        "meaning_1": "mass of suffering",
                        "meaning_combo": "mass of suffering",
                        "example_1": (
                            "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti."
                        ),
                        "source_1": "SN12.1",
                        "example_2": "",
                        "source_2": "",
                    }
                ],
            }
        ],
    )

    class FakeAIManager:
        def request(self, **_kwargs):
            return type(
                "FakeResponse",
                (),
                {
                    "content": (
                        '{"translation": "", "literal_translation": "", '
                        '"scores": {"1_0": {"score": 0}}}'
                    ),
                    "status_message": "ok",
                },
            )()

    result = translate_sentence(
        "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti.",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        verse_source="SN12.1",
    )

    option = result["analysis"][0]["data"][0]
    assert option["ai_score"] == 10
    assert option["selection_source"] == "db_example_source_text_overlap"


def test_format_markdown_table_fallback_rejects_samma_cymbal() -> None:
    analysis = [
        {
            "word": "sammāsambuddhassa",
            "status": "found",
            "data": [
                {
                    "key": "60847_0",
                    "id": 60847,
                    "pali": "sammāsambuddhassa",
                    "pos": "noun",
                    "grammar": "masc gen sg of sammāsambuddha",
                    "meaning_combo": "perfectly awakened Buddha",
                    "compound_construction": "sammā + sambuddha",
                    "construction": "sammā + sambuddha",
                    "root_key": "",
                    "ai_score": 10,
                    "components": [
                        [
                            {
                                "key": "60693_0",
                                "id": 60693,
                                "pali": "sammā",
                                "pos": "nt",
                                "meaning_1": "cymbal",
                                "meaning_combo": "cymbal",
                                "example_1": "example",
                                "example_2": "",
                                "ai_score": None,
                            },
                            {
                                "key": "60789_0",
                                "id": 60789,
                                "pali": "sammā",
                                "pos": "ind",
                                "meaning_1": "perfectly",
                                "meaning_combo": "perfectly; rightly; correctly",
                                "example_1": "example",
                                "example_2": "",
                                "ai_score": None,
                            },
                        ]
                    ],
                }
            ],
        }
    ]

    table = format_markdown_table(analysis)

    assert "| 60693 | - sammā | nt | cymbal |" not in table
    assert "| 60789 | - sammā | ind | perfectly; rightly; correctly |" in table


def test_format_markdown_table_fallback_uses_meaning_1_quality() -> None:
    analysis = [
        {
            "word": "testcompound",
            "status": "found",
            "data": [
                {
                    "key": "1_0",
                    "id": 1,
                    "pali": "testcompound",
                    "pos": "noun",
                    "meaning_combo": "compound",
                    "ai_score": 10,
                    "components": [
                        [
                            {
                                "key": "10_0",
                                "id": 10,
                                "pali": "part",
                                "pos": "nt",
                                "meaning_1": "",
                                "meaning_combo": "display text",
                                "example_1": "example",
                                "example_2": "",
                                "ai_score": None,
                            },
                            {
                                "key": "11_0",
                                "id": 11,
                                "pali": "part",
                                "pos": "nt",
                                "meaning_1": "real meaning",
                                "meaning_combo": "real meaning",
                                "example_1": "",
                                "example_2": "",
                                "ai_score": None,
                            },
                        ]
                    ],
                }
            ],
        }
    ]

    table = format_markdown_table(analysis)

    assert "| 11 | - part | nt | real meaning |" in table
