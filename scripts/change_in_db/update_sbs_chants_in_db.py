"""Update sbs_chant_eng_*/sbs_chapter_* from sbs_index.csv; fuzzy-prompts for unrecognized pali chants."""

from db.db_helpers import get_db_session
from db.models import SBS
from sqlalchemy.orm import Session
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

    sbs_entries: list[SBS] = db_session.query(SBS).all()

    for sbs in sbs_entries:
        for number in (1, 2):
            pali_attr = f"sbs_chant_pali_{number}"
            eng_attr = f"sbs_chant_eng_{number}"
            chap_attr = f"sbs_chapter_{number}"
            chant_pali: str = getattr(sbs, pali_attr, "")
            if not chant_pali:
                continue

            # Pass A: exact match → auto-correct eng/chapter
            found: tuple[str, str] | None = sbs_tools.fetch_sbs_index(chant_pali)
            if found is not None:
                english, chapter = found
                old_eng: str = getattr(sbs, eng_attr, "")
                old_chap: str = getattr(sbs, chap_attr, "")
                if old_eng != english or old_chap != chapter:
                    setattr(sbs, eng_attr, english)
                    setattr(sbs, chap_attr, chapter)
                    pr.amber(f"ID {sbs.id} {pali_attr}: auto-fixed eng/chapter")
                    auto_fixed += 1
                continue

            # Pass B: not in index → fuzzy match + prompt
            closest: tuple[str, float] | None = sbs_tools.find_closest_chant(
                chant_pali, threshold=FUZZY_THRESHOLD
            )
            if closest is not None:
                candidate, ratio = closest
                try:
                    answer = (
                        input(
                            f'ID {sbs.id} | {pali_attr}: "{chant_pali}" '
                            f'→ did you mean "{candidate}" (ratio={ratio:.2f})? [y/n]: '
                        )
                        .strip()
                        .lower()
                    )
                except EOFError:
                    answer = "n"
                if answer == "y":
                    fix: tuple[str, str] | None = sbs_tools.fetch_sbs_index(candidate)
                    if fix is not None:
                        setattr(sbs, pali_attr, candidate)
                        setattr(sbs, eng_attr, fix[0])
                        setattr(sbs, chap_attr, fix[1])
                        fuzzy_fixed += 1
                    continue

            unresolved.append(f'ID {sbs.id} {pali_attr}: "{chant_pali}"')

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
