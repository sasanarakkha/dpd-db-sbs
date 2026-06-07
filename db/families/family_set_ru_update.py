#!/usr/bin/env python3

"""Determine English family sets without corresponding Russian translation,
ask AI to translate them, and update the sets_ru.tsv file."""

import csv
import re
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.paths_ru import RuPaths
from tools.printer import printer as pr
from tools.ai_manager import AIManager
from tools.tools_for_ru_exporter import read_set_ru_from_tsv

_RE_NUMBERED = re.compile(r"^[0-9]+\.\s*")
_RE_DASH = re.compile(r"^-\s*")
_RE_STAR = re.compile(r"^\*\s*")


def _clean_translated_lines(lines: list[str]) -> list[str]:
    """Strip numbering, bullet prefixes, and markdown bold added by AI models."""
    cleaned = []
    for line in lines:
        line = _RE_NUMBERED.sub("", line)
        line = _RE_DASH.sub("", line)
        line = _RE_STAR.sub("", line)
        line = line.replace("**", "")
        cleaned.append(line.strip())
    return cleaned


def main() -> None:
    pr.tic()
    pr.green_title("Updating missing sets_ru with AI")

    pth = ProjectPaths()
    rupth = RuPaths()
    db_session = get_db_session(pth.dpd_db_path)

    sets_db = db_session.query(DpdHeadword).filter(DpdHeadword.family_set != "").all()

    unique_sets: set[str] = set()
    for i in sets_db:
        for fs in i.family_set_list:
            if fs and fs not in (" ", "+"):
                unique_sets.add(fs)

    set_ru_dict = read_set_ru_from_tsv()
    missing_sets: list[str] = []

    for fs in unique_sets:
        if fs not in set_ru_dict:
            missing_sets.append(fs)

    if not missing_sets:
        pr.green("No missing sets found.")
        pr.toc()
        return

    for fs in missing_sets:
        pr.green(f"Missing: {fs}")

    pr.green(f"Found {len(missing_sets)} missing sets to translate.")

    ai_manager = AIManager()

    missing_sets_str = "\n".join(missing_sets)
    sys_prompt = "You are an expert translator from English to Russian. You translate Pali/Buddhist terminology and categories. Provide ONLY the translations, one per line, corresponding exactly to the input lines. Do not include any explanations, numbers, bullets, or markdown formatting."
    prompt = f"Translate the following sets to Russian:\n\n{missing_sets_str}\n\nAgain, provide only the translated list line by line."

    response = ai_manager.request(prompt=prompt, prompt_sys=sys_prompt)
    if not response.content:
        pr.red("AI response failed or empty")
        return

    translated_lines = [
        line.strip() for line in response.content.split("\n") if line.strip()
    ]
    cleaned_lines = _clean_translated_lines(translated_lines)

    if len(cleaned_lines) != len(missing_sets):
        pr.red(
            f"Translation lines mismatch: {len(cleaned_lines)} translated vs {len(missing_sets)} missing."
        )
        pr.green(f"AI response:\n{response.content}")
        return

    for en_set, ru_set in zip(missing_sets, cleaned_lines):
        set_ru_dict[en_set] = ru_set
        pr.green(f"Translated: {en_set} -> {ru_set}")

    tmp_path = rupth.sets_ru_path.with_suffix(".tsv.tmp")
    with tmp_path.open("w", newline="") as file:
        writer = csv.writer(file, delimiter="\t")
        for key in sorted(set_ru_dict.keys()):
            writer.writerow([key, set_ru_dict[key]])
    tmp_path.rename(rupth.sets_ru_path)

    pr.yes("TSV updated successfully")
    pr.toc()


if __name__ == "__main__":
    main()
