"""Retrieve a CST passage by sutta/gāthā code, returning paragraphs and metadata."""

import re
from collections.abc import Callable
from dataclasses import dataclass, field

from bs4.element import Tag

from tools.cst_source_sutta_example import (
    GlobalData,
    an_anguttara_nikaya,
    clean_example,
    dn_digha_nikaya,
    find_cst_source_sutta_example,
    mn_majjhima_nikaya,
    sn_samyutta_nikaya,
)


@dataclass
class PassageResult:
    source: str
    vagga: str
    paragraphs: list[str] = field(default_factory=list)
    is_verse: bool = False


PREFIX_TO_BOOKS: dict[str, list[str]] = {
    "DHP": ["kn2"],
    "TH": ["kn8"],
    "THI": ["kn9"],
    "SNP": ["kn5"],
    "DN": ["dn1", "dn2", "dn3"],
    "MN": ["mn1", "mn2", "mn3"],
    "SN": ["sn1", "sn2", "sn3", "sn4", "sn5"],
    # AN is handled dynamically: nipāta N -> file "anN"
}

VERSE_PREFIXES: frozenset[str] = frozenset({"DHP", "TH", "THI", "SNP"})


def _get_an_books(number: str) -> list[str]:
    """Map AN nipāta number to book file, e.g. AN3.12 -> ['an3']."""
    first_seg = number.split(".")[0]
    return [f"an{first_seg}"]


def _parse_code(code: str) -> tuple[str, str, list[str]]:
    """Parse a sutta/gāthā code into (prefix, number, books).

    Returns (uppercase_prefix, number_string, list_of_book_codes).
    Raises ValueError for unrecognised codes.
    """
    m = re.match(r"^([A-Za-z]+)\s*([\d.]+)$", code.strip())
    if not m:
        raise ValueError(f"Cannot parse code: {code!r}")
    prefix = m.group(1).upper()
    number = m.group(2)

    if prefix == "AN":
        books = _get_an_books(number)
    else:
        books = PREFIX_TO_BOOKS.get(prefix, [])

    if not books:
        raise ValueError(f"Unknown or unsupported prefix: {prefix!r}")

    return prefix, number, books


PROSE_FORMATTERS: dict[str, Callable[[GlobalData], None]] = {
    "DN": dn_digha_nikaya,
    "MN": mn_majjhima_nikaya,
    "SN": sn_samyutta_nikaya,
    "AN": an_anguttara_nikaya,
}

PROSE_CONTENT_RENDS: frozenset[str] = frozenset({"bodytext", "centre"})


def _is_prose_content_rend(rend: object) -> bool:
    """Return True for raw CST content blocks that should be preserved."""
    if not isinstance(rend, str):
        return False
    return rend in PROSE_CONTENT_RENDS or rend.startswith("gatha")


def _clean_prose_paragraph(text: str) -> str:
    """Clean a CST prose paragraph for direct passage analysis."""
    paragraph = clean_example(text)
    return re.sub(r"^\d+\.\s*", "", paragraph)


def _find_prose_paragraphs(book: str, source_code: str) -> tuple[str, list[str]]:
    """Return full CST prose paragraphs for a source code."""
    prefix_match = re.match(r"^[A-Z]+", source_code)
    if not prefix_match:
        return "", []

    formatter = PROSE_FORMATTERS.get(prefix_match.group(0))
    if formatter is None:
        return "", []

    g = GlobalData(book, "")
    paragraphs: list[str] = []
    vagga = ""
    for soup in g.soups:
        for x in soup.find_all(["head", "p"]):
            if not isinstance(x, Tag):
                continue
            g.x = x
            formatter(g)
            if g.source != source_code or not g.sutta:
                continue
            if not _is_prose_content_rend(x.get("rend")):
                continue
            paragraph = _clean_prose_paragraph(x.text)
            if not paragraph or paragraph in paragraphs:
                continue
            if not vagga:
                vagga = g.sutta
            paragraphs.append(paragraph)

    return vagga, paragraphs


def get_passage_by_code(code: str) -> PassageResult:
    """Retrieve the passage(s) for a sutta/gāthā code.

    For verse books (DHP/TH/THI/SNP): returns an ordered list of gāthās (one per verse;
    DHP yields exactly 1, multi-verse suttas yield N). Each item contains a newline.
    For prose books (SN/AN/MN/DN): returns an ordered list of full paragraph strings.

    Raises ValueError if the code cannot be parsed or no examples are found.
    """
    prefix, number, books = _parse_code(code)
    source_code = f"{prefix}{number}"
    is_verse = prefix in VERSE_PREFIXES

    if is_verse:
        book = books[0]
        all_examples = find_cst_source_sutta_example(book, ".")
        matching = [e for e in all_examples if e.source == source_code]
        if not matching:
            raise ValueError(f"No examples found for {source_code!r} in book {book!r}")
        vagga = matching[0].sutta
        gathas: list[str] = []
        for e in matching:
            text = e.example.strip()
            if "\n" not in text:  # drop bare numbers / titles / colophons
                continue
            if text not in gathas:  # dedup
                gathas.append(text)
        if not gathas:  # defensive: rare single-line verse
            gathas = [max((e.example.strip() for e in matching), key=len)]
        return PassageResult(
            source=source_code, vagga=vagga, paragraphs=gathas, is_verse=True
        )

    # Prose path: scan books in order, stop at first book that yields matches
    for book in books:
        vagga, paragraphs = _find_prose_paragraphs(book, source_code)
        if not paragraphs:
            continue

        return PassageResult(
            source=source_code, vagga=vagga, paragraphs=paragraphs, is_verse=False
        )

    raise ValueError(f"No examples found for {source_code!r} in books {books!r}")
