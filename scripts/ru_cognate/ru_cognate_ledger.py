"""Build the ru_cognate ledger: units from dpd.db, the Wiktionary join, and ledger TSV I/O."""

import argparse
import csv
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot
from scripts.ru_cognate.ru_cognate_etyma import (
    KeyIndex,
    index_pali,
    index_protoslavic,
    index_russian,
    index_sanskrit,
    strip_accents,
)
from tools.paths import ProjectPaths
from tools.printer import printer as pr

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = REPO_ROOT / "shared_data" / "ru_cognate" / "ledger.tsv"

COLUMNS: list[str] = [
    "unit_type",
    "unit_key",
    "pali_meaning",
    "sanskrit",
    "headword_count",
    "en_cognate",
    "pie_root",
    "pie_id",
    "ru_candidates",
    "source",
    "method",
    "confidence",
    "status",
    "verifier_verdict",
    "verifier_note",
    "ru_flagged",
    "ru_final",
    "decision",
]

DUMP_FILES: dict[str, str] = {
    "sanskrit": "Sanskrit.jsonl",
    "pali": "Pali.jsonl",
    "protoslavic": "ProtoSlavic.jsonl",
    "russian": "Russian.jsonl",
}

MAX_CANDIDATES = 10

# DPD roots are verbal, so closed-class Russian words are never a root's cognate;
# family units keep them (e.g. family `ka` -> кто).
CLOSED_CLASS_RU: frozenset[str] = frozenset(
    """
и а но да ли бы же ни не абы ещё он
она оно они его её их им ему я ты мы вы
то тот этот сей сям там тут здесь где как кто что
когда вот вон уж уже в во на о об обо у
к ко с со из от до по за над под при
про без для или либо ибо аж чтобы ведь вне сквозь через
между перед
""".split()
)

Row = dict[str, str]


@dataclass
class Unit:
    """One ledger row plus the lookup terms used only while joining."""

    row: Row
    sanskrit_terms: list[str] = field(default_factory=list)
    pali_words: list[str] = field(default_factory=list)


def _blank_row(unit_type: str, unit_key: str) -> Row:
    row = {column: "" for column in COLUMNS}
    row["unit_type"] = unit_type
    row["unit_key"] = unit_key
    row["status"] = "pending"
    return row


def _dedup(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _pali_word(lemma: str) -> str:
    return re.sub(r"\s+\d+$", "", lemma)


def _family_sanskrit_terms(values: list[str]) -> list[str]:
    terms: list[str] = []
    for value in values:
        for part in value.split(", "):
            part = re.sub(r"\s*\[.*?\]", "", part).strip()
            if part and "+" not in part:
                terms.append(part)
    return _dedup(terms)


def _finish_unit(unit: Unit, members: list[Row]) -> Unit:
    unit.row["headword_count"] = str(len(members))
    unit.row["sanskrit"] = ", ".join(unit.sanskrit_terms)
    unit.row["en_cognate"] = ", ".join(
        _dedup([m["cognate"] for m in members if m["cognate"]])
    )
    unit.pali_words = _dedup([_pali_word(m["lemma_1"]) for m in members])
    if any(m["non_ia"] for m in members):
        unit.row["status"] = "none"
        unit.row["verifier_note"] = "non-IA"
    return unit


def build_units(roots: list[Row], headwords: list[Row]) -> list[Unit]:
    """Return one Unit per root, then one per rootless family_word (spec 1)."""
    by_root: dict[str, list[Row]] = {}
    by_family: dict[str, list[Row]] = {}
    for hw in headwords:
        if hw["root_key"]:
            by_root.setdefault(hw["root_key"], []).append(hw)
        elif hw["family_word"]:
            by_family.setdefault(hw["family_word"], []).append(hw)

    units: list[Unit] = []
    for root in roots:
        unit = Unit(_blank_row("root", root["root"]))
        unit.row["pali_meaning"] = root["root_meaning"]
        unit.sanskrit_terms = _dedup(
            [s.lstrip("√") for s in root["sanskrit_root"].split() if s.lstrip("√")]
        )
        units.append(_finish_unit(unit, by_root.get(root["root"], [])))

    for family_word in sorted(by_family):
        members = by_family[family_word]
        unit = Unit(_blank_row("family", family_word))
        headword_meaning = next(
            (
                m["meaning_1"]
                for m in members
                if _pali_word(m["lemma_1"]) == family_word and m["meaning_1"]
            ),
            "",
        )
        unit.row["pali_meaning"] = headword_meaning or next(
            (m["meaning_1"] for m in members if m["meaning_1"]), ""
        )
        unit.sanskrit_terms = _family_sanskrit_terms([m["sanskrit"] for m in members])
        units.append(_finish_unit(unit, members))
    return units


def read_ledger(path: Path) -> list[Row]:
    """Read the ledger TSV; raise ValueError if the header is not COLUMNS."""
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"{path}: unexpected ledger columns {reader.fieldnames}")
        return [dict(r) for r in reader]


def write_ledger(path: Path, rows: list[Row]) -> None:
    """Write the ledger atomically: temp file, then replace."""
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def clean_candidates(words: list[str], unit_type: str) -> list[str]:
    """Drop affixes, duplicates and (for roots) closed-class words; keep input order."""
    kept: list[str] = []
    for word in words:
        norm = strip_accents(word).strip().lower()
        if not norm or norm.startswith("-") or norm.endswith("-"):
            continue
        if norm in kept:
            continue
        if unit_type == "root" and norm in CLOSED_CLASS_RU:
            continue
        kept.append(norm)
    return kept


