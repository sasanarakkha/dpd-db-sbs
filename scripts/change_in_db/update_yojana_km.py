#!/usr/bin/env python3

"""Update all yojana-related distance measurements in the DPD database."""

# ruff: noqa: E402

NEW_KM_PER_YOJANA = 14
DRY_RUN = False

import re
from typing import cast

from num2words import num2words
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Russian
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def words_to_num(phrase: str) -> int:
    """Convert an English word-number phrase to an integer."""
    phrase = phrase.lower().replace("-", " ").strip()
    words = [w for w in phrase.split() if w != "and"]

    units = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
    }

    multipliers = {
        "hundred": 100,
        "thousand": 1_000,
        "million": 1_000_000,
        "billion": 1_000_000_000,
    }

    total = 0
    current = 0

    for word in words:
        if word in units:
            current += units[word]
        elif word in multipliers:
            if word == "hundred":
                current = (current or 1) * multipliers[word]
            else:
                total += (current or 1) * multipliers[word]
                current = 0

    return total + current


def recalculate_meaning_en(meaning: str, old_base: int, new_base: int) -> str:
    """Replace English word-number km values using the given ratio."""
    WORDS = (
        r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
        r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
        r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|"
        r"million|billion|and"
    )
    PHRASE = rf"(?:(?:{WORDS})[\s-]+)*(?:{WORDS})"

    # Combined pattern: optionally handle range, otherwise single
    PATTERN = re.compile(
        rf"\b({PHRASE})\s+(?:to\s+({PHRASE})\s+)?(kilometres?)\b", re.IGNORECASE
    )

    def replace_match(match):
        p1 = match.group(1)
        p2 = match.group(2)
        unit = match.group(3)

        n1 = words_to_num(p1)
        v1 = num2words(round(n1 * new_base / old_base)).replace(",", "")

        if p2:
            n2 = words_to_num(p2)
            v2 = num2words(round(n2 * new_base / old_base)).replace(",", "")
            return f"{v1} to {v2} {unit}"
        else:
            return f"{v1} {unit}"

    return PATTERN.sub(replace_match, meaning)


def _format_ru_km_value(km: int) -> str:
    """Format Russian km value (number + scale suffix, no км suffix)."""

    def _ru_thousand_form(n: int) -> str:
        """Return correct Russian form for thousands based on number agreement."""
        last_two = n % 100
        last_one = n % 10
        if 11 <= last_two <= 19:
            return "тысяч"
        elif last_one == 1:
            return "тысяча"
        elif 2 <= last_one <= 4:
            return "тысячи"
        else:
            return "тысяч"

    if km >= 1_000_000:
        val = km / 1_000_000
        formatted = f"{val:.3f}".rstrip("0").rstrip(".")
        return f"{formatted} миллиона"
    elif km >= 1_000:
        val = km / 1_000
        formatted = f"{val:.1f}".rstrip("0").rstrip(".")
        if km % 1000 == 0:
            form = _ru_thousand_form(int(val))
        else:
            form = "тысячи"
        return f"{formatted} {form}"
    else:
        return str(km)


def format_ru_km(km: int) -> str:
    """Format Russian km value with scale suffixes (тысячи, миллиона) and км."""
    return f"{_format_ru_km_value(km)} км"


