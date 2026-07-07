# Extract a source/translation/literal_translation TSV from any book's analysis JSON.

import argparse
import csv
import json
import re
from pathlib import Path

from exporter.analysis.paths import ensure_analysis_dirs
from tools.printer import printer as pr


def build_translation_map(items: list[dict]) -> dict[str, tuple[str, str]]:
    """Build {num: (translation, literal_translation)} from analysis JSON items."""
    return {
        item["num"]: (item["translation"], item["literal_translation"])
        for item in items
    }


def apply_combines(
    translations: dict[str, tuple[str, str]],
    combines: list[tuple[str, list[str]]],
) -> dict[str, tuple[str, str]]:
    """Add a combined entry per (new_key, sources) without removing the sources' own entries."""
    result = dict(translations)
    for new_key, sources in combines:
        translation_parts = []
        literal_parts = []
        for source in sources:
            if source not in translations:
                raise ValueError(
                    f"--combine source '{source}' not found in translations"
                )
            translation, literal_translation = translations[source]
            translation_parts.append(translation)
            literal_parts.append(literal_translation)
        result[new_key] = (" ".join(translation_parts), " ".join(literal_parts))
    return result


def natural_sort_key(text: str) -> list[int | str]:
    """Sort strings in human order (natural sort), e.g. DHP2, DHP11, DHP103."""
    return [
        int(chunk) if chunk.isdigit() else chunk.lower()
        for chunk in re.split(r"(\d+)", text)
    ]


def sorted_rows(
    translations: dict[str, tuple[str, str]],
) -> list[tuple[str, str, str]]:
    """Return (source, translation, literal_translation) rows, naturally sorted by source."""
    return [
        (source, translation, literal_translation)
        for source, (translation, literal_translation) in sorted(
            translations.items(), key=lambda item: natural_sort_key(item[0])
        )
    ]


def parse_combine_arg(value: str) -> tuple[str, list[str]]:
    """Parse a "NEWKEY=SRC1,SRC2" --combine argument into (new_key, [sources])."""
    new_key, _, sources_str = value.partition("=")
    sources = [source.strip() for source in sources_str.split(",") if source.strip()]
    return new_key.strip(), sources


def write_tsv(output: Path, rows: list[tuple[str, str, str]]) -> None:
    """Write extracted rows to a TSV file with a header."""
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["source", "translation", "literal_translation"])
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract source/translation/literal_translation TSV from a book's analysis JSON."
    )
    parser.add_argument("book_code", help="Analysis file stem, e.g. 'kn2'")
    parser.add_argument("output", type=Path, help="Destination TSV path")
    parser.add_argument(
        "--combine",
        action="append",
        default=[],
        metavar="NEWKEY=SRC1,SRC2",
        help="Synthesize an additional row NEWKEY from the space-joined SRC1,SRC2,... fields",
    )
    args = parser.parse_args()

    input_path = ensure_analysis_dirs().output_dir / f"{args.book_code}_analysis.json"
    with open(input_path, encoding="utf-8") as f:
        items = json.load(f)

    translations = build_translation_map(items)
    combines = [parse_combine_arg(value) for value in args.combine]
    translations = apply_combines(translations, combines)
    rows = sorted_rows(translations)

    write_tsv(args.output, rows)
    pr.green(f"{len(rows)} rows saved to {args.output}")


if __name__ == "__main__":
    main()
