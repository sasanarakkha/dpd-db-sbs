#!/usr/bin/env python3

"""Setup config for github Russian release."""

from rich import print

from tools.configger import config_update
from tools.printer import printer as pr


def main():
    pr.tic()
    print("[bright_yellow]github Russian release config options")

    config_update("regenerate", "db_rebuild", "no")
    config_update("regenerate", "inflections", "no")
    config_update("regenerate", "transliterations", "no")
    config_update("regenerate", "freq_maps", "no")

    config_update("dictionary", "make_mdict", "yes")
    config_update("dictionary", "link_url", "https://find.dhamma.gift/bw/")
    config_update("dictionary", "show_id", "no")
    config_update("dictionary", "show_sbs_data", "no")
    config_update("dictionary", "show_ru_data", "yes")
    config_update("dictionary", "show_ta_data", "no")
    config_update("dictionary", "show_grammar", "no")
    config_update("dictionary", "data_limit", "0")

    config_update("exporter", "make_dpd", "yes")
    config_update("exporter", "make_grammar", "yes")
    config_update("exporter", "make_deconstructor", "yes")
    config_update("exporter", "make_variants", "no")
    config_update("exporter", "make_ebook", "yes")
    config_update("exporter", "make_tbw", "yes")
    config_update("exporter", "make_tpr", "yes")
    config_update("exporter", "tarball_db", "yes")

    config_update("anki", "update", "no")
    config_update("goldendict", "copy_unzip", "yes")

    pr.toc()


if __name__ == "__main__":
    main()
