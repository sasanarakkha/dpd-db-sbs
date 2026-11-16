"""Benchmark helpers: deterministic samples, scoring, cost, and read-only DB access."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword, Russian
from kamma.translate.scripts import model_benchmark as mb
from kamma.translate.scripts.synonym_audit import JudgeEntry
from tools.ai_batch_processor import BatchProcessor


@pytest.fixture
def session() -> Generator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    for i in range(1, 41):
        db.add(DpdHeadword(id=i, lemma_1=f"w{i}", meaning_1="state"))
        raw = "идет; идет (в); другой" if i % 4 == 0 else "один; два"
        db.add(Russian(id=i, ru_meaning=f"знач{i}", ru_meaning_raw=raw))
    db.commit()
    yield db
    db.close()


def test_parse_candidate_splits_at_first_colon():
    assert mb.parse_candidate("openrouter:qwen/qwen3:free") == (
        "openrouter",
        "qwen/qwen3:free",
    )


def test_parse_candidate_rejects_missing_part():
    with pytest.raises(ValueError):
        mb.parse_candidate("deepseek")


def test_parse_price():
    assert mb.parse_price("deepseek-flash=0.14,0.28") == (
        "deepseek-flash",
        (0.14, 0.28),
    )
    with pytest.raises(ValueError):
        mb.parse_price("deepseek-flash=0.14")


def test_estimate_cost_per_100_uses_chars_over_four():
    stats = mb.ModelStats([mb.Call("x", 1.0, 4000, 400)])
    # 1000 in-tokens * $1/1M + 100 out-tokens * $2/1M = 0.0012 per request -> 0.12 per 100
    assert mb.estimate_cost_per_100(stats, (1.0, 2.0)) == pytest.approx(0.12)
    assert mb.estimate_cost_per_100(stats, None) is None


def test_spread_pick_is_deterministic_and_even():
    items = list(range(100))
    assert mb.spread_pick(items, 4) == [0, 25, 50, 75]
    assert mb.spread_pick(items, 4) == mb.spread_pick(items, 4)
    assert mb.spread_pick([1, 2], 5) == [1, 2]


def test_build_check_pairs_true_and_shuffled_differ():
    pairs = [(i, f"en{i}", f"ru{i}") for i in range(10)]
    out = mb.build_check_pairs(pairs, 10)
    assert len(out) == 20
    assert sum(1 for *_, true in out if true) == 10
    truth = {i: ru for i, _, ru in pairs}
    for pair_id, _, russian, is_true in out:
        assert (russian == truth[pair_id]) is is_true


def test_score_check_counts_none_as_wrong():
    verdicts = ["MATCH", "MISMATCH", None, "MATCH"]
    truth = [True, False, True, False]
    assert mb.score_check(verdicts, truth) == pytest.approx(0.5)


def test_partial_match_counts_as_true():
    assert mb.score_check(["PARTIAL_MATCH"], [True]) == 1.0


def _entry() -> JudgeEntry:
    return JudgeEntry(1, "ru_meaning_raw", "w", "state", ["a", "b", "досл. c"])


def test_count_guard_hits_counts_literal_gloss_drops():
    assert mb.count_guard_hits('{"1": [2, 1]}', [_entry()]) == 1
    assert mb.count_guard_hits('{"1": [1]}', [_entry()]) == 0
    assert mb.count_guard_hits("not json", [_entry()]) == 0
    assert mb.count_guard_hits(None, [_entry()]) == 0


def test_judge_agreement_failed_never_agrees():
    ref = {1: {0}, 2: set(), 3: {1}}
    got = {1: {0}, 2: set(), 3: None}
    assert mb.judge_agreement(got, ref) == pytest.approx(2 / 3)


def test_judge_sample_first_flagged_by_id(session: Session):
    entries = mb.judge_sample(session, n=3)
    assert [e.id for e in entries] == [4, 8, 12]
    assert entries[0].parts == ["идет", "идет (в)", "другой"]


def test_generate_sample_pairs_human_value(session: Session):
    sample = mb.generate_sample(session, n=4)
    assert len(sample) == 4
    assert sample == mb.generate_sample(session, n=4)
    assert all(human == f"знач{hw.id}" for hw, human in sample)


def test_check_sample_has_true_and_shuffled(session: Session):
    sample = mb.check_sample(session, n_true=5)
    assert sum(1 for *_, true in sample if true) == 5
    assert len(sample) == 10


def test_samples_never_commit(session: Session, monkeypatch: pytest.MonkeyPatch):
    def boom() -> None:
        raise AssertionError("benchmark must not commit")

    monkeypatch.setattr(session, "commit", boom)
    mb.judge_sample(session)
    mb.generate_sample(session)
    mb.check_sample(session)
    assert not session.dirty and not session.new and not session.deleted


def test_timed_request_exception_is_failed_call():
    class Boom:
        def request(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("down")

    call = mb.timed_request(Boom(), "p", None, ("a", "b"))  # type: ignore[arg-type]
    assert call.content is None and call.chars_in == 1


class FakeManager:
    """Counts requests; replies per a script of contents (None = failed)."""

    def __init__(self, replies: list[str | None]) -> None:
        self.replies = replies
        self.calls = 0

    def request(self, *args: object, **kwargs: object) -> object:
        reply = self.replies[min(self.calls, len(self.replies) - 1)]
        self.calls += 1
        return type("R", (), {"content": reply, "status_message": ""})()


def _runner(tmp_path, replies: list[str | None], max_failures: int = 3):
    manager = FakeManager(replies)
    runner = mb.Runner(manager, mb.CallStore(tmp_path / "calls.jsonl"), max_failures)  # type: ignore[arg-type]
    return manager, runner


def test_call_is_saved_to_disk_immediately(tmp_path):
    _, runner = _runner(tmp_path, ["ok"])
    runner.call("judge", ("a", "b"), "k1", "prompt", None, "1/1")
    lines = (tmp_path / "calls.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and '"key": "k1"' in lines[0]


def test_rerun_resumes_successes_without_requesting(tmp_path):
    manager, runner = _runner(tmp_path, ["ok"])
    runner.call("judge", ("a", "b"), "k1", "prompt", None, "1/1")
    manager2, runner2 = _runner(tmp_path, ["other"])
    call = runner2.call("judge", ("a", "b"), "k1", "prompt", None, "1/1")
    assert call.content == "ok" and manager2.calls == 0 and manager.calls == 1


def test_failed_call_is_logged_but_retried_on_rerun(tmp_path):
    _, runner = _runner(tmp_path, [None])
    runner.call("judge", ("a", "b"), "k1", "prompt", None, "1/1")
    assert len((tmp_path / "calls.jsonl").read_text().splitlines()) == 1
    manager2, runner2 = _runner(tmp_path, ["ok"])
    assert (
        runner2.call("judge", ("a", "b"), "k1", "prompt", None, "1/1").content == "ok"
    )
    assert manager2.calls == 1


def test_breaker_skips_after_consecutive_failures(tmp_path):
    manager, runner = _runner(tmp_path, [None], max_failures=2)
    for n in range(5):
        runner.call("gen", ("a", "b"), f"k{n}", "p", None, f"{n}/5")
    assert manager.calls == 2
    assert len((tmp_path / "calls.jsonl").read_text().splitlines()) == 2


def test_success_resets_breaker_and_other_model_unaffected(tmp_path):
    manager, runner = _runner(tmp_path, [None, "ok", None, None], max_failures=2)
    runner.call("gen", ("a", "b"), "k0", "p", None, "1")
    runner.call("gen", ("a", "b"), "k1", "p", None, "2")
    runner.call("gen", ("a", "b"), "k2", "p", None, "3")
    runner.call("gen", ("a", "b"), "k3", "p", None, "4")
    assert manager.calls == 4  # streak reset by the success, never reached 2 in a row
    runner.call("gen", ("a", "b"), "k4", "p", None, "5")
    assert manager.calls == 4  # now tripped
    runner.call("gen", ("c", "d"), "k0", "p", None, "1")
    assert manager.calls == 5  # a different model is not affected


def test_check_parser_accepts_fenced_json(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(BatchProcessor, "__init__", lambda self, *a, **k: None)
    processor = BatchProcessor()
    processor.strict_parse = True
    _, parse = mb.check_prompt_and_parser(processor, 7, "state", "состояние")
    reply = (
        '{"comparisons": [{"id": 7, "lemma": "", "match_status": "MATCH", '
        '"confidence": 1.0, "reasoning": "ok"}]}'
    )
    assert parse(reply) == "MATCH"
    assert parse("```json\n" + reply + "\n```") == "MATCH"
