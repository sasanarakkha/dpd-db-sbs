"""Test Pāḷi passage variant handling in AI analysis reports."""

from typing import cast

import pytest

from sqlalchemy.orm import Session

import exporter.analysis.translate_core as translate_core
from tools.ai_manager import AIManager
from exporter.analysis.translate_core import (
    _build_missing_scores_prompt,
    _extract_word_key_map,
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

    assert "jarāmaraṇaṃ soka-parideva-dukkha-domanass'upāyāsā sambhavanti." in report
    assert "### Variants" in report
    assert (
        "soka-parideva-dukkha-domanass'upāyāsā//"
        "sokaparidevadukkhadomanass'upāyāsā" in report
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


def test_build_system_prompt_uses_compact_context_json() -> None:
    analysis = [
        {
            "word": "samma",
            "data": [
                {
                    "key": "12345_0",
                    "pali": "samma",
                    "meaning_combo": "rightly",
                }
            ],
        }
    ]
    missing_groups = [
        {
            "word": "samma",
            "context": "samma",
            "missing_keys": ["12345_0"],
            "options": [{"key": "12345_0", "meaning_combo": "rightly"}],
        }
    ]

    system_prompt = build_system_prompt(analysis)
    missing_scores_prompt = _build_missing_scores_prompt("samma", missing_groups)

    assert '"key":"12345_0"' in system_prompt
    assert '  "key"' not in system_prompt
    assert '"missing_keys":["12345_0"]' in missing_scores_prompt
    assert '  "missing_keys"' not in missing_scores_prompt


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
        "evam'etassa kevalassa dukkhakkhandhassa nirodho hotī'ti. nirodho, nirodho'ti"
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


def _patch_sammasambuddhassa_analysis(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_translate_sentence_retry_accepts_flat_score_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    _patch_sammasambuddhassa_analysis(monkeypatch)

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs["prompt"])
            content = (
                '{"translation": "", "literal_translation": "", '
                '"scores": {"60847_0": {"score": 10}}}'
            )
            if len(calls) == 2:
                content = '{"60789_0": {"score": 10}}'
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
    assert component_options[1]["ai_score"] == 10


def test_translate_sentence_retry_ignores_unrelated_flat_score_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    _patch_sammasambuddhassa_analysis(monkeypatch)

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs["prompt"])
            content = (
                '{"translation": "", "literal_translation": "", '
                '"scores": {"60847_0": {"score": 10}}}'
            )
            if len(calls) == 2:
                content = '{"unrelated_key": {"score": 5}}'
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
    assert "unrelated_key" not in debug["final_scores"]
    assert component_options[1]["ai_score"] is None


def test_coerce_flat_score_map_shapes() -> None:
    expected = {"a_0", "b_0"}

    assert translate_core._coerce_flat_score_map({"a_0": {"score": 3}}, expected) == {
        "scores": {"a_0": {"score": 3}}
    }
    assert translate_core._coerce_flat_score_map({"a_0": 7}, expected) == {
        "scores": {"a_0": {"score": 7}}
    }
    untouched = {"scores": {"a_0": {"score": 1}}}
    assert translate_core._coerce_flat_score_map(untouched, expected) is untouched
    prose_like = {"x": "y", "z": "w", "a_0": {"score": 1}}
    assert translate_core._coerce_flat_score_map(prose_like, expected) is prose_like


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


def test_translate_sentence_db_example_preserves_ai_contextual_meaning(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "dharaṇī",
                "status": "found",
                "data": [
                    {
                        "key": "35009_0",
                        "id": 35009,
                        "pali": "dharaṇī",
                        "pos": "fem",
                        "meaning_1": "earth",
                        "meaning_combo": "earth; world; lit. carrier",
                        "example_1": "dharaṇī siñcati.",
                        "source_1": "TH50",
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
                        '"scores": {"35009_0": {"score": 10, '
                        '"contextual_meaning": "earth", '
                        '"selected_pos": "fem"}}}'
                    ),
                    "status_message": "ok",
                },
            )()

    result = translate_sentence(
        "dharaṇī siñcati.",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        verse_source="TH50",
    )

    option = result["analysis"][0]["data"][0]
    assert option["ai_score"] == 10
    assert option["meaning_combo"] == "earth"
    assert option["selected_pos"] == "fem"
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


def test_build_system_prompt_json_instruction_at_start() -> None:
    prompt = build_system_prompt([])
    first_line = prompt.strip().splitlines()[0]
    assert "JSON" in first_line


def test_translate_sentence_reformat_triggered_when_prose_returned(
    monkeypatch,
) -> None:
    """When the first response is not JSON, a second reformat request is made."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [],
    )
    calls: list[dict] = []

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                content = "Here is a detailed prose analysis of the verse..."
            else:
                content = '{"translation": "reformatted", "literal_translation": "lit", "scores": {}}'
            return type("R", (), {"content": content, "status_message": "ok"})()

    result = translate_sentence(
        "sabbaṃ",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
    )

    assert len(calls) == 2
    assert result["translation"] == "reformatted"


def test_translate_sentence_reformat_progress_events(monkeypatch) -> None:
    """Reformat path emits ai_reformat_start and ai_reformat_done progress events."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [],
    )
    events: list[str] = []

    class FakeAIManager:
        def request(self, **kwargs):
            events.append("request")
            if len([e for e in events if e == "request"]) == 1:
                content = "Prose analysis, not JSON."
            else:
                content = '{"translation": "", "literal_translation": "", "scores": {}}'
            return type("R", (), {"content": content, "status_message": "ok"})()

    translate_sentence(
        "sabbaṃ",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        progress=events.append,
    )

    assert "ai_reformat_start" in events
    assert "ai_reformat_done" in events
    assert events.index("ai_reformat_start") < events.index("ai_reformat_done")


