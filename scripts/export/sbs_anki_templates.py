#!/usr/bin/env python3
"""Extract Anki note type card templates and CSS to Markdown files."""

import argparse
from pathlib import Path
from anki.collection import Collection
from tools.configger import config_read
from tools.printer import printer as pr
from tools.paths_dps import DPSPaths


MODEL_SLUG_MAP: dict[str, str] = {
    "common roots": "common-roots",
    "pali class abbrev": "grammar-abbrev",
    "pali class Grammar": "grammar-gramm",
    "pali class Sandhi": "grammar-sandhi",
    "Vibhanga": "vibhanga",
    "DHP Vocab": "dhp",
    "Paritta": "paritta",
    "Pātimokkha word by word": "pat",
    "Phonetic Class": "phonetic-class",
    "Roots Class": "roots",
    "SBS Vocab": "sbs",
    "Advanced Suttas": "suttas",
    "pali class Vocab": "class",
    "Pāli": "dps",
}


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


def write_md(path: Path, title: str, content: str, lang: str) -> None:
    """Write content to a Markdown file with a specific language block."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n```{lang}\n{content}\n```\n")
    pr.yes(str(path))


def main(output_dir: Path | None = None) -> None:
    pr.tic()
    if output_dir is None:
        output_dir = DPSPaths().sbs_anki_templates_dir

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        pr.red("Output directory not defined.")
        return

    col = get_anki_collection()
    if not col:
        return

    try:
        all_models = col.models.all()

        # Determine common CSS
        css_counts: dict[str, int] = {}
        for m in all_models:
            css = m["css"]
            css_counts[css] = css_counts.get(css, 0) + 1

        if not css_counts:
            pr.red("No note types found in collection.")
            return

        common_css = max(css_counts, key=lambda k: css_counts[k])
        write_md(output_dir / "styling.md", "Styling", common_css, "css")

        # Extract templates per model
        for model in all_models:
            model_name: str = model["name"]
            if model_name not in MODEL_SLUG_MAP:
                pr.amber(f"skipping unknown model: {model_name}")
                continue

            slug = MODEL_SLUG_MAP[model_name]

            if model["css"] != common_css:
                write_md(
                    output_dir / f"{slug}-styling.md",
                    f"{model_name} — Styling",
                    model["css"],
                    "css",
                )

            tmpls: list[dict] = model["tmpls"]
            multi = len(tmpls) > 1

            for tmpl in tmpls:
                tmpl_name: str = tmpl["name"]
                if multi:
                    tmpl_slug = tmpl_name.lower().replace(" ", "-")
                    front_path = output_dir / f"{slug}-{tmpl_slug}-front.md"
                    back_path = output_dir / f"{slug}-{tmpl_slug}-back.md"
                    front_title = f"{model_name} — {tmpl_name} — Front Template"
                    back_title = f"{model_name} — {tmpl_name} — Back Template"
                else:
                    front_path = output_dir / f"{slug}-front.md"
                    back_path = output_dir / f"{slug}-back.md"
                    front_title = f"{model_name} — Front Template"
                    back_title = f"{model_name} — Back Template"

                write_md(front_path, front_title, tmpl["qfmt"], "html")
                write_md(back_path, back_title, tmpl["afmt"], "html")

    finally:
        col.close()

    pr.toc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract Anki note type card templates and CSS to Markdown files."
    )
    parser.add_argument("--output-dir", help="Output directory for Markdown files")
    args = parser.parse_args()
    main(Path(args.output_dir) if args.output_dir else None)
