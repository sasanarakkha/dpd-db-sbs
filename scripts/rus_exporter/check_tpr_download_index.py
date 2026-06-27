"""Check and report the current state of the TPR download list index for the DPD with Russian entry."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from tools.configger import config_test
from tools.printer import printer as pr


def main() -> None:
    if not config_test("exporter", "make_tpr", "yes"):
        pr.green_title("disabled in config.ini")
        return

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test-path",
        type=str,
        help="Path to use instead of the real submodule for testing",
    )
    parser.add_argument(
        "--skip-reset",
        action="store_true",
        help="Skip resetting the submodule to upstream (use to verify local changes)",
    )
    args = parser.parse_args()

    if args.test_path:
        submodule_path = Path(args.test_path)
    else:
        # Path(__file__).parents[2] / "resources" / "tpr_downloads"
        # scripts/rus_exporter/check_tpr_download_index.py -> parents[2] is project root
        submodule_path = Path(__file__).parents[2] / "resources" / "tpr_downloads"

    if not submodule_path.exists():
        pr.red(f"Submodule path missing: {submodule_path}")
        sys.exit(1)

    if not args.test_path and not args.skip_reset:
        pr.green("Resetting submodule to upstream...")
        try:
            subprocess.run(
                ["git", "fetch", "origin", "master"], cwd=submodule_path, check=True
            )
            subprocess.run(
                ["git", "reset", "--hard", "origin/master"],
                cwd=submodule_path,
                check=True,
            )
            subprocess.run(["git", "clean", "-fd"], cwd=submodule_path, check=True)
        except subprocess.CalledProcessError as e:
            pr.red(f"Failed to reset submodule: {e}")
            sys.exit(1)
    elif args.skip_reset:
        pr.amber("Skipping reset: checking current local state...")

    json_path = submodule_path / "download_source_files" / "download_list.json"
    if not json_path.exists():
        pr.red(f"JSON file missing: {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        download_list = json.load(f)

    for i, entry in enumerate(download_list):
        pr.cyan(f"{i}: {entry.get('name')}")

    ru_idx = None
    for i, entry in enumerate(download_list):
        if entry.get("name") == "DPD with Russian":
            ru_idx = i
            break

    last_idx = len(download_list) - 1

    if ru_idx is None:
        pr.red("DPD with Russian entry not found in download_list.json")
    elif ru_idx == last_idx:
        pr.yes(f"DPD with Russian is the last entry (index {ru_idx}) — OK")
    else:
        pr.amber(
            f"DPD with Russian is at {ru_idx}, last is {last_idx}. Run exporter/tpr/tpr_exporter_ru.py to fix."
        )


if __name__ == "__main__":
    main()
