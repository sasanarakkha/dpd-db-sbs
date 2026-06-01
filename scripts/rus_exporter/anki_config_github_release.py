"""Configure config.ini anki section with CI paths before running headless Anki."""

import os

from tools.configger import config_update
from tools.printer import printer as pr


def main() -> None:
    pr.tic()
    workspace = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
    collection_path = f"{workspace}/temp/anki_collection/collection.anki2"
    backup_path = f"{workspace}/temp/anki_backup/"
    config_update("anki", "db_path_sbs", collection_path)
    config_update("anki", "backup_path_sbs", backup_path)
    pr.yes(f"anki db_path_sbs → {collection_path}")
    pr.toc()


if __name__ == "__main__":
    main()
