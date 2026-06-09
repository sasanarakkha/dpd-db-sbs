"""Preview proposed SBS.dhp_example changes per verse for human review."""

import argparse
import json
from pathlib import Path
from typing import Any, NotRequired, TypedDict, cast

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


class InputVerse(TypedDict):
    num: str
    vagga: str
    text: str
    speech_mark_options: NotRequired[dict[str, list[str]]]


class AnalysisOption(TypedDict):
    key: str
    id: int | str
    pali: str
    ai_score: float
    compound_type: NotRequired[str]
    pos: NotRequired[str]
    components: NotRequired[list[list[Any]]]


class TokenAnalysis(TypedDict):
    word: str
    status: str
    data: list[AnalysisOption]


class VerseAnalysis(TypedDict):
    num: str
    vagga: str
    text: str
    verse_text: NotRequired[str]
    translation: str
    literal_translation: str
    analysis: list[TokenAnalysis]


class ProposedChange(TypedDict):
    id: int
    pali: str
    status: str
    dhp_example: str


def _build_speech_marks_section(speech_mark_options: dict[str, list[str]]) -> str:
    if not speech_mark_options:
        return ""
    options_lines = [
        f"- **{word}**: {', '.join(variants)}"
        for word, variants in speech_mark_options.items()
    ]
    return "### Speech Mark Options\n\n" + "\n".join(options_lines)


def _build_proposed_changes_section(rows: list[ProposedChange]) -> str:
    if not rows:
        return ""
    table_header = "| ID | Pali | Status | Proposed dhp_example |\n"
    table_sep = "|---|---|---|---|\n"
    table_rows = "\n".join(
        f"| {row['id']} | {row['pali']} | {row['status']} | `{row['dhp_example']}` |"
        for row in rows
    )
    return "### Proposed SBS Changes\n\n" + table_header + table_sep + table_rows


def _collect_verse_changes(
    verse: VerseAnalysis,
    verse_text: str,
    sbs_map: dict[int, SBS],
    db_session: Session,
) -> list[ProposedChange]:
    proposed_changes: list[ProposedChange] = []
    updated_ids: set[int] = set()

    for token_data in verse.get("analysis", []):
        word = token_data.get("word", "")
        options: list[AnalysisOption] = token_data.get("data", [])
        if not options:
            continue

        best_option = max(options, key=lambda x: x.get("ai_score", 0))
        all_entries = collect_all_ids(cast(dict[str, Any], best_option), word)
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
            proposed_changes.append(
                {
                    "id": headword_id,
                    "pali": component_pali,
                    "status": status,
                    "dhp_example": proposed_example,
                }
            )
            updated_ids.add(headword_id)

    return proposed_changes


def _load_or_analyze_verse(
    verse_num: str,
    force: bool,
    all_analysis: list[VerseAnalysis],
    input_verses: dict[str, InputVerse],
    analysis_path: Path,
    db_session: Session,
) -> list[VerseAnalysis] | None:
    """Return analysis results for a single verse, running analysis if missing or forced.

    Returns None when the verse is not found in input and cannot be analyzed.
    """
    if force:
        all_analysis = [v for v in all_analysis if v["num"] != verse_num]

    analysis_results = [v for v in all_analysis if v["num"] == verse_num]
    if not analysis_results:
        input_verse = input_verses.get(verse_num)
        if not input_verse:
            pr.no(f"Verse '{verse_num}' not found in input either")
            return None
        msg = (
            f"Re-analyzing verse '{verse_num}'..."
            if force
            else f"Verse '{verse_num}' not yet analyzed — running analysis now..."
        )
        pr.green(msg)
        ai_manager = AIManager()
        result = translate_sentence(
            input_verse["text"],
            db_session,
            ai_manager,
            verse_source=verse_num,
            speech_mark_options=input_verse.get("speech_mark_options"),
        )
        verse_text: str = result.get("verse_text") or input_verse["text"]
        new_entry: VerseAnalysis = {
            "num": verse_num,
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
        return [new_entry]

    return analysis_results


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

    input_verses: dict[str, InputVerse] = {
        v["num"]: v for v in json.loads(input_path.read_text(encoding="utf-8"))
    }
    all_analysis: list[VerseAnalysis] = json.loads(
        analysis_path.read_text(encoding="utf-8")
    )

    paths = ProjectPaths()
    db_session: Session = get_db_session(paths.dpd_db_path)

    if args.verse:
        analysis_results = _load_or_analyze_verse(
            args.verse,
            args.force,
            all_analysis,
            input_verses,
            analysis_path,
            db_session,
        )
        if analysis_results is None:
            db_session.close()
            return
    else:
        analysis_results = all_analysis

    try:
        sbs_map: dict[int, SBS] = {sbs.id: sbs for sbs in db_session.query(SBS).all()}

        reports_dir = Path("exporter/analysis/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        for verse in analysis_results:
            verse_num = verse["num"]
            verse_text = verse.get("verse_text") or verse.get("text", "")

            analysis_report = generate_markdown_report(
                cast(dict[str, Any], verse), verse_text, verse_num
            )

            input_verse = input_verses.get(verse_num, {})
            speech_mark_options = input_verse.get("speech_mark_options", {})
            speech_marks_section = _build_speech_marks_section(speech_mark_options)

            proposed_changes_rows = _collect_verse_changes(
                verse, verse_text, sbs_map, db_session
            )
            proposed_changes_section = _build_proposed_changes_section(
                proposed_changes_rows
            )

            report_parts = [analysis_report]
            if speech_marks_section:
                report_parts.append(speech_marks_section)
            if proposed_changes_section:
                report_parts.append(proposed_changes_section)

            report_content = "\n\n".join(report_parts)
            report_path = reports_dir / f"{book}_{verse_num}.md"
            report_path.write_text(report_content, encoding="utf-8")
            pr.yes(f"Saved: {report_path}")

    finally:
        db_session.close()


if __name__ == "__main__":
    main()
