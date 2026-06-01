"""Update sbs_chant_eng_*/sbs_chapter_* from sbs_index.csv; fuzzy-prompts for unrecognized pali chants."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword, SBS
from sqlalchemy.orm import Session, joinedload
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.sbs_table_functions import SBS_table_tools

FUZZY_THRESHOLD = 0.8


def update_sbs_chants(db_session: Session, sbs_tools: SBS_table_tools) -> None:
    pr.tic()
    pr.green("update sbs chants")
    pr.bip()

    auto_fixed = 0
    fuzzy_fixed = 0
    unresolved: list[str] = []

    results = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.sbs))
        .filter(DpdHeadword.sbs != None)  # noqa: E711
        .all()
    )

    for dpd_word in results:
        sbs: SBS = dpd_word.sbs
        if not sbs:
            continue

        for number in (1, 2):
            chant_pali: str = getattr(sbs, f"sbs_chant_pali_{number}", "") or ""
            if not chant_pali:
                continue

            # Pass A: exact match → auto-correct eng/chapter
            result = sbs_tools.fetch_sbs_index(chant_pali)
            if result is not None:
                english, chapter = result
                old_eng: str = getattr(sbs, f"sbs_chant_eng_{number}", "") or ""
                old_chap: str = getattr(sbs, f"sbs_chapter_{number}", "") or ""
                if old_eng != english or old_chap != chapter:
                    setattr(sbs, f"sbs_chant_eng_{number}", english)
                    setattr(sbs, f"sbs_chapter_{number}", chapter)
                    pr.amber(
                        f"ID {sbs.id} sbs_chant_pali_{number}: auto-fixed eng/chapter"
                    )
                    auto_fixed += 1
                continue

            # Pass B: not in index → fuzzy match + prompt
            closest = sbs_tools.find_closest_chant(
                chant_pali, threshold=FUZZY_THRESHOLD
            )
            if closest is not None:
                candidate, ratio = closest
                try:
                    answer = (
                        input(
                            f'ID {sbs.id} | sbs_chant_pali_{number}: "{chant_pali}" '
                            f'→ did you mean "{candidate}" (ratio={ratio:.2f})? [y/n]: '
                        )
                        .strip()
                        .lower()
                    )
                except EOFError:
                    answer = "n"
                if answer == "y":
                    fix = sbs_tools.fetch_sbs_index(candidate)
                    if fix:
                        setattr(sbs, f"sbs_chant_pali_{number}", candidate)
                        setattr(sbs, f"sbs_chant_eng_{number}", fix[0])
                        setattr(sbs, f"sbs_chapter_{number}", fix[1])
                        fuzzy_fixed += 1
                    continue

            unresolved.append(f'ID {sbs.id} sbs_chant_pali_{number}: "{chant_pali}"')

    db_session.commit()

    if auto_fixed:
        pr.yes(f"{auto_fixed} auto-fixed")
    if fuzzy_fixed:
        pr.yes(f"{fuzzy_fixed} fuzzy-fixed")
    if unresolved:
        pr.no(f"{len(unresolved)} unresolved")
        for item in unresolved:
            pr.amber(item)
    if not auto_fixed and not fuzzy_fixed and not unresolved:
        pr.yes("no changes needed")

    pr.toc()


if __name__ == "__main__":
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    sbs_tools = SBS_table_tools()
    update_sbs_chants(db_session, sbs_tools)
    db_session.close()
