import csv
import json
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, Russian

from kamma.translate.scripts.synonym_audit import (
    TSV_HEADER,
    JudgeEntry,
    TsvFieldMismatchError,
    append_audit_log,
    apply_review_tsv,
    build_tsv_row,
    main,
    record_last_audit,
    append_judgment,
    build_judge_prompt,
    find_cached_judgment,
    find_exact_dups,
    find_near_dups,
    judge_entries,
    judge_with_chain,
    load_judgment_cache,
    make_cache_record,
    normalize,
    parse_judge_response,
    rebuild_field,
    resolve_chain,
    split_meanings,
    update_failure_streak,
    variants_hash,
)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "kamma.translate.scripts.synonym_audit.time.sleep", lambda _s: None
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


def test_find_exact_dups_keeps_bracket_only_variants():
    parts = ["готовый (разг.)", "готовый"]
    assert find_exact_dups(parts) == []


def test_find_exact_dups_dot_case_variants_collapse():
    assert find_exact_dups(["наступающий", "Наступающий."]) == [1]


def test_find_exact_dups_identical_bracketed_variants_collapse():
    assert find_exact_dups(["идет (в)", "Идёт (в)"]) == [1]


def test_bracket_only_pair_goes_to_near_dups_with_ratio_one():
    parts = ["идет", "идет (в)"]
    assert find_exact_dups(parts) == []
    pairs = find_near_dups(parts, threshold=0.85)
    assert [(i, j) for i, j, _ in pairs] == [(0, 1)]
    assert pairs[0][2] == 1.0


def test_split_meanings_ignores_semicolons_inside_brackets():
    assert split_meanings("a (b; c); d") == ["a (b; c)", "d"]


def test_split_meanings_unbalanced_closing_bracket_never_goes_negative():
    assert split_meanings("a) ; b; c") == ["a)", "b", "c"]


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
    result = judge_entries(
        ai_manager,
        [_entry(1, ["a", "b"])],
        provider="deepseek",
        model="deepseek-v4-pro",
    )

    assert result.verdicts == {1: set()}
    assert result.request_failures == 2
    assert result.any_success


def test_judge_entries_retries_after_request_exception():
    ai_manager: Any = _FakeAIManager([RuntimeError("quota"), '{"1": []}'])
    result = judge_entries(
        ai_manager,
        [_entry(1, ["a", "b"])],
        provider="deepseek",
        model="deepseek-v4-pro",
    )

    assert result.verdicts == {1: set()}
    assert result.request_failures == 1


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


# --- 2.2 judge robustness ---


def test_parse_judge_response_accepts_markdown_fences():
    entries = [_entry(1, ["a", "b", "c"])]
    assert parse_judge_response('```json\n{"1": [1]}\n```', entries) == {1: {1}}
    assert parse_judge_response('```\n{"1": []}\n```', entries) == {1: set()}


def test_find_cached_judgment_skips_failed_records(tmp_path):
    path = tmp_path / "j.jsonl"
    entry = _entry(1, ["a", "b"])
    append_judgment(path, make_cache_record(entry, None, "flash"))
    cache = load_judgment_cache(path)
    assert (
        find_cached_judgment(cache, 1, "ru_meaning_raw", variants_hash(entry.parts))
        is None
    )


def test_find_cached_judgment_serves_keep_and_trim_from_any_model(tmp_path):
    path = tmp_path / "j.jsonl"
    keep = _entry(1, ["a", "b"])
    trim = _entry(2, ["c", "d"])
    append_judgment(path, make_cache_record(keep, set(), "some-fallback"))
    append_judgment(path, make_cache_record(trim, {1}, "deepseek-flash"))
    cache = load_judgment_cache(path)
    hit_keep = find_cached_judgment(
        cache, 1, "ru_meaning_raw", variants_hash(keep.parts)
    )
    hit_trim = find_cached_judgment(
        cache, 2, "ru_meaning_raw", variants_hash(trim.parts)
    )
    assert hit_keep is not None and hit_keep.verdict == "keep"
    assert hit_trim is not None and hit_trim.drop_indexes == [1]


