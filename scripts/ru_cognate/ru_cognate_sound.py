"""Compute a code-side sound label (close/weak/none) between a Pāḷi/Sanskrit source and a Russian word."""

import re
import unicodedata

CLASS_BY_LETTER: dict[str, str] = {
    **dict.fromkeys("kc", "K"),
    **dict.fromkeys("gjh", "G"),
    **dict.fromkeys("śṣs", "S"),
    **dict.fromkeys("tṭ", "T"),
    **dict.fromkeys("dḍ", "D"),
    **dict.fromkeys("nṇñṅṃ", "N"),
    "p": "P",
    "b": "B",
    "m": "M",
    **dict.fromkeys("rṛlḷ", "R"),
    "v": "V",
}

RUSSIAN_CLASS_BY_LETTER: dict[str, str] = {
    **dict.fromkeys("кчц", "K"),
    **dict.fromkeys("гжз", "G"),
    **dict.fromkeys("сшх", "S"),
    "т": "T",
    "д": "D",
    "н": "N",
    "п": "P",
    "б": "B",
    "м": "M",
    **dict.fromkeys("рл", "R"),
    "в": "V",
}

RANK: dict[str, int] = {"none": 0, "weak": 1, "close": 2}


def skeleton(source: str) -> list[str]:
    """Return the first two consonant classes of an IAST source, collapsed and aspirate-free."""
    text = unicodedata.normalize("NFC", source.lower())
    classes: list[str] = []
    previous_is_consonant = False
    for char in text:
        cls = CLASS_BY_LETTER.get(char)
        if cls is None:
            previous_is_consonant = False
            continue
        is_aspirate = char == "h" and previous_is_consonant
        previous_is_consonant = True
        if is_aspirate:
            continue
        if not classes or classes[-1] != cls:
            classes.append(cls)
    return classes[:2]


def sources(unit_key: str, sanskrit: str) -> list[str]:
    """Return the unit key (no root sign, no homonym number) plus every ledger Sanskrit value."""
    key = re.sub(r"\s*\d+$", "", unit_key.strip()).replace("√", "")
    values = [v.replace("√", "") for v in re.split(r"[,\s<]+", sanskrit)]
    return [v for v in [key, *values] if v]


def _russian_classes(word: str) -> list[str]:
    return [
        RUSSIAN_CLASS_BY_LETTER[c] for c in word.lower() if c in RUSSIAN_CLASS_BY_LETTER
    ]


def _label_for_source(source: str, russian: list[str]) -> str:
    classes = skeleton(source)
    if not classes:
        return "weak"
    if russian and russian[0] == classes[0]:
        if len(classes) == 1 or classes[1] in russian[1:]:
            return "close"
    if any(c in classes for c in russian):
        return "weak"
    return "none"


def sound_label(unit_key: str, sanskrit: str, word: str) -> str:
    """Return the best label (close > weak > none) of the word over all sources."""
    russian = _russian_classes(word)
    best = "none"
    for source in sources(unit_key, sanskrit):
        label = _label_for_source(source, russian)
        if RANK[label] > RANK[best]:
            best = label
    return best
