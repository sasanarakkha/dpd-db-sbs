"""Tests for the ru_cognate AI batch script: prompts, response validation, ledger updates, CLI loop."""

import json
from pathlib import Path

import pytest

from scripts.ru_cognate import ru_cognate_ai as ai
from scripts.ru_cognate.ru_cognate_ledger import COLUMNS, read_ledger, write_ledger
from tools.ai_manager import AIResponse

Row = dict[str, str]


def make_row(key: str, status: str = "pending", **extra: str) -> Row:
    row = {c: "" for c in COLUMNS}
    row.update(
        unit_type="root" if key.startswith("√") else "family",
        unit_key=key,
        pali_meaning=f"meaning of {key}",
        sanskrit=f"skt-{key}",
        status=status,
    )
    row.update(extra)
    return row


def wrap(items: list[dict[str, object]]) -> str:
    return json.dumps({"comparisons": items}, ensure_ascii=False)


def propose_item(key: str, **extra: object) -> dict[str, object]:
    item: dict[str, object] = {
        "unit_key": key,
        "pie_root": "*dʰwer-",
        "ru_candidates": ["дверь"],
        "source": "Wiktionary",
        "confidence": 8,
        "verdict": "cognate",
    }
    item.update(extra)
    return item


def label(word: str, **extra: str) -> dict[str, object]:
    """One per-word verify label; defaults are the three model keep labels (sound is code-side)."""
    item: dict[str, object] = {
        "word": word,
        "note": f"{word} from PIE *dʰwer-",
        "etymon": "same",
        "form": "base",
        "meaning": "close",
    }
    item.update(extra)
    return item


def verify_item(key: str, *words: dict[str, object]) -> dict[str, object]:
    return {"unit_key": key, "words": list(words) if words else [label("дверь")]}


# ---------- prompts ----------


def test_verify_prompt_has_claim_only() -> None:
    row = make_row(
        "dvāra",
        "proposed",
        pie_root="dʰwer",
        ru_candidates="дверь",
        source="Wiktionary: sa dvāra; ru дверь",
        confidence="9",
        method="agent",
        en_cognate="door",
    )
    members = {("family", "dvāra"): ["dvāra (nt) door"]}
    prompt = ai.build_verify_prompt([row], members)
    assert "dvāra (nt) door" in prompt
    assert "dvāra" in prompt
    assert "dʰwer" in prompt
    assert "дверь" in prompt
    assert "Wiktionary: sa dvāra" in prompt
    assert "confidence" not in prompt.lower().replace('"verifier_verdict"', "")
    assert "reasoning" not in prompt.lower()


def test_propose_prompt_has_members_and_rules() -> None:
    row = make_row("dvāra", en_cognate="door")
    members = {("family", "dvāra"): ["dvāra (nt) door", "dvārika (adj) doorkeeper"]}
    prompt = ai.build_propose_prompt([row], members)
    assert "dvāra (nt) door" in prompt
    assert "dvārika (adj) doorkeeper" in prompt
    assert "door" in prompt
    assert "none" in prompt.lower()
    assert "loan" in prompt.lower()
    assert "skt-dvāra" in prompt


# ---------- word / response validation ----------


def test_parse_words_valid_and_normalised() -> None:
    assert ai.parse_words(["Дверь", "буди́ть", "ёж"]) == ["дверь", "будить", "ёж"]
    assert ai.parse_words([]) == []
    assert ai.parse_words(["дверь", "дверь"]) == ["дверь"]


@pytest.mark.parametrize(
    "bad",
    [["door"], ["дверь", "брат", "мать", "три"], "дверь", [""], [3]],
)
def test_parse_words_invalid(bad: object) -> None:
    assert ai.parse_words(bad) is None


def test_parse_response_unparseable_is_none() -> None:
    assert ai.parse_response("sorry, no json here") is None


def test_parse_response_reads_items() -> None:
    items = ai.parse_response("```json\n" + wrap([propose_item("a")]) + "\n```")
    assert items is not None
    assert items[0]["unit_key"] == "a"


# ---------- propose updates ----------


