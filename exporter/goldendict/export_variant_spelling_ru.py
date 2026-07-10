"""Compile HTML data for variants and spelling mistakes."""

import csv
from typing import List, Tuple

from minify_html import minify

from tools.goldendict_exporter import DictEntry
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.paths_ru import RuPaths
from tools.printer import printer as pr
from tools.utils import (
    RenderedSizes,
    default_rendered_sizes,
    squash_whitespaces,
    sum_rendered_sizes,
)
from exporter.jinja2_env import get_jinja2_env
from exporter.goldendict.data_classes_dps import VariantData, SpellingData


def generate_variant_spelling_html(
    pth: ProjectPaths, rupth: RuPaths
) -> Tuple[List[DictEntry], RenderedSizes]:
    """Generate html for variant readings and spelling corrections."""

    pr.green_tmr("generating variants html")

    rendered_sizes = []

    jinja_env = get_jinja2_env("exporter/goldendict/ru_components/templates")

    variant_dict = test_and_make_variant_dict(pth)
    spelling_dict = test_and_make_spelling_dict(pth)

    variant_data_list, sizes = generate_variant_data_list(
        rupth,
        variant_dict,
        jinja_env,
    )
    rendered_sizes.append(sizes)

    spelling_data_list, sizes = generate_spelling_data_list(
        rupth,
        spelling_dict,
        jinja_env,
    )
    rendered_sizes.append(sizes)

    variant_spelling_data_list = variant_data_list + spelling_data_list

    pr.yes(len(variant_spelling_data_list))
    return variant_spelling_data_list, sum_rendered_sizes(rendered_sizes)


def test_and_make_variant_dict(pth: ProjectPaths) -> dict:
    variant_dict: dict = {}

    with open(pth.variant_readings_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            variant = row["variant"]
            main = row["main"]

            # test if variant equals main reading
            if variant == main:
                pr.red(f"ERROR: variant==main! {variant}: {main}")
                continue

            # test if variant occurs twice
            if variant in variant_dict:
                pr.red(f"ERROR: dupes! {variant}")
                continue

            # all ok then add
            variant_dict[variant] = main

    return variant_dict


def generate_variant_data_list(
    rupth: RuPaths,
    variant_dict: dict,
    jinja_env,
) -> Tuple[List[DictEntry], RenderedSizes]:
    size_dict = default_rendered_sizes()

    variant_data_list: List[DictEntry] = []

    # The plain header has no per-entry variables — render it once.
    header_squashed = squash_whitespaces(VariantData("", "", jinja_env).header)

    for __counter__, (variant, main) in enumerate(variant_dict.items()):
        template = jinja_env.get_template("dpd_variant_reading_ru.jinja")
        content = template.render(main=main)

        html = ""
        html += "<body>"
        html += content
        html += "</body></html>"

        html = header_squashed + minify(html)

        size_dict["variant_readings"] += len(html)
        synonyms = add_niggahitas([variant])

        size_dict["variant_synonyms"] += len(str(synonyms))

        res = DictEntry(
            word=variant,
            definition_html=html,
            definition_plain="",
            synonyms=synonyms,
        )

        variant_data_list.append(res)

    return variant_data_list, size_dict


def test_and_make_spelling_dict(pth: ProjectPaths) -> dict:
    spelling_dict: dict = {}

    with open(pth.spelling_mistakes_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            mistake = row["mistake"]
            correction = row["correction"]

            # test if mistake equals correction
            if mistake == correction:
                pr.red(f"ERROR: mistake==correction! {mistake}: {correction}")
                continue

            # test if variant occurs twice
            if mistake in spelling_dict:
                pr.red(f"ERROR: dupes! {mistake}")
                continue

            # all ok then add
            spelling_dict[mistake] = correction

        assert "mātāpituraakhatañca" in spelling_dict

    return spelling_dict


def generate_spelling_data_list(
    rupth: RuPaths,
    spelling_dict: dict,
    jinja_env,
) -> Tuple[List[DictEntry], RenderedSizes]:
    size_dict = default_rendered_sizes()

    spelling_data_list: List[DictEntry] = []

    # The plain header has no per-entry variables — render it once.
    header_squashed = squash_whitespaces(SpellingData("", "", jinja_env).header)

    for __counter__, (mistake, correction) in enumerate(spelling_dict.items()):
        template = jinja_env.get_template("dpd_spelling_mistake_ru.jinja")
        content = template.render(correction=correction)

        html = ""
        html += "<body>"
        html += content
        html += "</body></html>"

        html = header_squashed + minify(html)

        size_dict["spelling_mistakes"] += len(html)
        synonyms = add_niggahitas([mistake])

        size_dict["spelling_synonyms"] += len(str(synonyms))

        res = DictEntry(
            word=mistake,
            definition_html=html,
            definition_plain="",
            synonyms=synonyms,
        )

        spelling_data_list.append(res)

    return spelling_data_list, size_dict


if __name__ == "__main__":
    pth = ProjectPaths()
    ru_path = RuPaths()
    generate_variant_spelling_html(pth, ru_path)
