#!/usr/bin/env python3

"""Zip DPD+TA into dpd+ta-goldendict.zip and dpd+ta-mdict.zip."""

import os
from zipfile import ZipFile, ZIP_DEFLATED

from tools.paths import ProjectPaths
from tools.printer import printer as pr


def zip_goldendict(pth: ProjectPaths) -> None:
    pr.green_title("zipping ta goldendict")

    if pth.dpd_goldendict_dir.exists():
        output_zip_file = os.path.join(pth.share_dir, "dpd+ta-goldendict.zip")

        with ZipFile(
            output_zip_file, "w", compression=ZIP_DEFLATED, compresslevel=5
        ) as output_zip:
            for root, dirs, files in os.walk(pth.dpd_goldendict_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, pth.dpd_goldendict_dir)
                    output_zip.write(file_path, relative_path)

        pr.yes("ok")
    else:
        pr.no("error")
        pr.red("no dpd goldendict dir found")


def zip_mdict(pth: ProjectPaths) -> None:
    pr.green_title("zipping ta mdict")

    mdict_files = [
        pth.dpd_mdx_path,
        pth.dpd_mdd_path,
    ]

    for file in mdict_files:
        if not file.exists():
            pr.no("error")
            pr.red(f"mdict file not found: {file}")
            return

    output_mdict_zip = os.path.join(pth.share_dir, "dpd+ta-mdict.zip")

    with ZipFile(
        output_mdict_zip, "w", compression=ZIP_DEFLATED, compresslevel=5
    ) as mdict_zip:
        for mdict_file in mdict_files:
            file_content = mdict_file.read_bytes()
            mdict_zip.writestr(mdict_file.name, file_content)

    pr.yes("ok")


def main() -> None:
    pr.tic()
    pr.title("zipping dpd+ta for goldendict and mdict")
    pth = ProjectPaths()
    zip_goldendict(pth)
    zip_mdict(pth)
    pr.toc()


if __name__ == "__main__":
    main()
