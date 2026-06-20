from tools.ai_batch_processor import (
    BatchProcessor,
    ComparisonResult,
    WordComparison,
)


def _processor() -> BatchProcessor:
    return object.__new__(BatchProcessor)


def test_extract_headword_id_int() -> None:
    assert _processor().extract_headword_id({"id": 42}) == 42


def test_extract_headword_id_str() -> None:
    assert _processor().extract_headword_id({"id": "42"}) == 42


def test_extract_headword_id_list() -> None:
    assert _processor().extract_headword_id({"id": [42]}) == 42


def test_extract_headword_id_empty_list() -> None:
    assert _processor().extract_headword_id({"id": []}) is None


def test_extract_headword_id_missing() -> None:
    assert _processor().extract_headword_id({}) is None


def test_extract_headword_id_invalid_type() -> None:
    assert _processor().extract_headword_id({"id": None}) is None
    assert _processor().extract_headword_id({"id": {"x": 1}}) is None


def test_comparison_result_from_dict_valid() -> None:
    result = _processor()._comparison_result_from_dict(
        {
            "id": 7,
            "lemma": "dhamma",
            "match_status": "MATCH",
            "confidence": 0.9,
            "reasoning": "same concept",
            "suggested_fix": None,
        }
    )
    assert result == ComparisonResult(
        headword_id=7,
        lemma_1="dhamma",
        match_status="MATCH",
        confidence=0.9,
        reasoning="same concept",
        suggested_fix=None,
    )


def test_comparison_result_from_dict_defaults() -> None:
    result = _processor()._comparison_result_from_dict({"id": 1})
    assert result is not None
    assert result.lemma_1 == ""
    assert result.match_status == "MATCH"
    assert result.confidence == 0.0
    assert result.reasoning == ""
    assert result.suggested_fix is None


def test_comparison_result_from_dict_invalid_id() -> None:
    assert _processor()._comparison_result_from_dict({"lemma": "dhamma"}) is None


def test_process_batch_results_filters_invalid() -> None:
    results = _processor().process_batch_results(
        [
            {"id": 1, "match_status": "MATCH"},
            {"lemma": "no_id"},
            {"id": 2, "match_status": "MISMATCH"},
        ]
    )
    assert [r.headword_id for r in results] == [1, 2]


def test_create_comparison_prompt_standard_mode_includes_word_data() -> None:
    processor = _processor()
    comp = WordComparison(
        headword_id=1,
        lemma_1="dhamma",
        english_meaning="phenomenon",
        russian_meaning="явление",
        grammar="nt",
    )
    prompt = processor.create_comparison_prompt([comp], mode="meaning")
    assert "dhamma" in prompt
    assert "phenomenon" in prompt
    assert "явление" in prompt
    assert "Russian grammarian" not in prompt


def test_create_comparison_prompt_ru_raw_mode_skips_english() -> None:
    processor = _processor()
    comp = WordComparison(
        headword_id=1,
        lemma_1="dhamma",
        english_meaning="phenomenon",
        russian_meaning="явление",
        grammar="nt",
    )
    prompt = processor.create_comparison_prompt([comp], mode="meaning_ru_raw")
    assert "Russian language grammarian" in prompt
    assert "Pali Lemma" not in prompt


def test_create_comparison_prompt_lit_mode_includes_regular_russian() -> None:
    processor = _processor()
    comp = WordComparison(
        headword_id=1,
        lemma_1="dhamma",
        english_meaning="phenomenon",
        russian_meaning="буквально явление",
        russian_meaning_alt="явление",
        grammar="nt",
    )
    prompt = processor.create_comparison_prompt([comp], mode="meaning_lit")
    assert "Regular Russian: явление" in prompt
    assert "Literal English" in prompt


def test_parse_ai_response_valid_json() -> None:
    response = (
        '{"comparisons": [{"id": 5, "lemma": "dhamma", '
        '"match_status": "MATCH", "confidence": 0.9, "reasoning": "ok"}]}'
    )
    results = _processor().parse_ai_response(response)
    assert len(results) == 1
    assert results[0].headword_id == 5
    assert results[0].match_status == "MATCH"


def test_parse_ai_response_invalid_json_falls_back_to_manual() -> None:
    comp = WordComparison(
        headword_id=9,
        lemma_1="dhamma",
        english_meaning="phenomenon",
        russian_meaning="явление",
    )
    results = _processor().parse_ai_response(
        "This is a clear MISMATCH because the meanings are opposite.", comp
    )
    assert len(results) == 1
    assert results[0].headword_id == 9
    assert results[0].match_status == "MISMATCH"


def test_parse_ai_response_invalid_json_no_word_comparison() -> None:
    results = _processor().parse_ai_response("not json at all")
    assert results == []
