#!/usr/bin/env python3

"""Add help and abbreviations to the Lookup table (ru)."""

from dataclasses import dataclass
from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from tools.lookup_sync import sync_lookup_column
from tools.paths import ProjectPaths
from tools.paths_ru import RuPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_as_dict_with_different_key, read_tsv_dict


@dataclass
class GlobalVars:
    pth: ProjectPaths
    rupth: RuPaths
    db_session: Session


def normalize_other_abbreviation_key(key: str) -> str:
    return key[:-1] if key.endswith(".") else key


def ensure_abbrev_other_column(g: GlobalVars) -> None:
    """Add abbrev_other column to lookup table if it doesn't already exist."""
    insp = sa_inspect(g.db_session.get_bind())
    columns = [col["name"] for col in insp.get_columns("lookup")]
    if "abbrev_other" not in columns:
        g.db_session.execute(
            text("ALTER TABLE lookup ADD COLUMN abbrev_other TEXT DEFAULT ''")
        )
        g.db_session.commit()
        pr.green("added abbrev_other column to lookup")


def add_help_ru(g: GlobalVars) -> None:
    pr.green("adding help (ru)")

    ru_help_data = read_tsv_as_dict_with_different_key(g.rupth.help_tsv_path, 2)
    data = {key: v["ru_meaning"] for key, v in ru_help_data.items()}
    sync_lookup_column(g.db_session, "help", data)


def add_abbreviations_ru(g: GlobalVars) -> None:
    """Add abbreviations to lookup (ru)"""
    pr.green("adding abbreviations (ru)")

    ru_abbrevs = read_tsv_as_dict_with_different_key(g.rupth.abbreviations_tsv_path, 5)
    sync_lookup_column(g.db_session, "abbrev", ru_abbrevs)


def add_abbreviations_other_ru(g: GlobalVars) -> None:
    """Add other-source abbreviations (PTS, CPD, Cone, CST, General) to lookup."""
    pr.green("adding abbreviations other")

    rows = read_tsv_dict(g.pth.abbreviations_other_tsv_path)
    rows.sort(key=lambda row: normalize_other_abbreviation_key(row["abbreviation"]))

    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        key = normalize_other_abbreviation_key(row["abbreviation"])
        if not key:
            continue
        entry = {
            "source": row["source"],
            "meaning": row["meaning"],
            "notes": row["notes"],
        }
        grouped.setdefault(key, []).append(entry)

    sync_lookup_column(g.db_session, "abbrev_other", grouped)


def main() -> None:
    pr.tic()
    pr.yellow_title("adding help and abbreviations to lookup (ru)")
    pth = ProjectPaths()
    g = GlobalVars(pth=pth, rupth=RuPaths(), db_session=get_db_session(pth.dpd_db_path))
    ensure_abbrev_other_column(g)
    add_help_ru(g)
    add_abbreviations_ru(g)
    add_abbreviations_other_ru(g)
    pr.toc()


if __name__ == "__main__":
    main()
