"""Verify strict shadow copies keep structural parity with their upstream sources."""

import ast
import json
from pathlib import Path

import pytest

type WhitelistEntry = dict[str, object]


def get_registry_path() -> Path:
    return Path("kamma/upstream_sync/registry.json")


def load_registry() -> dict[str, object]:
    path = get_registry_path()
    if not path.exists():
        pytest.skip("registry.json not found")
    return json.loads(path.read_text(encoding="utf-8"))


def get_python_pairs() -> list[tuple[str, str]]:
    registry = load_registry()
    pairs: list[tuple[str, str]] = []

    for shadow, upstream in registry.get("russian_copies", {}).items():  # type: ignore[union-attr]
        if shadow.endswith(".py") and upstream.endswith(".py"):
            pairs.append((shadow, upstream))

    for shadow, upstream in registry.get("sbs_copies", {}).items():  # type: ignore[union-attr]
        if shadow.endswith(".py") and upstream.endswith(".py"):
            pairs.append((shadow, upstream))

    for shadow, upstream in registry.get("dps_copies", {}).items():  # type: ignore[union-attr]
        if shadow.endswith(".py") and upstream.endswith(".py"):
            pairs.append((shadow, upstream))

    for shadow, upstream in registry.get("tamil_copies", {}).items():  # type: ignore[union-attr]
        if shadow.endswith(".py") and upstream.endswith(".py"):
            pairs.append((shadow, upstream))

    return pairs


