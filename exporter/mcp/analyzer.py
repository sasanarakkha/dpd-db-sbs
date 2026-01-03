import re
from typing import Any
from sqlalchemy.orm import Session
from db.models import DpdHeadword, Lookup
from tools.pali_alphabet import pali_alphabet
from tools.clean_machine import clean_machine

suffixes = {
    "tta"
    "tā"
    "a"
    "ā"
    "ika"
    "aka"
    "ikā"
    "ī"
    "ka"
    "aṃ"
    "ana"
    "āni"
    "o"
    "e"
    "ūni"
    "ya"
    "ena"
    "u"
    "ū"
    "āya"
    "iya"
    "*tta"
    "*tā"
    "*a"
    "*ā"
    "*ika"
    "*aka"
    "*ikā"
    "*ī"
    "*ka"
    "*aṃ"
    "*ana"
    "*āni"
    "*o"
    "*e"
    "*ūni"
    "*ya"
    "*ena"
    "*u"
    "*ū"
    "*āya"
    "*iya"
}


def tokenize_sentence(sentence: str) -> list[str]:
    """Tokenize a Pāḷi sentence and normalize to lowercase using valid Pāḷi characters."""
    pali_chars = set()
    for item in pali_alphabet:
        for char in item:
            pali_chars.add(char)
    pali_chars.add(" ")

    sentence = sentence.lower()
    sentence = clean_machine(sentence)
    clean_chars = [char if char in pali_chars else " " for char in sentence]
    clean_sentence = "".join(clean_chars)

    tokens = [token for token in clean_sentence.split() if token]
    return tokens


def get_word_details(
    token: str, db_session: Session, from_construction: bool = False
) -> list[dict[str, Any]]:
    """Helper to get word details for a given token, generating specific options based on lookup grammar."""
    lookup_entry = db_session.query(Lookup).filter(Lookup.lookup_key == token).first()
    if not lookup_entry or not lookup_entry.headwords:
        return []

    headword_ids = lookup_entry.headwords_unpack
    headwords = (
        db_session.query(DpdHeadword).filter(DpdHeadword.id.in_(headword_ids)).all()
    )

    grammar_list = lookup_entry.grammar_unpack if lookup_entry.grammar else []

    word_details = []
    for hw in headwords:
        # Check for specific grammar matches in the lookup entry
        matched_grammar = False

        # We need to match the Headword to the Grammar entry.
        # Usually matching by lemma_1 is safest.
        if grammar_list:
            for i, (g_lemma, g_pos, g_gram) in enumerate(grammar_list):
                if (
                    g_lemma == hw.lemma_clean
                    and "-" not in hw.stem
                    and "!" not in hw.stem
                    and "(gram)" not in hw.meaning_1
                ):
                    matched_grammar = True
                    entry = {
                        "key": f"{hw.id}_{i}",  # Unique key for this specific inflection option
                        "id": hw.id,
                        "lemma_1": token if from_construction else hw.lemma_1,
                        "pos": g_pos,  # Use specific pos
                        "grammar": g_gram,  # Use specific grammar
                        "meaning_combo": hw.meaning_combo,
                        "compound_type": hw.compound_type,
                        "root_key": root_combo(hw),
                        "construction": hw.construction_line1_clean,
                        "components": [],
                    }
                    if (
                        ("comp" in hw.grammar and "in comp" not in hw.grammar)
                        or "sandhi" in hw.grammar
                    ) and not hw.root_key:
                        entry["components"] = get_components_from_construction(
                            hw.construction_line1_clean, db_session
                        )

                    word_details.append(entry)

        # Fallback: if no specific grammar matched (or list empty), use generic headword data
        if not matched_grammar:
            entry = {
                "key": f"{hw.id}_default",
                "id": hw.id,
                "lemma_1": hw.lemma_1,
                "pos": hw.pos,
                "grammar": hw.grammar,
                "meaning_combo": hw.meaning_combo,
                "compound_type": hw.compound_type,
                "root_key": root_combo(hw),
                "construction": hw.construction_line1_clean,
                "components": [],
            }

            if (
                ("comp" in hw.grammar and "in comp" not in hw.grammar)
                or "sandhi" in hw.grammar
            ) and not hw.root_key:
                entry["components"] = get_components_from_construction(
                    hw.construction_line1_clean, db_session
                )

            word_details.append(entry)

    return word_details


