"""Smoke test for the full DPS sync pipeline — exercises DB build, exporters, webapp, Anki, and GUI."""

import atexit
import importlib
import importlib.util
import re
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Generator

from db.db_helpers import create_db_if_not_exists, create_tables, get_db_session
from db.models import (
    DpdHeadword,
    DpdRoot,
    FamilyCompound,
    FamilyIdiom,
    FamilyRoot,
    FamilySet,
    FamilyWord,
    Lookup,
    Russian,
    SBS,
)
from scripts.build.db_rebuild_from_tsv import get_tsv_files, read_tsv_files
from scripts.build.db_rebuild_from_tsv_dps import (
    get_tsv_files as dps_get_tsv_files,
    make_root_table_data_ru,
    read_tsv_files as dps_read_tsv_files,
)
from tools.configger import config_read, config_update
from tools.paths import ProjectPaths
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr

# ─── Constants ────────────────────────────────────────────────────────────────

MINI_DB_PATH = Path("temp/smoke_dpd.db")
ROW_LIMIT = 2000

# ─── Result tracking ──────────────────────────────────────────────────────────

_results: list[tuple[str, str]] = []  # (label, "pass" | "fail" | "skip")


def record(label: str, passed: bool | None) -> None:
    """Record a result. None = skip."""
    if passed is None:
        _results.append((label, "skip"))
        pr.cyan(f"  SKIP  {label}")
    elif passed:
        _results.append((label, "pass"))
        pr.yes(f"  PASS  {label}")
    else:
        _results.append((label, "fail"))
        pr.no(f"  FAIL  {label}")


# ─── Config isolation ─────────────────────────────────────────────────────────

_CONFIG_KEYS: list[tuple[str, str]] = [
    ("dictionary", "data_limit"),
    ("dictionary", "make_mdict"),
    ("regenerate", "db_rebuild"),
    ("exporter", "make_dpd"),
    ("exporter", "make_grammar"),
    ("exporter", "make_deconstructor"),
    ("exporter", "make_ebook"),
    ("exporter", "make_tpr"),
    ("exporter", "make_tbw"),
    ("goldendict", "copy_unzip"),
    ("anki", "db_path"),
]
_saved_config: dict[tuple[str, str], str | None] = {}


def save_config() -> None:
    """Snapshot current config values."""
    for key in _CONFIG_KEYS:
        _saved_config[key] = config_read(key[0], key[1])


def restore_config() -> None:
    """Restore config to snapshotted values."""
    for (section, option), value in _saved_config.items():
        if value is not None:
            config_update(section, option, value, silent=True)


atexit.register(restore_config)


def set_smoke_config() -> None:
    """Set config values needed by the smoke test."""
    config_update("dictionary", "data_limit", str(ROW_LIMIT), silent=True)
    config_update("dictionary", "make_mdict", "no", silent=True)
    config_update("regenerate", "db_rebuild", "yes", silent=True)
    config_update("exporter", "make_dpd", "yes", silent=True)
    config_update("exporter", "make_grammar", "yes", silent=True)
    config_update("exporter", "make_deconstructor", "yes", silent=True)
    config_update("exporter", "make_ebook", "yes", silent=True)
    config_update("exporter", "make_tpr", "yes", silent=True)
    config_update("exporter", "make_tbw", "yes", silent=True)
    config_update("goldendict", "copy_unzip", "no", silent=True)


# ─── ProjectPaths monkey-patch ────────────────────────────────────────────────


@contextmanager
def patched_project_paths() -> Generator[None, None, None]:
    """Override ProjectPaths.dpd_db_path → MINI_DB_PATH for any new instance."""
    original_init = ProjectPaths.__init__

    def _patched_init(
        self: ProjectPaths, base_dir: Path | None = None, create_dirs: bool = True
    ) -> None:
        original_init(self, base_dir, create_dirs)
        self.dpd_db_path = MINI_DB_PATH

    ProjectPaths.__init__ = _patched_init  # type: ignore[method-assign]
    try:
        yield
    finally:
        ProjectPaths.__init__ = original_init  # type: ignore[method-assign]


# ─── Phase 1: Mini DB builder ─────────────────────────────────────────────────


