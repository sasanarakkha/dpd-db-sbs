#!/usr/bin/env python3

"""Setup config for DPD-RU for local use."""

from rich import print

from tools.configger import config_update
from tools.printer import printer as pr


def main():
    pr.tic()
    print("[bright_yellow]local DPD-RU config options")

    config_update("regenerate", "db_rebuild", "no")
    config_update("regenerate", "inflections", "no")
    config_update("regenerate", "transliterations", "no")
    config_update("regenerate", "freq_maps", "no")

    config_update("dictionary", "make_mdict", "no")
    config_update("dictionary", "link_url", "https://buddhas-words.sbs.rocks/")
    config_update("dictionary", "show_id", "no")
    config_update("dictionary", "show_sbs_data", "no")
    config_update("dictionary", "show_ru_data", "no")
    config_update("dictionary", "show_ta_data", "no")
    config_update("dictionary", "show_grammar", "no")

    config_update("exporter", "make_dpd", "yes")
    config_update("exporter", "make_grammar", "no")
    config_update("exporter", "make_deconstructor", "no")
    config_update("exporter", "make_variants", "no")
    config_update("exporter", "make_ebook", "no")
    config_update("exporter", "make_pdf", "no")
    config_update("exporter", "make_tpr", "no")
    config_update("exporter", "tarball_db", "no")

    config_update("deconstructor", "use_premade", "yes")

    config_update("anki", "update", "no")
    config_update("goldendict", "copy_unzip", "yes")

    pr.toc()


if __name__ == "__main__":
    main()
