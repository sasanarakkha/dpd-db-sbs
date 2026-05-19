#!/usr/bin/env python
"""
Two-phase resumable script: extract DHP word forms, fill missing SBS.dhp_example via AI.
Phase 1: Extract unique words from kn2 (Dhammapada), identify headwords with missing dhp_example.
Phase 2: For each missing headword, use AI to pick best DHP verse and fill SBS.dhp_example.
"""

import json
import re
import ast
import argparse

from db.db_helpers import get_db_session
from db.models import Lookup, SBS, DpdHeadword
from tools.paths import ProjectPaths
from tools.cst_sc_text_sets import make_cst_text_list
from tools.cst_source_sutta_example import find_cst_source_sutta_example
from tools.ai_manager import AIManager
from tools.printer import printer as pr


def make_decon_word_list(deconstruction: list[str]) -> list[str]:
    """Mirror gui2 deconstructor word splitting."""
    word_list: list[str] = []
    for deconstruction_item in deconstruction:
        words = deconstruction_item.split(" + ")
        for word in words:
            word_list.append(word.strip())
    return sorted(set(word_list), key=lambda x: word_list.index(x))


def resolve_lookup(lookup_dict: dict[str, Lookup], word: str) -> list[int]:
    """Resolve a word to headword IDs using Lookup table."""
    item = lookup_dict.get(word)
    if not item:
        return []
    if item.headwords_unpack:
        return list(item.headwords_unpack)
    if not item.deconstructor_unpack:
        return []
    ids: list[int] = []
    for part in make_decon_word_list(item.deconstructor_unpack):
        ids.extend(resolve_lookup(lookup_dict, part))
    return ids


def phase_1_extract(
    session, paths: ProjectPaths
) -> tuple[set[int], dict[int, list[str]]]:
    """
    Phase 1: Extract words from kn2, resolve to headword IDs, identify missing dhp_example.
    Returns: (missing_ids, id_to_words)
    """
    pr.cyan("PHASE 1: Extract missing headwords")

    # Extract words from kn2
    words = make_cst_text_list(["kn2"])
    pr.yes(f"Extracted {len(words)} unique words from kn2")

    unique_words = list(set(words))

    # Bulk fetch Lookup rows
    lookup_dict: dict[str, Lookup] = {
        r.lookup_key: r
        for r in session.query(Lookup).filter(Lookup.lookup_key.in_(unique_words)).all()
    }
    pr.yes(f"Found {len(lookup_dict)} Lookup rows")

    # Load decon parts
    extra_keys: set[str] = set()
    for r in lookup_dict.values():
        if not r.headwords_unpack and r.deconstructor_unpack:
            for part in make_decon_word_list(r.deconstructor_unpack):
                if part not in lookup_dict:
                    extra_keys.add(part)

    if extra_keys:
        for r in session.query(Lookup).filter(Lookup.lookup_key.in_(extra_keys)).all():
            lookup_dict[r.lookup_key] = r
        pr.yes(f"Loaded {len(extra_keys)} additional decon parts")

    # Resolve all words and collect IDs
    resolved_ids: set[int] = set()
    id_to_words: dict[int, list[str]] = {}

    for word in unique_words:
        ids = resolve_lookup(lookup_dict, word)
        resolved_ids.update(ids)
        for hw_id in ids:
            if hw_id not in id_to_words:
                id_to_words[hw_id] = []
            if word not in id_to_words[hw_id]:
                id_to_words[hw_id].append(word)

    pr.yes(f"Resolved {len(resolved_ids)} unique headword IDs")

    # Bulk fetch existing SBS rows
    existing_sbs: dict[int, SBS] = {
        r.id: r for r in session.query(SBS).filter(SBS.id.in_(resolved_ids)).all()
    }
    pr.yes(f"Found {len(existing_sbs)} existing SBS rows")

    # Auto-create missing SBS rows
    missing_sbs_ids = resolved_ids - set(existing_sbs.keys())
    for hw_id in missing_sbs_ids:
        new_sbs = SBS(id=hw_id)
        session.add(new_sbs)
    session.flush()
    if missing_sbs_ids:
        pr.yes(f"Auto-created {len(missing_sbs_ids)} new SBS rows")

    # Fetch all SBS rows (including newly created)
    all_sbs: dict[int, SBS] = {
        r.id: r for r in session.query(SBS).filter(SBS.id.in_(resolved_ids)).all()
    }

    # Filter: keep only IDs where dhp_example is empty
    missing_ids: set[int] = {
        hw_id
        for hw_id, sbs_row in all_sbs.items()
        if not sbs_row.dhp_example or sbs_row.dhp_example.strip() == ""
    }

    pr.yes(f"Identified {len(missing_ids)} headwords with empty dhp_example")
    return missing_ids, id_to_words


