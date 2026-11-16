#!/usr/bin/env python3
"""Check Tamil or Russian translations in the database for character and length anomalies."""

import argparse
import json
import re
import sys
from pathlib import Path

from sqlalchemy import or_
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Russian, Tamil
from kamma.translate.scripts.ids_file import read_ids_file
from tools.paths import ProjectPaths
from tools.printer import printer as pr

# List of common Pali/Sanskrit/Buddhist words that might exist in the English dictionary
PALI_STOPWORDS: set[str] = {
    "para",
    "sutta",
    "cara",
    "mana",
    "nama",
    "sama",
    "bhikkhu",
    "tada",
    "yada",
    "sada",
    "vada",
    "pali",
    "dharma",
    "karma",
    "nirvana",
    "sutra",
    "sangha",
    "buddha",
    "tatha",
    "gatha",
    "yoga",
    "kama",
    "deva",
    "raja",
    "dhamma",
    "arhat",
    "arahant",
    "bhagavant",
    "thigo",
    "thago",
    "vav",
    "iti",
    "malla",
    "saka",
    "kalla",
    "pala",
    "sala",
    "tala",
    "bala",
    "nala",
    "mala",
    "panna",
    "kana",
    "dana",
    "nana",
    "yana",
    "hana",
    "rana",
    "vana",
    "pana",
    "thana",
    "gona",
    "atta",
    "anta",
    "amsa",
    "java",
    "tava",
    "lava",
    "vava",
    "kho",
    "eva",
    "api",
    "iva",
    "suv",
    "ati",
    "adi",
    "purisa",
    "dhura",
}

# A robust fallback list of common English words in case the system dictionary is missing
FALLBACK_ENGLISH_WORDS: set[str] = {
    "the",
    "and",
    "of",
    "to",
    "in",
    "is",
    "that",
    "it",
    "he",
    "was",
    "for",
    "on",
    "are",
    "as",
    "with",
    "his",
    "they",
    "at",
    "be",
    "this",
    "have",
    "from",
    "or",
    "one",
    "had",
    "by",
    "word",
    "but",
    "not",
    "what",
    "all",
    "were",
    "we",
    "when",
    "your",
    "can",
    "said",
    "there",
    "use",
    "an",
    "each",
    "which",
    "she",
    "do",
    "how",
    "their",
    "if",
    "will",
    "up",
    "other",
    "about",
    "out",
    "many",
    "then",
    "them",
    "these",
    "so",
    "some",
    "her",
    "would",
    "make",
    "like",
    "him",
    "into",
    "time",
    "has",
    "look",
    "two",
    "more",
    "write",
    "go",
    "see",
    "number",
    "no",
    "way",
    "could",
    "people",
    "my",
    "than",
    "first",
    "water",
    "been",
    "call",
    "who",
    "oil",
    "its",
    "now",
    "find",
    "long",
    "down",
    "day",
    "did",
    "get",
    "come",
    "made",
    "may",
    "part",
    "over",
    "under",
    "afterwards",
    "before",
    "whoever",
    "unpleasant",
    "disagreeable",
    "offending",
    "agreeable",
    "pleasant",
    "apprentice",
    "dwelling",
    "scattered",
    "dishonest",
    "uncivilized",
    "shaken",
    "prayer",
    "spell",
    "produced",
    "artificially",
    "burning",
    "definition",
    "meaning",
    "translation",
    "here",
    "sure",
    "sorry",
    "error",
}


def load_english_dictionary() -> set[str]:
    """Load system English dictionary if available; otherwise use fallback list."""
    dict_path = Path("/usr/share/dict/words")
    if dict_path.exists():
        try:
            with open(dict_path, "r", encoding="utf-8") as f:
                return {line.strip().lower() for line in f}
        except OSError:
            pass
    return FALLBACK_ENGLISH_WORDS


LAST_TRANSLATED_PATH = (
    Path(__file__).resolve().parents[3] / "temp" / "last_translated.json"
)
HANGUL_PATTERN = re.compile(r"[\u1100-\u11FF\u3130-\u318F\uAC00-\uD7AF]")


