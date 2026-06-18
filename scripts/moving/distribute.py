#!/usr/bin/env python3

"""Unified entry point for the dictionary distribution tasks formerly split
across scripts/moving/{unzip,copy,move}_*.py — select a task by name."""

import argparse
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from zipfile import ZipFile

from tools.configger import config_test
from tools.printer import printer as pr

_SHARE_MDICT_MEMBERS = {
    "dpd-grammar-mdict.mdx",
    "dpd-grammar-mdict.mdd",
    "dpd-deconstructor-mdict.mdd",
    "dpd-deconstructor-mdict.mdx",
    "dpd-variants-mdict.mdx",
    "dpd-variants-mdict.mdd",
}


def _project_paths() -> tuple[Path, Path]:
    project_dir = Path(__file__).resolve().parent.parent.parent
    deva_dir = project_dir.parent.parent
    return project_dir, deva_dir


def _software_dir(deva_dir: Path) -> Path:
    return (
        deva_dir
        / "filesrv1"
        / "share1"
        / "Sharing between users"
        / "1 For Everyone"
        / "Software"
    )


def _require_dirs(*dirs: Path) -> None:
    for d in dirs:
        if not d.exists():
            pr.no(f"destination not found: {d}")
            sys.exit(1)


def _unzip(
    src: Path,
    dest: Path,
    *,
    member_predicate: Callable[[str], bool] | None = None,
) -> None:
    if not src.exists():
        pr.red(f"{src} is missing. Cannot proceed with unzipping.")
        return
    with ZipFile(src, "r") as zip_obj:
        members = None
        if member_predicate is not None:
            members = [m for m in zip_obj.namelist() if member_predicate(m)]
        zip_obj.extractall(dest, members=members)
    pr.green(f"{src.name} has been unpacked to {dest}")


def _copy_file(src: Path, dest: Path) -> None:
    if not src.exists():
        pr.red(f"{src} is missing. Cannot proceed with copying.")
        return
    shutil.copy2(src, dest)
    pr.green(f"{src.name} copied to {dest}")


def _copy_tree(src: Path, dest: Path, *, archive_base: Path | None = None) -> None:
    if not src.exists():
        pr.red(f"{src} is missing. Cannot proceed with copying.")
        return
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    pr.green(f"{src.name} folder copied to {dest}")
    if archive_base is not None:
        shutil.make_archive(str(archive_base), "zip", str(dest))
        pr.green(f"{archive_base}.zip has been created")


def _move_file(src: Path, dest: Path) -> None:
    if not src.exists():
        pr.red(f"{src} is missing. Cannot proceed with moving.")
        return
    shutil.move(src, dest)
    pr.green(f"{src.name} moved to {dest}")


def _copy_pair(paths: list[tuple[Path, Path]]) -> None:
    """Copy each (src, dest_dir) pair, but only if every src exists.

    Mirrors the original mdx/mdd scripts: either both files get copied, or
    each missing one is reported and nothing is copied.
    """
    missing = [src for src, _ in paths if not src.exists()]
    if missing:
        for src in missing:
            pr.red(f"{src} is missing. Cannot proceed with copying.")
        return
    for src, dest_dir in paths:
        shutil.copy2(src, dest_dir)
    pr.green(", ".join(src.name for src, _ in paths) + " copied to the server folder")


def _task_unzip_dpd_to_filesrv() -> None:
    _, deva_dir = _project_paths()
    downloads_dir = deva_dir / "Downloads" / "DPDs"
    software_dir = _software_dir(deva_dir)
    gd_dir = software_dir / "Golden Dictionary" / "Default"
    md_dir = software_dir / "MDict" / "dpd"
    kd_dir = software_dir / "Ebook Readers Dictionary"
    _require_dirs(gd_dir, md_dir, kd_dir)

    _unzip(downloads_dir / "dpd-goldendict.zip", gd_dir)
    _unzip(downloads_dir / "dpd-mdict.zip", md_dir)
    _move_file(downloads_dir / "dpd-kindle.mobi", kd_dir / "dpd-kindle.mobi")
    _move_file(downloads_dir / "dpd-kindle.epub", kd_dir / "dpd-kindle.epub")
    _move_file(downloads_dir / "dpd-kobo.zip", kd_dir / "dpd-kobo.zip")
    _unzip(downloads_dir / "dpd-pdf.zip", kd_dir)