def test_apply_propose_cognate_sets_proposed_agent() -> None:
    row = make_row("a")
    changed, problems = ai.apply_propose([row], [propose_item("a")])
    assert (changed, problems) == (1, [])
    assert row["status"] == "proposed"
    assert row["method"] == "agent"
    assert row["ru_candidates"] == "дверь"
    assert row["pie_root"] == "*dʰwer-"
    assert row["confidence"] == "8"


def test_apply_propose_unsure_is_proposed() -> None:
    row = make_row("a")
    ai.apply_propose([row], [propose_item("a", verdict="unsure")])
    assert row["status"] == "proposed"


def test_apply_propose_unsure_without_words_is_none() -> None:
    row = make_row("a")
    item = propose_item("a", verdict="unsure", ru_candidates=[])
    changed, problems = ai.apply_propose([row], [item])
    assert (changed, problems) == (1, [])
    assert row["status"] == "none"
    assert row["method"] == "agent"


def test_apply_propose_cognate_without_words_unchanged() -> None:
    row = make_row("a")
    before = dict(row)
    changed, problems = ai.apply_propose([row], [propose_item("a", ru_candidates=[])])
    assert changed == 0
    assert row == before
    assert problems


def test_verify_rules_ask_for_a_label_per_word() -> None:
    rules = ai.VERIFY_RULES
    assert "EVERY word" in rules
    for name in ("word", "note", "etymon", "form", "meaning"):
        assert f'"{name}"' in rules
    assert '"sound"' not in rules
    assert "same|different|loan|uncertain" in rules
    assert "base|derivative" in rules
    assert "close|weak|none" not in rules
    assert "close|drifted|far" in rules


def test_verify_rules_judge_meaning_against_member_headwords() -> None:
    rules = ai.VERIFY_RULES
    assert "member headwords" in rules
    assert "not the root meaning" in rules
    assert "√dā 1" in rules


def test_verify_schema_puts_note_first_and_has_no_verdict() -> None:
    rules = ai.VERIFY_RULES
    order = [rules.index(f'"{n}": "') for n in ("word", "note", "etymon", "form")]
    assert order == sorted(order)
    assert (
        rules.index('"note": "')
        < rules.index('"etymon": "')
        < rules.index('"meaning": "')
    )
    assert "verifier_verdict" not in rules
    assert "ru_final" not in rules


def test_verify_rules_have_anchors_but_not_the_generalisation_tests() -> None:
    rules = ai.VERIFY_RULES
    assert "вонь" in rules
    assert "есть has sound" not in rules
    assert "audible root consonant" not in rules
    assert "one short sentence" in rules
    for held_out in ("едкий", "расти", "ячмень"):
        assert held_out not in rules


def test_verify_rules_treat_claimed_pie_as_hint() -> None:
    assert "the claimed PIE root is only a hint" in ai.VERIFY_RULES


