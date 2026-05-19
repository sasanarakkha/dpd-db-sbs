#!/usr/bin/env python3
"""Quick starter template for getting a database session and iterating through headwords."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    pr.tic()
    pth = ProjectPaths()
    pr.green_tmr("connecting to database")
    db_session = get_db_session(pth.dpd_db_path)
    pr.yes("ok")

    pr.green_tmr("querying headwords")
    db = db_session.query(DpdHeadword).all()
    pr.yes(len(db))

    for i in db:
        if i.su is not None:
            pr.white(i.lemma_1)

    db_session.close()
    pr.toc()


if __name__ == "__main__":
    main()