def phase_2_ai_loop(
    session,
    paths: ProjectPaths,
    missing_ids: set[int],
    id_to_words: dict[int, list[str]],
    lookup_dict: dict[str, Lookup],
    dry_run: bool = False,
    limit: int | None = None,
) -> None:
    """
    Phase 2: For each missing headword, use AI to fill dhp_example.
    Implements resume via temp/dhp_progress.json.
    """
    pr.cyan("PHASE 2: AI Fill Loop")

    # Load progress file
    progress_path = paths.dpd_db_path.parent / "temp" / "dhp_progress.json"
    processed_ids: set[int] = set()
    if progress_path.exists():
        with open(progress_path) as f:
            processed_ids = set(json.load(f))
        skipped = len(processed_ids & missing_ids)
        pr.yes(f"Resuming: skipping {skipped} already-processed headwords")

    # Filter to unprocessed
    to_process = sorted(missing_ids - processed_ids)
    if limit:
        to_process = to_process[:limit]
    pr.yes(f"Processing {len(to_process)} headwords")

    # Initialize AI manager
    ai_manager = AIManager()

    # Failures TSV
    failures_path = paths.dpd_db_path.parent / "temp" / "dhp_failures.tsv"
    failures_file = open(failures_path, "a")
    if failures_path.stat().st_size == 0:
        failures_file.write("headword_id\tword_forms\treason\n")

    try:
        for i, headword_id in enumerate(to_process, 1):
            pr.cyan(f"[{i}/{len(to_process)}] Processing headword {headword_id}")

            # Get word forms and DHP verses
            word_forms = id_to_words.get(headword_id, [])
            if not word_forms:
                pr.amber("No word forms found")
                failures_file.write(f"{headword_id}\t\tNo word forms in id_to_words\n")
                processed_ids.add(headword_id)
                continue

            # Collect DHP verse candidates
            candidates = []
            seen = set()

            for word_form in word_forms:
                verses = find_cst_source_sutta_example("kn2", re.escape(word_form))
                if verses:
                    for verse in verses:
                        key = (verse.source, verse.sutta, verse.example)
                        if key not in seen:
                            seen.add(key)
                            candidates.append(verse)
                            if len(candidates) >= 20:
                                break
                if len(candidates) >= 20:
                    break

            if not candidates:
                pr.amber("No DHP verses found")
                failures_file.write(
                    f"{headword_id}\t{'; '.join(word_forms)}\tNo DHP verses found\n"
                )
                processed_ids.add(headword_id)
                continue

            # Collect sibling headword IDs (all IDs sharing these word forms)
            sibling_ids = set()
            for wf in word_forms:
                for hw_id in id_to_words:
                    if wf in id_to_words[hw_id]:
                        sibling_ids.add(hw_id)

            # Fetch sibling headword rows
            siblings = {
                r.id: r
                for r in session.query(DpdHeadword)
                .filter(DpdHeadword.id.in_(sibling_ids))
                .all()
            }

            # Build prompt
            word_forms_joined = ", ".join(word_forms)

            headword_entries = []
            for hw_id in sorted(siblings.keys()):
                hw = siblings[hw_id]
                construction = hw.construction or ""
                example_1 = hw.example_1 or ""
                headword_entries.append(
                    f"  ID {hw_id}: {hw.lemma_1} ({hw.pos}) — {hw.meaning_1} | {construction}\n"
                    f"  Example: {example_1}"
                )

            verses_text = []
            for verse in candidates[:20]:
                verses_text.append(
                    f'  {verse.source} ({verse.sutta}): "{verse.example}"'
                )

            user_prompt = f"""A Pāḷi word appears in the Dhammapada. Your tasks:
1. Pick the headword ID that best fits the DHP verse context.
2. Select the single most representative DHP verse.

Word form(s) in text: {word_forms_joined}

Dictionary entries matching this word:
{chr(10).join(headword_entries)}

Candidate Dhammapada verses containing this word:
{chr(10).join(verses_text)}

Write dhp_example as one complete pada or prose sentence — do not truncate.
Return ONLY this Python dict (no extra text):
{{"headword_id": <int>, "dhp_source": "<DHP source>", "dhp_sutta": "<sutta name>", "dhp_example": "<full sentence>"}}"""

            sys_prompt = """You are a Pāḷi lexicography assistant. Follow instructions exactly.
Return ONLY the Python dict — no explanation, no markdown, no code block."""

            # Get AI response
            try:
                ai_response = ai_manager.request(
                    prompt=user_prompt, prompt_sys=sys_prompt
                )
            except Exception as e:
                pr.amber(f"AI request failed: {e}")
                failures_file.write(
                    f"{headword_id}\t{'; '.join(word_forms)}\tAI request failed\n"
                )
                processed_ids.add(headword_id)
                continue

            if not ai_response or not ai_response.content:
                pr.amber("AI returned empty response")
                failures_file.write(
                    f"{headword_id}\t{'; '.join(word_forms)}\tEmpty AI response\n"
                )
                processed_ids.add(headword_id)
                continue

            # Parse response
            response_text = ai_response.content
            try:
                # Find {...} block
                match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if not match:
                    raise ValueError("No dict block found")
                dict_str = match.group(0)
                # Try ast.literal_eval first, then json.loads
                try:
                    result = ast.literal_eval(dict_str)
                except (ValueError, SyntaxError):
                    result = json.loads(dict_str)
            except Exception as e:
                pr.amber(f"Failed to parse response: {e}")
                failures_file.write(
                    f"{headword_id}\t{'; '.join(word_forms)}\tParse error\n"
                )
                processed_ids.add(headword_id)
                continue

            # Validate response
            required_keys = {"headword_id", "dhp_source", "dhp_sutta", "dhp_example"}
            if not isinstance(result, dict) or not required_keys.issubset(
                result.keys()
            ):
                pr.amber("Invalid response structure")
                failures_file.write(
                    f"{headword_id}\t{'; '.join(word_forms)}\tInvalid structure\n"
                )
                processed_ids.add(headword_id)
                continue

            selected_hw_id = result["headword_id"]
            if selected_hw_id not in sibling_ids:
                pr.amber(f"Selected ID {selected_hw_id} not in siblings")
                failures_file.write(
                    f"{headword_id}\t{'; '.join(word_forms)}\tInvalid selected ID\n"
                )
                processed_ids.add(headword_id)
                continue

            if dry_run:
                pr.green("✓ [DRY RUN] Would write:")
                pr.yes(
                    f"  id: {result['headword_id']}, "
                    f"  dhp_source: {result['dhp_source']}, "
                    f"dhp_sutta: {result['dhp_sutta']}, "
                    f"example: {result['dhp_example'][:40]}..."
                )
            else:
                # Update SBS row
                sbs_row = session.query(SBS).filter(SBS.id == selected_hw_id).first()
                if not sbs_row:
                    sbs_row = SBS(id=selected_hw_id)
                    session.add(sbs_row)

                sbs_row.dhp_source = result["dhp_source"]
                sbs_row.dhp_sutta = result["dhp_sutta"]
                sbs_row.dhp_example = result["dhp_example"]

                session.commit()
                pr.green("✓ Committed to DB")

            # Update progress
            processed_ids.add(headword_id)
            with open(progress_path, "w") as f:
                json.dump(list(processed_ids), f)

    finally:
        failures_file.close()

    pr.green_tmr(f"Processed {len(to_process)} headwords")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Populate SBS.dhp_example via AI")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Phase 1 always runs; Phase 2 prints without writing to DB",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Process only N headwords (for testing)"
    )
    args = parser.parse_args()

    paths = ProjectPaths()
    session = get_db_session(paths.dpd_db_path)

    try:
        # Phase 1
        missing_ids, id_to_words = phase_1_extract(session, paths)

        # Rebuild lookup dict for Phase 2
        words = make_cst_text_list(["kn2"])
        unique_words = list(set(words))
        lookup_dict: dict[str, Lookup] = {
            r.lookup_key: r
            for r in session.query(Lookup)
            .filter(Lookup.lookup_key.in_(unique_words))
            .all()
        }
        extra_keys: set[str] = set()
        for r in lookup_dict.values():
            if not r.headwords_unpack and r.deconstructor_unpack:
                for part in make_decon_word_list(r.deconstructor_unpack):
                    if part not in lookup_dict:
                        extra_keys.add(part)
        if extra_keys:
            for r in (
                session.query(Lookup).filter(Lookup.lookup_key.in_(extra_keys)).all()
            ):
                lookup_dict[r.lookup_key] = r

        # Phase 2
        phase_2_ai_loop(
            session,
            paths,
            missing_ids,
            id_to_words,
            lookup_dict,
            dry_run=args.dry_run,
            limit=args.limit,
        )

        pr.green("✓ Script complete")

    finally:
        session.close()


if __name__ == "__main__":
    main()