def extract_ast_info(filepath: str) -> dict[str, set[str]] | None:
    fp = Path(filepath)
    if not fp.exists():
        return None
    try:
        tree = ast.parse(fp.read_text(encoding="utf-8"), filename=filepath)
    except SyntaxError:
        return None

    imports = set()
    functions = set()
    classes = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for alias in node.names:
                    imports.add(f"{node.module}.{alias.name}")
        elif isinstance(node, ast.FunctionDef):
            functions.add(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.add(node.name)

    return {"imports": imports, "functions": functions, "classes": classes}


WHITELIST: dict[str, WhitelistEntry] = {
    "db/families/family_compound_ru.py": {"functions": ["compile_cf_html"]},
    "db/families/family_idiom_ru.py": {
        "functions": [
            "compile_idioms_html",
            "sync_idiom_numbers_with_family_compound",
            "update_db_cache",
        ],
        "imports": ["re", "json", "db.models.DbInfo"],
    },
    "db/tpd/tpd_to_lookup.py": {
        "functions": [
            "compile_roots_data",
            "make_meaning_plus_case",
            "make_clean_meaning_list",
        ],
        "imports": ["re", "db.models.DpdRoot"],
    },
    "db/families/family_root_ru.py": {
        "functions": [
            "compile_rf_html",
            "make_root_header",
            "make_anki_matrix_data",
            "update_lookup_table",
        ],
        "imports": [
            "collections.defaultdict",
            "db.models.Lookup",
            "db.families.root_info.generate_root_info_html",
            "db.families.root_matrix.generate_root_matrix",
            "tools.lookup_is_another_value.is_another_value",
            "tools.lookup_sync.sync_lookup_column",
            "tools.pali_sort_key.pali_list_sorter",
            "tools.update_test_add.update_test_add",
        ],
    },
    "db/families/family_set_ru.py": {"functions": ["compile_sf_html"]},
    "db/families/family_word_ru.py": {"functions": ["compile_wf_html"]},
    "db/lookup/help_abbrev_add_to_lookup_ru.py": {
        "functions": ["add_abbreviations", "add_help", "add_abbreviations_other"],
        "imports": ["tools.tsv_read_write.read_tsv_as_dict"],
        "missing": True,
    },
    "db/rpd/rpd_to_lookup_ru.py": {"missing": True},
    "exporter/deconstructor/deconstructor_exporter_ru.py": {
        "functions": ["generate_deconstructor_html"],
        "classes": ["GlobalVars"],
    },
    "exporter/goldendict/export_dpd_ru.py": {
        "imports": [
            "db.models.SuttaInfo",
            "exporter.goldendict.data_classes.HeadwordData",
        ]
    },
    "exporter/goldendict/export_dpd_sbs.py": {
        "imports": [
            "db.models.SuttaInfo",
            "exporter.goldendict.data_classes.HeadwordData",
        ]
    },
    "exporter/goldendict/export_epd_sbs.py": {
        "imports": [
            "exporter.goldendict.data_classes.EpdData",
            "exporter.jinja2_env.get_jinja2_env",
            "tools.paths.ProjectPaths",
            "tools.utils.RenderedSizes",
            "tools.utils.default_rendered_sizes",
        ]
    },
    "exporter/goldendict/export_rpd.py": {
        "imports": ["exporter.goldendict.data_classes.EpdData"]
    },
    "exporter/goldendict/export_help_ru.py": {
        "imports": [
            "exporter.goldendict.data_classes.AbbreviationsData",
            "exporter.goldendict.data_classes.HelpData",
        ]
    },
    "exporter/goldendict/export_help_sbs.py": {
        "imports": [
            "tools.paths.ProjectPaths",
            "tools.utils.RenderedSizes",
            "tools.utils.default_rendered_sizes",
            "exporter.goldendict.data_classes.HelpData",
            "exporter.goldendict.data_classes.AbbreviationsData",
        ]
    },
    "exporter/goldendict/export_roots_ru.py": {
        "imports": ["exporter.goldendict.data_classes.RootsData"]
    },
    "exporter/goldendict/export_roots_sbs.py": {
        "imports": [
            "tools.paths.ProjectPaths",
            "tools.utils.RenderedSizes",
            "tools.utils.default_rendered_sizes",
            "exporter.goldendict.data_classes.RootsData",
        ]
    },
    "exporter/goldendict/export_variant_spelling_ru.py": {
        "functions": ["generate_spelling_data_list", "generate_variant_data_list"],
        "imports": [
            "exporter.goldendict.data_classes.VariantData",
            "exporter.goldendict.data_classes.SpellingData",
        ],
    },
    "exporter/goldendict/main_ru.py": {
        "imports": [
            "exporter.goldendict.export_dpd.generate_dpd_html",
            "exporter.goldendict.export_epd.generate_epd_html",
            "exporter.goldendict.export_help.generate_help_html",
            "exporter.goldendict.export_roots.generate_root_html",
        ]
    },
    "exporter/goldendict/main_sbs.py": {
        "imports": [
            "exporter.goldendict.export_dpd.generate_dpd_html",
            "exporter.goldendict.export_epd.generate_epd_html",
            "exporter.goldendict.export_help.generate_help_html",
            "exporter.goldendict.export_roots.generate_root_html",
        ]
    },
    "exporter/grammar_dict/grammar_dict_ru.py": {
        "functions": ["generate_grammar_dict"],
        "classes": ["GlobalVars"],
    },
    "exporter/kindle/kindle_exporter_ru.py": {
        "functions": [
            "html_friendly",
            "make_mobi",
            "parse_args",
            "render_deconstructor_entry",
            "render_dpd_xhtml",
            "render_epd_entry",
            "render_epd_letter_templ",
            "render_epd_xhtml",
            "render_abbreviation_entry",
            "render_ebook_entry",
            "render_ebook_letter_templ",
            "save_abbreviations_xhtml_page",
            "save_content_opf_xhtml",
            "save_title_page_xhtml",
            "zip_epub",
        ],
        "imports": [
            "argparse",
            "exporter.kindle.data_classes.KindleData",
            "pathlib.Path",
        ],
    },
    "exporter/tbw/tbw_exporter_ru.py": {
        "functions": ["generate_tbw_html", "save_js_files_for_tbw"],
        "classes": ["GlobalVars"],
    },
    "exporter/tpr/tpr_exporter_ru.py": {
        "functions": ["generate_tpr_html"],
        "imports": ["tools.uposatha_day.UposathaManger"],
    },
    "exporter/webapp/data_classes_ru.py": {
        "classes": ["SpellingData", "VariantData"],
        "imports": [
            "tools.configger.config_test",
            "tools.meaning_construction.make_grammar_line",
        ],
    },
    "exporter/webapp/main_ru.py": {
        "imports": [
            "exporter.webapp.preloads.load_data",
            "tools.translit.auto_translit_to_roman",
        ],
        "functions": [
            "home_page",
            "db_search_html",
            "db_search_gd",
            "db_search_json",
        ],
    },
    "exporter/webapp/preloads_ru.py": {
        "functions": [
            "load_data",
            "make_ascii_to_unicode_dict",
            "make_headwords_clean_set",
            "make_roots_count_dict",
        ],
        "imports": [
            "collections.defaultdict",
            "typing.Dict",
            "tools.pali_sort_key.pali_list_sorter",
            "unidecode.unidecode",
        ],
    },
    "exporter/webapp/toolkit_ru.py": {
        "functions": [
            "make_dpd_html",
            "get_dpd_html",
            "get_epd_html",
            "get_help_html",
            "get_root_html",
            "get_variant_spelling_html",
        ],
        "imports": [
            "exporter.webapp.data_classes.AbbreviationsData",
            "exporter.webapp.data_classes.DeconstructorData",
            "exporter.webapp.data_classes.EpdData",
            "exporter.webapp.data_classes.GrammarData",
            "exporter.webapp.data_classes.HeadwordData",
            "exporter.webapp.data_classes.HelpData",
            "exporter.webapp.data_classes.ManualVariantData",
            "exporter.webapp.data_classes.RootsData",
            "exporter.webapp.data_classes.SeeData",
            "exporter.webapp.data_classes.AbbreviationsOtherData",
            "exporter.webapp.data_classes.SpellingData",
            "exporter.webapp.data_classes.VariantData",
        ],
    },
    "scripts/backup/backup_dps.py": {
        "functions": [
            "backup_dpd_headwords_and_roots",
            "backup_dpd_roots",
            "split_tsv_file",
            "backup_dpd_headwords",
            "git_commit",
        ],
        "imports": ["db.models.DpdHeadword", "pathlib.Path"],
    },
    "scripts/build/db_rebuild_from_tsv_dps.py": {
        "functions": [
            "make_pali_root_table_data",
            "check_tsv_files",
            "make_pali_word_table_data",
        ],
        "imports": [
            "tools.configger.config_test",
            "db.db_helpers.create_db_if_not_exists",
            "tools.configger.config_update",
            "rich.print",
        ],
    },
    "scripts/export/dps_anki_updater.py": {
        "functions": [
            "unicode_combo_characters",
            "make_new_family_note",
            "update_family",
            "update_family_note",
            "family_updater",
        ],
        "imports": ["tools.configger.config_test"],
    },
    "scripts/rus_exporter/docs_add_indexes.py": {"functions": ["docs_add_indexes"]},
    "scripts/rus_exporter/ru_zip_goldendict_mdict.py": {
        "functions": ["zip_goldendict", "zip_mdict"]
    },
    "tools/degree_of_completion_ru.py": {"functions": ["degree_of_completion"]},
    "tools/paths_dps.py": {"classes": ["ProjectPaths"]},
    "tools/paths_ru.py": {"classes": ["ProjectPaths"]},
    "tools/ru_spelling.py": {
        "classes": ["CustomSpellChecker"],
        "functions": ["add_to_dictionary"],
        "imports": ["tools.paths.ProjectPaths"],
    },
    "tools/utils_sbs.py": {
        "functions": ["list_into_batches", "squash_whitespaces", "extract_body"]
    },
}


def whitelist_values(shadow_whitelist: WhitelistEntry, key: str) -> set[str]:
    value = shadow_whitelist.get(key, [])
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


@pytest.mark.parametrize("shadow, upstream", get_python_pairs())
def test_shadow_copy_parity(shadow, upstream):
    """
    Test that the shadow copy maintains parity with the upstream file.
    Specifically:
    1. It should have all the imports that the upstream file has (to catch missing dependencies).
    2. It should have all the classes/functions the upstream file has (structural parity).
    """
    upstream_info = extract_ast_info(upstream)
    shadow_info = extract_ast_info(shadow)

    if not upstream_info:
        pytest.skip(f"Upstream file {upstream} not found or invalid.")

    if not shadow_info:
        pytest.fail(f"Shadow file {shadow} not found or invalid.")

    # Check for missing imports
    missing_imports = upstream_info["imports"] - shadow_info["imports"]

    # Check for missing functions
    missing_functions = upstream_info["functions"] - shadow_info["functions"]

    # Check for missing classes
    missing_classes = upstream_info["classes"] - shadow_info["classes"]

    # Filter with whitelist
    shadow_whitelist = WHITELIST.get(shadow, {})
    missing_imports -= whitelist_values(shadow_whitelist, "imports")
    missing_functions -= whitelist_values(shadow_whitelist, "functions")
    missing_classes -= whitelist_values(shadow_whitelist, "classes")

    errors = []
    # Note: Sometimes shadow copies intentionally drop things or rename things.
    # However, for a strict check, any missing import might be a missing dependency.
    # We will log them as errors. In practice, this might need a whitelist.
    if missing_imports:
        errors.append(f"Missing imports: {missing_imports}")
    if missing_functions:
        errors.append(f"Missing functions: {missing_functions}")
    if missing_classes:
        errors.append(f"Missing classes: {missing_classes}")

    if errors:
        pytest.fail(
            f"Parity mismatch in {shadow} compared to {upstream}:\n" + "\n".join(errors)
        )