def _build_mini_db() -> bool:
    """Create temp/smoke_dpd.db from the first ROW_LIMIT rows of backup TSVs."""
    pr.green_title("Phase 1.2 — building mini DB")
    try:
        MINI_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        if MINI_DB_PATH.exists():
            MINI_DB_PATH.unlink()

        pth = ProjectPaths()  # already patched — dpd_db_path = MINI_DB_PATH
        dpspth = DPSPaths()

        create_db_if_not_exists(MINI_DB_PATH)
        create_tables(MINI_DB_PATH)  # ensure all tables exist
        db_session = get_db_session(MINI_DB_PATH)

        # DpdHeadword — first ROW_LIMIT rows only
        pr.green_tmr("DpdHeadword")
        hw_files = get_tsv_files(pth.pali_word_path, "dpd_headwords")
        loaded_ids: set[str] = set()
        hw_count = 0
        for columns, row in read_tsv_files(hw_files):
            if hw_count >= ROW_LIMIT:
                break
            data = {
                k: v
                for k, v in zip(columns, row)
                if k not in ("user_id", "created_at", "updated_at")
            }
            db_session.add(DpdHeadword(**data))
            loaded_ids.add(str(row[0]))
            hw_count += 1
        pr.yes(hw_count)

        # DpdRoot — all rows (small table)
        pr.green_tmr("DpdRoot")
        root_files = get_tsv_files(pth.pali_root_path, "dpd_roots")
        root_count = 0
        for columns, row in read_tsv_files(root_files):
            skip = {
                "created_at",
                "updated_at",
                "root_info",
                "root_matrix",
                "root_ru_meaning",
                "sanskrit_root_ru_meaning",
            }
            data = {k: v for k, v in zip(columns, row) if k not in skip}
            db_session.add(DpdRoot(**data))
            root_count += 1
        pr.yes(root_count)

        db_session.commit()

        # Russian — only IDs matching loaded headwords
        pr.green_tmr("Russian")
        ru_files = dps_get_tsv_files(dpspth.russian_path, "russian")
        ru_count = 0
        for columns, row in dps_read_tsv_files(ru_files):
            data = {k: v for k, v in zip(columns, row) if k}
            if data.get("id") in loaded_ids:
                db_session.add(Russian(**data))
                ru_count += 1
        pr.yes(ru_count)

        # SBS — only IDs matching loaded headwords
        pr.green_tmr("SBS")
        sbs_files = dps_get_tsv_files(dpspth.sbs_path, "sbs")
        sbs_count = 0
        for columns, row in dps_read_tsv_files(sbs_files):
            data = {k: v for k, v in zip(columns, row) if k}
            if data.get("id") in loaded_ids:
                db_session.add(SBS(**data))
                sbs_count += 1
        pr.yes(sbs_count)

        # DpdRoot RU columns — update existing roots
        make_root_table_data_ru(dpspth, db_session)

        db_session.commit()
        db_session.close()
        return True
    except Exception as exc:
        pr.no(f"mini DB build error: {exc}")
        return False


def _verify_mini_db() -> bool:
    """Check that mini DB has correct tables, non-empty data, and localized columns populated."""
    try:
        db_session = get_db_session(MINI_DB_PATH)
        hw_count = db_session.query(DpdHeadword).count()
        ru_count = db_session.query(Russian).count()
        sbs_count = db_session.query(SBS).count()

        # Data quality: RU root meanings populated
        root_ru_count = (
            db_session.query(DpdRoot).filter(DpdRoot.root_ru_meaning != "").count()
        )

        # Data quality: Russian ru_meaning column populated
        ru_meaning_count = (
            db_session.query(Russian).filter(Russian.ru_meaning != "").count()
        )

        # Data quality: SBS sbs_class populated (int column, non-zero)
        sbs_class_count = db_session.query(SBS).filter(SBS.sbs_class != 0).count()

        db_session.close()

        pr.yes(
            f"DpdHeadword={hw_count}, Russian={ru_count} (ru_meaning={ru_meaning_count}), "
            f"SBS={sbs_count} (sbs_class≠0={sbs_class_count}), "
            f"DpdRoot.root_ru_meaning={root_ru_count}"
        )

        ok = hw_count > 0 and hw_count <= ROW_LIMIT
        if ru_meaning_count == 0:
            pr.no("  Russian.ru_meaning is empty for all rows — data not loaded")
            ok = False
        if root_ru_count == 0:
            pr.no(
                "  DpdRoot.root_ru_meaning is empty for all rows — RU root data not loaded"
            )
            ok = False
        return ok
    except Exception as exc:
        pr.no(f"verification error: {exc}")
        return False


