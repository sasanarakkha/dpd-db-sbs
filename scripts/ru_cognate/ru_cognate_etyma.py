"""Parse kaikki.org Wiktionary JSONL dumps into Proto-Indo-European (PIE) key indexes for the ru_cognate join."""

import json
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

Entry = dict[str, Any]
KeyIndex = dict[str, set[str]]

ACCENTS = {"̀", "́"}
PIE_TEXT_RE = re.compile(r"Proto-Indo-European \*([^\s,.;:()“”]+)")
INHERIT_TEMPLATES = {"root", "inh", "inh+", "der"}
LOAN_TEMPLATES = {
    "bor",
    "bor+",
    "lbor",
    "ubor",
    "obor",
    "learned borrowing",
    "unadapted borrowing",
    "calque",
    "clq",
    "pclq",
    "translit",
}


def strip_accents(text: str) -> str:
    """Return NFC text with the grave and acute combining marks removed."""
    decomposed = unicodedata.normalize("NFD", text)
    return unicodedata.normalize(
        "NFC", "".join(c for c in decomposed if c not in ACCENTS)
    )


def norm_pie(term: str) -> str:
    """Normalise a PIE term to a join key: no accents, no `*`, no edge hyphens."""
    return strip_accents(term).replace("*", "").strip("-")


def _template_terms(template: dict[str, Any]) -> list[str]:
    """Return the PIE terms of one `ine-pro` template (empty list if not one)."""
    args: dict[str, str] = template.get("args", {})
    if args.get("2") != "ine-pro":
        return []
    name = template.get("name")
    if name == "root":
        index = 3
        terms: list[str] = []
        while str(index) in args:
            if args[str(index)]:
                terms.append(args[str(index)])
            index += 1
        return terms
    if name in INHERIT_TEMPLATES:
        term = args.get("3") or args.get("4") or ""
        return [term] if term else []
    return []


def _is_suffix(term: str) -> bool:
    return term.startswith("-") or term.startswith("*-")


def pie_keys(entry: Entry) -> set[str]:
    """Return the normalised PIE keys of one entry, from templates and `etymology_text`."""
    terms: list[str] = []
    for template in entry.get("etymology_templates", []):
        terms.extend(_template_terms(template))
    terms.extend(PIE_TEXT_RE.findall(entry.get("etymology_text", "")))
    return {norm_pie(t) for t in terms if t and not _is_suffix(t) and norm_pie(t)}


def is_loan(entry: Entry) -> bool:
    """Return True when the entry's own etymology is a borrowing, calque or transliteration.

    A word that also has its own inheritance chain (`inh`/`inh+` with arg 1 = its language)
    is inherited: a loan template there describes one later sense (e.g. имя, "calque of English name").
    """
    lang = entry.get("lang_code")
    templates = entry.get("etymology_templates", [])
    if any(
        t.get("name") in ("inh", "inh+") and t.get("args", {}).get("1") == lang
        for t in templates
    ):
        return False
    return any(
        t.get("name") in LOAN_TEMPLATES and t.get("args", {}).get("1") == lang
        for t in templates
    )


def _romanization(entry: Entry) -> str:
    for form in entry.get("forms", []):
        if "romanization" in form.get("tags", []):
            return strip_accents(form.get("form", ""))
    return ""


def _sanskrit_hops(entry: Entry) -> list[str]:
    """Return Devanagari words named by a `sa`→`sa` root template or an `etymon` template."""
    targets: list[str] = []
    for template in entry.get("etymology_templates", []):
        args: dict[str, str] = template.get("args", {})
        if args.get("1") != "sa":
            continue
        if template.get("name") == "root" and args.get("2") == "sa" and args.get("3"):
            targets.append(args["3"])
        elif template.get("name") == "etymon":
            target = args.get("2", "")
            if target and not target.startswith(":") and "3" not in args:
                targets.append(target.split("<", 1)[0])
    return targets


def _load(line: str, needles: tuple[str, ...]) -> Entry | None:
    """Parse a JSONL line if it contains one of the needles (cheap prefilter)."""
    if needles and not any(n in line for n in needles):
        return None
    line = line.strip()
    return json.loads(line) if line else None


def index_sanskrit(lines: Iterable[str]) -> tuple[KeyIndex, KeyIndex]:
    """Index Sanskrit entries; return (by IAST romanization, by Devanagari word) key sets.

    Each Sanskrit entry also inherits, in one hop only, the own keys of the entry
    named by its `sa`→`sa` root or `etymon` template. Homonyms are unioned.
    """
    own_by_word: KeyIndex = defaultdict(set)
    records: list[tuple[str, str, list[str]]] = []
    for line in lines:
        entry = _load(line, ())
        if entry is None:
            continue
        word = entry["word"]
        own_by_word[word] |= pie_keys(entry)
        records.append((word, _romanization(entry), _sanskrit_hops(entry)))
    by_word: KeyIndex = defaultdict(set)
    by_rom: KeyIndex = defaultdict(set)
    for word, rom, hops in records:
        keys = set(own_by_word[word])
        for target in hops:
            keys |= own_by_word.get(target, set())
        by_word[word] |= keys
        if rom:
            by_rom[rom] |= keys
    return dict(by_rom), dict(by_word)


def index_pali(lines: Iterable[str], sanskrit_by_word: KeyIndex) -> KeyIndex:
    """Index Pāḷi entries by word; one `pi`→`sa` `inh`/`der` hop into the Sanskrit index."""
    index: KeyIndex = defaultdict(set)
    for line in lines:
        entry = _load(line, ())
        if entry is None:
            continue
        keys = pie_keys(entry)
        for template in entry.get("etymology_templates", []):
            args: dict[str, str] = template.get("args", {})
            if (
                template.get("name") in INHERIT_TEMPLATES - {"root"}
                and args.get("1") == "pi"
                and args.get("2") == "sa"
                and args.get("3")
            ):
                keys |= sanskrit_by_word.get(args["3"], set())
        index[entry["word"]] |= keys
    return dict(index)


def index_protoslavic(lines: Iterable[str]) -> KeyIndex:
    """Index Proto-Slavic entries by accent-free word (no `*`) to their PIE keys."""
    index: KeyIndex = defaultdict(set)
    for line in lines:
        entry = _load(line, ("ine-pro", "Proto-Indo-European"))
        if entry is None:
            continue
        index[strip_accents(entry["word"]).lstrip("*")] |= pie_keys(entry)
    return dict(index)


def index_russian(lines: Iterable[str], protoslavic: KeyIndex) -> dict[str, set[str]]:
    """Index Russian words by PIE key, direct or via the Proto-Slavic hop; loans dropped.

    Returns {pie_key: {russian words}}, stress marks stripped, `ё` kept.
    """
    index: dict[str, set[str]] = defaultdict(set)
    for line in lines:
        entry = _load(line, ("ine-pro", "sla-pro", "Proto-Indo-European"))
        if entry is None or is_loan(entry):
            continue
        keys = pie_keys(entry)
        for template in entry.get("etymology_templates", []):
            args: dict[str, str] = template.get("args", {})
            if (
                template.get("name") in INHERIT_TEMPLATES - {"root"}
                and args.get("1") == "ru"
                and args.get("2") == "sla-pro"
                and args.get("3")
            ):
                psl_word = strip_accents(args["3"]).lstrip("*")
                keys |= protoslavic.get(psl_word, set())
        word = strip_accents(entry["word"])
        for key in keys:
            index[key].add(word)
    return dict(index)