def test_find_cached_judgment_latest_timestamp_wins(tmp_path):
    path = tmp_path / "j.jsonl"
    entry = _entry(1, ["a", "b"])
    older = make_cache_record(entry, set(), "m-old")
    older.timestamp = "2026-01-01T00:00:00+00:00"
    newer = make_cache_record(entry, {0}, "m-new")
    newer.timestamp = "2026-06-01T00:00:00+00:00"
    append_judgment(path, newer)
    append_judgment(path, older)  # written later but older timestamp
    cache = load_judgment_cache(path)
    hit = find_cached_judgment(cache, 1, "ru_meaning_raw", variants_hash(entry.parts))
    assert hit is not None and hit.model == "m-new"


def test_failure_streak_reaches_limit_after_five_failed_requests():
    streak = 0
    for _ in range(5):
        streak = update_failure_streak(streak, request_failures=1, any_success=False)
    assert streak == 5


def test_failure_streak_resets_when_any_request_succeeded():
    # five FAILED entries inside one successful request must not build a streak
    assert update_failure_streak(4, request_failures=0, any_success=True) == 0


# --- 2.3 judge chain ---


class _PairFakeManager:
    def __init__(self, by_model: dict[str, list[str | None | Exception]]) -> None:
        self.by_model = by_model
        self.calls: list[str | None] = []
        self.providers = {"deepseek": object(), "openrouter": object()}
        self.DEFAULT_MODELS = [
            ("deepseek", "flash", 0, 150.0),
            ("openrouter", "fallback", 0, 150.0),
            ("nvidia", "uninitialised", 0, 150.0),
        ]

    def request(
        self,
        prompt: str,
        *,
        prompt_sys: str,
        provider_preference: str | None,
        model: str | None,
    ) -> _FakeResponse:
        del prompt, prompt_sys, provider_preference
        self.calls.append(model)
        assert model is not None
        queue = self.by_model[model]
        content = queue[min(self.calls.count(model) - 1, len(queue) - 1)]
        if isinstance(content, Exception):
            raise content
        return _FakeResponse(content)


def test_resolve_chain_walks_default_models_skipping_uninitialised():
    manager: Any = _PairFakeManager({})
    assert resolve_chain(manager, None, None) == [
        ("deepseek", "flash"),
        ("openrouter", "fallback"),
    ]


def test_resolve_chain_explicit_pair_only():
    manager: Any = _PairFakeManager({})
    assert resolve_chain(manager, "openrouter", "x") == [("openrouter", "x")]


def test_chain_advances_to_second_pair_on_transport_failure():
    manager: Any = _PairFakeManager({"flash": [None], "fallback": ['{"1": [1]}']})
    chain = [("deepseek", "flash"), ("openrouter", "fallback")]
    result = judge_with_chain(manager, [_entry(1, ["a", "b"])], chain)
    assert "fallback" in manager.calls
    assert result.model == "fallback"
    assert result.verdicts == {1: {1}}


def test_chain_does_not_call_second_pair_when_first_succeeds():
    manager: Any = _PairFakeManager({"flash": ['{"1": []}'], "fallback": ['{"1": []}']})
    chain = [("deepseek", "flash"), ("openrouter", "fallback")]
    result = judge_with_chain(manager, [_entry(1, ["a", "b"])], chain)
    assert "fallback" not in manager.calls
    assert result.model == "flash"


def test_chain_unparseable_reply_does_not_advance():
    manager: Any = _PairFakeManager(
        {"flash": ["not json", "not json", '{"1": []}'], "fallback": ['{"1": [0]}']}
    )
    chain = [("deepseek", "flash"), ("openrouter", "fallback")]
    result = judge_with_chain(manager, [_entry(1, ["a", "b"])], chain)
    assert "fallback" not in manager.calls
    assert result.model == "flash"
    assert result.verdicts == {1: set()}


def test_chain_all_pairs_failing_returns_failed_verdicts():
    manager: Any = _PairFakeManager({"flash": [None], "fallback": [RuntimeError("x")]})
    chain = [("deepseek", "flash"), ("openrouter", "fallback")]
    result = judge_with_chain(manager, [_entry(1, ["a", "b"])], chain)
    assert result.verdicts == {1: None}
    assert not result.any_success
    assert result.request_failures >= 2


# --- 2.4 modes + TSV ---


def test_tsv_header_columns_and_order():
    assert TSV_HEADER == [
        "id",
        "field",
        "lemma",
        "english",
        "current_value",
        "proposed_value",
        "dropped",
        "max_ratio",
        "verdict",
        "judge_model",
        "decision",
    ]


