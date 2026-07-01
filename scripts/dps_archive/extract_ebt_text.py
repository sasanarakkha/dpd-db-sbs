"""Extract clean Pāḷi mūla text for EBT collections into separate markdown files."""

import json
import re
from pathlib import Path

from tools.printer import printer as pr
from tools.sort_naturally import natural_sort

SC_ROOT = Path("resources/sc-data/sc_bilara_data/root/pli/ms/sutta")
OUTPUT_DIR = Path("misc/ebt-md")

EBT_COLLECTIONS: dict[str, list[Path]] = {
    "dn": [SC_ROOT / "dn"],
    "mn": [SC_ROOT / "mn"],
    "sn": [SC_ROOT / "sn"],
    "an": [SC_ROOT / "an"],
    "kn_ebt": [
        SC_ROOT / "kn/dhp",
        SC_ROOT / "kn/ud",
        SC_ROOT / "kn/iti",
        SC_ROOT / "kn/snp",
        SC_ROOT / "kn/thag",
        SC_ROOT / "kn/thig",
    ],
}

# Collections where gāthā-level ### headers should be inserted.
# "dhp"   → verse number is the numeric suffix of the prefix before ":"
#            e.g. dhp14:1  → gāthā 14
# "thag" / "thig" → verse number is the section number (first number after ":")
#            e.g. thag16.1:3.2 → gāthā 3  (section 0 = metadata, skipped)
GATHA_COLLECTIONS = {"dhp", "thag", "thig"}


def read_json_files(dirs: list[Path]) -> list[tuple[str, dict[str, str]]]:
    """Return (filename_stem, segment_dict) pairs in dir-list order, files within each dir sorted naturally."""
    result: list[tuple[str, dict[str, str]]] = []
    for d in dirs:
        if not d.exists():
            continue
        files = natural_sort([p for p in d.rglob("*.json") if p.is_file()])
        result.extend(
            (p.stem, json.loads(p.read_text(encoding="utf-8"))) for p in files
        )
    return result


def _collection_prefix(stem: str) -> str:
    """Return the base collection name from a file stem, e.g. 'thag16.1_root-pli-ms' → 'thag'."""
    name = stem.replace("_root-pli-ms", "")
    m = re.match(r"([a-z]+)", name)
    return m.group(1) if m else ""


def _dhp_gatha_num(seg_id: str) -> int | None:
    """Return the DHP verse number from a segment id like 'dhp14:2', or None for sub-zero lines."""
    prefix = seg_id.split(":")[0]  # e.g. 'dhp14'
    m = re.search(r"(\d+)$", prefix)
    return int(m.group(1)) if m else None


def _section_num(seg_id: str) -> int:
    """Return the section number from a segment id like 'thag16.1:3.2' → 3."""
    after_colon = seg_id.split(":")[1] if ":" in seg_id else "0"
    return int(after_colon.split(".")[0])


def _build_file_prose(stem: str, segments: dict[str, str]) -> list[str]:
    """Render one sutta file as prose lines (no gāthā headers)."""
    heading = stem.replace("_root-pli-ms", "")
    lines = [f"## {heading}\n"]
    for text in segments.values():
        clean = text.replace("ṁ", "ṃ").strip()
        if clean:
            lines.append(clean)
    lines.append("")
    return lines


def _build_file_gatha(
    stem: str, segments: dict[str, str], collection: str
) -> list[str]:
    """Render one sutta file with ### Gāthā N headers (DHP, THAG, THIG)."""
    heading = stem.replace("_root-pli-ms", "")
    lines = [f"## {heading}\n"]
    last_gatha: int | None = None

    for seg_id, text in segments.items():
        clean = text.replace("ṁ", "ṃ").strip()
        if not clean:
            continue

        if collection == "dhp":
            gatha_num = _dhp_gatha_num(seg_id)
            sub = seg_id.split(":")[1] if ":" in seg_id else ""
            is_prose = sub.startswith("0")
            if not is_prose and gatha_num is not None and gatha_num != last_gatha:
                lines.append(f"\n### Gāthā {gatha_num}\n")
                last_gatha = gatha_num
        else:
            section = _section_num(seg_id)
            if section > 0 and section != last_gatha:
                lines.append(f"\n### Gāthā {section}\n")
                last_gatha = section

        lines.append(clean)

    lines.append("")
    return lines


def build_md(
    file_entries: list[tuple[str, dict[str, str]]], kn_order: bool = False
) -> str:
    """Build markdown text, preserving insertion order.

    When kn_order=True, each file is routed to gāthā-aware rendering if its
    collection prefix is in GATHA_COLLECTIONS, otherwise to prose rendering.
    """
    lines: list[str] = []
    for stem, segments in file_entries:
        if kn_order:
            coll = _collection_prefix(stem)
            if coll in GATHA_COLLECTIONS:
                lines.extend(_build_file_gatha(stem, segments, coll))
            else:
                lines.extend(_build_file_prose(stem, segments))
        else:
            lines.extend(_build_file_prose(stem, segments))
    return "\n".join(lines)


def main() -> None:
    pr.bip()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pr.green(f"output dir: {OUTPUT_DIR}")

    for name, dirs in EBT_COLLECTIONS.items():
        pr.green(f"processing {name}")
        file_entries = read_json_files(dirs)
        if not file_entries:
            pr.no(f"{name}: no files found")
            continue

        md_text = build_md(file_entries, kn_order=(name == "kn_ebt"))
        out_path = OUTPUT_DIR / f"{name}.md"
        out_path.write_text(md_text, encoding="utf-8")
        size_kb = out_path.stat().st_size // 1024
        pr.yes(f"{name}.md — {len(file_entries)} files, {size_kb} KB")


if __name__ == "__main__":
    main()
