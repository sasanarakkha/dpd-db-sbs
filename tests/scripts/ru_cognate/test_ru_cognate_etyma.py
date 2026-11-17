"""Tests for the Wiktionary etymon parser used by the ru_cognate join."""

import json
from pathlib import Path
from typing import Any

from scripts.ru_cognate.ru_cognate_etyma import (
    index_protoslavic,
    index_pali,
    index_russian,
    index_sanskrit,
    is_loan,
    norm_pie,
    pie_keys,
    strip_accents,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def lines(name: str) -> list[str]:
    return (FIXTURES / name).read_text(encoding="utf-8").splitlines()


def entries(name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in lines(name)]


def find(name: str, word: str, pos: str | None = None) -> dict[str, Any]:
    for entry in entries(name):
        if entry["word"] == word and (pos is None or entry["pos"] == pos):
            return entry
    raise AssertionError(f"{word} not in {name}")


def test_strip_accents() -> None:
    assert strip_accents("буди́ть") == "будить"
    assert strip_accents("buddhá") == "buddha"
    assert strip_accents("ёж") == "ёж"
    assert strip_accents("dvā́ra") == "dvāra"


def test_norm_pie() -> None:
    assert norm_pie("*dʰwṓr") == norm_pie("dʰwṓr")
    assert norm_pie("*dʰwer-") == "dʰwer"
    assert norm_pie("*bʰúdʰs") == "bʰudʰs"
    assert norm_pie("*néwos") == "newos"


def test_pie_keys_none_for_pali_internal_root() -> None:
    assert pie_keys(find("pali.jsonl", "rosa", "noun")) == set()


def test_pie_keys_none_for_sanskrit_internal_root() -> None:
    mata_root = [e for e in entries("sanskrit.jsonl") if e["word"] == "मातृ"][1]
    assert pie_keys(mata_root) == set()


def test_pie_keys_term_in_arg4() -> None:
    assert "bʰudʰs" in pie_keys(find("sanskrit.jsonl", "बुध्", "root"))


def test_pie_keys_from_text_only() -> None:
    assert pie_keys(find("sanskrit.jsonl", "नव")) == {"newos"}


def test_pie_keys_skips_suffix_terms() -> None:
    keys = pie_keys(find("sanskrit.jsonl", "द्वार"))
    assert keys == {"dʰwer", norm_pie("dʰwṓr")}
    assert "s" not in keys


def test_pie_keys_root_template_russian() -> None:
    assert "dʰwer" in pie_keys(find("russian.jsonl", "дверь"))


def test_is_loan() -> None:
    assert is_loan(find("russian.jsonl", "лук"))
    assert is_loan(find("russian.jsonl", "новояз"))
    assert not is_loan(find("russian.jsonl", "дверь"))
    assert not is_loan(find("russian.jsonl", "брат"))


def test_sanskrit_index_hops_and_homonyms() -> None:
    by_rom, by_word = index_sanskrit(lines("sanskrit.jsonl"))
    assert norm_pie("dʰwṓr") in by_rom["dvāra"]
    assert "dʰwer" in by_word["द्वार्"]
    assert {"kʷer", "kreH"} <= by_rom["kṛ"]
    assert "bʰudʰs" in by_rom["budh"]
    assert "newos" in by_rom["nava"]
    assert norm_pie("méh₂tēr") in by_rom["mātṛ"]


def test_sanskrit_hop_via_etymon_template() -> None:
    dvara = find("sanskrit.jsonl", "द्वार")
    own = pie_keys(dvara)
    # The `etymon` hop target द्वार् carries the same keys; the hop must not lose them.
    _, by_word = index_sanskrit(lines("sanskrit.jsonl"))
    assert own <= by_word["द्वार"]


def test_pali_index_hop_via_sanskrit() -> None:
    _, by_word = index_sanskrit(lines("sanskrit.jsonl"))
    pali = index_pali(lines("pali.jsonl"), by_word)
    assert norm_pie("méh₂tēr") in pali["mātar"]
    assert "rosa" not in pali or pali["rosa"] == set()


def test_protoslavic_index() -> None:
    psl = index_protoslavic(lines("protoslavic.jsonl"))
    assert norm_pie("bʰréh₂tēr") in psl["bratrъ"]
    assert "newos" in psl["novъ"]
    assert "dʰwer" in psl["dvьrь"]


def test_russian_index_via_protoslavic_and_loans() -> None:
    psl = index_protoslavic(lines("protoslavic.jsonl"))
    ru = index_russian(lines("russian.jsonl"), psl)
    assert "брат" in ru[norm_pie("bʰréh₂tēr")]
    assert "дверь" in ru["dʰwer"]
    assert "будить" in ru["bʰewdʰ"]
    assert all("лук" not in words for words in ru.values())
    assert all("новояз" not in words for words in ru.values())


def test_protoslavic_new_key_is_text_only() -> None:
    novu = find("protoslavic.jsonl", "novъ")
    template_pie = [
        t
        for t in novu.get("etymology_templates", [])
        if "ine-pro" in t["args"].values()
    ]
    assert template_pie == []
    assert "newos" in pie_keys(novu)


def test_russian_pie_only_in_text_is_indexed() -> None:
    line = json.dumps(
        {
            "word": "и́мя",
            "lang_code": "ru",
            "etymology_templates": [
                {"name": "inh", "args": {"1": "ru", "2": "orv", "3": "имѧ"}}
            ],
            "etymology_text": "From Proto-Indo-European *h₁nómn̥.",
        },
        ensure_ascii=False,
    )
    ru = index_russian([line], {})
    assert ru[norm_pie("h₁nómn̥")] == {"имя"}


def test_inherited_word_with_later_sense_calque_is_not_loan() -> None:
    entry = {
        "word": "имя",
        "lang_code": "ru",
        "etymology_templates": [
            {"name": "inh", "args": {"1": "ru", "2": "orv", "3": "имѧ"}},
            {"name": "calque", "args": {"1": "ru", "2": "en", "3": "name"}},
        ],
    }
    assert not is_loan(entry)
