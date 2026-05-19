"""Fills SBS.dhp_example from AI verse analysis, bolding the matched word form."""

import argparse
import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, SBS
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.speech_marks import SpeechMarkManager
from tools.speech_marks_replacement import replace_speech_marks


def strip_bold_tags(text: str) -> str:
    """Remove <b> and </b> tags from text."""
    return re.sub(r"</?b>", "", text)


def find_token_in_apos_verse(token: str, verse: str) -> str:
    """Find the apostrophe-containing form of a token as it appears in the verse.

    Scans the verse ignoring apostrophe characters to match the token, then returns
    the corresponding substring which may include apostrophes.
    """
    n = len(verse)
    tok_len = len(token)
    for start in range(n):
        j = 0
        k = start
        while k < n and j < tok_len:
            if verse[k] == "'":
                k += 1
                continue
            if verse[k] == token[j]:
                j += 1
                k += 1
            else:
                break
        if j == tok_len:
            return verse[start:k]
    return token


def bold_component_in_token(
    apos_token: str,
    component_pali: str,
    headword_id: int,
    db_session: Session,
    is_first_component: bool = False,
) -> str:
    """Bold component_pali within apos_token using actual inflections from DpdHeadword.

    For first component of a compound: bold only the component itself.
    For later components: bold from component start to end of token.

    Strategy (in order):
    0. Exact match wins — component_pali directly found in apos_token.
    1. Try any inflection from DpdHeadword(headword_id).inflections; bold appropriately.
    2. For sandhi (apostrophe in token): bold left or right side.
    3. Direct substring match.
    4. Fallback: bold the whole token.
    """
    # 0. Exact match wins — prioritise the headword's own form over inflections
    if component_pali in apos_token:
        if "'" in apos_token:
            left, _, right = apos_token.partition("'")
            if component_pali in left:
                idx = left.index(component_pali)
                return left[:idx] + "<b>" + left[idx:] + "</b>'" + right
            else:
                idx = right.index(component_pali)
                return left + "'<b>" + right[:idx] + component_pali + "</b>"
        else:
            idx = apos_token.index(component_pali)
            if is_first_component:
                return (
                    apos_token[:idx]
                    + "<b>"
                    + component_pali
                    + "</b>"
                    + apos_token[idx + len(component_pali) :]
                )
            else:
                return apos_token[:idx] + "<b>" + apos_token[idx:] + "</b>"

    # 1. Try inflections from database
    try:
        headword = db_session.query(DpdHeadword).filter_by(id=headword_id).first()
        if headword:
            inflections = headword.inflections_list
            if inflections:
                # Search for any inflection in the token
                for inflection in inflections:
                    if inflection in apos_token:
                        # Handle sandhi: if apostrophe exists, bold only the relevant part
                        if "'" in apos_token:
                            left, _, right = apos_token.partition("'")
                            if inflection in left:
                                idx = left.index(inflection)
                                return left[:idx] + "<b>" + left[idx:] + "</b>'" + right
                            else:
                                idx = right.index(inflection)
                                return left + "'<b>" + right[:idx] + inflection + "</b>"
                        else:
                            # No sandhi: for first component, bold exact inflection; otherwise bold to end
                            idx = apos_token.index(inflection)
                            if is_first_component:
                                return (
                                    apos_token[:idx]
                                    + "<b>"
                                    + inflection
                                    + "</b>"
                                    + apos_token[idx + len(inflection) :]
                                )
                            else:
                                return (
                                    apos_token[:idx] + "<b>" + apos_token[idx:] + "</b>"
                                )
    except Exception:
        pass  # Fall back to heuristics if DB lookup fails

    # 2. Direct match (fallback if inflections not found)
    if component_pali in apos_token:
        # For first component, bold only the exact component; otherwise bold to end
        if is_first_component:
            return apos_token.replace(component_pali, f"<b>{component_pali}</b>", 1)
        else:
            idx = apos_token.index(component_pali)
            return apos_token[:idx] + "<b>" + apos_token[idx:] + "</b>"

    # 3. Strip final ṃ and try
    pali_no_m = component_pali.rstrip("ṃ")
    if len(pali_no_m) > 1 and pali_no_m in apos_token:
        # For first component, bold only the stripped form; otherwise bold to end
        if is_first_component:
            return apos_token.replace(pali_no_m, f"<b>{pali_no_m}</b>", 1)
        else:
            idx = apos_token.index(pali_no_m)
            return apos_token[:idx] + "<b>" + apos_token[idx:] + "</b>"

    # 4. Stem match: strip trailing short vowel, bold from stem position
    stem = component_pali.rstrip("aāiīuūeo")
    if len(stem) > 1 and stem in apos_token:
        idx = apos_token.index(stem)
        if is_first_component:
            # For first component, bold only up to len(component_pali)
            end = min(idx + len(component_pali), len(apos_token))
            return (
                apos_token[:idx]
                + "<b>"
                + apos_token[idx:end]
                + "</b>"
                + apos_token[end:]
            )
        else:
            # For later component, bold to end of token
            return apos_token[:idx] + "<b>" + apos_token[idx:] + "</b>"

    # 5. Apostrophe-split: bold left or right side
    if "'" in apos_token:
        left, _, right = apos_token.partition("'")
        pali_norm = pali_no_m.rstrip("aāiīuūeo")
        if pali_norm and (left.startswith(pali_norm) or pali_norm.startswith(left)):
            return f"<b>{left}</b>'{right}"
        return f"{left}'<b>{right}</b>"

    # 6. Fallback: bold whole token
    return f"<b>{apos_token}</b>"


