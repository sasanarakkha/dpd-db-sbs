import json

from tools.ai_json_parser import JSONParser


def _parser() -> JSONParser:
    return JSONParser()


def test_extract_direct_parse() -> None:
    content = json.dumps({"comparisons": [{"id": 1}]})
    assert _parser().extract_json_from_response(content) == content


def test_extract_brace_matching_strips_surrounding_text() -> None:
    inner = json.dumps({"comparisons": [{"id": 1}]})
    content = f"Here is the result:\n{inner}\nLet me know if you need anything else."
    assert _parser().extract_json_from_response(content) == inner


def test_extract_pattern_matching_markdown_fence() -> None:
    inner = json.dumps({"comparisons": [{"id": 1}]})
    content = f"```json\n{inner}\n```"
    assert _parser().extract_json_from_response(content) == inner


def test_enhanced_brace_matching_ignores_stray_brace_after_json() -> None:
    # a stray '{...}' in trailing prose defeats simple find('{')/rfind('}')
    # brace matching (it would over-extend to the last '}' in the prose)
    # but the string-aware, depth-counting enhanced matcher stops at the
    # real closing brace of the JSON object.
    payload = {"comparisons": [{"id": 1}]}
    inner = json.dumps(payload)
    content = inner + "\nNote: {this is unrelated trailing text}"
    assert _parser()._try_enhanced_brace_matching(content) == inner


def test_extract_returns_none_when_no_comparisons_key() -> None:
    content = json.dumps({"other": True})
    assert _parser().extract_json_from_response(content) is None


def test_strip_markdown_blocks() -> None:
    content = '```json\n{"a": 1}\n```'
    assert _parser()._strip_markdown_blocks(content) == '{"a": 1}'


def test_fix_syntax_issues_trailing_comma() -> None:
    content = '{"comparisons": [{"id": 1},]}'
    assert _parser()._fix_syntax_issues(content) == '{"comparisons": [{"id": 1}]}'


def test_fix_truncated_strings_closes_unclosed_reasoning() -> None:
    content = '{"id": 1, "reasoning": "this got cut off}'
    fixed = _parser()._fix_truncated_strings(content)
    assert fixed == '{"id": 1, "reasoning": "this got cut off"}'


def test_fix_truncated_strings_leaves_closed_reasoning_unchanged() -> None:
    content = '{"id": 1, "reasoning": "complete"}'
    assert _parser()._fix_truncated_strings(content) == content


def test_fix_missing_fields_adds_lemma_after_suggested_fix() -> None:
    content = (
        '"id": 1, "match_status": "ok", "confidence": 0.9, '
        '"reasoning": "fine", "suggested_fix": "none"'
    )
    fixed = _parser()._fix_missing_fields(content)
    assert fixed.endswith('"suggested_fix": "none", "lemma": ""')


def test_fix_incomplete_array_closes_dangling_comparisons() -> None:
    content = '{"comparisons": [{"id": 1, "ok": true}'
    fixed = _parser()._fix_incomplete_array(content)
    assert fixed == '{"comparisons": [{"id": 1, "ok": true}]}'


def test_clean_json_content_recovers_truncated_reasoning() -> None:
    content = (
        '{"comparisons": [{"id": 1, "match_status": "ok", "confidence": 0.9, '
        '"reasoning": "cut off}]}'
    )
    cleaned = _parser().clean_json_content(content)
    assert cleaned is not None
    data = json.loads(cleaned)
    assert data["comparisons"][0]["id"] == 1
    assert data["comparisons"][0]["reasoning"] == "cut off"


def test_clean_json_content_returns_none_on_unrecoverable_input() -> None:
    assert _parser().clean_json_content("not json at all {{{") is None