def recalculate_meaning_ru(meaning: str, old_base: int, new_base: int) -> str:
    """Replace Russian km phrases with the standard 'примерно N км' format."""
    RU_WORD_TO_NUM: dict[str, int] = {
        # genitive forms
        "семи": 7,
        "десяти": 10,
        "двадцати": 20,
        "сорока": 40,
        "шестидесяти": 60,
        "восьмидесяти": 80,
        "ста": 100,
        "ста сорока": 140,
        "двухсот": 200,
        "двухсот сорока": 240,
        "трёхсот": 300,
        "четырёхсот": 400,
        "тысячи": 1000,
        "двух тысяч": 2000,
        "четырёх тысяч": 4000,
        "шести тысяч": 6000,
        "восьми тысяч": 8000,
        "двадцати тысяч": 20000,
        "сорока тысяч": 40000,
        # nominative forms
        "семь": 7,
        "десять": 10,
        "двадцать": 20,
        "сорок": 40,
        "шестьдесят": 60,
        "восемьдесят": 80,
        "сто": 100,
        "сто двадцать": 120,
        "сто сорок": 140,
        "сто пятьдесят": 150,
        "двести": 200,
        "двести сорок": 240,
        "триста": 300,
        "триста двадцать": 320,
        "тысяча": 1000,
        "тысяча двести": 1200,
        "две тысячи": 2000,
        "две тысячи четыреста": 2400,
        "три тысячи": 3000,
        "четыре тысячи": 4000,
        "пять тысяч": 5000,
        "шесть тысяч": 6000,
        "восемь тысяч": 8000,
        "десять тысяч": 10000,
        "двенадцать тысяч": 12000,
        "двадцать тысяч": 20000,
        "сорок тысяч": 40000,
        "двести тысяч": 200000,
        "один миллион шестьсот восемьдесят тысяч": 1680000,
        "один миллиард триста шестьдесят миллионов": 1360000000,
    }

    RU_PREFIX_WORDS = r"примерно|приблизительно|около"

    sorted_keys = sorted(RU_WORD_TO_NUM.keys(), key=len, reverse=True)
    RU_PHRASE = r"(" + "|".join(re.escape(k) for k in sorted_keys) + r")"

    # Pass 1: Digits
    DIGIT_KM_RU = re.compile(
        rf"\b(?:(?:{RU_PREFIX_WORDS})\s+)*(\d+)\s*(?:км|километр\w*)", re.IGNORECASE
    )

    def replace_digit(match):
        old_km = int(match.group(1))
        new_km = round(old_km * new_base / old_base)
        return f"примерно {format_ru_km(new_km)}"

    meaning = DIGIT_KM_RU.sub(replace_digit, meaning)

    # Pass 2: Word Ranges
    RU_RANGE_PATTERN = re.compile(
        rf"\b(?:(?:{RU_PREFIX_WORDS})\s+)*{RU_PHRASE}\s+(?:до|или|и)\s+{RU_PHRASE}\s*(?:км|километр\w*)",
        re.IGNORECASE,
    )

    def replace_ru_range(match):
        p1, p2 = match.group(1).lower(), match.group(2).lower()
        v1 = round(RU_WORD_TO_NUM[p1] * new_base / old_base)
        v2 = round(RU_WORD_TO_NUM[p2] * new_base / old_base)
        fmt1 = _format_ru_km_value(v1)
        fmt2 = _format_ru_km_value(v2)
        return f"примерно {fmt1}–{fmt2} км"

    meaning = RU_RANGE_PATTERN.sub(replace_ru_range, meaning)

    # Pass 3: Single Words
    ru_word_pattern = re.compile(
        rf"\b(?:(?:{RU_PREFIX_WORDS})\s+)*{RU_PHRASE}\s*(?:км|километр\w*)",
        re.IGNORECASE,
    )

    def replace_word(match):
        phrase = match.group(1).lower()
        new_km = round(RU_WORD_TO_NUM[phrase] * new_base / old_base)
        return f"примерно {format_ru_km(new_km)}"

    meaning = ru_word_pattern.sub(replace_word, meaning)

    return meaning


def detect_current_base(db_session: Session) -> int:
    """Auto-detect km-per-yojana from 'yojana 1'.meaning_1."""
    entry = (
        db_session.query(DpdHeadword).filter(DpdHeadword.lemma_1 == "yojana 1").first()
    )
    if not entry:
        raise ValueError("'yojana 1' not found in database")

    # Extract km phrase from meaning_1 (English column)
    # Pattern: "approximately X kilometres"
    match = re.search(
        r"approximately\s+([\w\s-]+)\s+kilometres?", entry.meaning_1, re.IGNORECASE
    )
    if not match:
        raise ValueError(f"Cannot parse km value from: {entry.meaning_1!r}")

    return words_to_num(match.group(1))