def bold_word_toplevel(apos_token: str) -> str:
    """Bold the entire token for a top-level (non-component) word."""
    return f"<b>{apos_token}</b>"


def bold_word_in_verse(
    verse_text: str,
    apos_token: str,
    component_pali: str,
    headword_id: int,
    db_session: Session,
    is_first_component: bool = False,
    is_top_level: bool = False,
) -> str:
    """Bold component_pali in apos_token, then replace apos_token in verse_text."""
    if is_top_level:
        bolded_token = bold_word_toplevel(apos_token)
    else:
        bolded_token = bold_component_in_token(
            apos_token, component_pali, headword_id, db_session, is_first_component
        )
    escaped_token = re.escape(apos_token)
    pattern = rf"(?<![a-zA-Zāīūḍḷṅñṇṃśṣ])({escaped_token})(?![a-zA-Zāīūḍḷṅñṇṃśṣ])"
    return re.sub(pattern, bolded_token, verse_text)


def collect_all_ids(
    option: dict[str, Any], word_in_verse: str, component_index: int = 0, depth: int = 0
) -> list[tuple[int, str, str, bool, bool]]:
    """Recursively collect (headword_id, component_pali, word_in_verse, is_first_component, is_top_level) from an option tree.

    Traverses all nested components. Skips decon_ keys and empty IDs at every level.
    is_first_component is True if this component is the first in a child compound (depth > 0 and component_index == 0).
    is_top_level is True for entries at depth=0 (standalone top-level words, not compound parts).
    """
    results: list[tuple[int, str, str, bool, bool]] = []

    hw_id = option.get("id")
    key = option.get("key", "")
    pali = option.get("pali", word_in_verse)

    # Only set is_first=True for first component of child compounds, not top-level
    is_first = component_index == 0 and depth > 0
    is_top_level = depth == 0
    if hw_id and not key.startswith("decon_"):
        results.append((int(hw_id), pali, word_in_verse, is_first, is_top_level))

    should_recurse = (
        option.get("compound_type", "")
        or option.get("pos", "") in {"sandhi", "sandhi/compound"}
        or key.startswith("decon_")
    )
    if should_recurse:
        components_list = option.get("components", [])
        for i, comp_list in enumerate(components_list):
            if not comp_list:
                continue
            best_comp = max(comp_list, key=lambda x: x.get("ai_score", 0))
            results.extend(
                collect_all_ids(
                    best_comp, word_in_verse, component_index=i, depth=depth + 1
                )
            )

    return results


