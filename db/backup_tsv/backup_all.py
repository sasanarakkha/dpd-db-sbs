#!/usr/bin/env python3

"""Save all tables to db/backup_tsv folder."""

from rich.console import Console

from db.backup_tsv.backup_dpd_headwords_and_roots import (
    backup_dpd_headwords,
    backup_dpd_roots,
)
from db.backup_tsv.backup_dps import (
    backup_roots_ru,
    backup_ru,
    backup_sbs,
)
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr

console = Console()


def backup_all_tables():
    pr.tic()
    console.print("[bold bright_yellow]Backing up all tables to db/backup_tsv folder")
    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)

    dps_headwords_path = str(pth.pali_word_path)
    dps_roots_path = str(pth.pali_root_path)
    dps_ru_roots_path = str(dpspth.ru_root_path)
    dps_ru_path = str(dpspth.russian_path)
    dps_sbs_path = str(dpspth.sbs_path)

    backup_dpd_headwords(db_session, pth, dps_headwords_path)
    backup_dpd_roots(db_session, pth, dps_roots_path)
    backup_ru(db_session, dpspth, dps_ru_path)
    backup_roots_ru(db_session, dpspth, dps_ru_roots_path)
    backup_sbs(db_session, dpspth, dps_sbs_path)

    db_session.close()
    pr.toc()


if __name__ == "__main__":
    backup_all_tables()
