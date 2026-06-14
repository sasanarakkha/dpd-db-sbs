#!/usr/bin/env python3

"""Export SBS Anki decks to .apkg files."""

from pathlib import Path
import argparse
from anki.collection import Collection
from tools.configger import config_read
from tools.printer import printer as pr
from scripts.export.sbs_anki_deck_config import DECKS


def get_anki_collection() -> Collection | None:
    """Get Anki collection from config path."""
    anki_db_path = config_read("anki", "db_path_sbs")
    if not anki_db_path:
        pr.red("db_path_sbs not found in config.ini")
        return None
    try:
        return Collection(anki_db_path)
    except Exception as e:
        pr.red(f"Error opening Anki collection: {e}")
        return None


def main(output_dir: str | None = None, with_scheduling: bool = False) -> None:
    pr.tic()

    out_dir = Path(output_dir) if output_dir is not None else Path("temp/anki_decks")
    out_dir.mkdir(parents=True, exist_ok=True)

    col = get_anki_collection()
    if not col:
        return

    try:
        # Import exporter here to avoid circular import issues in some environments
        from anki.exporting import AnkiPackageExporter

        pr.green("exporting decks to .apkg")

        # Map deck names to IDs
        all_decks = col.decks.all()
        deck_name_to_id = {d["name"]: d["id"] for d in all_decks}

        for deck_config in DECKS:
            deck_name = deck_config.deck_name
            if deck_name in deck_name_to_id:
                deck_id = deck_name_to_id[deck_name]
                slug = deck_config.slug
                output_path = out_dir / f"{slug}.apkg"

                pr.green(f"exporting {deck_name}")

                exporter = AnkiPackageExporter(col)
                exporter.did = deck_id
                exporter.includeSched = with_scheduling
                exporter.includeMedia = True

                exporter.exportInto(str(output_path))
                pr.yes(f"saved to {output_path}")
            else:
                pr.amber(f"Deck '{deck_name}' not found in collection")

    finally:
        col.close()

    pr.toc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export SBS Anki decks to .apkg files."
    )
    parser.add_argument("--output-dir", help="Output directory for .apkg files")
    parser.add_argument(
        "--with-scheduling", action="store_true", help="Include scheduling information"
    )
    args = parser.parse_args()

    main(output_dir=args.output_dir, with_scheduling=args.with_scheduling)
