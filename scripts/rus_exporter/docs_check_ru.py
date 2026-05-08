"""Check docs_rus for dead internal links and broken image assets."""

import re
import sys
from pathlib import Path
from urllib.parse import unquote
from tools.printer import printer as pr

DOCS_DIR = Path("docs_rus")
IMG_REF_RE = re.compile(r"!\[.*?\]\(([^)]+)\)")
# List item link: - [text](target.md) or - [text](target.md#anchor)
LIST_LINK_RE = re.compile(r"^(\s*-\s+)\[([^\]]+)\]\(([^)]+\.md(?:#[^)]*)?)\)")


def strip_fragment(path_str: str) -> str:
    """Remove #anchor or MkDocs suffixes from path."""
    return path_str.split("#")[0]


def check_file(file_path: Path) -> list[str]:
    """Check a single markdown file for dead links and broken images."""
    if not file_path.exists():
        return []

    lines = file_path.read_text().splitlines()
    new_lines = []
    broken_images = []
    changed = False

    for line in lines:
        # 1. Check list-item links
        match = LIST_LINK_RE.match(line)
        if match:
            _, _, target = match.groups()
            clean_target = unquote(strip_fragment(target))

            # Resolve relative to the file
            target_path = (file_path.parent / clean_target).resolve()

            # Check if it exists
            if not target_path.exists():
                pr.amber(f"removed dead link: {file_path}: {line.strip()}")
                changed = True
                continue  # Skip adding this line to new_lines (removes it)

        # 2. Check image refs
        for img_match in IMG_REF_RE.finditer(line):
            img_path_str = img_match.group(1)
            if img_path_str.startswith(("http://", "https://")):
                continue

            clean_img_path = unquote(strip_fragment(img_path_str))
            img_path = (file_path.parent / clean_img_path).resolve()

            if not img_path.exists():
                broken_images.append(f"{file_path}: {img_path_str}")

        new_lines.append(line)

    if changed:
        file_path.write_text("\n".join(new_lines) + "\n")

    return broken_images


def main():
    pr.green("check docs_rus links and assets")

    if not DOCS_DIR.exists():
        pr.no(f"directory not found: {DOCS_DIR}")
        sys.exit(1)

    all_broken_images = []

    for md_file in DOCS_DIR.rglob("*.md"):
        broken = check_file(md_file)
        all_broken_images.extend(broken)

    if all_broken_images:
        pr.no(f"{len(all_broken_images)} broken images")
        for item in all_broken_images:
            pr.amber(item)
        sys.exit(1)

    pr.yes("ok")


if __name__ == "__main__":
    main()
