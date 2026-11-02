#!/usr/bin/env python3

"""Print exact surface-form counts for a fixed list of words across all four corpora.

Counts are strict matches of the form itself, with no inflections or sandhi
variants added. Both the EBT subset (same scope as ebt_counter.py) and the
full canon are printed, plus which headword (if any) the form belongs to.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from scripts.build.ebt_counter import _merge_ebt_freq, _sya_is_ebt
from tools.pali_text_files import bjt_texts, cst_texts, ebts, sc_texts
from tools.paths import ProjectPaths
from tools.printer import printer as pr

# Note: no, te and taṃ are homographs, so their counts include every use.
WORDS: list[str] = [
    "ahaṃ",
    "maṃ",
    "mayā",
    "me",
    "mayhaṃ",
    "mama",
    "mamaṃ",
    "mayi",
    "mayaṃ",
    "amhākaṃ",
    "no",
    "tvaṃ",
    "taṃ",
    "tuvaṃ",
    "tayā",
    "te",
    "tava",
    "tumhe",
    "tumhākaṃ",
    "vo",
]

CORPORA: list[str] = ["cst", "bjt", "sc", "sya"]


def _full_canon(freq: dict[str, dict[str, int]]) -> dict[str, int]:
    """Sum every file in a corpus into one word-count dict."""
    total: dict[str, int] = defaultdict(int)
    for file_freq in freq.values():
        for word, count in file_freq.items():
            total[word] += count
    return total


def _ebt_file_keys(
    raw: dict[str, dict[str, dict[str, int]]],
) -> dict[str, list[str]]:
    """Derive the EBT file keys per corpus, exactly as ebt_counter.py does."""
    cst_file_to_book: dict[str, str] = {
        f: book for book, files in cst_texts.items() for f in files
    }
    ebt_books: set[str] = {cst_file_to_book[f] for f in ebts if f in cst_file_to_book}
    sc_ebt_basenames: set[str] = {
        f for book in ebt_books for f in sc_texts.get(book, [])
    }
    return {
        "cst": [f.replace(".txt", ".xml") for f in ebts],
        "bjt": [f for book in ebt_books for f in bjt_texts.get(book, [])],
        "sc": [k for k in raw["sc"] if Path(k).name in sc_ebt_basenames],
        "sya": [k for k in raw["sya"] if _sya_is_ebt(k)],
    }


def _headwords_by_lemma(pth: ProjectPaths) -> dict[str, list[str]]:
    """Map the form without a number suffix to the matching lemma_1 values."""
    session = get_db_session(pth.dpd_db_path)
    headwords: dict[str, list[str]] = defaultdict(list)
    for (lemma_1,) in session.query(DpdHeadword.lemma_1).all():
        headwords[re.sub(r" \d.*$", "", lemma_1)].append(lemma_1)
    session.close()
    return headwords


def _print_table(
    title: str,
    counts: dict[str, dict[str, int]],
    headwords: dict[str, list[str]],
) -> None:
    pr.yellow_title(title)
    pr.white(f"{'word':<12}{'cst':>8}{'bjt':>8}{'sc':>8}{'sya':>8}{'max':>8}  headword")
    for word in WORDS:
        per_corpus = {corpus: counts[corpus].get(word, 0) for corpus in CORPORA}
        best = max(per_corpus.values())
        matches = headwords.get(word, [])
        found = matches[0] if matches else "-"
        if len(matches) > 1:
            found += f" (+{len(matches) - 1})"
        pr.white(
            f"{word:<12}"
            f"{per_corpus['cst']:>8}{per_corpus['bjt']:>8}"
            f"{per_corpus['sc']:>8}{per_corpus['sya']:>8}{best:>8}  {found}"
        )
    print()


def main() -> None:
    pr.tic()
    pth = ProjectPaths()

    pr.green_tmr("loading frequency data")
    raw: dict[str, dict[str, dict[str, int]]] = {}
    for corpus, path in (
        ("cst", pth.cst_file_freq),
        ("bjt", pth.bjt_file_freq),
        ("sc", pth.sc_file_freq),
        ("sya", pth.sya_file_freq),
    ):
        with path.open(encoding="utf-8") as f:
            raw[corpus] = json.load(f)

    ebt_keys = _ebt_file_keys(raw)
    ebt: dict[str, dict[str, int]] = {
        corpus: _merge_ebt_freq(raw[corpus], ebt_keys[corpus]) for corpus in CORPORA
    }
    full: dict[str, dict[str, int]] = {
        corpus: _full_canon(raw[corpus]) for corpus in CORPORA
    }

    pr.yes("ok")
    pr.green_tmr("looking up headwords")
    headwords = _headwords_by_lemma(pth)
    pr.yes("ok")

    _print_table("EBT counts (exact form)", ebt, headwords)
    _print_table("full canon counts (exact form)", full, headwords)

    pr.toc()


if __name__ == "__main__":
    main()