def test_build_tsv_row_dropped_joined_and_decision_empty():
    row = build_tsv_row(
        entry_id=5,
        field="ru_meaning_raw",
        lemma="dhamma",
        english="law",
        current_value="закон; закон (в)",
        proposed_value="закон",
        parts=["закон", "закон (в)"],
        drop={1},
        max_ratio=1.0,
        verdict="trim",
        judge_model="deepseek-flash",
    )
    assert len(row) == len(TSV_HEADER)
    record = dict(zip(TSV_HEADER, row, strict=True))
    assert record["dropped"] == "закон (в)"
    assert record["decision"] == ""
    assert record["max_ratio"] == "1.0000"
    assert record["judge_model"] == "deepseek-flash"


def test_build_tsv_row_multiple_dropped_pipe_joined_in_index_order():
    row = build_tsv_row(
        entry_id=1,
        field="ru_meaning",
        lemma="x",
        english="y",
        current_value="a; b; c",
        proposed_value="a",
        parts=["a", "b", "c"],
        drop={2, 1},
        max_ratio=0.9,
        verdict="trim",
        judge_model="m",
    )
    assert dict(zip(TSV_HEADER, row, strict=True))["dropped"] == "b | c"


@pytest.mark.parametrize(
    "argv",
    [
        ["--apply-tsv", "x.tsv", "--ai"],
        ["--apply-tsv", "x.tsv", "--fix"],
        ["--apply-tsv", "x.tsv", "--limit", "5"],
        ["--ai", "--field", "ta_meaning"],
        ["--fix-ai"],
    ],
)
def test_invalid_flag_combinations_exit_with_argparse_error(
    monkeypatch: pytest.MonkeyPatch, argv: list[str]
):
    monkeypatch.setattr(sys, "argv", ["synonym_audit.py", *argv])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_help_lists_new_flags_and_not_fix_ai(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setattr(sys, "argv", ["synonym_audit.py", "--help"])
    with pytest.raises(SystemExit):
        main()
    out = capsys.readouterr().out
    assert "--apply-tsv" in out and "--allow-peak" in out
    assert "--fix-ai" not in out


# --- 2.5 apply-tsv ---


@pytest.fixture
def ru_session() -> Generator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _write_review(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TSV_HEADER, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in TSV_HEADER})


def _add(session: Session, rid: int, raw: str) -> None:
    session.add(Russian(id=rid, ru_meaning_raw=raw))
    session.commit()


def _raw(session: Session, rid: int) -> str:
    session.expire_all()
    record = session.get(Russian, rid)
    assert record is not None
    return record.ru_meaning_raw


def _approved(
    rid: int, current: str, proposed: str, decision: str = ""
) -> dict[str, str]:
    return {
        "id": str(rid),
        "field": "ru_meaning_raw",
        "current_value": current,
        "proposed_value": proposed,
        "decision": decision,
    }


def test_apply_writes_approved_row_and_records_undo(
    ru_session: Session, tmp_path: Path
):
    _add(ru_session, 1, "a; a (b)")
    tsv, applied = tmp_path / "r.tsv", tmp_path / "applied.tsv"
    _write_review(tsv, [_approved(1, "a; a (b)", "a")])
    totals = apply_review_tsv(ru_session, Russian, "ru_meaning_raw", tsv, applied)
    assert _raw(ru_session, 1) == "a"
    assert totals["applied"] == 1
    lines = applied.read_text(encoding="utf-8").splitlines()
    assert lines[-1].split("\t") == ["1", "ru_meaning_raw", "a; a (b)", "a"]


@pytest.mark.parametrize("decision", ["n", "N", "no", "NO", "skip", "Skip"])
def test_apply_rejected_decision_skips_row(
    ru_session: Session, tmp_path: Path, decision: str
):
    _add(ru_session, 1, "a; b")
    tsv = tmp_path / "r.tsv"
    _write_review(tsv, [_approved(1, "a; b", "a", decision)])
    totals = apply_review_tsv(
        ru_session, Russian, "ru_meaning_raw", tsv, tmp_path / "a.tsv"
    )
    assert _raw(ru_session, 1) == "a; b"
    assert totals["rejected"] == 1 and totals["applied"] == 0