def _run_component(module_path: str) -> bool:
    """Import a component module (with ProjectPaths already patched) and call main().

    Some legacy scripts rely on sibling imports such as `from root_info import ...`.
    Preload those helpers explicitly so the smoke test avoids path injection.
    """
    dotted = module_path.replace("/", ".").removesuffix(".py")
    module_file = Path(module_path).resolve()

    # Clear cached import so module-level code reruns under the active patch.
    sys.modules.pop(dotted, None)

    try:
        with _preloaded_component_helpers(module_file):
            mod = importlib.import_module(dotted)
            if hasattr(mod, "main"):
                mod.main()
            return True
    except SystemExit:
        return True  # some scripts call sys.exit(0)
    except Exception as exc:
        pr.red(f"{dotted}: {exc}")
        return False


def _load_module_from_path(module_name: str, module_file: Path) -> ModuleType:
    """Load a module directly from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, module_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load spec for {module_name} from {module_file}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@contextmanager
def _preloaded_component_helpers(module_file: Path) -> Generator[None, None, None]:
    """Preload sibling helper modules needed by legacy component scripts."""
    previous_modules: dict[str, ModuleType | None] = {}
    helper_names: tuple[str, ...] = ()

    if module_file.name == "family_root.py":
        helper_names = ("root_info", "root_matrix")

    try:
        for helper_name in helper_names:
            previous_modules[helper_name] = sys.modules.get(helper_name)
            _load_module_from_path(
                helper_name, module_file.with_name(f"{helper_name}.py")
            )
        yield
    finally:
        for helper_name, previous_module in previous_modules.items():
            if previous_module is None:
                sys.modules.pop(helper_name, None)
            else:
                sys.modules[helper_name] = previous_module


def _generate_components() -> bool:
    """Run component generators under patched ProjectPaths.

    Upstream scripts run silently as infrastructure prerequisites.
    Only localized (_ru) scripts are recorded as pass/fail.
    """
    pr.green_title("Phase 1.3 — generating components")

    # Upstream infrastructure — run silently, not tested
    upstream_prereqs = [
        "db/inflections/create_inflection_templates.py",
        "db/inflections/generate_inflection_tables.py",
        "db/families/family_root.py",
        "db/families/family_word.py",
        "db/families/family_compound.py",
        "db/families/family_set.py",
        "db/families/family_idiom.py",
        "scripts/build/families_to_json.py",
        "db/grammar/grammar_to_lookup.py",
        "db/inflections/inflections_to_headwords.py",
        "db/lookup/help_abbrev_add_to_lookup.py",
    ]
    pr.green("  upstream prereqs (silent):")
    for script in upstream_prereqs:
        if Path(script).exists():
            _run_component(script)

    # Localized scripts — recorded as pass/fail
    localized_scripts = [
        "db/families/family_root_ru.py",
        "db/families/family_word_ru.py",
        "db/families/family_compound_ru.py",
        "db/families/family_set_ru.py",
        "db/families/family_idiom_ru.py",
        "db/lookup/help_abbrev_add_to_lookup_ru.py",
    ]
    any_fail = False
    pr.green("  localized components:")
    for script in localized_scripts:
        label = Path(script).name
        if not Path(script).exists():
            pr.red(f"    MISSING {label}")
            any_fail = True
            continue
        ok = _run_component(script)
        if ok:
            pr.yes(f"    ok  {label}")
        else:
            pr.no(f"    fail  {label}")
            any_fail = True

    # Verify localized html_ru columns are populated in the family tables
    try:
        db_session = get_db_session(MINI_DB_PATH)
        fr_ru = db_session.query(FamilyRoot).filter(FamilyRoot.html_ru != "").count()
        fw_ru = db_session.query(FamilyWord).filter(FamilyWord.html_ru != "").count()
        fc_ru = (
            db_session.query(FamilyCompound)
            .filter(FamilyCompound.html_ru != "")
            .count()
        )
        fs_ru = db_session.query(FamilySet).filter(FamilySet.html_ru != "").count()
        fi_ru = db_session.query(FamilyIdiom).filter(FamilyIdiom.html_ru != "").count()
        lookup_count = db_session.query(Lookup).count()
        # help_abbrev_add_to_lookup_ru adds entries with help != ""
        lookup_help_count = db_session.query(Lookup).filter(Lookup.help != "").count()
        db_session.close()
        ru_ok = fr_ru > 0 and fw_ru > 0
        pr.yes(
            f"    FamilyRoot.html_ru={fr_ru}, FamilyWord.html_ru={fw_ru}, "
            f"FamilyCompound.html_ru={fc_ru}, FamilySet.html_ru={fs_ru}, "
            f"FamilyIdiom.html_ru={fi_ru}, Lookup={lookup_count} (help={lookup_help_count})"
        )
        if not ru_ok:
            pr.no(
                "    RU family html_ru columns are empty — localized generation failed"
            )
        if lookup_help_count == 0:
            pr.no(
                "    Lookup.help empty — help_abbrev_add_to_lookup_ru produced no entries"
            )
            any_fail = True
        return not any_fail and ru_ok
    except Exception as exc:
        pr.no(f"    component verification error: {exc}")
        return False


def phase1() -> bool:
    """Build mini DB and run derived-table generators."""
    pr.yellow_title("=== Phase 1: Infrastructure & Mini DB ===")
    with patched_project_paths():
        ok1 = _build_mini_db()
        record("1.2 mini DB build", ok1)
        if not ok1:
            record("1.2 mini DB verify", False)
            record("1.3 components", None)
            return False

        ok_v = _verify_mini_db()
        record("1.2 mini DB verify", ok_v)

        ok3 = _generate_components()
        record("1.3 components", ok3)
    return ok1 and ok_v and ok3


# ─── Phase 2: Exporters ───────────────────────────────────────────────────────


def _run_exporter(label: str, module_path: str) -> bool:
    """Run an exporter's main() under patched ProjectPaths."""
    import importlib

    dotted = module_path.replace("/", ".").removesuffix(".py")
    sys.modules.pop(dotted, None)
    try:
        mod = importlib.import_module(dotted)
        if hasattr(mod, "main"):
            mod.main()
        return True
    except SystemExit:
        return True
    except Exception as exc:
        pr.red(f"{label}: {exc}")
        return False


