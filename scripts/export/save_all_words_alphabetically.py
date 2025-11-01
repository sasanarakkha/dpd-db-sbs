#!/usr/bin/env python3

"""Filter all words with meaning_1, sort them alphabetically, and save to a txt file."""

from db.models import DpdHeadword
from sqlalchemy import and_, not_
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from db.db_helpers import get_db_session

from rich.console import Console

from tools.printer import printer as pr
from tools.pali_sort_key import pali_sort_key


def save_lemmas_alphabetically():
    """
    Fetch all DpdHeadword entries with a non-empty `meaning_1`,
    sort them alphabetically by `lemma_1`, and save them to a text file.
    """
    console = Console()
    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)

    pr.tic()
    console.print("[bold bright_yellow]Fetching all words with meanings...")

    # Query and filter words
    words_with_meaning = (
        db_session.query(DpdHeadword)
        .filter(and_(
            DpdHeadword.meaning_1 != "", 
            not_(DpdHeadword.meaning_1.startswith("(gram)")),
            not_(DpdHeadword.meaning_1.startswith("(comm)")),
            DpdHeadword.pos != "prefix",
            DpdHeadword.pos != "abbrev",
            DpdHeadword.pos != "cs",
            DpdHeadword.pos != "letter",
            DpdHeadword.pos != "root",
            DpdHeadword.pos != "suffix",
        ))
        .all()
    )

    # Sort alphabetically using Pāḷi sort key
    sorted_words = sorted(words_with_meaning, key=lambda x: pali_sort_key(x.lemma_1))

    console.print(f"Found {len(sorted_words)} words to save.")

    # Define the output path for the .txt file
    output_path = dpspth.total_words_meaning

    # Write to a .txt file
    with open(output_path, "w", encoding="utf-8") as f:
        for word in sorted_words:
            # if word.compound_construction:
            #     construction = word.compound_construction.replace("<b>", "").replace("</b>", "")
            # else:
            #     construction = word.construction_summary
            f.write(f"{word.lemma_clean}\t{word.pos}\t{word.meaning_1}\n")

    db_session.close()
    console.print(f"[green]Successfully saved to {output_path}[/green]")
    pr.toc()

if __name__ == "__main__":
    save_lemmas_alphabetically()