"""Produce/refresh the two committed seed archives in resources/anki/."""

import sqlite3
import tarfile
import shutil
from pathlib import Path

from tools.configger import config_read
from tools.printer import printer as pr


def _build_seed(src_path: Path, tmp_seed: Path) -> None:
    """Copy collection file then wipe notes/cards, keeping note types and decks."""
    shutil.copy2(src_path, tmp_seed)
    con = sqlite3.connect(tmp_seed)
    con.execute("DELETE FROM notes")
    con.execute("DELETE FROM cards")
    con.execute("DELETE FROM revlog")
    con.execute("DELETE FROM graves")
    con.commit()
    con.close()


def main() -> None:
    pr.tic()
    pr.green("reading config")

    db_path_sbs = config_read("anki", "db_path_sbs")
    if not db_path_sbs:
        pr.no("db_path_sbs not set in config.ini — run local anki config first")
        pr.toc()
        return

    src_path = Path(db_path_sbs)
    if not src_path.exists():
        pr.no(f"source collection not found: {src_path}")
        pr.toc()
        return

    media_dir = src_path.parent / "collection.media"

    pr.green("building seed collection")
    tmp_seed = Path("temp/seed_tmp/collection.anki2")
    tmp_seed.parent.mkdir(parents=True, exist_ok=True)
    if tmp_seed.exists():
        tmp_seed.unlink()

    _build_seed(src_path, tmp_seed)

    out = Path("resources/anki/seed_collection.anki2.tar.gz")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out, "w:gz") as tar:
        tar.add(tmp_seed, arcname="collection.anki2")
    shutil.rmtree(tmp_seed.parent)
    pr.yes(f"seed → {out}")

    pr.green("building media archive")
    if not media_dir.exists():
        pr.no(f"media dir not found: {media_dir}")
        pr.toc()
        return

    media_out = Path("resources/anki/collection_media.tar.gz")
    with tarfile.open(media_out, "w:gz") as tar:
        for f in sorted(media_dir.iterdir()):
            tar.add(f, arcname=f.name)
    pr.yes(f"media → {media_out}")

    pr.toc()


if __name__ == "__main__":
    main()