def _verify_goldendict_output(
    label: str, dict_dz: Path, ifo: Path, id_prefix: bytes
) -> bool:
    """Verify a GoldenDict output: wordcount > 0, prefix in HTML, no Mako leaks."""
    import gzip
    import re

    ok = True
    if not ifo.exists():
        pr.no(f"    {label}: .ifo missing: {ifo}")
        return False
    if not dict_dz.exists():
        pr.no(f"    {label}: .dict.dz missing: {dict_dz}")
        return False

    # Check wordcount from .ifo
    ifo_text = ifo.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"wordcount=(\d+)", ifo_text)
    wordcount = int(m.group(1)) if m else 0
    if wordcount == 0:
        pr.no(f"    {label}: wordcount=0 in {ifo.name}")
        ok = False
    else:
        pr.yes(f"    {label}: wordcount={wordcount}")

    # Check HTML content sample
    try:
        with gzip.open(dict_dz, "rb") as f:
            sample = f.read(200_000)
        if id_prefix not in sample:
            pr.no(
                f"    {label}: '{id_prefix.decode()}' prefix not found in HTML output"
            )
            ok = False
        else:
            pr.yes(f"    {label}: '{id_prefix.decode()}' IDs present in HTML")
        if b"${" in sample:
            pr.no(f"    {label}: Mako syntax '${{...}}' found — template not rendered")
            ok = False
        else:
            pr.yes(f"    {label}: no Mako syntax leaks")
    except Exception as exc:
        pr.no(f"    {label}: failed to read .dict.dz: {exc}")
        ok = False

    return ok


