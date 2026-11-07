"""Tests for the pure root_example checking logic, using synthetic data only."""

from scripts.find.root_example_checker import Finding, check_root_examples


def test_ok_example_not_reported() -> None:
    assert check_root_examples({"√a": "foo"}, {"foo": {"√a"}}) == []


def test_wrong_root_reports_found_roots() -> None:
    findings = check_root_examples({"√vadh": "attharaṇa"}, {"attharaṇa": {"√thar"}})
    assert findings == [Finding("√vadh", "attharaṇa", "WRONG_ROOT", ("√thar",))]


def test_not_found() -> None:
    findings = check_root_examples({"√an": "anjati"}, {})
    assert findings == [Finding("√an", "anjati", "NOT_FOUND", ())]


def test_ok_if_any_headword_has_root() -> None:
    assert check_root_examples({"√a": "foo"}, {"foo": {"√b", "√a"}}) == []


def test_found_roots_sorted() -> None:
    findings = check_root_examples({"√a": "foo"}, {"foo": {"√c", "√b"}})
    assert findings[0].found_roots == ("√b", "√c")


def test_empty_root_example_skipped() -> None:
    assert check_root_examples({"√a": "", "√b": "  "}, {}) == []


def test_whitespace_around_commas() -> None:
    findings = check_root_examples({"√a": "foo ,  bar,baz "}, {"foo": {"√a"}})
    assert [f.word for f in findings] == ["bar", "baz"]
    assert all(f.kind == "NOT_FOUND" for f in findings)


def test_numbered_lemma_keys_are_caller_stripped() -> None:
    # lemma_roots keys are already lemma_clean ("attharaṇa 1" -> "attharaṇa")
    assert check_root_examples({"√thar": "attharaṇa"}, {"attharaṇa": {"√thar"}}) == []


def test_numbered_example_word_matches_clean_key() -> None:
    # root_example carries the numbered lemma: "nissanda 1", "vatthu 2"
    assert check_root_examples({"√sand": "nissanda 1"}, {"nissanda": {"√sand"}}) == []
    findings = check_root_examples({"√vas 1": "vatthu 2"}, {"vatthu": {"√vas 2"}})
    assert findings == [Finding("√vas 1", "vatthu 2", "WRONG_ROOT", ("√vas 2",))]
