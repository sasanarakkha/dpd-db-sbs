import json
from typing import Any

from kamma.translate.scripts.synonym_audit import (
    JudgeEntry,
    append_judgment,
    build_judge_prompt,
    find_exact_dups,
    find_near_dups,
    judge_entries,
    load_judgment_cache,
    make_cache_record,
    normalize,
    parse_judge_response,
    rebuild_field,
    split_meanings,
    variants_hash,
)


def test_split_meanings_strips_and_drops_empties():
    assert split_meanings("готовый; завершённый; ; собранный") == [
        "готовый",
        "завершённый",
        "собранный",
    ]


def test_split_meanings_single_part_no_semicolon():
    assert split_meanings("готовый") == ["готовый"]


def test_split_meanings_all_empty():
    assert split_meanings("  ; ; ") == []


def test_normalize_lowercases_and_collapses_yo():
    assert normalize("Ёлка") == "елка"


def test_normalize_strips_bracketed_segments():
    assert normalize("готовый (разг.)") == "готовый"


def test_normalize_collapses_whitespace():
    assert normalize("готовый   собранный") == "готовый собранный"


def test_normalize_strips_trailing_dot():
    assert normalize("готовый.") == "готовый"


def test_normalize_equal_after_case_and_yo_variants():
    assert normalize("Готовый") == normalize("готовый")
    assert normalize("ёлка") == normalize("елка")


def test_find_exact_dups_collapses_case_and_yo_variants():
    parts = ["готовый", "Готовый", "ёлка", "елка", "собранный"]
    assert find_exact_dups(parts) == [1, 3]


def test_find_exact_dups_no_duplicates():
    parts = ["готовый", "завершённый", "собранный"]
    assert find_exact_dups(parts) == []


def test_find_exact_dups_bracket_and_dot_variants_collapse():
    parts = ["готовый (разг.)", "готовый."]
    assert find_exact_dups(parts) == [1]


def test_find_near_dups_flags_near_identical_pair():
    parts = ["готовый", "готовенький"]
    pairs = find_near_dups(parts, threshold=0.6)
    assert len(pairs) == 1
    i, j, ratio = pairs[0]
    assert (i, j) == (0, 1)
    assert ratio >= 0.6


def test_find_near_dups_does_not_flag_distinct_meanings():
    parts = ["готовый", "завершённый"]
    assert find_near_dups(parts, threshold=0.85) == []


def test_find_near_dups_excludes_exact_dups_already_flagged():
    parts = ["готовый", "Готовый", "готовенький"]
    pairs = find_near_dups(parts, threshold=0.6)
    assert len(pairs) == 1
    i, j, _ratio = pairs[0]
    assert (i, j) == (0, 2)


def test_find_near_dups_respects_threshold():
    parts = ["готовый", "готовенький"]
    assert find_near_dups(parts, threshold=0.99) == []


def test_rebuild_field_preserves_order_and_casing():
    parts = ["Готовый", "завершённый", "Собранный"]
    assert rebuild_field(parts, drop=set()) == "Готовый; завершённый; Собранный"


def test_rebuild_field_drops_given_indexes():
    parts = ["готовый", "Готовый", "собранный"]
    assert rebuild_field(parts, drop={1}) == "готовый; собранный"


def test_rebuild_field_empty_after_dropping_all():
    parts = ["готовый", "Готовый"]
    assert rebuild_field(parts, drop={0, 1}) == ""


def test_rebuild_field_with_judge_produced_drop_set():
    parts = ["готовый", "завершённый", "собранный"]
    content = '{"42": [1]}'
    entries = [
        JudgeEntry(
            id=42, field="ru_meaning_raw", lemma_1="x", english="ready", parts=parts
        )
    ]
    verdicts = parse_judge_response(content, entries)
    assert verdicts is not None
    drop = verdicts[42]
    assert drop is not None
    assert rebuild_field(parts, drop) == "готовый; собранный"


