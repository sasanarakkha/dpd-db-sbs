"""Tests for class_relation: determine_sbs_class classification logic."""

from types import SimpleNamespace

import pytest

from scripts.change_in_db.class_relation import determine_sbs_class


def _word(**kwargs: object) -> SimpleNamespace:
    """Build a word-like namespace with safe empty defaults for every attribute read by determine_sbs_class."""
    defaults: dict[str, str] = {
        "pos": "",
        "pattern": "",
        "grammar": "",
        "neg": "",
        "verb": "",
        "stem": "",
        "construction": "",
        "compound_type": "",
        "phonetic": "",
        "plus_case": "",
        "derived_from": "",
        "lemma_1": "",
        "lemma_2": "",
        "root_base": "",
    }
    return SimpleNamespace(**{**defaults, **kwargs})


@pytest.mark.parametrize(
    "attrs,expected",
    [
        # BPC — early exact-match rules (lines 162–261)
        ({"pos": "adj", "construction": "inf + kāma"}, 9),  # inf kāma adj
        ({"pattern": "ū adj"}, 6),  # ū adj
        ({"pattern": "ū masc"}, 6),  # ū masc
        (
            {"grammar": "dat inf", "lemma_1": "dakkhāya", "pos": "inf"},
            9,
        ),  # dat of purpose
        ({"grammar": "loc abs"}, 10),  # loc abs
        ({"grammar": "gen abs"}, 10),  # gen abs
        ({"pos": "card", "stem": "du"}, 12),  # cardinal number
        ({"pos": "ordin", "stem": "du"}, 12),  # ordinal number
        ({"pos": "imp"}, 4),  # imperative
        ({"pos": "fut"}, 5),  # future
        ({"pos": "opt"}, 7),  # optative
        ({"grammar": "adj, compar"}, 11),  # comparative adjective
        ({"grammar": "adv, compar"}, 13),  # comparative adverb
        # BPC — main nested block
        ({"pattern": "a masc"}, 2),  # a masc
        ({"pos": "aor", "pattern": "bharati aor"}, 4),  # aorist
        ({"pos": "pr", "pattern": "gacchati pr"}, 3),  # present
        ({"pattern": "ā fem"}, 7),  # ā fem
        ({"pattern": "ī fem"}, 8),  # ī fem
        ({"pos": "pp"}, 11),  # past participle
        ({"pos": "adj"}, 11),  # adjective (general)
        ({"pos": "inf"}, 9),  # infinitive
        ({"pos": "prp"}, 10),  # present participle
        ({"verb": "pass"}, 13),  # passive
        ({"verb": "caus"}, 14),  # causative
        ({"pos": "ptp"}, 14),  # potential participle
        # IPC
        ({"pos": "sandhi", "construction": "a + i > ī"}, 16),  # vowel sandhi
        ({"pos": "sandhi", "construction": "yaṃ + karoti"}, 17),  # ṃ sandhi
        # compound types
        ({"compound_type": "kammadhāraya"}, 19),  # comp 1st
        ({"compound_type": "bahubbīhi"}, 20),  # comp 2nd
        # no rule matches → None
        ({}, None),
    ],
)
def test_determine_sbs_class(attrs: dict[str, str], expected: int | None) -> None:
    assert determine_sbs_class(_word(**attrs)) == expected