def find_entries(db_session: Session) -> list[tuple[DpdHeadword, Russian | None]]:
    """Return all yojana distance entries with their Russian rows (if any)."""
    rows = (
        db_session.query(DpdHeadword, Russian)
        .outerjoin(Russian, Russian.id == DpdHeadword.id)
        .filter(
            DpdHeadword.lemma_1.like("%yojana%"),
            or_(
                and_(
                    DpdHeadword.meaning_1 != "",
                    DpdHeadword.meaning_1.like("%kilometre%"),
                ),
                and_(
                    DpdHeadword.meaning_1 == "",
                    DpdHeadword.meaning_2.like("%kilometre%"),
                ),
            ),
        )
        .order_by(DpdHeadword.lemma_1)
        .all()
    )
    return cast(list[tuple[DpdHeadword, Russian | None]], rows)


def main() -> None:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    try:
        current_base = detect_current_base(db_session)
    except Exception as e:
        pr.no(str(e))
        return

    pr.green(f"Current standard: 1 yojana = {current_base} km")
    pr.green(f"New standard:     1 yojana = {NEW_KM_PER_YOJANA} km")

    if current_base == NEW_KM_PER_YOJANA:
        pr.yes("No conversion needed — database is already at the target standard")
        db_session.close()
        return

    entries = find_entries(db_session)
    pr.green(f"Entries to update: {len(entries)}")
    pr.green("")

    # Phase 1: Collect all changes (don't apply yet)
    changes: list[tuple[DpdHeadword, Russian | None, dict[str, tuple[str, str]]]] = []

    for hw, ru in entries:
        entry_changes: dict[str, tuple[str, str]] = {}

        # --- English ---
        en_col = "meaning_1" if hw.meaning_1 else "meaning_2"
        old_en = getattr(hw, en_col)
        new_en = recalculate_meaning_en(old_en, current_base, NEW_KM_PER_YOJANA)

        if new_en != old_en:
            entry_changes[en_col] = (old_en, new_en)

        # --- Russian ---
        if ru is not None:
            for ru_col in ("ru_meaning", "ru_meaning_raw"):
                old_ru = getattr(ru, ru_col)
                if not old_ru:
                    continue
                new_ru = recalculate_meaning_ru(old_ru, current_base, NEW_KM_PER_YOJANA)
                if new_ru != old_ru:
                    entry_changes[ru_col] = (old_ru, new_ru)

        if entry_changes:
            changes.append((hw, ru, entry_changes))

    # Phase 2: Print all changes
    for hw, ru, entry_changes in changes:
        for col, (old_val, new_val) in entry_changes.items():
            if col in ("meaning_1", "meaning_2"):
                pr.amber(f"{hw.lemma_1} [{col}]")
            else:
                pr.amber(f"{hw.lemma_1} [{col}]")
            pr.amber(f"  OLD: {old_val}")
            pr.green(f"  NEW: {new_val}")

    pr.green("")
    changed_count = len(changes)

    # Phase 3: Ask for confirmation
    if DRY_RUN:
        pr.no(f"DRY RUN — {changed_count} entries would be updated, no changes written")
        db_session.close()
        return

    pr.amber(f"READY TO COMMIT: {changed_count} entries")
    response = input("Proceed? (yes/no): ").strip().lower()

    if response not in ("yes", "y"):
        pr.amber("Update cancelled. No changes written to database.")
        db_session.close()
        return

    # Phase 4: Apply changes and commit
    for hw, ru, entry_changes in changes:
        for col, (old_val, new_val) in entry_changes.items():
            if col in ("meaning_1", "meaning_2"):
                setattr(hw, col, new_val)
            else:
                setattr(ru, col, new_val)

    db_session.commit()
    pr.yes(f"{changed_count} entries updated and committed to database")
    db_session.close()


if __name__ == "__main__":
    main()