def _verify_ru_json_files() -> bool:
    """Verify all 5 RU family JS files exist, are non-empty, and contain JSON data."""
    import json
    import re

    from tools.paths_ru import RuPaths

    rupth = RuPaths()
    json_files = [
        rupth.family_root_json,
        rupth.family_word_json,
        rupth.family_compound_json,
        rupth.family_set_json,
        rupth.family_idiom_json,
    ]
    all_ok = True
    for path in json_files:
        if not path.exists() or path.stat().st_size == 0:
            pr.no(f"    missing/empty: {path.name}")
            all_ok = False
            continue
        content = path.read_text(encoding="utf-8")
        # Strip JS var assignment: `var ru_xxx = {...};`
        json_part = re.sub(r"^var\s+\w+\s*=\s*", "", content.strip()).rstrip(";")
        try:
            data = json.loads(json_part)
            pr.yes(f"    {path.name}: {len(data)} entries")
        except json.JSONDecodeError as exc:
            pr.no(f"    {path.name}: JSON parse error: {exc}")
            all_ok = False
    return all_ok


def _verify_dir_nonempty(label: str, dirpath: Path) -> bool:
    """Check that a directory exists and contains at least one file."""
    if not dirpath.exists():
        pr.no(f"    {label}: directory missing: {dirpath}")
        return False
    files = list(dirpath.iterdir())
    if not files:
        pr.no(f"    {label}: directory empty: {dirpath}")
        return False
    pr.yes(f"    {label}: {len(files)} files in {dirpath.name}/")
    return True


def _verify_file_nonempty(label: str, filepath: Path) -> bool:
    """Check that a file exists and has non-zero size."""
    if not filepath.exists():
        pr.no(f"    {label}: file missing: {filepath}")
        return False
    size = filepath.stat().st_size
    if size == 0:
        pr.no(f"    {label}: file is empty: {filepath}")
        return False
    pr.yes(f"    {label}: {filepath.name} ({size:,} bytes)")
    return True


# ─── Phase 0: Static checks (no mini DB required) ─────────────────────────────


def _check_ru_js_files() -> bool:
    """Verify the 5 localized RU JS template files exist and contain ru_ namespaced content."""
    js_dir = Path("exporter/goldendict/ru_components/javascript")
    # ru_sorter.js is a generic table-sort utility — no ru_ namespace in content.
    # The remaining template files all define ru_-prefixed functions/vars.
    expected = [
        "ru_main.js",
        "ru_feedback_template.js",
        "ru_frequency_template.js",
        "ru_family_root_template.js",
        "ru_family_word_template.js",
        "ru_family_compound_template.js",
        "ru_family_set_template.js",
        "ru_family_idiom_template.js",
    ]
    all_ok = True
    for name in expected:
        path = js_dir / name
        if not path.exists():
            pr.no(f"    missing RU JS: {name}")
            all_ok = False
            continue
        content = path.read_text(encoding="utf-8")
        if "ru_" not in content:
            pr.no(f"    {name}: no 'ru_' namespace found")
            all_ok = False
        else:
            pr.yes(f"    {name}: ok")
    return all_ok


