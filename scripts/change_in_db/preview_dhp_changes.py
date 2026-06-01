"""Preview proposed SBS.dhp_example changes per verse for human review."""

import argparse
import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import SBS
from exporter.analysis.translate_core import (
    generate_markdown_report,
    translate_sentence,
)
from exporter.analysis.example_bolding import (
    bold_word_in_verse,
    collect_all_ids,
    find_token_in_apos_verse,
)
from tools.ai_manager import AIManager
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preview proposed SBS.dhp_example changes per verse."
    )
    parser.add_argument("--book", required=True, help="CST book code (e.g., kn2)")
    parser.add_argument("--verse", help="Process a specific verse only (e.g., DHP1)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-analysis even if verse already exists in analysis file",
    )
    args = parser.parse_args()

    book = args.book
    input_path = Path("exporter/analysis/input") / f"{book}.json"
    analysis_path = Path("exporter/analysis/output") / f"{book}_analysis.json"

    if not input_path.exists():
        pr.no(f"Input file not found: {input_path}")
        return

    if not analysis_path.exists():
        pr.no(f"Analysis file not found: {analysis_path}")
        return

    with open(input_path, encoding="utf-8") as f:
        input_verses: dict[str, dict[str, Any]] = {v["num"]: v for v in json.load(f)}

    with open(analysis_path, encoding="utf-8") as f:
        all_analysis: list[dict[str, Any]] = json.load(f)

    paths = ProjectPaths()
    db_session: Session = get_db_session(paths.dpd_db_path)

    if args.verse:
        if args.force:
            all_analysis = [v for v in all_analysis if v["num"] != args.verse]

        analysis_results = [v for v in all_analysis if v["num"] == args.verse]
        if not analysis_results:
            # Auto-analyze missing verse
            input_verse = input_verses.get(args.verse)
            if not input_verse:
                pr.no(f"Verse '{args.verse}' not found in {input_path} either")
                db_session.close()
                return
            msg = f"Verse '{args.verse}' not yet analyzed — running analysis now..."
            if args.force:
                msg = f"Re-analyzing verse '{args.verse}'..."
            pr.green(msg)
            ai_manager = AIManager()
            result = translate_sentence(
                input_verse["text"],
                db_session,
                ai_manager,
                verse_source=args.verse,
                speech_mark_options=input_verse.get("speech_mark_options"),
            )
            verse_text: str = result.get("verse_text") or input_verse["text"]
            new_entry = {
                "num": args.verse,
                "vagga": input_verse["vagga"],
                "text": input_verse["text"],
                "verse_text": verse_text,
                "translation": result["translation"],
                "literal_translation": result["literal_translation"],
                "analysis": result["analysis"],
            }
            all_analysis.append(new_entry)
            with open(analysis_path, "w", encoding="utf-8") as f:
                json.dump(all_analysis, f, ensure_ascii=False, indent=2)
            pr.yes(f"Analysis saved to {analysis_path}")
            analysis_results = [new_entry]
    else:
        analysis_results = all_analysis

    try:
        sbs_map: dict[int, SBS] = {sbs.id: sbs for sbs in db_session.query(SBS).all()}

        reports_dir = Path("exporter/analysis/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        for verse in analysis_results:
            verse_num = verse["num"]
            verse_text = verse.get("verse_text") or verse.get("text", "")

            # Section 1: Analysis report
            analysis_report = generate_markdown_report(verse, verse_text, verse_num)

            # Section 2: Speech mark options
            input_verse = input_verses.get(verse_num, {})
            speech_mark_options = input_verse.get("speech_mark_options", {})
            speech_marks_section = ""
            if speech_mark_options:
                options_lines = [
                    f"- **{word}**: {', '.join(variants)}"
                    for word, variants in speech_mark_options.items()
                ]
                speech_marks_section = "### Speech Mark Options\n\n" + "\n".join(
                    options_lines
                )

            # Section 3: Proposed SBS changes
            proposed_changes_rows = []
            updated_ids: set[int] = set()

            for token_data in verse.get("analysis", []):
                word = token_data.get("word", "")
                options: list[dict[str, Any]] = token_data.get("data", [])
                if not options:
                    continue

                best_option = max(options, key=lambda x: x.get("ai_score", 0))
                all_entries = collect_all_ids(best_option, word)
                apos_word = find_token_in_apos_verse(word, verse_text)

                for (
                    headword_id,
                    component_pali,
                    _word_in_verse,
                    is_first_component,
                    is_top_level,
                ) in all_entries:
                    if headword_id in updated_ids:
                        continue

                    sbs = sbs_map.get(headword_id)
                    status = "SKIP" if sbs and sbs.dhp_example else "NEW"
                    proposed_example = bold_word_in_verse(
                        verse_text,
                        apos_word,
                        component_pali,
                        headword_id,
                        db_session,
                        is_first_component,
                        is_top_level,
                    )

                    proposed_changes_rows.append(
                        {
                            "id": headword_id,
                            "pali": component_pali,
                            "status": status,
                            "dhp_example": proposed_example,
                        }
                    )
                    updated_ids.add(headword_id)

            proposed_changes_section = ""
            if proposed_changes_rows:
                table_header = "| ID | Pali | Status | Proposed dhp_example |\n"
                table_sep = "|---|---|---|---|\n"
                table_rows = "\n".join(
                    f"| {row['id']} | {row['pali']} | {row['status']} | `{row['dhp_example']}` |"
                    for row in proposed_changes_rows
                )
                proposed_changes_section = (
                    "### Proposed SBS Changes\n\n"
                    + table_header
                    + table_sep
                    + table_rows
                )

            # Combine all sections
            report_parts = [analysis_report]
            if speech_marks_section:
                report_parts.append(speech_marks_section)
            if proposed_changes_section:
                report_parts.append(proposed_changes_section)

            report_content = "\n\n".join(report_parts)

            # Write to file
            report_path = reports_dir / f"{book}_{verse_num}.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            pr.yes(f"Saved: {report_path}")

    finally:
        db_session.close()


if __name__ == "__main__":
    main()