def clean_ledger(rows: list[Row]) -> tuple[int, int]:
    """Clean ru_candidates of proposed rows; return (rows_changed, words_dropped)."""
    changed = 0
    dropped = 0
    for row in rows:
        if row["status"] != "proposed":
            continue
        old = [w for w in row["ru_candidates"].split(", ") if w]
        new = clean_candidates(old, row["unit_type"])
        if new == old:
            continue
        changed += 1
        dropped += len(old) - len(new)
        row["ru_candidates"] = ", ".join(new)
        if not new:
            row["status"] = "pending"
            for column in ("pie_root", "source", "method"):
                row[column] = ""
    return changed, dropped


def join_units(
    units: list[Unit],
    sanskrit_by_rom: KeyIndex,
    pali_by_word: KeyIndex,
    russian_by_key: KeyIndex,
) -> None:
    """Fill pie_root / ru_candidates / source and set proposed for every join hit (spec 4)."""
    for unit in units:
        row = unit.row
        if row["status"] != "pending":
            continue
        keys: set[str] = set()
        sa_hits: list[str] = []
        pi_hits: list[str] = []
        for term in unit.sanskrit_terms:
            found = sanskrit_by_rom.get(strip_accents(term), set())
            if found:
                keys |= found
                sa_hits.append(term)
        for word in unit.pali_words:
            found = pali_by_word.get(strip_accents(word), set())
            if found:
                keys |= found
                pi_hits.append(word)
        matched = sorted(k for k in keys if k in russian_by_key)
        words = {w.lower() for k in matched for w in russian_by_key[k]}
        if not words:
            continue
        ordered = sorted(words, key=lambda w: (len(w), w))
        ordered = clean_candidates(ordered, row["unit_type"])
        if not ordered:
            continue
        shown = ordered[:MAX_CANDIDATES]
        extra = len(ordered) - len(shown)
        source = "Wiktionary: " + "; ".join(
            part
            for part in (
                f"sa {', '.join(sa_hits)}" if sa_hits else "",
                f"pi {', '.join(pi_hits)}" if pi_hits else "",
                f"ru {', '.join(shown)}",
            )
            if part
        )
        row["pie_root"] = ", ".join(matched)
        row["ru_candidates"] = ", ".join(shown)
        row["source"] = source + (f" +{extra} more" if extra else "")
        row["method"] = "join"
        row["status"] = "proposed"


def load_db_rows() -> tuple[list[Row], list[Row]]:
    """Read roots and headwords read-only from dpd.db as plain string rows."""
    session = get_db_session(ProjectPaths().dpd_db_path)
    try:
        roots = [
            {
                "root": r.root or "",
                "sanskrit_root": r.sanskrit_root or "",
                "root_meaning": r.root_meaning or "",
            }
            for r in session.query(
                DpdRoot.root, DpdRoot.sanskrit_root, DpdRoot.root_meaning
            )
        ]
        headwords = [
            {
                "lemma_1": r.lemma_1 or "",
                "root_key": r.root_key or "",
                "family_word": r.family_word or "",
                "sanskrit": r.sanskrit or "",
                "meaning_1": r.meaning_1 or "",
                "non_ia": r.non_ia or "",
                "cognate": r.cognate or "",
            }
            for r in session.query(
                DpdHeadword.lemma_1,
                DpdHeadword.root_key,
                DpdHeadword.family_word,
                DpdHeadword.sanskrit,
                DpdHeadword.meaning_1,
                DpdHeadword.non_ia,
                DpdHeadword.cognate,
            )
        ]
    finally:
        session.close()
    return roots, headwords


def _read_lines(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as f:
        return f.readlines()


def run_full_join(dumps: Path, ledger: Path) -> int:
    """Create the ledger from the DB and the dumps. Refuse if it exists. Return exit code."""
    if ledger.exists():
        pr.red(f"Ledger already exists, not touching it: {ledger}")
        return 1
    missing = [n for n in DUMP_FILES.values() if not (dumps / n).exists()]
    if missing:
        pr.red(f"Missing dumps in {dumps}: {', '.join(missing)}")
        return 1

    pr.green_tmr("building units")
    roots, headwords = load_db_rows()
    units = build_units(roots, headwords)
    pr.yes(len(units))

    pr.green_tmr("indexing dumps")
    by_rom, by_word = index_sanskrit(_read_lines(dumps / DUMP_FILES["sanskrit"]))
    pali = index_pali(_read_lines(dumps / DUMP_FILES["pali"]), by_word)
    psl = index_protoslavic(_read_lines(dumps / DUMP_FILES["protoslavic"]))
    with (dumps / DUMP_FILES["russian"]).open(encoding="utf-8") as f:
        russian = index_russian(f, psl)
    pr.yes(len(russian))

    pr.green_tmr("joining")
    join_units(units, by_rom, pali, russian)
    pr.yes("ok")

    ledger.parent.mkdir(parents=True, exist_ok=True)
    write_ledger(ledger, [u.row for u in units])
    counts = Counter((u.row["unit_type"], u.row["status"]) for u in units)
    for (unit_type, status), count in sorted(counts.items()):
        pr.summary(f"{unit_type} {status}", count)
    pr.summary("total", len(units))
    return 0


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dumps",
        type=Path,
        required=True,
        help="Folder holding Sanskrit.jsonl, Pali.jsonl, ProtoSlavic.jsonl, Russian.jsonl",
    )
    args = parser.parse_args()
    sys.exit(run_full_join(args.dumps, LEDGER_PATH))


if __name__ == "__main__":
    main()