def test_build_judge_prompt_renders_entry_fields_and_numbered_variants():
    entries = [
        JudgeEntry(
            id=1,
            field="ru_meaning_raw",
            lemma_1="dhamma",
            english="teaching; law",
            parts=["учение", "закон"],
        )
    ]
    prompt = build_judge_prompt(entries)
    assert "Entry id: 1" in prompt
    assert "Pāli headword: dhamma" in prompt
    assert "English glosses: teaching; law" in prompt
    assert "Russian variants:" in prompt
    assert "  0. учение" in prompt
    assert "  1. закон" in prompt
    assert prompt.rstrip().endswith("Return the JSON object now.")


def test_build_judge_prompt_joins_multiple_entries_with_blank_line():
    entries = [
        JudgeEntry(id=1, field="ru_meaning_raw", lemma_1="a", english="a", parts=["x"]),
        JudgeEntry(id=2, field="ru_meaning_raw", lemma_1="b", english="b", parts=["y"]),
    ]
    prompt = build_judge_prompt(entries)
    assert "Entry id: 1" in prompt
    assert "Entry id: 2" in prompt
    assert "\n\n" in prompt


def _entry(entry_id: int, parts: list[str]) -> JudgeEntry:
    return JudgeEntry(
        id=entry_id, field="ru_meaning_raw", lemma_1="x", english="y", parts=parts
    )


def test_parse_judge_response_valid_drop_list():
    entries = [_entry(1, ["a", "b", "c"])]
    result = parse_judge_response('{"1": [2]}', entries)
    assert result == {1: {2}}


def test_parse_judge_response_empty_list_means_keep():
    entries = [_entry(1, ["a", "b"])]
    result = parse_judge_response('{"1": []}', entries)
    assert result == {1: set()}


def test_parse_judge_response_none_content_returns_none():
    entries = [_entry(1, ["a", "b"])]
    assert parse_judge_response(None, entries) is None


def test_parse_judge_response_malformed_json_returns_none():
    entries = [_entry(1, ["a", "b"])]
    assert parse_judge_response("not json", entries) is None


def test_parse_judge_response_out_of_range_index_fails_that_entry():
    entries = [_entry(1, ["a", "b", "c"])]
    result = parse_judge_response('{"1": [5]}', entries)
    assert result == {1: None}


def test_parse_judge_response_non_integer_index_fails_that_entry():
    entries = [_entry(1, ["a", "b", "c"])]
    result = parse_judge_response('{"1": [1.5]}', entries)
    assert result == {1: None}


def test_parse_judge_response_boolean_index_fails_that_entry():
    entries = [_entry(1, ["a", "b", "c"])]
    result = parse_judge_response('{"1": [true]}', entries)
    assert result == {1: None}


def test_parse_judge_response_drop_all_fails_that_entry():
    entries = [_entry(1, ["a", "b", "c"])]
    result = parse_judge_response('{"1": [0, 1, 2]}', entries)
    assert result == {1: None}


def test_parse_judge_response_missing_entry_id_fails_only_that_entry():
    entries = [_entry(1, ["a", "b"]), _entry(2, ["c", "d"])]
    result = parse_judge_response('{"1": [0]}', entries)
    assert result == {1: {0}, 2: None}


def test_parse_judge_response_guard_strips_dosl_index_from_drop_set():
    entries = [_entry(1, ["a", "b", "досл. c"])]
    result = parse_judge_response('{"1": [1, 2]}', entries)
    assert result == {1: {1}}


def test_parse_judge_response_guard_is_case_insensitive_and_strips_whitespace():
    entries = [_entry(1, ["a", "  ДОСЛ. b"])]
    result = parse_judge_response('{"1": [1]}', entries)
    assert result == {1: set()}


def test_parse_judge_response_guard_converts_full_drop_attempt_to_partial_trim():
    entries = [_entry(1, ["досл. a", "b"])]
    result = parse_judge_response('{"1": [0, 1]}', entries)
    assert result == {1: {1}}


def test_parse_judge_response_guard_never_lets_dosl_survive_in_drop_set():
    entries = [_entry(1, ["a", "b", "досл. c"])]
    result = parse_judge_response('{"1": [0, 1, 2]}', entries)
    assert result is not None
    dropped = result[1]
    assert dropped is None or 2 not in dropped


def test_variants_hash_stable_and_order_sensitive():
    assert variants_hash(["a", "b"]) == variants_hash(["a", "b"])
    assert variants_hash(["a", "b"]) != variants_hash(["b", "a"])