def test_verify_run_sends_member_headwords(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    path = tmp_path / "ledger.tsv"
    write_ledger(path, [make_row("√agg", "proposed", ru_candidates="огонь")])
    fake = FakeAsk([wrap([verify_item("√agg", label("огонь"))])])
    members = {("root", "√agg"): ["aggi (masc) fire"]}
    assert ai.run_batches("verify", path, fake, members, 25, 0, False) == 0
    assert "aggi (masc) fire" in fake.calls[0][0]


def test_apply_propose_none_sets_status_none() -> None:
    row = make_row("a")
    item = propose_item("a", verdict="none", ru_candidates=[], pie_root="")
    ai.apply_propose([row], [item])
    assert row["status"] == "none"
    assert row["method"] == "agent"
    assert row["ru_candidates"] == ""


@pytest.mark.parametrize(
    "bad",
    [
        propose_item("zzz"),
        propose_item("a", ru_candidates=["дверь", "брат", "мать", "три"]),
        propose_item("a", ru_candidates=["door"]),
        propose_item("a", verdict="maybe"),
        propose_item("a", confidence=11),
        propose_item("a", ru_candidates=[]),
    ],
)
def test_apply_propose_invalid_leaves_row_unchanged(bad: dict[str, object]) -> None:
    row = make_row("a")
    before = dict(row)
    changed, problems = ai.apply_propose([row], [bad])
    assert changed == 0
    assert row == before
    assert problems


# ---------- verify updates ----------


def verify_row(
    candidates: str = "дверь", sanskrit: str = "dvāra", key: str = "a"
) -> Row:
    return make_row(key, "proposed", ru_candidates=candidates, sanskrit=sanskrit)


def test_all_four_keep_labels_keep_the_word() -> None:
    row = verify_row()
    changed, problems = ai.apply_verify([row], [verify_item("a")])
    assert (changed, problems) == (1, [])
    assert row["status"] == "verified"
    assert row["verifier_verdict"] == "confirmed"
    assert row["ru_final"] == "дверь"
    assert row["ru_flagged"] == ""


def test_code_weak_sound_is_flagged_not_kept() -> None:
    row = verify_row("ворота")
    ai.apply_verify([row], [verify_item("a", label("ворота"))])
    assert (row["ru_final"], row["ru_flagged"]) == ("", "ворота")
    assert (row["status"], row["verifier_verdict"]) == ("disputed", "rejected")


def test_drifted_meaning_is_flagged_not_kept() -> None:
    row = verify_row()
    ai.apply_verify([row], [verify_item("a", label("дверь", meaning="drifted"))])
    assert (row["ru_final"], row["ru_flagged"]) == ("", "дверь")


def test_weak_sound_with_drifted_meaning_is_dropped() -> None:
    row = verify_row("ворота")
    ai.apply_verify([row], [verify_item("a", label("ворота", meaning="drifted"))])
    assert (row["ru_final"], row["ru_flagged"]) == ("", "")
    assert row["status"] == "disputed"


def test_derivative_is_dropped() -> None:
    row = verify_row()
    ai.apply_verify([row], [verify_item("a", label("дверь", form="derivative"))])
    assert (row["ru_final"], row["ru_flagged"]) == ("", "")
    assert row["status"] == "disputed"


@pytest.mark.parametrize("etymon", ["different", "loan", "uncertain"])
def test_non_same_etymon_is_dropped(etymon: str) -> None:
    row = verify_row()
    ai.apply_verify([row], [verify_item("a", label("дверь", etymon=etymon))])
    assert (row["ru_final"], row["ru_flagged"]) == ("", "")


def test_code_sound_none_with_close_meaning_is_dropped() -> None:
    row = verify_row("мама", "dvāra", key="dvāra")
    ai.apply_verify([row], [verify_item("dvāra", label("мама"))])
    assert (row["ru_final"], row["ru_flagged"]) == ("", "")


def test_far_meaning_is_dropped_even_with_close_sound() -> None:
    row = verify_row()
    ai.apply_verify([row], [verify_item("a", label("дверь", meaning="far"))])
    assert (row["ru_final"], row["ru_flagged"]) == ("", "")


def test_fourth_kept_word_goes_to_flagged() -> None:
    row = verify_row("дверь, двор, два, дверца")
    item = verify_item(
        "a", label("дверь"), label("двор"), label("два"), label("дверца")
    )
    ai.apply_verify([row], [item])
    assert row["ru_final"] == "дверь, двор, два"
    assert row["ru_flagged"] == "дверца"
    assert row["status"] == "verified"


def test_only_flagged_words_make_the_row_disputed_with_flagged_filled() -> None:
    row = verify_row("ворота, дверь")
    item = verify_item("a", label("ворота"), label("дверь", meaning="drifted"))
    ai.apply_verify([row], [item])
    assert row["ru_final"] == ""
    assert row["ru_flagged"] == "ворота, дверь"
    assert (row["status"], row["verifier_verdict"]) == ("disputed", "rejected")


def test_kept_and_flagged_follow_reply_order() -> None:
    row = verify_row("ворота, дверь, два")
    item = verify_item("a", label("ворота"), label("два"), label("дверь"))
    ai.apply_verify([row], [item])
    assert row["ru_final"] == "два, дверь"
    assert row["ru_flagged"] == "ворота"


def test_accented_reply_word_matches_plain_candidate() -> None:
    row = verify_row("еда", "ad")
    ai.apply_verify([row], [verify_item("a", label("еда́"))])
    assert row["ru_final"] == "еда"


def test_verifier_note_lists_every_word_with_labels() -> None:
    row = verify_row("еда, есть", "ad", key="√ad")
    item = verify_item(
        "√ad",
        label("еда", note="from *h₁ed-"),
        label("есть", note="same root"),
    )
    ai.apply_verify([row], [item])
    assert row["verifier_note"] == (
        "еда [same/base/sound close (code)/meaning close]: from *h₁ed-; "
        "есть [same/base/sound none (code)/meaning close]: same root"
    )


@pytest.mark.parametrize(
    "bad",
    [
        verify_item("zzz"),
        verify_item("a", label("дверь"), label("дверца")),
        verify_item("a", label("брат")),
        verify_item("a", label("дверь"), label("дверь")),
        verify_item("a", label("дверь", etymon="maybe")),
        verify_item("a", label("дверь", form="root")),
        verify_item("a", label("дверь", meaning="same")),
        verify_item("a", label("дверь", note="")),
        {"unit_key": "a", "words": "дверь"},
    ],
)
def test_apply_verify_invalid_leaves_row_unchanged(bad: dict[str, object]) -> None:
    row = verify_row()
    before = dict(row)
    changed, problems = ai.apply_verify([row], [bad])
    assert changed == 0
    assert row == before
    assert problems


def test_candidate_missing_from_reply_leaves_row_unchanged() -> None:
    row = verify_row("дверь, дверца")
    before = dict(row)
    changed, problems = ai.apply_verify([row], [verify_item("a", label("дверь"))])
    assert changed == 0
    assert row == before
    assert any("дверца" in p for p in problems)


def test_extra_word_not_in_candidates_is_a_problem() -> None:
    row = verify_row("дверь")
    changed, problems = ai.apply_verify(
        [row], [verify_item("a", label("дверь"), label("брат"))]
    )
    assert changed == 0
    assert any("брат" in p for p in problems)


# ---------- CLI loop ----------


class FakeAsk:
    """Records calls and answers each with the next canned reply."""

    def __init__(self, replies: list[str | None]) -> None:
        self.replies = replies
        self.calls: list[tuple[str, bool]] = []

    def __call__(self, prompt: str, system: str, grounding: bool) -> str | None:
        self.calls.append((prompt, grounding))
        return self.replies[len(self.calls) - 1]


@pytest.fixture
def ledger(tmp_path: Path) -> Path:
    path = tmp_path / "ledger.tsv"
    write_ledger(path, [make_row("a"), make_row("b"), make_row("c")])
    return path


def statuses(path: Path) -> list[str]:
    return [r["status"] for r in read_ledger(path)]


def no_peak(allow_peak: bool) -> None:
    return None


def test_propose_runs_batches_and_saves(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    fake = FakeAsk(
        [
            wrap([propose_item("a"), propose_item("b", verdict="none")]),
            wrap([propose_item("c")]),
        ]
    )
    code = ai.run_batches("propose", ledger, fake, {}, 2, 0, False)
    assert code == 0
    assert statuses(ledger) == ["proposed", "none", "proposed"]
    assert [grounding for _, grounding in fake.calls] == [False, False]


def test_verify_uses_grounded_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    path = tmp_path / "ledger.tsv"
    write_ledger(
        path,
        [
            make_row("a", "proposed", ru_candidates="дверь", sanskrit="dvāra"),
            make_row("b"),
        ],
    )
    fake = FakeAsk([wrap([verify_item("a")])])
    assert ai.run_batches("verify", path, fake, {}, 25, 0, False) == 0
    assert statuses(path) == ["verified", "pending"]
    assert [grounding for _, grounding in fake.calls] == [True]


def test_peak_before_batch_two_stops_cleanly(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[bool] = []

    def peak_second(allow_peak: bool) -> None:
        calls.append(allow_peak)
        if len(calls) == 2:
            raise SystemExit(1)

    monkeypatch.setattr(ai, "require_offpeak", peak_second)
    fake = FakeAsk([wrap([propose_item("a"), propose_item("b")])])
    code = ai.run_batches("propose", ledger, fake, {}, 2, 0, False)
    assert code == 0
    assert len(fake.calls) == 1
    assert statuses(ledger) == ["proposed", "proposed", "pending"]


def test_first_batch_blocked_exits_one(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def blocked(allow_peak: bool) -> None:
        raise SystemExit(1)

    monkeypatch.setattr(ai, "require_offpeak", blocked)
    fake = FakeAsk([])
    with pytest.raises(SystemExit) as exc:
        ai.run_batches("propose", ledger, fake, {}, 2, 0, False)
    assert exc.value.code == 1
    assert fake.calls == []
    assert statuses(ledger) == ["pending"] * 3


def test_no_content_stops_with_exit_two_and_keeps_good_batches(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    fake = FakeAsk([wrap([propose_item("a"), propose_item("b")]), None])
    code = ai.run_batches("propose", ledger, fake, {}, 2, 0, False)
    assert code == 2
    assert statuses(ledger) == ["proposed", "proposed", "pending"]


def test_unparseable_batch_leaves_rows_and_moves_on(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    fake = FakeAsk(["garbage", wrap([propose_item("c")])])
    code = ai.run_batches("propose", ledger, fake, {}, 2, 0, False)
    assert code == 0
    assert statuses(ledger) == ["pending", "pending", "proposed"]
    assert len(fake.calls) == 2


def test_max_batches_caps_the_run(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    fake = FakeAsk([wrap([propose_item("a")])])
    assert ai.run_batches("propose", ledger, fake, {}, 1, 1, False) == 0
    assert len(fake.calls) == 1
    assert statuses(ledger) == ["proposed", "pending", "pending"]


def test_allow_peak_is_passed_to_guard(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[bool] = []

    def record(allow_peak: bool) -> None:
        seen.append(allow_peak)

    monkeypatch.setattr(ai, "require_offpeak", record)
    fake = FakeAsk([wrap([propose_item("a")])])
    ai.run_batches("propose", ledger, fake, {}, 1, 1, True)
    assert seen == [True]


def test_prompts_put_unit_key_alone_on_its_line() -> None:
    """The model copies the whole line after `unit_key:`, so nothing else may follow the key."""
    row = make_row("√akkh", "proposed", pie_root="x", ru_candidates="око")
    for prompt in (
        ai.build_verify_prompt([row], {}),
        ai.build_propose_prompt([row], {}),
    ):
        assert "- unit_key: √akkh\n" in prompt
        assert "(root)" not in prompt


class FakeManager:
    """Stand-in for AIManager that records the kwargs of every request."""

    def __init__(
        self, grounded: list[tuple[str, str, int, float]] | None = None
    ) -> None:
        self.GROUNDED_MODELS: list[tuple[str, str, int, float]] = (
            [("deepseek", "deepseek-v4-pro", 1, 150.0)]
            if grounded is None
            else grounded
        )
        self.calls: list[dict[str, object]] = []

    def request(self, **kwargs: object) -> AIResponse:
        self.calls.append(kwargs)
        return AIResponse(content="{}", status_message="Success")


def test_verify_call_enables_thinking_and_max_tokens() -> None:
    manager = FakeManager()
    ask = ai.make_ask(manager)  # pyright: ignore[reportArgumentType]
    assert ask("p", "s", True) == "{}"
    call = manager.calls[0]
    assert call["grounding"] is True
    assert call["thinking"] == {"type": "enabled"}
    assert call["max_tokens"] == 32768


def test_propose_call_sends_no_thinking_or_max_tokens() -> None:
    manager = FakeManager()
    ask = ai.make_ask(manager)  # pyright: ignore[reportArgumentType]
    ask("p", "s", False)
    call = manager.calls[0]
    assert call["grounding"] is False
    assert "thinking" not in call
    assert "max_tokens" not in call


def test_verify_refuses_non_deepseek_grounded_chain() -> None:
    manager = FakeManager([("deepseek", "m", 1, 1.0), ("gemini", "g", 1, 1.0)])
    ask = ai.make_ask(manager)  # pyright: ignore[reportArgumentType]
    with pytest.raises(SystemExit):
        ask("p", "s", True)
    assert manager.calls == []
    assert ask("p", "s", False) == "{}"
    assert len(manager.calls) == 1


def test_verify_refuses_empty_grounded_chain() -> None:
    manager = FakeManager([])
    ask = ai.make_ask(manager)  # pyright: ignore[reportArgumentType]
    with pytest.raises(SystemExit):
        ask("p", "s", True)
    assert manager.calls == []


def test_verify_options_constant_not_mutated() -> None:
    manager = FakeManager()
    ask = ai.make_ask(manager)  # pyright: ignore[reportArgumentType]
    ask("p", "s", True)
    cast_thinking = manager.calls[0]["thinking"]
    assert isinstance(cast_thinking, dict)
    cast_thinking["type"] = "disabled"
    ask("p", "s", True)
    assert manager.calls[1]["thinking"] == {"type": "enabled"}
    assert ai.VERIFY_REQUEST_OPTIONS == {
        "thinking": {"type": "enabled"},
        "max_tokens": 32768,
    }


# ---------- thinking off and two-pass verify ----------


def test_no_thinking_verify_call_disables_thinking_without_max_tokens() -> None:
    manager = FakeManager()
    ask = ai.make_ask(manager, thinking=False)  # pyright: ignore[reportArgumentType]
    assert ask("p", "s", True) == "{}"
    call = manager.calls[0]
    assert call["grounding"] is True
    assert call["thinking"] == {"type": "disabled"}
    assert "max_tokens" not in call


def test_no_thinking_verify_still_refuses_non_deepseek_chain() -> None:
    manager = FakeManager([("deepseek", "m", 1, 1.0), ("gemini", "g", 1, 1.0)])
    ask = ai.make_ask(manager, thinking=False)  # pyright: ignore[reportArgumentType]
    with pytest.raises(SystemExit):
        ask("p", "s", True)
    assert manager.calls == []


def pair_row(candidates: str = "дверь", sanskrit: str = "dvāra") -> Row:
    return make_row("a", "proposed", ru_candidates=candidates, sanskrit=sanskrit)


def pair(
    row: Row, labels_a: list[dict[str, object]], labels_b: list[dict[str, object]]
) -> tuple[int, list[str]]:
    return ai.apply_verify_pair(
        [row], [verify_item("a", *labels_a)], [verify_item("a", *labels_b)]
    )


DROP = {"etymon": "different"}
FLAG = {"meaning": "drifted"}


def test_pair_keep_keep_is_kept() -> None:
    row = pair_row()
    assert pair(row, [label("дверь")], [label("дверь")]) == (1, [])
    assert row["ru_final"] == "дверь"
    assert row["status"] == "verified"


def test_pair_keep_flag_is_flagged() -> None:
    row = pair_row()
    pair(row, [label("дверь")], [label("дверь", **FLAG)])
    assert (row["ru_final"], row["ru_flagged"]) == ("", "дверь")
    assert row["status"] == "disputed"
    assert row["verifier_note"].endswith(" || pass 2 differs: дверь keep/flag")


def test_pair_keep_drop_is_dropped() -> None:
    row = pair_row()
    pair(row, [label("дверь")], [label("дверь", **DROP)])
    assert (row["ru_final"], row["ru_flagged"]) == ("", "")


def test_pair_drop_keep_is_dropped() -> None:
    row = pair_row()
    pair(row, [label("дверь", **DROP)], [label("дверь")])
    assert (row["ru_final"], row["ru_flagged"]) == ("", "")


def test_pair_flag_drop_is_dropped() -> None:
    row = pair_row()
    pair(row, [label("дверь", **FLAG)], [label("дверь", **DROP)])
    assert (row["ru_final"], row["ru_flagged"]) == ("", "")


def test_pair_drop_drop_is_dropped_and_disputed_without_diff_note() -> None:
    row = pair_row()
    pair(row, [label("дверь", **DROP)], [label("дверь", **DROP)])
    assert (row["ru_final"], row["ru_flagged"]) == ("", "")
    assert row["status"] == "disputed"
    assert "pass 2 differs" not in row["verifier_note"]


def test_pair_flag_flag_is_flagged() -> None:
    row = pair_row()
    pair(row, [label("дверь", **FLAG)], [label("дверь", **FLAG)])
    assert row["ru_flagged"] == "дверь"
    assert row["ru_final"] == ""


def test_pair_second_pass_missing_word_leaves_row_unchanged() -> None:
    row = pair_row("дверь, дверца")
    changed, problems = pair(row, [label("дверь"), label("дверца")], [label("дверь")])
    assert changed == 0
    assert row["status"] == "proposed"
    assert len(problems) == 1
    assert problems[0].startswith("pass 2: ")


def test_pair_disagreement_is_noted() -> None:
    row = pair_row()
    pair(row, [label("дверь")], [label("дверь", **DROP)])
    assert row["verifier_note"].endswith(" || pass 2 differs: дверь keep/drop")


def test_pair_fourth_kept_word_overflows_to_flagged() -> None:
    words = ["дверь", "двор", "два", "дверца"]
    row = pair_row(", ".join(words))
    both = [label(w) for w in words]
    pair(row, both, both)
    assert row["ru_final"] == "дверь, двор, два"
    assert row["ru_flagged"] == "дверца"


def test_run_batches_two_passes_asks_twice_and_combines_passes(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    rows = read_ledger(ledger)
    for r in rows:
        r.update(status="proposed", ru_candidates="дверь", sanskrit="dvāra")
    write_ledger(ledger, rows)
    first = wrap(
        [verify_item("a"), verify_item("b"), verify_item("c", label("дверь", **DROP))]
    )
    second = wrap(
        [
            verify_item("a"),
            verify_item("b", label("дверь", **DROP)),
            verify_item("c", label("дверь", **DROP)),
        ]
    )
    fake = FakeAsk([first, second])
    assert ai.run_batches("verify", ledger, fake, {}, 3, 0, False, passes=2) == 0
    assert len(fake.calls) == 2
    assert fake.calls[0] == fake.calls[1]
    out = {r["unit_key"]: r for r in read_ledger(ledger)}
    assert out["a"]["ru_final"] == "дверь"
    assert (out["b"]["ru_final"], out["b"]["ru_flagged"]) == ("", "")
    assert (out["c"]["ru_final"], out["c"]["ru_flagged"]) == ("", "")
    assert out["c"]["status"] == "disputed"


def test_run_batches_two_passes_unparseable_second_leaves_rows(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    rows = read_ledger(ledger)
    for r in rows:
        r.update(status="proposed", ru_candidates="дверь", sanskrit="dvāra")
    write_ledger(ledger, rows)
    fake = FakeAsk([wrap([verify_item(k) for k in "abc"]), "garbage"])
    assert ai.run_batches("verify", ledger, fake, {}, 3, 0, False, passes=2) == 0
    assert statuses(ledger) == ["proposed"] * 3


def test_run_batches_two_passes_second_none_exits_two(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    rows = read_ledger(ledger)
    for r in rows:
        r.update(status="proposed", ru_candidates="дверь", sanskrit="dvāra")
    write_ledger(ledger, rows)
    fake = FakeAsk([wrap([verify_item(k) for k in "abc"]), None])
    assert ai.run_batches("verify", ledger, fake, {}, 3, 0, False, passes=2) == 2
    assert statuses(ledger) == ["proposed"] * 3


@pytest.mark.parametrize("flag", ["--passes", "--no-thinking"])
def test_main_rejects_two_pass_and_no_thinking_for_propose(
    flag: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    argv = ["ai", "propose", flag] + (["2"] if flag == "--passes" else [])
    monkeypatch.setattr("sys.argv", argv)
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    monkeypatch.setattr(ai, "load_members", lambda: {})
    with pytest.raises(SystemExit) as exc:
        ai.main()
    assert exc.value.code == 2


def test_model_sound_label_is_ignored_in_favour_of_code() -> None:
    row = verify_row()
    ai.apply_verify([row], [verify_item("a", label("дверь", sound="none"))])
    assert row["ru_final"] == "дверь"
    assert row["status"] == "verified"


def test_verifier_note_marks_sound_as_code_computed() -> None:
    row = verify_row()
    ai.apply_verify([row], [verify_item("a")])
    assert "sound close (code)" in row["verifier_note"]


# ---------- --units-file ----------


def proposed_ledger(ledger: Path) -> None:
    rows = read_ledger(ledger)
    for r in rows:
        r.update(status="proposed", ru_candidates="дверь", sanskrit="dvāra")
    write_ledger(ledger, rows)


def test_read_units_strips_and_drops_empty(tmp_path: Path) -> None:
    path = tmp_path / "units.txt"
    path.write_text("√kus 2\n\n  b  \n", encoding="utf-8")
    assert ai.read_units(path) == {"√kus 2", "b"}


def test_verify_with_units_only_touches_listed_rows(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    proposed_ledger(ledger)
    fake = FakeAsk([wrap([verify_item("b")])])
    assert ai.run_batches("verify", ledger, fake, {}, 5, 0, False, units={"b"}) == 0
    assert len(fake.calls) == 1
    assert statuses(ledger) == ["proposed", "verified", "proposed"]


def test_units_prompt_contains_only_listed_rows(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    rows = read_ledger(ledger)
    for r in rows:
        r.update(
            status="proposed", ru_candidates="дверь", sanskrit=f"skt-{r['unit_key']}"
        )
    write_ledger(ledger, rows)
    fake = FakeAsk([wrap([verify_item("b")])])
    ai.run_batches("verify", ledger, fake, {}, 5, 0, False, units={"b"})
    assert "skt-b" in fake.calls[0][0]
    assert "skt-a" not in fake.calls[0][0]
    assert "skt-c" not in fake.calls[0][0]


def test_units_unknown_key_returns_one_and_leaves_ledger(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    proposed_ledger(ledger)
    before = ledger.read_bytes()
    fake = FakeAsk([])
    assert (
        ai.run_batches("verify", ledger, fake, {}, 5, 0, False, units={"b", "zzz"}) == 1
    )
    assert fake.calls == []
    assert ledger.read_bytes() == before


def test_units_skips_rows_not_in_wanted_status(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    rows = read_ledger(ledger)
    for r in rows:
        r.update(status="proposed", ru_candidates="дверь", sanskrit="dvāra")
    rows[0]["status"] = "verified"
    write_ledger(ledger, rows)
    fake = FakeAsk([wrap([verify_item("b")])])
    assert (
        ai.run_batches("verify", ledger, fake, {}, 5, 0, False, units={"a", "b"}) == 0
    )
    assert statuses(ledger) == ["verified", "verified", "proposed"]


def test_units_all_ineligible_is_nothing_to_do(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    rows = read_ledger(ledger)
    for r in rows:
        r.update(status="proposed", ru_candidates="дверь", sanskrit="dvāra")
    rows[0]["status"] = "verified"
    write_ledger(ledger, rows)
    before = ledger.read_bytes()
    fake = FakeAsk([])
    assert ai.run_batches("verify", ledger, fake, {}, 5, 0, False, units={"a"}) == 0
    assert fake.calls == []
    assert ledger.read_bytes() == before


def test_units_batches_follow_ledger_order(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ai, "require_offpeak", no_peak)
    rows = read_ledger(ledger)
    for r in rows:
        r.update(
            status="proposed", ru_candidates="дверь", sanskrit=f"skt-{r['unit_key']}"
        )
    write_ledger(ledger, rows)
    fake = FakeAsk([wrap([verify_item("a")]), wrap([verify_item("c")])])
    ai.run_batches("verify", ledger, fake, {}, 1, 0, False, units={"c", "a"})
    assert "skt-a" in fake.calls[0][0]
    assert "skt-c" in fake.calls[1][0]
