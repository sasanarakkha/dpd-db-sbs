"""Apply a named config.ini profile before running the exporter or Anki scripts."""

import argparse
import os

from tools.configger import config_update
from tools.printer import printer as pr

PROFILES: dict[str, dict[str, dict[str, str]]] = {
    "local_rus": {
        "regenerate": {
            "db_rebuild": "no",
            "inflections": "no",
            "transliterations": "no",
            "freq_maps": "no",
        },
        "dictionary": {
            "make_mdict": "no",
            "link_url": "https://buddhas-words.sbs.rocks/",
            "show_id": "no",
            "show_sbs_data": "no",
            "show_ru_data": "no",
            "show_ta_data": "no",
            "show_grammar": "no",
        },
        "exporter": {
            "make_dpd": "yes",
            "make_grammar": "no",
            "make_deconstructor": "no",
            "make_variants": "no",
            "make_ebook": "no",
            "make_pdf": "no",
            "make_tpr": "no",
            "tarball_db": "no",
        },
        "deconstructor": {"use_premade": "yes"},
        "anki": {"update": "no"},
        "goldendict": {"copy_unzip": "yes"},
    },
    "local_sbs": {
        "regenerate": {
            "db_rebuild": "no",
            "inflections": "no",
            "transliterations": "no",
            "freq_maps": "no",
        },
        "dictionary": {
            "make_mdict": "no",
            "link_url": "https://buddhas-words.sbs.rocks/",
            "show_id": "yes",
            "show_sbs_data": "yes",
            "show_ru_data": "yes",
            "show_ta_data": "no",
            "show_grammar": "yes",
        },
        "exporter": {
            "make_dpd": "yes",
            "make_grammar": "no",
            "make_deconstructor": "no",
            "make_variants": "no",
            "make_ebook": "no",
            "make_pdf": "no",
            "make_tpr": "yes",
            "tarball_db": "no",
        },
        "deconstructor": {"use_premade": "yes"},
        "anki": {"update": "no"},
        "goldendict": {"copy_unzip": "yes"},
    },
    "release_rus": {
        "regenerate": {
            "db_rebuild": "no",
            "inflections": "no",
            "transliterations": "no",
            "freq_maps": "no",
        },
        "dictionary": {
            "make_mdict": "yes",
            "link_url": "https://find.dhamma.gift/bw/",
            "show_id": "no",
            "show_sbs_data": "no",
            "show_ru_data": "yes",
            "show_ta_data": "no",
            "show_grammar": "no",
            "data_limit": "0",
        },
        "exporter": {
            "make_dpd": "yes",
            "make_grammar": "yes",
            "make_deconstructor": "yes",
            "make_variants": "no",
            "make_ebook": "yes",
            "make_tbw": "yes",
            "make_tpr": "yes",
            "tarball_db": "yes",
        },
        "anki": {"update": "no"},
        "goldendict": {"copy_unzip": "yes"},
    },
    "release_sbs": {
        "regenerate": {
            "db_rebuild": "no",
            "inflections": "no",
            "transliterations": "no",
            "freq_maps": "no",
        },
        "dictionary": {
            "make_mdict": "yes",
            "link_url": "https://find.dhamma.gift/bw/",
            "show_id": "no",
            "show_sbs_data": "yes",
            "show_ru_data": "no",
            "show_ta_data": "no",
            "show_grammar": "no",
            "data_limit": "0",
        },
        "exporter": {
            "make_dpd": "yes",
            "make_grammar": "no",
            "make_deconstructor": "no",
            "make_variants": "no",
            "make_ebook": "no",
            "make_tbw": "no",
            "make_tpr": "no",
            "tarball_db": "no",
        },
        "anki": {"update": "no"},
        "goldendict": {"copy_unzip": "no"},
    },
    "release_ta": {
        "regenerate": {
            "db_rebuild": "no",
            "inflections": "no",
            "transliterations": "no",
            "freq_maps": "no",
        },
        "dictionary": {
            "make_mdict": "yes",
            "link_url": "https://find.dhamma.gift/bw/",
            "show_id": "no",
            "show_sbs_data": "no",
            "show_ru_data": "no",
            "show_ta_data": "yes",
            "show_grammar": "no",
            "data_limit": "0",
        },
        "exporter": {
            "make_dpd": "yes",
            "make_grammar": "no",
            "make_deconstructor": "no",
            "make_variants": "no",
            "make_ebook": "no",
            "make_tbw": "no",
            "make_tpr": "no",
            "tarball_db": "no",
        },
        "anki": {"update": "no"},
        "goldendict": {"copy_unzip": "no"},
    },
    "server_sbs": {
        "regenerate": {
            "db_rebuild": "no",
            "inflections": "no",
            "transliterations": "no",
            "freq_maps": "no",
        },
        "dictionary": {
            "make_mdict": "yes",
            "link_url": "https://buddhas-words.sbs.rocks/",
            "show_id": "no",
            "show_sbs_data": "yes",
            "show_ru_data": "no",
            "show_ta_data": "no",
            "show_grammar": "no",
        },
        "exporter": {
            "make_dpd": "yes",
            "make_grammar": "no",
            "make_deconstructor": "no",
            "make_variants": "no",
            "make_ebook": "no",
            "make_pdf": "no",
            "make_tpr": "no",
            "tarball_db": "no",
        },
        "deconstructor": {"use_premade": "yes"},
        "anki": {"update": "no"},
        "goldendict": {"copy_unzip": "no"},
    },
    "release_full_ru": {
        "regenerate": {
            "db_rebuild": "yes",
            "inflections": "yes",
            "transliterations": "yes",
            "freq_maps": "yes",
        },
        "deconstructor": {"use_premade": "yes"},
        "dictionary": {
            "make_mdict": "yes",
            "link_url": "https://find.dhamma.gift/bw/",
            "show_id": "no",
            "show_sbs_data": "no",
            "show_ru_data": "no",
            "show_ta_data": "no",
            "show_grammar": "no",
            "data_limit": "0",
        },
        "exporter": {
            "make_dpd": "yes",
            "make_grammar": "yes",
            "make_deconstructor": "yes",
            "make_variants": "yes",
            "make_ebook": "yes",
            "tarball_db": "yes",
            "make_tbw": "yes",
            "make_tpr": "yes",
            "make_sc_ru": "yes",
        },
        "anki": {"update": "no"},
        "goldendict": {"copy_unzip": "no"},
    },
}