def test_cache_round_trip_write_and_lookup(tmp_path):
    cache_path = tmp_path / "judgments.jsonl"
    entry = _entry(7, ["a", "b", "c"])
    record = make_cache_record(entry, {1}, "deepseek-v4-pro")
    append_judgment(cache_path, record)

    cache = load_judgment_cache(cache_path)
    key = (7, "ru_meaning_raw", variants_hash(entry.parts), "deepseek-v4-pro")
    assert key in cache
    assert cache[key].verdict == "trim"
    assert cache[key].drop_indexes == [1]


def test_cache_round_trip_keep_and_failed_verdicts(tmp_path):
    cache_path = tmp_path / "judgments.jsonl"
    keep_entry = _entry(1, ["a", "b"])
    failed_entry = _entry(2, ["c", "d"])
    append_judgment(cache_path, make_cache_record(keep_entry, set(), "flash"))
    append_judgment(cache_path, make_cache_record(failed_entry, None, "flash"))

    cache = load_judgment_cache(cache_path)
    keep_key = (1, "ru_meaning_raw", variants_hash(keep_entry.parts), "flash")
    failed_key = (2, "ru_meaning_raw", variants_hash(failed_entry.parts), "flash")
    assert cache[keep_key].verdict == "keep"
    assert cache[keep_key].drop_indexes == []
    assert cache[failed_key].verdict == "failed"
    assert cache[failed_key].drop_indexes is None


def test_cache_lookup_misses_on_model_mismatch(tmp_path):
    cache_path = tmp_path / "judgments.jsonl"
    entry = _entry(1, ["a", "b"])
    append_judgment(cache_path, make_cache_record(entry, {0}, "deepseek-v4-flash"))

    cache = load_judgment_cache(cache_path)
    wrong_model_key = (
        1,
        "ru_meaning_raw",
        variants_hash(entry.parts),
        "deepseek-v4-pro",
    )
    assert wrong_model_key not in cache


def test_append_judgment_writes_valid_jsonl_lines(tmp_path):
    cache_path = tmp_path / "judgments.jsonl"
    entry = _entry(1, ["a", "b"])
    append_judgment(cache_path, make_cache_record(entry, {0}, "flash"))
    append_judgment(cache_path, make_cache_record(entry, {0}, "flash"))

    lines = cache_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        json.loads(line)  # must not raise


class _FakeResponse:
    def __init__(self, content: str | None) -> None:
        self.content = content


class _FakeAIManager:
    def __init__(self, responses: list[str | None | Exception]) -> None:
        self.responses = responses
        self.calls = 0

    def request(
        self,
        prompt: str,
        *,
        prompt_sys: str,
        provider_preference: str | None,
        model: str | None,
    ) -> _FakeResponse:
        del prompt, prompt_sys, provider_preference, model
        content = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        if isinstance(content, Exception):
            raise content
        return _FakeResponse(content)


def test_judge_entries_counts_malformed_batch_responses_as_request_failures():
    ai_manager: Any = _FakeAIManager(["not json", "not json", '{"1": []}'])
    verdicts, request_failures = judge_entries(
        ai_manager,
        [_entry(1, ["a", "b"])],
        provider="deepseek",
        model="deepseek-v4-pro",
    )

    assert verdicts == {1: set()}
    assert request_failures == 2


def test_judge_entries_retries_after_request_exception():
    ai_manager: Any = _FakeAIManager([RuntimeError("quota"), '{"1": []}'])
    verdicts, request_failures = judge_entries(
        ai_manager,
        [_entry(1, ["a", "b"])],
        provider="deepseek",
        model="deepseek-v4-pro",
    )

    assert verdicts == {1: set()}
    assert request_failures == 1


def test_load_judgment_cache_skips_malformed_lines(tmp_path):
    cache_path = tmp_path / "judgments.jsonl"
    entry = _entry(7, ["a", "b"])
    valid_record = make_cache_record(entry, {1}, "deepseek-v4-pro")
    cache_path.write_text(
        "not json\n" + json.dumps(valid_record.__dict__, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    cache = load_judgment_cache(cache_path)
    key = (7, "ru_meaning_raw", variants_hash(entry.parts), "deepseek-v4-pro")
    assert list(cache) == [key]