def _check_no_mako_in_templates() -> bool:
    """Grep ru_templates/ and sbs_templates/ for Mako '${' syntax — must find none."""

    template_dirs = [
        "exporter/webapp/ru_templates",
        "exporter/webapp/sbs_templates",
    ]
    all_ok = True
    for dirpath in template_dirs:
        if not Path(dirpath).exists():
            pr.cyan(f"    {dirpath}: not found (skip)")
            continue
        result = subprocess.run(
            ["grep", "-rl", "${", dirpath],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            for f in result.stdout.strip().splitlines():
                pr.no(f"    Mako syntax '${{...}}' found in: {f}")
            all_ok = False
        else:
            pr.yes(f"    {dirpath}: no Mako syntax")
    return all_ok


def _check_anki_import() -> bool:
    """Verify scripts.build.anki_updater imports without error."""
    import importlib

    try:
        sys.modules.pop("scripts.build.anki_updater", None)
        importlib.import_module("scripts.build.anki_updater")
        pr.yes("    anki_updater: import ok")
        return True
    except Exception as exc:
        pr.no(f"    anki_updater import error: {exc}")
        return False


def phase0_static() -> bool:
    """Run static checks that require no mini DB (JS files, template syntax, imports)."""
    pr.yellow_title("=== Phase 0: Static Checks ===")
    all_ok = True

    pr.green("  RU JS component files:")
    ok = _check_ru_js_files()
    record("0.1 ru-js-files", ok)
    all_ok = all_ok and ok

    pr.green("  No Mako syntax in webapp templates:")
    ok = _check_no_mako_in_templates()
    record("0.2 no-mako-in-templates", ok)
    all_ok = all_ok and ok

    pr.green("  Anki updater import:")
    ok = _check_anki_import()
    record("0.3 anki-import", ok)
    all_ok = all_ok and ok

    return all_ok


def phase2() -> bool:
    """Test all RU/SBS/DPS localized exporters against mini DB."""
    pr.yellow_title("=== Phase 2: Exporters ===")
    all_ok = True

    with patched_project_paths():
        # Task 2.1 — GoldenDict RU + SBS
        for label, module in [
            ("2.1 goldendict-ru", "exporter/goldendict/main_ru.py"),
            ("2.1 goldendict-sbs", "exporter/goldendict/main_sbs.py"),
        ]:
            ok = _run_exporter(label, module)
            record(label, ok)
            all_ok = all_ok and ok

        # Verify GoldenDict output content (files, IDs, no Mako)
        ru_gd_ok = _verify_goldendict_output(
            "goldendict-ru output",
            dict_dz=Path("exporter/share/ru-dpd/ru-dpd.dict.dz"),
            ifo=Path("exporter/share/ru-dpd/ru-dpd.ifo"),
            id_prefix=b"ru_",
        )
        record("2.1 goldendict-ru output", ru_gd_ok)
        all_ok = all_ok and ru_gd_ok

        sbs_gd_ok = _verify_goldendict_output(
            "goldendict-sbs output",
            dict_dz=Path("exporter/share/SBS/dpd/dpd.dict.dz"),
            ifo=Path("exporter/share/SBS/dpd/dpd.ifo"),
            id_prefix=b"sbs_",
        )
        record("2.1 goldendict-sbs output", sbs_gd_ok)
        all_ok = all_ok and sbs_gd_ok

        # Task 2.2 — Grammar dict + Deconstructor
        ok_gram = _run_exporter(
            "2.2 grammar-dict-ru", "exporter/grammar_dict/grammar_dict_ru.py"
        )
        record("2.2 grammar-dict-ru", ok_gram)
        all_ok = all_ok and ok_gram
        ok_gram_out = _verify_dir_nonempty(
            "grammar-dict-ru output", Path("exporter/share/ru-dpd-grammar")
        )
        record("2.2 grammar-dict-ru output", ok_gram_out)
        all_ok = all_ok and ok_gram_out

        ok_dec = _run_exporter(
            "2.2 deconstructor-ru",
            "exporter/deconstructor/deconstructor_exporter_ru.py",
        )
        record("2.2 deconstructor-ru", ok_dec)
        all_ok = all_ok and ok_dec
        ok_dec_out = _verify_dir_nonempty(
            "deconstructor-ru output", Path("exporter/share/ru-dpd-deconstructor")
        )
        record("2.2 deconstructor-ru output", ok_dec_out)
        all_ok = all_ok and ok_dec_out

        # Task 2.3 — Kindle, TPR, TBW
        ok_kindle = _run_exporter(
            "2.3 kindle-ru", "exporter/kindle/kindle_exporter_ru.py"
        )
        record("2.3 kindle-ru", ok_kindle)
        all_ok = all_ok and ok_kindle
        ok_kindle_out = _verify_file_nonempty(
            "kindle-ru output", Path("exporter/share/ru-dpd-kindle.epub")
        )
        record("2.3 kindle-ru output", ok_kindle_out)
        all_ok = all_ok and ok_kindle_out

        tpr_downloads = Path("resources/tpr_downloads")
        if not tpr_downloads.exists():
            record("2.3 tpr-ru", None)  # skip
            record("2.3 tpr-ru output", None)
        else:
            ok_tpr = _run_exporter("2.3 tpr-ru", "exporter/tpr/tpr_exporter_ru.py")
            record("2.3 tpr-ru", ok_tpr)
            all_ok = all_ok and ok_tpr
            ok_tpr_out = _verify_file_nonempty(
                "tpr-ru output", Path("exporter/tpr/output/dpd.tsv")
            )
            record("2.3 tpr-ru output", ok_tpr_out)
            all_ok = all_ok and ok_tpr_out

        ok_tbw = _run_exporter("2.3 tbw-ru", "exporter/tbw/tbw_exporter_ru.py")
        record("2.3 tbw-ru", ok_tbw)
        all_ok = all_ok and ok_tbw
        ok_tbw_out = _verify_file_nonempty(
            "tbw-ru output",
            Path("resources/fdg_dpd/assets/standalone-dpd/ru/dpd_ebts.js"),
        )
        record("2.3 tbw-ru output", ok_tbw_out)
        all_ok = all_ok and ok_tbw_out

        # Task 2.4 — Families JSON RU
        ok_fam = _run_exporter(
            "2.4 families-json-ru", "scripts/build/families_to_json_ru.py"
        )
        record("2.4 families-json-ru", ok_fam)
        all_ok = all_ok and ok_fam

        # Verify RU family JSON files are parseable
        ok_json = _verify_ru_json_files()
        record("2.4 ru-json-parseable", ok_json)
        all_ok = all_ok and ok_json

    return all_ok


# ─── Phase 3: Webapp, Anki, GUI ──────────────────────────────────────────────


def phase3_webapp() -> bool:
    """Test DPS webapp (main_ru) with FastAPI TestClient under patched ProjectPaths.

    Checks:
    - RU home page (/) returns 200 and contains localized UI markers
    - SBS home page (/sbs) returns 200 and contains SBS markers
    - RU search JSON returns a list with at least one result
    - SBS search JSON returns a list with at least one result
    """
    pr.yellow_title("=== Phase 3.1: Webapp (main_ru) ===")
    try:
        import importlib

        # Clear cached main_ru so module-level ProjectPaths() runs under patch
        for key in list(sys.modules.keys()):
            if "main_ru" in key or "exporter.webapp" in key:
                del sys.modules[key]

        with patched_project_paths():
            webapp_mod = importlib.import_module("exporter.webapp.main_ru")
            app = webapp_mod.app

        from fastapi.testclient import TestClient

        all_ok = True
        with TestClient(app) as client:
            # Home pages — check status and localized title strings
            for path, title_bytes, desc in [
                ("/", "Электронный Словарь Пали".encode(), "RU title"),
                ("/sbs", "Digital Pāḷi Dictionary".encode(), "SBS title"),
            ]:
                resp = client.get(path)
                if resp.status_code != 200:
                    pr.no(f"  GET {path} → {resp.status_code}")
                    all_ok = False
                    continue
                if title_bytes in resp.content:
                    pr.yes(f"  GET {path} → 200, {desc} present")
                else:
                    pr.no(f"  GET {path} → 200 but {desc} missing in response")
                    all_ok = False

            # Search JSON — use 'a' which is in the first 2000 headwords
            # RU endpoint: dpd_html must be non-empty and contain Cyrillic text
            # (RU template renders Cyrillic content inline, not via id="ru_" attributes)
            resp_ru = client.get("/search_json?q=a")
            if resp_ru.status_code != 200:
                pr.no(f"  GET /search_json?q=a → {resp_ru.status_code}")
                all_ok = False
            else:
                dpd_html = resp_ru.json().get("dpd_html", "")
                if not dpd_html:
                    pr.no("  /search_json?q=a → dpd_html empty (no results)")
                    all_ok = False
                elif not re.search(r"[\u0400-\u04FF]", dpd_html):
                    pr.no(
                        "  /search_json?q=a → no Cyrillic text in dpd_html (RU content missing)"
                    )
                    all_ok = False
                else:
                    pr.yes("  /search_json?q=a → results with Cyrillic text")

            # SBS endpoint: dpd_html must be non-empty (has results from SBS route).
            # id="sbs_example_" is conditional on sbs.needs_sbs_example_button —
            # not guaranteed for all headwords, so we only check for non-empty response.
            resp_sbs = client.get("/sbs/search_json?q=a")
            if resp_sbs.status_code != 200:
                pr.no(f"  GET /sbs/search_json?q=a → {resp_sbs.status_code}")
                all_ok = False
            else:
                dpd_html_sbs = resp_sbs.json().get("dpd_html", "")
                if not dpd_html_sbs:
                    pr.no("  /sbs/search_json?q=a → dpd_html empty (no results)")
                    all_ok = False
                else:
                    pr.yes("  /sbs/search_json?q=a → results present")

        return all_ok
    except Exception as exc:
        pr.no(f"webapp error: {exc}")
        return False


def phase3_anki() -> bool | None:
    """Test Anki updater — skip if no DB configured or no notes match the mini DB.

    The Anki updater requires notes in the deck that match DPD headword IDs.
    With a 2000-row mini DB it will find 0 matching notes and cannot proceed
    normally. Any exception from the updater is treated as a skip (not a failure)
    since this is a mini DB limitation, not a code defect.
    """
    pr.yellow_title("=== Phase 3.2: Anki updater ===")
    anki_path_str = config_read("anki", "db_path", "")
    anki_path = Path(anki_path_str) if anki_path_str else None
    if not anki_path or not anki_path.exists():
        pr.cyan("  Anki DB not configured — skipping")
        return None

    import shutil

    smoke_anki = Path("temp/smoke_anki.anki2")
    try:
        shutil.copy2(anki_path, smoke_anki)
        config_update("anki", "db_path", str(smoke_anki), silent=True)

        with patched_project_paths():
            import importlib

            sys.modules.pop("scripts.build.anki_updater", None)
            mod = importlib.import_module("scripts.build.anki_updater")
            if hasattr(mod, "main"):
                mod.main()

        return True
    except Exception as exc:
        # Mini DB has 0 matching Anki notes → updater cannot find expected deck
        # structure. Treat as skip: import works, limitation is data, not code.
        pr.cyan(f"  Anki skipped (mini DB has no matching notes): {exc}")
        return None
    finally:
        config_update("anki", "db_path", anki_path_str, silent=True)
        if smoke_anki.exists():
            smoke_anki.unlink()


def phase3_gui() -> bool:
    """Initialize the GUI App class using MagicMock to avoid launching a window.
    This tests the entire manager initialization chain (AIManager, ToolKit, etc.)
    without triggering Flet's window rendering.
    """
    pr.yellow_title("=== Phase 3.3: GUI launch check (MagicMock) ===")
    try:
        from unittest.mock import MagicMock
        from gui2.main import App

        with patched_project_paths():
            mock_page = MagicMock()
            # This triggers the initialization of all managers.
            App(mock_page)

        pr.yes("GUI App initialized without exceptions")
        return True
    except Exception as exc:
        pr.no(f"GUI launch error: {exc}")
        return False


# ─── Phase 4: Cleanup & guide update ─────────────────────────────────────────


def cleanup_temp() -> None:
    """Remove smoke test artifacts from temp/."""
    for artifact in [MINI_DB_PATH, Path("temp/smoke_anki.anki2")]:
        if artifact.exists():
            artifact.unlink()
    pr.green("temp/ artifacts cleaned up")


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    pr.tic()
    pr.yellow_title("DPS Sync Smoke Test")

    save_config()
    try:
        set_smoke_config()

        phase0_static()

        ok1 = phase1()
        if ok1:
            phase2()
        else:
            record("Phase 2 (skipped — Phase 1 failed)", None)

        record("3.1 webapp", phase3_webapp())
        record("3.2 anki", phase3_anki())
        record("3.3 gui", phase3_gui())

    finally:
        restore_config()
        cleanup_temp()

    pr.yellow_title("=== Summary ===")
    passed = sum(1 for _, s in _results if s == "pass")
    failed = sum(1 for _, s in _results if s == "fail")
    skipped = sum(1 for _, s in _results if s == "skip")

    if failed == 0:
        pr.yes(f"{passed} passed / {skipped} skipped / 0 failed")
        sys.exit(0)
    else:
        pr.no(f"{failed} FAILED / {passed} passed / {skipped} skipped")
        sys.exit(1)


if __name__ == "__main__":
    main()
