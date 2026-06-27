#!/usr/bin/env python3

"""Zip DPD+<locale> GoldenDict and MDict archives for CI release."""

import argparse
from zipfile import ZIP_DEFLATED, ZipFile

from tools.paths import ProjectPaths
from tools.printer import printer as pr

LOCALES = ("rus", "sbs", "ta")


def zip_goldendict(pth: ProjectPaths, locale: str) -> None:
    pr.green_title(f"zipping {locale} goldendict")

    if not pth.dpd_goldendict_dir.exists():
        pr.no("error")
        pr.red("no dpd goldendict dir found")
        return

    output_zip = pth.share_dir / f"dpd+{locale}-goldendict.zip"
    with ZipFile(output_zip, "w", compression=ZIP_DEFLATED, compresslevel=5) as zf:
        for file_path in pth.dpd_goldendict_dir.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(pth.dpd_goldendict_dir))

    pr.yes("ok")


def zip_mdict(pth: ProjectPaths, locale: str) -> None:
    pr.green_title(f"zipping {locale} mdict")

    mdict_files = [pth.dpd_mdx_path, pth.dpd_mdd_path]

    for file in mdict_files:
        if not file.exists():
            pr.no("error")
            pr.red(f"mdict file not found: {file}")
            return

    output_zip = pth.share_dir / f"dpd+{locale}-mdict.zip"
    with ZipFile(output_zip, "w", compression=ZIP_DEFLATED, compresslevel=5) as zf:
        for mdict_file in mdict_files:
            zf.writestr(mdict_file.name, mdict_file.read_bytes())

    pr.yes("ok")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Zip DPD+<locale> GoldenDict and MDict archives."
    )
    parser.add_argument("--locale", choices=LOCALES, required=True)
    args = parser.parse_args()

    pr.tic()
    pr.green_title(f"zipping dpd+{args.locale} for goldendict and mdict")
    pth = ProjectPaths()
    zip_goldendict(pth, args.locale)
    zip_mdict(pth, args.locale)
    pr.toc()


if __name__ == "__main__":
    main()