def _apply_apos_fallback(text: str, smm: SpeechMarkManager) -> str:
    """Apply apostrophes via speech_marks; take first variant for multi-variant words."""
    text = replace_speech_marks(text, smm)
    # replace_speech_marks joins multi-variant words with //; take first variant
    text = re.sub(r"([^/ \n\t]+)(?://[^/ \n\t]+)+", r"\1", text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fill SBS.dhp_example from AI analysis."
    )
    parser.add_argument("--book", required=True, help="CST book code (e.g., kn2)")
    parser.add_argument("--verse", help="Process a specific verse only (e.g., DHP1)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show proposed changes without committing",
    )
    parser.add_argument("--limit", type=int, help="Limit number of verses to process")
    args = parser.parse_args()

    book = args.book
    analysis_path = Path("exporter/mcp/output") / f"{book}_analysis.json"

    if not analysis_path.exists():
        pr.no(f"Analysis file not found: {analysis_path}")
        return

    with open(analysis_path, encoding="utf-8") as f:
        all_analysis: list[dict[str, Any]] = json.load(f)

    if args.verse:
        analysis_results = [v for v in all_analysis if v["num"] == args.verse]
        if not analysis_results:
            pr.no(f"Verse '{args.verse}' not found in {analysis_path}")
            return
    elif args.limit:
        analysis_results = all_analysis[: args.limit]
    else:
        analysis_results = all_analysis

    paths = ProjectPaths()
    db_session: Session = get_db_session(paths.dpd_db_path)
    speech_marks_manager = SpeechMarkManager(paths)

    try:
        sbs_map: dict[int, SBS] = {sbs.id: sbs for sbs in db_session.query(SBS).all()}

        filled_count = 0
        skipped_count = 0

        for verse in analysis_results:
            dhp_source: str = verse["num"]
            dhp_sutta: str = verse["vagga"]

            # Use verse_text from analysis JSON (set by ai_batch_translate, has apostrophes);
            # fall back to applying speech_marks to the raw CST text for older analysis entries.
            verse_text: str = verse.get("verse_text") or _apply_apos_fallback(
                verse["text"], speech_marks_manager
            )

            pr.green(f"Processing {dhp_source}...")

            updated_in_verse: set[int] = set()

            for token_data in verse.get("analysis", []):
                word = token_data.get("word", "")
                options: list[dict[str, Any]] = token_data.get("data", [])
                if not options:
                    continue

                best_option = max(options, key=lambda x: x.get("ai_score", 0))
                all_entries = collect_all_ids(best_option, word)

                # Locate this token's apostrophe form in the verse text
                apos_word = find_token_in_apos_verse(word, verse_text)

                for (
                    headword_id,
                    component_pali,
                    _word_in_verse,
                    is_first_component,
                    is_top_level,
                ) in all_entries:
                    if headword_id in updated_in_verse:
                        skipped_count += 1
                        continue

                    if component_pali not in apos_word.replace("'", ""):
                        skipped_count += 1
                        continue

                    sbs = sbs_map.get(headword_id)
                    if sbs and sbs.dhp_example and sbs.dhp_example.strip():
                        skipped_count += 1
                        updated_in_verse.add(headword_id)
                        continue

                    example = bold_word_in_verse(
                        verse_text,
                        apos_word,
                        component_pali,
                        headword_id,
                        db_session,
                        is_first_component,
                        is_top_level,
                    )

                    if args.dry_run:
                        pr.yes(
                            f"  [DRY-RUN] ID {headword_id} '{component_pali}': {dhp_source}"
                        )
                        for line in example.splitlines():
                            pr.yes(f"    {line}")
                    else:
                        if not sbs:
                            sbs = SBS(id=headword_id)
                            db_session.add(sbs)
                            sbs_map[headword_id] = sbs

                        sbs.dhp_source = dhp_source
                        sbs.dhp_sutta = dhp_sutta
                        sbs.dhp_example = example
                        filled_count += 1

                    updated_in_verse.add(headword_id)

            if not args.dry_run:
                db_session.commit()

        pr.yes(f"Finished. Filled: {filled_count}, Skipped: {skipped_count}")

    except Exception as e:
        pr.no(f"An error occurred: {e}")
        db_session.rollback()
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