def test_translate_sentence_reformat_debug_keys_populated(monkeypatch) -> None:
    """Debug dict gets reformat keys when prose response triggers reformat."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [],
    )
    call_count = 0

    class FakeAIManager:
        def request(self, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                content = "Prose, not JSON."
            else:
                content = (
                    '{"translation": "ok", "literal_translation": "ok", "scores": {}}'
                )
            return type("R", (), {"content": content, "status_message": "ok"})()

    debug: dict = {}
    translate_sentence(
        "sabbaṃ",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert "reformat_raw_response" in debug
    assert "reformat_status_message" in debug
    assert "reformat_parse_error" in debug
    assert debug["reformat_parse_error"] == ""


def test_extract_word_key_map_detects_disambiguation_map() -> None:
    """A flat {word: option_key} map whose values are real keys is recognised."""
    analysis = [
        {"word": "x", "data": [{"key": "35009_0"}, {"key": "62854_0"}]},
    ]

    assert _extract_word_key_map(
        {"dharaṇī": "35009_0", "siñcati": "62854_0"}, analysis
    ) == {"dharaṇī": "35009_0", "siñcati": "62854_0"}


def test_extract_word_key_map_detects_nested_disambiguation_map() -> None:
    """A nested antigravity disambiguation map is recognised."""
    analysis = [
        {"word": "x", "data": [{"key": "35009_0"}, {"key": "62854_0"}]},
    ]

    assert _extract_word_key_map(
        {"disambiguation": {"dharaṇī": "35009_0", "siñcati": "62854_0"}},
        analysis,
    ) == {"dharaṇī": "35009_0", "siñcati": "62854_0"}


def test_extract_word_key_map_rejects_non_map_shapes() -> None:
    """Proper schema, dict-valued, unknown-key, and empty responses are not maps."""
    analysis = [{"word": "x", "data": [{"key": "35009_0"}]}]

    # Proper {translation, scores} schema is not a disambiguation map.
    assert _extract_word_key_map({"translation": "x", "scores": {}}, analysis) is None
    # Dict-valued wrong schema (matches the reformat fallback test) is not a map.
    assert _extract_word_key_map({"passa": {"lemma": "passati"}}, analysis) is None
    # String values that match no real option key are not a map.
    assert _extract_word_key_map({"a": "nope", "b": "nada"}, analysis) is None
    # Empty response is not a map.
    assert _extract_word_key_map({}, analysis) is None
    # No analysis keys to match against → never a map.
    assert _extract_word_key_map({"dharaṇī": "35009_0"}, []) is None


def test_translate_sentence_uses_word_key_map_skips_reformat(monkeypatch) -> None:
    """A word→key first response drives scores directly and fetches only the translation.

    The wasteful prose-reformat round-trip must NOT fire; instead a lightweight
    translation-only call supplies translation/literal_translation.
    """
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "dharaṇī",
                "status": "found",
                "data": [
                    {
                        "key": "35009_0",
                        "id": 35009,
                        "pali": "dharaṇī",
                        "pos": "fem",
                        "meaning_combo": "earth",
                    }
                ],
            },
            {
                "word": "siñcati",
                "status": "found",
                "data": [
                    {
                        "key": "62854_0",
                        "id": 62854,
                        "pali": "siñcati",
                        "pos": "verb",
                        "meaning_combo": "sprinkles",
                    }
                ],
            },
        ],
    )
    calls: list[dict] = []

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                content = '{"dharaṇī": "35009_0", "siñcati": "62854_0"}'
            else:
                content = (
                    '{"translation": "The earth is sprinkled.", '
                    '"literal_translation": "earth sprinkles."}'
                )
            return type("R", (), {"content": content, "status_message": "ok"})()

    debug: dict = {}
    result = translate_sentence(
        "dharaṇī siñcati",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    # Exactly two calls: the map first call + a translation-only call. No retry,
    # because the map already supplies every top-level option key.
    assert len(calls) == 2
    # The second call is the translation prompt, NOT the prose-reformat prompt.
    assert "did not match" not in calls[1]["prompt"]
    assert "Translate" in calls[1]["prompt"]
    # Scores come straight from the discarded-no-longer first call.
    assert result["analysis"][0]["data"][0]["ai_score"] == 10
    assert result["analysis"][1]["data"][0]["ai_score"] == 10
    # Translation comes from the follow-up call.
    assert result["translation"] == "The earth is sprinkled."
    assert result["literal_translation"] == "earth sprinkles."
    # The prose-reformat debug keys are absent because reformat never ran.
    assert "reformat_raw_response" not in debug
    assert debug["translation_raw_response"]


def test_translate_sentence_word_key_map_applies_contextual_meanings(
    monkeypatch,
) -> None:
    """A word→key map path should apply contextual meanings from the follow-up."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "dharaṇī",
                "status": "found",
                "data": [
                    {
                        "key": "35009_0",
                        "id": 35009,
                        "pali": "dharaṇī",
                        "pos": "fem",
                        "meaning_combo": "earth; world; lit. carrier",
                        "example_1": "dharaṇī siñcati.",
                        "source_1": "TH50",
                        "example_2": "",
                        "source_2": "",
                    }
                ],
            }
        ],
    )
    calls: list[dict] = []

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                content = '{"dharaṇī": "35009_0"}'
            else:
                content = (
                    '{"translation": "The earth is sprinkled.", '
                    '"literal_translation": "earth sprinkles.", '
                    '"meanings": {"dharaṇī": "earth"}}'
                )
            return type("R", (), {"content": content, "status_message": "ok"})()

    result = translate_sentence(
        "dharaṇī siñcati.",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        verse_source="TH50",
    )

    option = result["analysis"][0]["data"][0]
    assert '"meanings"' in calls[1]["prompt"]
    assert option["ai_score"] == 10
    assert option["meaning_combo"] == "earth"
    assert option["selection_source"] == "db_example_source_text_overlap"


