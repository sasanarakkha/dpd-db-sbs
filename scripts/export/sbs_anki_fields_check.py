"""Check that Anki note type field lists match their field-list-*.md reference files."""

import sys
from pathlib import Path

from anki.collection import Collection

from tools.configger import config_read
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr


MODEL_FIELD_LIST_MAP: dict[str, str] = {
    "common roots": "field-list-common-roots.md",
    "DHP Vocab": "field-list-dhp.md",
    "Pāli": "field-list-dps.md",
    "pali class abbrev": "field-list-grammar-abbr.md",
    "pali class Grammar": "field-list-grammar-gramm.md",
    "pali class Sandhi": "field-list-grammar-sandhi.md",
    "Paritta": "field-list-parittas.md",
    "Pātimokkha word by word": "field-list-pat.md",
    "Phonetic Class": "field-list-roots-class.md",
    "Roots Class": "field-list-roots-class.md",
    "SBS Vocab": "field-list-sbs.md",
    "Advanced Suttas": "field-list-suttas-class.md",
    "Vibhanga": "field-list-vibhanga.md",
    "pali class Vocab": "field-list-vocab-class.md",
}


def parse_field_list_md(path: Path) -> list[str]:
    """Read field names from the fenced code block in a field-list .md file."""
    if not path.exists():
        pr.amber(f"field-list file missing: {path}")
        return []
    text = path.read_text(encoding="utf-8")
    in_block = False
    fields: list[str] = []
    for line in text.splitlines():
        if line.startswith("```"):
            if in_block:
                break
            in_block = True
            continue
        if in_block:
            stripped = line.strip()
            if stripped:
                fields.append(stripped)
    if not fields:
        pr.amber(f"no fields found in fenced block: {path.name}")
    return fields


def get_anki_fields(col: Collection, model_name: str) -> list[str]:
    """Extract ordered field names for the named Anki note type."""
    model = col.models.by_name(model_name)
    if model is None:
        pr.amber(f"model not found in collection: {model_name}")
        return []
    return [fld["name"] for fld in model["flds"]]


def compare_fields(
    anki_fields: list[str], file_fields: list[str]
) -> tuple[list[str], list[str], bool]:
    """Compare two field lists; return (only_in_anki, only_in_file, order_differs)."""
    anki_set = set(anki_fields)
    file_set = set(file_fields)
    only_in_anki = [f for f in anki_fields if f not in file_set]
    only_in_file = [f for f in file_fields if f not in anki_set]
    common_anki = [f for f in anki_fields if f in file_set]
    common_file = [f for f in file_fields if f in anki_set]
    order_differs = common_anki != common_file
    return only_in_anki, only_in_file, order_differs


def main() -> None:
    pr.tic()
    anki_db_path = config_read("anki", "db_path_sbs")
    if not anki_db_path:
        pr.red("db_path_sbs not found in config.ini")
        sys.exit(1)

    style_dir = DPSPaths().sbs_anki_style_dir
    col: Collection | None = None
    any_mismatch = False

    try:
        col = Collection(anki_db_path)

        for model_name, filename in MODEL_FIELD_LIST_MAP.items():
            anki_fields = get_anki_fields(col, model_name)
            file_fields = parse_field_list_md(style_dir / filename)

            if not anki_fields or not file_fields:
                any_mismatch = True
                continue

            only_in_anki, only_in_file, order_differs = compare_fields(
                anki_fields, file_fields
            )

            if not only_in_anki and not only_in_file and not order_differs:
                pr.green(f"{model_name}: OK")
            else:
                any_mismatch = True
                pr.red(f"{model_name}: MISMATCH")
                if only_in_anki:
                    pr.red(f"  only in Anki: {only_in_anki}")
                if only_in_file:
                    pr.red(f"  only in file: {only_in_file}")
                if order_differs:
                    pr.red("  field order differs")

    except Exception as e:
        pr.red(f"Error opening Anki collection: {e}")
        any_mismatch = True
    finally:
        if col is not None:
            col.close()

    pr.toc()

    if any_mismatch:
        sys.exit(1)


if __name__ == "__main__":
    main()
