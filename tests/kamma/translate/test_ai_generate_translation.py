"""Structural tests for same-root retrieval functions against the real dpd.db."""

import re

from db.models import DpdHeadword, DpdRoot, Russian
from kamma.translate.scripts.ai_generate_translation import (
    db_session,
    get_root_ru_meaning,
    get_same_root_lit_examples,
    get_same_root_meaning_examples,
    get_verified_root_keys,
    reset_grounded_drafts,
    select_reset_grounded_rows,
)


def _verified_gam_word() -> DpdHeadword:
    """A √gam word with verified ru_meaning and a non-empty construction."""
    word = (
        db_session.query(DpdHeadword)
        .join(Russian, DpdHeadword.id == Russian.id)
        .filter(
            DpdHeadword.root_key == "√gam",
            DpdHeadword.construction != "",
            Russian.ru_meaning != "",
        )
        .first()
    )
    assert word is not None
    return word


def test_meaning_examples_exclude_self() -> None:
    word = _verified_gam_word()
    assert word.lemma_1 not in [t[0] for t in get_same_root_meaning_examples(word)]


def test_lit_examples_exclude_self() -> None:
    word = _verified_gam_word()
    assert word.lemma_1 not in [t[0] for t in get_same_root_lit_examples(word)]


def test_examples_respect_limit() -> None:
    word = _verified_gam_word()
    assert len(get_same_root_meaning_examples(word)) <= 5
    assert len(get_same_root_lit_examples(word)) <= 5
    assert len(get_same_root_meaning_examples(word, limit=2)) <= 2
    assert len(get_same_root_lit_examples(word, limit=2)) <= 2


def test_lit_examples_no_multiline_construction() -> None:
    word = _verified_gam_word()
    for t in get_same_root_lit_examples(word):
        assert "\n" not in t[1]


def test_meaning_examples_deduped_by_base_lemma() -> None:
    word = _verified_gam_word()
    base_lemmas = [
        re.sub(r"\s+\d+$", "", t[0]) for t in get_same_root_meaning_examples(word)
    ]
    assert len(base_lemmas) == len(set(base_lemmas))


def test_lit_examples_deduped_by_construction() -> None:
    word = _verified_gam_word()
    constructions = [t[1] for t in get_same_root_lit_examples(word)]
    assert len(constructions) == len(set(constructions))


def test_lit_examples_prefix_affinity_ordering() -> None:
    word = _verified_gam_word()
    first_tok = word.construction.split("\n")[0].split()[0]
    examples = get_same_root_lit_examples(word)

    def matches(constr: str) -> bool:
        return constr == first_tok or constr.startswith(first_tok + " ")

    match_flags = [matches(t[1]) for t in examples]
    if not any(match_flags):
        import pytest

        pytest.skip("no returned example matches the target's first token")
    seen_non_match = False
    for flag in match_flags:
        if not flag:
            seen_non_match = True
        elif seen_non_match:
            raise AssertionError("a matching example appeared after a non-matching one")


def test_empty_root_key_returns_empty() -> None:
    word = DpdHeadword(id=0, lemma_1="x", pos="adj", root_key="", construction="")
    assert get_same_root_meaning_examples(word) == []
    assert get_same_root_lit_examples(word) == []


def test_get_root_ru_meaning_matches_db() -> None:
    root = db_session.query(DpdRoot).filter(DpdRoot.root_ru_meaning != "").first()
    assert root is not None
    assert get_root_ru_meaning(root.root) == root.root_ru_meaning
    assert get_root_ru_meaning("") == ""
    assert get_root_ru_meaning("√doesnotexist") == ""


def test_caches_return_stable_results() -> None:
    word = _verified_gam_word()
    assert get_same_root_meaning_examples(word) == get_same_root_meaning_examples(word)
    assert get_same_root_lit_examples(word) == get_same_root_lit_examples(word)


def test_verified_root_keys_shape() -> None:
    verified_roots = get_verified_root_keys()
    assert isinstance(verified_roots, set)
    assert len(verified_roots) > 0
    assert "" not in verified_roots
    assert "√gam" in verified_roots


def test_reset_candidates_are_eligible() -> None:
    verified_roots = get_verified_root_keys()
    rows = select_reset_grounded_rows(limit=20)
    for word, russian in rows:
        assert russian.ru_meaning_raw != ""
        assert not russian.ru_meaning
        assert word.root_key != ""
        assert word.root_key in verified_roots


def test_reset_candidates_ordering_and_limit() -> None:
    rows = select_reset_grounded_rows(limit=20)
    assert len(rows) <= 20
    ebt_counts = [word.ebt_count for word, _russian in rows]
    assert ebt_counts == sorted(ebt_counts, reverse=True)


def test_reset_dry_run_changes_nothing() -> None:
    before = [(r.id, r.ru_meaning_raw) for _, r in select_reset_grounded_rows(2)]
    reset_grounded_drafts(2, dry_run=True)
    db_session.expire_all()
    for russian_id, ru_meaning_raw in before:
        russian = db_session.query(Russian).filter(Russian.id == russian_id).first()
        assert russian is not None
        assert russian.ru_meaning_raw == ru_meaning_raw