PROFILE_DESCRIPTIONS: dict[str, str] = {
    "local_rus": "DPD-RU for local use — minimal rebuild, GoldenDict copy, no SBS/grammar data",
    "local_sbs": "DPD-SBS-RU for local use — minimal rebuild, SBS+RU+grammar data, GoldenDict copy",
    "release_rus": "GitHub release for DPD-RU — Russian data, full grammar/ebook/tpr/tarball",
    "release_sbs": "GitHub release for DPD-SBS — SBS data only, minimal exports",
    "release_ta": "GitHub release for DPD-TA — Tamil data only, minimal exports",
    "server_sbs": "DPD-SBS for the fileserver — SBS data, MDict, no copy/unzip",
    "release_full_ru": "Full Russian release — complete DB rebuild, all regenerations, all exporters",
    "anki_ci": "CI Anki paths — sets anki.db_path_sbs and anki.backup_path_sbs from GITHUB_WORKSPACE",
}


def apply_profile(profile: str) -> None:
    if profile == "anki_ci":
        workspace = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
        collection_path = f"{workspace}/temp/anki_collection/collection.anki2"
        backup_path = f"{workspace}/temp/anki_backup/"
        config_update("anki", "db_path_sbs", collection_path)
        config_update("anki", "backup_path_sbs", backup_path)
        pr.yes(f"anki db_path_sbs → {collection_path}")
        return

    sections = PROFILES[profile]
    for section, keys in sections.items():
        for key, value in keys.items():
            config_update(section, key, value)
    pr.yes(f"config profile applied: {profile}")


def main() -> None:
    profile_help_lines = "\n".join(
        f"  {name:<18} {desc}" for name, desc in PROFILE_DESCRIPTIONS.items()
    )
    parser = argparse.ArgumentParser(
        description="Apply a named config.ini profile before running the exporter or Anki scripts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Profiles:\n{profile_help_lines}",
    )
    parser.add_argument(
        "--profile",
        required=True,
        choices=list(PROFILE_DESCRIPTIONS.keys()),
        metavar="PROFILE",
        help=(
            "Config profile to apply. "
            f"Choices: {', '.join(PROFILE_DESCRIPTIONS)}. "
            "Run with --help to see descriptions."
        ),
    )
    args = parser.parse_args()

    pr.tic()
    pr.cyan(f"Applying config profile: {args.profile}")
    apply_profile(args.profile)
    pr.toc()


if __name__ == "__main__":
    main()