def check_translations(
    lang: str,
    specific_ids: list[int] | None = None,
    auto_delete: bool = False,
    ids_file: Path | None = None,
    db_session: Session | None = None,
) -> list[int]:
    """Query translation entries, check for potential errors, and optionally delete flagged ones.

    Returns the flagged ids. `ids_file` (new `{lang, mode, ids}` shape or a bare list)
    restricts the scan to its ids, combined with `specific_ids`.
    """
    project_root = Path(__file__).resolve().parents[3]
    if db_session is None:
        pth = ProjectPaths(base_dir=project_root)
        db_session = get_db_session(pth.dpd_db_path)

    if lang == "ta":
        model_cls = Tamil
        filter_cond = Tamil.ta_meaning != ""
    elif lang == "ru":
        model_cls = Russian
        filter_cond = or_(
            Russian.ru_meaning != "",
            Russian.ru_meaning_raw != "",
            Russian.ru_meaning_lit != "",
        )
    else:
        raise ValueError(f"Unsupported language: {lang}")

    # Determine which IDs to check
    ids_to_check: list[int] | None = specific_ids

    if ids_file is not None:
        ids_to_check = sorted(set(specific_ids or []) | set(read_ids_file(ids_file)))
        if not ids_to_check:
            pr.amber(f"No ids found in {ids_file}. Nothing to check.")
            return []

    # If no specific IDs are provided, try to load from last run's JSON file
    if not ids_to_check:
        if LAST_TRANSLATED_PATH.exists():
            try:
                with open(LAST_TRANSLATED_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("lang") == lang:
                        ids_to_check = data.get("ids") or []
                        pr.white(
                            f"Loaded {len(ids_to_check or [])} IDs from the last translation run."
                        )
            except (OSError, json.JSONDecodeError) as e:
                pr.amber(f"Warning: Failed to load last translated IDs: {e}")

    if ids_to_check:
        results: list[DpdHeadword] = (
            db_session.query(DpdHeadword)
            .join(model_cls)
            .filter(DpdHeadword.id.in_(ids_to_check))
            .all()
        )
        pr.white(
            f"Checking {len(results)} specified {lang.upper()} translation entries:"
        )
    else:
        # Fallback to checking all translation data for this language
        results: list[DpdHeadword] = (
            db_session.query(DpdHeadword)
            .join(model_cls)
            .filter(filter_cond)
            .order_by(DpdHeadword.id.desc())
            .all()
        )
        pr.white(
            f"Checking all {len(results)} {lang.upper()} translation entries in database:"
        )

    if not results:
        pr.amber(
            f"No matching translated {lang.upper()} entries found in the database."
        )
        return []

    pr.white("-" * 60)

    english_words = load_english_dictionary()
    flagged_ids: list[int] = []
    flagged_columns: dict[int, list[str]] = {}

    # Common citation cleaning regex pattern (includes TH/THI)
    citation_pattern = r"\b(DN|MN|SN|AN|Snp|Dhp|Ud|Iti|Vv|Pv|Thag|Thig|Ap|Bv|Cp|Ja|Kh|Vin|Pāc|Pār|Mv|Cv|Pari|Vibh|Dhs|Pug|Kvu|Yam|Patth|Vism|TH|THI)\s?\d*(?:\.\d+)*(?:-\d+)?\b"
    # Binomial scientific name cleaning pattern (e.g. Calotropis gigantea, aconitum ferox)
    binomial_pattern = r"\b[a-zA-ZāīūṭḍṇñṅḷṃśṣĀĪŪṬḌṆÑṄḶṂŚṢ]+\s+[a-z][a-zA-ZāīūṭḍṇñṅḷṃśṣĀĪŪṬḌṆÑṄḶṂŚṢ]*\b"

    def audit_field(
        text: str, field_label: str, eng_length: int, is_sutta_entry: bool
    ) -> list[str]:
        field_flags = []
        if not text:
            return field_flags

        if HANGUL_PATTERN.search(text):
            field_flags.append(f"Hangul in {field_label}")

        if is_sutta_entry:
            # Sutta entries (family_set starting with "suttas of") are citation references,
            # so they are allowed to contain Latin (SN, MN, etc.) and have longer descriptions.
            return field_flags

        # Check if the entry is grammatical - if so, skip Latin check
        is_grammatical = bool(
            re.search(r"\b(gram|грам|грамм|grammar)\b", text, flags=re.IGNORECASE)
        )

        flagged_tokens = []
        if not is_grammatical:
            # 1. Clean citations, roots (e.g., √kit), and binomial scientific names
            cleaned = re.sub(citation_pattern, "", text, flags=re.IGNORECASE)
            cleaned = re.sub(r"√[a-zA-ZāīūṭḍṇñṅḷṃśṣĀĪŪṬḌṆÑṄḶṂŚṢ]+", "", cleaned)
            cleaned = re.sub(binomial_pattern, "", cleaned)

            # 2. Extract Latin/IAST word tokens of length >= 3
            tokens = re.findall(r"\b[a-zA-ZāīūṭḍṇñṅḷṃśṣĀĪŪṬḌṆÑṄḶṂŚṢ]{3,}\b", cleaned)
            for token in tokens:
                t_lower = token.lower()
                if t_lower in english_words and t_lower not in PALI_STOPWORDS:
                    flagged_tokens.append(token)

        if flagged_tokens:
            field_flags.append(f"Latin words in {field_label}: {flagged_tokens}")

        # 3. Check for ratio-based length checks
        ratio = len(text) / eng_length if eng_length > 0 else 999.0
        if len(text) > 120 and ratio > 3.0:
            field_flags.append(f"{field_label} is unusually long (ratio {ratio:.1f}x)")

        return field_flags

    for row in results:
        flags: list[str] = []
        meaning_lines: list[str] = []
        eng_meaning = row.meaning_1 or row.meaning_2 or ""
        eng_len = len(eng_meaning)
        is_sutta_entry = bool(row.family_set and row.family_set.startswith("suttas of"))

        if lang == "ta":
            ta_meaning = row.ta.ta_meaning
            flags.extend(audit_field(ta_meaning, "ta_meaning", eng_len, is_sutta_entry))
            meaning_lines.append(f"ta_meaning     : {ta_meaning}")

        elif lang == "ru":
            ru_info = row.ru
            # Check ru_meaning_raw only (raw AI translation output)
            if ru_info.ru_meaning_raw:
                raw_flags = audit_field(
                    ru_info.ru_meaning_raw,
                    "ru_meaning_raw",
                    eng_len,
                    is_sutta_entry,
                )
                if raw_flags:
                    flagged_columns.setdefault(row.id, []).append("ru_meaning_raw")
                flags.extend(raw_flags)
                meaning_lines.append(f"ru_meaning_raw : {ru_info.ru_meaning_raw}")

        if flags:
            status = f"FLAGGED ({', '.join(flags)})"
            flagged_ids.append(row.id)
            pr.white(f"ID: {row.id} | Lemma: {row.lemma_1} | Status: {status}")
            pr.white(f"   English Meaning: {eng_meaning}")
            for line in meaning_lines:
                pr.white(f"   {line}")
            pr.white("")

    pr.white("-" * 60)
    pr.white(
        f"Validation complete: {len(flagged_ids)} flagged out of {len(results)} entries."
    )

    if flagged_ids:
        do_delete = auto_delete
        if not do_delete and sys.stdin.isatty():
            try:
                choice = (
                    input(
                        f"\nDo you want to delete these {len(flagged_ids)} flagged entries from the database? (y/n): "
                    )
                    .strip()
                    .lower()
                )
                if choice in ("y", "yes"):
                    do_delete = True
            except KeyboardInterrupt:
                pr.amber("Operation cancelled.")

        if do_delete:
            deleted_count = 0
            for row_id in flagged_ids:
                if lang == "ta":
                    db_session.query(Tamil).filter(Tamil.id == row_id).delete()
                    deleted_count += 1
                elif lang == "ru":
                    ru_row = (
                        db_session.query(Russian).filter(Russian.id == row_id).first()
                    )
                    if ru_row:
                        for column in flagged_columns.get(row_id, []):
                            setattr(ru_row, column, "")
                        deleted_count += 1
            db_session.commit()
            pr.green(
                f"Successfully deleted/cleaned {deleted_count} entries from the database."
            )

    return flagged_ids


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser (default language: ru)."""
    parser = argparse.ArgumentParser(
        description="Verify Tamil or Russian translation database entries."
    )
    parser.add_argument(
        "-lang",
        "--lang",
        choices=["ta", "ru"],
        default="ru",
        help="Language to check: 'ta' for Tamil, 'ru' for Russian (default: ru).",
    )
    parser.add_argument(
        "-ids",
        "--ids",
        type=int,
        nargs="+",
        help="Specific entry IDs to check (ignores JSON state file).",
    )
    parser.add_argument(
        "--ids-file",
        type=Path,
        help="JSON file of ids to check: {lang, mode, ids} or a bare list "
        "(e.g. temp/ai_from_batch_api/processed_ids.json).",
    )
    parser.add_argument(
        "-delete",
        "--delete",
        action="store_true",
        help="Automatically delete the flagged entries from the database without prompting.",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    check_translations(
        lang=args.lang,
        specific_ids=args.ids,
        auto_delete=args.delete,
        ids_file=args.ids_file,
    )