def test_translate_sentence_uses_nested_word_key_map_skips_reformat(
    monkeypatch,
) -> None:
    """A nested disambiguation map follows the same translation-only path."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "dharaṇī",
                "status": "found",
                "data": [
                    {
                        "key": "35009_0",
                        "id": 35009,
                        "pali": "dharaṇī",
                        "pos": "fem",
                        "meaning_combo": "earth",
                    }
                ],
            },
            {
                "word": "siñcati",
                "status": "found",
                "data": [
                    {
                        "key": "62854_0",
                        "id": 62854,
                        "pali": "siñcati",
                        "pos": "verb",
                        "meaning_combo": "sprinkles",
                    }
                ],
            },
        ],
    )
    calls: list[dict] = []

    class FakeAIManager:
        def request(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                content = (
                    '{"disambiguation": {"dharaṇī": "35009_0", "siñcati": "62854_0"}}'
                )
            else:
                content = (
                    '{"translation": "The earth is sprinkled.", '
                    '"literal_translation": "earth sprinkles."}'
                )
            return type("R", (), {"content": content, "status_message": "ok"})()

    debug: dict = {}
    result = translate_sentence(
        "dharaṇī siñcati",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
        debug=debug,
    )

    assert len(calls) == 2
    assert "did not match" not in calls[1]["prompt"]
    assert "Translate" in calls[1]["prompt"]
    assert result["analysis"][0]["data"][0]["ai_score"] == 10
    assert result["analysis"][1]["data"][0]["ai_score"] == 10
    assert result["translation"] == "The earth is sprinkled."
    assert result["literal_translation"] == "earth sprinkles."
    assert "reformat_raw_response" not in debug
    assert debug["translation_raw_response"]


def test_translate_sentence_reformat_triggered_on_wrong_schema(monkeypatch) -> None:
    """Valid JSON in the wrong schema (no translation/scores keys) triggers reformat."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [],
    )
    call_count = 0

    class FakeAIManager:
        def request(self, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                content = '{"passa": {"lemma": "passati", "meaning": "see"}}'
            else:
                content = '{"translation": "Behold!", "literal_translation": "See!", "scores": {}}'
            return type("R", (), {"content": content, "status_message": "ok"})()

    result = translate_sentence(
        "passa",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
    )

    assert call_count == 2
    assert result["translation"] == "Behold!"


def test_missing_scores_prompt_specifies_score_object_format() -> None:
    """Retry prompt must include an explicit {"score": N} value format example."""
    missing_groups = [
        {
            "word": "sammā",
            "context": "sammā",
            "missing_keys": ["60789_0"],
            "options": [{"key": "60789_0", "meaning_combo": "rightly"}],
        }
    ]
    prompt = _build_missing_scores_prompt("sammā", missing_groups)
    assert '"score"' in prompt


def test_missing_scores_prompt_requires_contextual_meaning_for_decon_keys() -> None:
    """When missing keys include a decon_ key, prompt must contain contextual_meaning instruction."""
    missing_groups = [
        {
            "word": "okassa",
            "context": "okassa",
            "missing_keys": ["decon_okassa_0"],
            "options": [{"key": "decon_okassa_0", "meaning_combo": "[Deconstructed]"}],
        }
    ]
    prompt = _build_missing_scores_prompt("okassa", missing_groups)
    assert "contextual_meaning" in prompt


def test_translate_sentence_retry_contextual_meaning_applied_to_decon_option(
    monkeypatch,
) -> None:
    """When retry returns contextual_meaning for a decon_ key, meaning_combo is updated."""
    monkeypatch.setattr(
        "exporter.analysis.translate_core.analyze_sentence",
        lambda _sentence, _db_session: [
            {
                "word": "okassa",
                "status": "found",
                "data": [
                    {
                        "key": "decon_okassa_0",
                        "id": 0,
                        "pali": "okassa",
                        "pos": "sandhi",
                        "meaning_combo": "[Deconstructed]",
                    }
                ],
            }
        ],
    )
    call_count = 0

    class FakeAIManager:
        def request(self, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                content = '{"translation": "to the dwelling", "literal_translation": "to the house", "scores": {}}'
            else:
                content = '{"scores": {"decon_okassa_0": {"score": 10, "contextual_meaning": "to the dwelling"}}}'
            return type("R", (), {"content": content, "status_message": "ok"})()

    result = translate_sentence(
        "okassa",
        cast(Session, object()),
        ai_manager=cast(AIManager, FakeAIManager()),
    )

    option = result["analysis"][0]["data"][0]
    assert option["ai_score"] == 10
    assert option["meaning_combo"] == "to the dwelling"
