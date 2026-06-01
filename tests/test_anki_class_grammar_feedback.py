"""Test grammar Anki feedback link generation."""

from scripts.work_with_csv.anki_class_grammar import make_feedback_link


def test_make_feedback_link_prefills_update_date() -> None:
    feedback = make_feedback_link("kamma", "05-30")

    assert "entry.438735500=kamma" in feedback
    assert "entry.957833742=Anki Deck Grammar" in feedback
    assert "entry.1940411063=Anki-05-30" in feedback