def _task_unzip_dpd_to_gd() -> None:
    _, deva_dir = _project_paths()
    downloads_dir = deva_dir / "Downloads" / "DPDs"
    goldendict_dir = deva_dir / "Documents" / "GoldenDict"
    sync_mdict_dir = deva_dir / "Mdict"

    _unzip(downloads_dir / "dpd-goldendict.zip", goldendict_dir)
    _unzip(downloads_dir / "dpd-mdict.zip", sync_mdict_dir)


def _task_unzip_dpd_to_share() -> None:
    project_dir, deva_dir = _project_paths()
    downloads_dir = deva_dir / "Downloads" / "DPDs"
    share_dir = project_dir / "exporter" / "share"

    _unzip(
        downloads_dir / "dpd-goldendict.zip",
        share_dir,
        member_predicate=lambda m: m.startswith(
            ("dpd-deconstructor/", "dpd-grammar/", "dpd-variants/")
        ),
    )
    _unzip(
        downloads_dir / "dpd-mdict.zip",
        share_dir,
        member_predicate=lambda m: m in _SHARE_MDICT_MEMBERS,
    )


def _task_unzip_dpd_sbs_to_filesrv() -> None:
    _, deva_dir = _project_paths()
    downloads_dir = deva_dir / "Downloads" / "DPDs"
    software_dir = _software_dir(deva_dir)
    gd_dir = software_dir / "Golden Dictionary" / "Default" / "dpd"
    md_dir = software_dir / "MDict" / "dpd"
    _require_dirs(gd_dir, md_dir)

    _unzip(downloads_dir / "dpd+sbs-goldendict.zip", gd_dir)
    _unzip(downloads_dir / "dpd+sbs-mdict.zip", md_dir)


def _task_unzip_rudpd_to_filesrv() -> None:
    _, deva_dir = _project_paths()
    downloads_dir = deva_dir / "Downloads" / "DPDs"
    software_dir = _software_dir(deva_dir)
    gd_dir = software_dir / "Golden Dictionary" / "Optional"
    md_dir = software_dir / "MDict" / "ru-dpd"
    kd_dir = software_dir / "Ebook Readers Dictionary"
    _require_dirs(gd_dir, md_dir, kd_dir)

    _unzip(downloads_dir / "ru-dpd-goldendict.zip", gd_dir)
    _unzip(downloads_dir / "ru-dpd-mdict.zip", md_dir)
    _copy_file(downloads_dir / "ru-dpd-kindle.mobi", kd_dir / "ru-dpd-kindle.mobi")
    _copy_file(downloads_dir / "ru-dpd-kindle.epub", kd_dir / "ru-dpd-kindle.epub")


def _task_unzip_classes_to_filesrv() -> None:
    _, deva_dir = _project_paths()
    downloads_dir = deva_dir / "Downloads" / "Pali_classes"
    materials_dir = (
        deva_dir
        / "filesrv1"
        / "share1"
        / "Sharing between users"
        / "13 For Pāli class"
        / "offline materials"
    )
    beginner_dir = materials_dir / "beginner"
    intermediate_dir = materials_dir / "intermediate"
    _require_dirs(beginner_dir, intermediate_dir)

    _unzip(downloads_dir / "beginner_pali_course_exercises_docx.zip", beginner_dir)
    _unzip(downloads_dir / "beginner_pali_course_pdfs.zip", beginner_dir)
    _unzip(
        downloads_dir / "intermediate_pali_course_exercises_docx.zip",
        intermediate_dir,
    )
    _unzip(downloads_dir / "intermediate_pali_course_pdfs.zip", intermediate_dir)


def _task_move_mdict() -> None:
    if not config_test("dictionary", "make_mdict", "yes"):
        pr.amber("moving is disabled in the config")
        return
    project_dir, deva_dir = _project_paths()
    sync_mdict_dir = (
        deva_dir / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "MDict"
    )
    share_dir = project_dir / "exporter" / "share"
    _unzip(share_dir / "dpd-mdict.zip", sync_mdict_dir)