def test_apply_stale_row_skipped(ru_session: Session, tmp_path: Path):
    _add(ru_session, 1, "changed since review")
    tsv = tmp_path / "r.tsv"
    _write_review(tsv, [_approved(1, "a; b", "a")])
    totals = apply_review_tsv(
        ru_session, Russian, "ru_meaning_raw", tsv, tmp_path / "a.tsv"
    )
    assert _raw(ru_session, 1) == "changed since review"
    assert totals["stale"] == 1


def test_apply_unchanged_rows_skipped(ru_session: Session, tmp_path: Path):
    _add(ru_session, 1, "a; b")
    _add(ru_session, 2, "c; d")
    tsv = tmp_path / "r.tsv"
    _write_review(tsv, [_approved(1, "a; b", ""), _approved(2, "c; d", "c; d")])
    totals = apply_review_tsv(
        ru_session, Russian, "ru_meaning_raw", tsv, tmp_path / "a.tsv"
    )
    assert totals["unchanged"] == 2 and totals["applied"] == 0


def test_apply_wrong_field_aborts_before_any_write(ru_session: Session, tmp_path: Path):
    _add(ru_session, 1, "a; b")
    _add(ru_session, 2, "c; d")
    tsv = tmp_path / "r.tsv"
    bad = _approved(2, "c; d", "c")
    bad["field"] = "ru_meaning"
    _write_review(tsv, [_approved(1, "a; b", "a"), bad])
    with pytest.raises(TsvFieldMismatchError):
        apply_review_tsv(ru_session, Russian, "ru_meaning_raw", tsv, tmp_path / "a.tsv")
    assert _raw(ru_session, 1) == "a; b"
    assert _raw(ru_session, 2) == "c; d"


def test_apply_hand_edited_proposed_value_written_as_edited(
    ru_session: Session, tmp_path: Path
):
    _add(ru_session, 1, "a; b; c")
    tsv = tmp_path / "r.tsv"
    _write_review(tsv, [_approved(1, "a; b; c", "a; c (edited)")])
    apply_review_tsv(ru_session, Russian, "ru_meaning_raw", tsv, tmp_path / "a.tsv")
    assert _raw(ru_session, 1) == "a; c (edited)"


def test_apply_mixed_totals_and_applied_rows_match_writes(
    ru_session: Session, tmp_path: Path
):
    _add(ru_session, 1, "a; b")
    _add(ru_session, 2, "c; d")
    _add(ru_session, 3, "e; f")
    tsv, applied = tmp_path / "r.tsv", tmp_path / "applied.tsv"
    _write_review(
        tsv,
        [
            _approved(1, "a; b", "a"),
            _approved(2, "c; d", "c", "n"),
            _approved(3, "stale value", "e"),
        ],
    )
    totals = apply_review_tsv(ru_session, Russian, "ru_meaning_raw", tsv, applied)
    assert totals == {"applied": 1, "rejected": 1, "unchanged": 0, "stale": 1}
    data_lines = applied.read_text(encoding="utf-8").splitlines()[1:]
    assert [line.split("\t")[0] for line in data_lines] == ["1"]


# --- 2.6 audit run record ---


def test_audit_log_appends_one_line_and_last_audit_preserves_state(tmp_path: Path):
    log = tmp_path / "log.md"
    log.write_text("# Translate pipeline log\n\n---\n- old line\n", encoding="utf-8")
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"last_op": "check", "totals": {"checked": 3}}))

    append_audit_log(
        log,
        start="2026-11-16T10:00:00+00:00",
        end="2026-11-16T10:01:00+00:00",
        mode="ai",
        field="ru_meaning_raw",
        flagged=12,
        changed=0,
        exit_code=0,
    )
    record_last_audit(state, field="ru_meaning_raw", mode="ai", flagged=12, ts="T")

    lines = log.read_text(encoding="utf-8").splitlines()
    assert lines[-1].startswith(
        "- 2026-11-16T10:00:00+00:00 → 2026-11-16T10:01:00+00:00 |"
    )
    assert "op=4 mode=ai" in lines[-1] and "exit=0" in lines[-1]
    assert len(lines) == 5  # header(3) + old line + one new line
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["last_audit"] == {
        "field": "ru_meaning_raw",
        "mode": "ai",
        "flagged": 12,
        "ts": "T",
    }
    assert saved["last_op"] == "check" and saved["totals"] == {"checked": 3}
