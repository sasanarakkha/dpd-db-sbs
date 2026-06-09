#!/usr/bin/env python3

"""Filter idiom headwords and replace <b> </b> with a space in SBS.sbs_example_1."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword, SBS
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    target = "<b> </b>"
    replacement = " "

    words_to_update = (
        db_session.query(DpdHeadword, SBS)
        .join(SBS, SBS.id == DpdHeadword.id)
        .filter(
            DpdHeadword.pos == "idiom",
            SBS.sbs_example_1.contains(target),
        )
        .all()
    )

    for word, sbs in words_to_update:
        old_value = sbs.sbs_example_1
        new_value = old_value.replace(target, replacement)
        sbs.sbs_example_1 = new_value

        pr.yellow_title(f"{word.id} sbs_example_1:")
        pr.white("")
        pr.white(old_value)
        pr.white("")
        pr.white(new_value)
        pr.white("")

    # db_session.commit()
    db_session.close()


if __name__ == "__main__":
    main()