def get_components_from_construction(
    construction: str, db_session: Session
) -> list[dict[str, Any]]:
    """Helper to break down a construction string into component details."""
    components = []
    parts = construction.split(" + ")
    for part in parts:
        if part not in suffixes:
            # Fetch details for the part
            part_details_list = get_word_details(
                part, db_session, from_construction=True
            )
            if part_details_list:
                # We need to save all possible option so AI can pick which is better
                components.append(part_details_list)
            else:
                # If no details found, just add the word itself as a placeholder (wrapped in a list)
                components.append(
                    [
                        {
                            "key": f"missing_{part}",
                            "id": "",
                            "lemma_1": part,
                            "pos": "",
                            "grammar": "in comp",
                            "meaning_combo": "",
                            "construction": "",
                        }
                    ]
                )
    return components


def analyze_sentence(sentence: str, db_session: Session) -> list[dict[str, Any]]:
    """Analyze a Pāḷi sentence and return grammatical details for each word, including components."""
    tokens = tokenize_sentence(sentence)
    results = []

    for token in tokens:
        lookup_entry = (
            db_session.query(Lookup).filter(Lookup.lookup_key == token).first()
        )

        word_data = []
        status = "not_found"

        # TODO think of the way how to identify and make use of idioms

        if lookup_entry:
            # 0. Check for api ca iti etc
            if (
                lookup_entry.headwords
                and lookup_entry.deconstructor
                and any(
                    decon.count(" + ") == 1
                    and re.search(
                        r" \+ (api|ca|eva|iti|iva|hi)$", re.sub(r" \[.+", "", decon)
                    )
                    for decon in lookup_entry.deconstructor_unpack
                )
            ):
                decons = lookup_entry.deconstructor_unpack
                for i, decon in enumerate(decons):
                    entry = {
                        "key": f"decon_{token}_{i}",
                        "id": "",
                        "lemma_1": token,
                        "pos": "sandhi",
                        "grammar": "sandhi/compound",
                        "meaning_combo": "[AI_meaning]",
                        "compound_type": "",
                        "root_key": "",
                        "construction": decon,
                        "components": get_components_from_construction(
                            decon, db_session
                        ),
                    }
                    word_data.append(entry)

                status = "found"

            # 1. Check for Headwords
            elif lookup_entry.headwords:
                # Re-use get_word_details which now handles grammar unpacking
                word_data = get_word_details(token, db_session)
                status = "found" if word_data else "not_found"

            # 2. If no headwords, check Deconstructor
            elif lookup_entry.deconstructor:
                decons = lookup_entry.deconstructor_unpack
                for i, decon in enumerate(decons):
                    entry = {
                        "key": f"decon_{token}_{i}",
                        "id": "",
                        "lemma_1": token,
                        "pos": "sandhi",
                        "grammar": "sandhi/compound",
                        "meaning_combo": "[Deconstructed]",
                        "compound_type": "",
                        "root_key": "",
                        "construction": decon,
                        "components": get_components_from_construction(
                            decon, db_session
                        ),
                    }
                    word_data.append(entry)

                status = "found"

        results.append({"word": token, "status": status, "data": word_data})

    return results


def root_combo(i: DpdHeadword):
    # uniting root info into one line
    root_combo = ""
    if i.rt:
        root_combo = (
            f"{i.root_clean} {i.rt.root_group} {i.root_sign} ({i.rt.root_meaning})"
        )
    return root_combo
