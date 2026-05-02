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


def main():
    pr.tic()
    pr.green_title("Updating missing sets_ru with AI")

    pth = ProjectPaths()
    rupth = RuPaths()
    db_session = get_db_session(pth.dpd_db_path)

    sets_db = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.family_set != "")
        .all()
    )

    unique_sets = set()
    for i in sets_db:
        for fs in i.family_set_list:
            if fs and fs not in (" ", "+"):
                unique_sets.add(fs)

    set_ru_dict = read_set_ru_from_tsv()
    missing_sets = []

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
        
    translated_lines = [line.strip() for line in response.content.split("\n") if line.strip()]

    # Some models might add bullet points or numbering despite instructions.
    # Cleaning them up:
    cleaned_lines = []
    for line in translated_lines:
        line = re.sub(r"^[0-9]+\.\s*", "", line)
        line = re.sub(r"^-\s*", "", line)
        line = re.sub(r"^\*\s*", "", line)
        # remove markdown like `**text**` if AI still added it
        line = line.replace("**", "")
        cleaned_lines.append(line.strip())

    # Sometimes AI might output an intro sentence or summary. We should filter them out 
    # if it's glaring, but usually sys_prompt and repetition handles it well.
    if len(cleaned_lines) != len(missing_sets):
        pr.red(f"Translation lines mismatch: {len(cleaned_lines)} translated vs {len(missing_sets)} missing.")
        pr.green(f"AI response:\n{response.content}")
        return
        
    # Update dictionary
    for en_set, ru_set in zip(missing_sets, cleaned_lines):
        set_ru_dict[en_set] = ru_set
        pr.green(f"Translated: {en_set} -> {ru_set}")
        
    # Overwrite the TSV file, sorted by the English set name
    with open(rupth.sets_ru_path, "w", newline="") as file:
        writer = csv.writer(file, delimiter="\t")
        for key in sorted(set_ru_dict.keys()):
            writer.writerow([key, set_ru_dict[key]])
            
    pr.yes("TSV updated successfully")
    pr.toc()

if __name__ == "__main__":
    main()