def _task_move_mdict_ru() -> None:
    if not config_test("dictionary", "make_mdict", "yes"):
        pr.amber("moving is disabled in the config")
        return
    project_dir, deva_dir = _project_paths()
    sync_mdict_dir = (
        deva_dir
        / "Library"
        / "Mobile Documents"
        / "com~apple~CloudDocs"
        / "Documents"
        / "MDict"
    )
    share_dir = project_dir / "exporter" / "share"
    _unzip(share_dir / "ru-dpd-mdict.zip", sync_mdict_dir)


def _task_copy_dpdsbs_from_sbs2filesrv() -> None:
    project_dir, deva_dir = _project_paths()
    share_sbs_dir = project_dir / "exporter" / "share" / "SBS"
    software_dir = _software_dir(deva_dir)
    gd_dir = software_dir / "Golden Dictionary" / "Default"
    md_dir = software_dir / "MDict" / "dpd"
    _require_dirs(gd_dir, md_dir)

    _unzip(share_sbs_dir / "dpd.zip", gd_dir / "dpd")
    _copy_pair(
        [
            (share_sbs_dir / "dpd-mdict.mdx", md_dir),
            (share_sbs_dir / "dpd-mdict.mdd", md_dir),
        ]
    )


def _task_copy_dpdsbs_from_share2sbs() -> None:
    project_dir, _ = _project_paths()
    share_dir = project_dir / "exporter" / "share"
    sbs_dir = share_dir / "SBS"
    sbs_dir.mkdir(parents=True, exist_ok=True)

    dpd_goldendict_src = share_dir / "dpd"
    _copy_tree(
        dpd_goldendict_src,
        sbs_dir / dpd_goldendict_src.name,
        archive_base=sbs_dir / "dpd",
    )
    _copy_pair(
        [
            (share_dir / "dpd-mdict.mdx", sbs_dir),
            (share_dir / "dpd-mdict.mdd", sbs_dir),
        ]
    )


def _task_copy_rudpd_from_share2filesrv() -> None:
    project_dir, deva_dir = _project_paths()
    share_dir = project_dir / "exporter" / "share"
    software_dir = _software_dir(deva_dir)
    gd_dir = software_dir / "Golden Dictionary" / "Optional"
    md_dir = software_dir / "MDict" / "ru-dpd"
    _require_dirs(gd_dir, md_dir)

    dpd_goldendict_src = share_dir / "ru-dpd"
    _copy_tree(dpd_goldendict_src, gd_dir / dpd_goldendict_src.name)
    _copy_pair(
        [
            (share_dir / "ru-dpd-mdict.mdx", md_dir),
            (share_dir / "ru-dpd-mdict.mdd", md_dir),
        ]
    )


TASKS: dict[str, Callable[[], None]] = {
    "unzip_dpd_to_filesrv": _task_unzip_dpd_to_filesrv,
    "unzip_dpd_to_gd": _task_unzip_dpd_to_gd,
    "unzip_dpd_to_share": _task_unzip_dpd_to_share,
    "unzip_dpd_sbs_to_filesrv": _task_unzip_dpd_sbs_to_filesrv,
    "unzip_rudpd_to_filesrv": _task_unzip_rudpd_to_filesrv,
    "unzip_classes_to_filesrv": _task_unzip_classes_to_filesrv,
    "move_mdict": _task_move_mdict,
    "move_mdict_ru": _task_move_mdict_ru,
    "copy_dpdsbs_from_sbs2filesrv": _task_copy_dpdsbs_from_sbs2filesrv,
    "copy_dpdsbs_from_share2sbs": _task_copy_dpdsbs_from_share2sbs,
    "copy_rudpd_from_share2filesrv": _task_copy_rudpd_from_share2filesrv,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one of the dictionary distribution tasks."
    )
    parser.add_argument("task", choices=sorted(TASKS))
    args = parser.parse_args()

    pr.tic()
    TASKS[args.task]()
    pr.toc()


if __name__ == "__main__":
    main()
