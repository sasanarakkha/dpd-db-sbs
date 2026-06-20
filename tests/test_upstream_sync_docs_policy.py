"""Verify upstream sync docs do not authorize autonomous commits."""

from pathlib import Path


def test_guide_uses_commit_preparation_wording() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")

    assert "then commit" not in guide
    assert "then prepare the commit message" in guide


def test_guide_has_no_stale_backup_todo_or_grep_command() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")

    assert "TODO backup dps" not in guide
    assert "grep -r" not in guide
    assert "`grep`" not in guide
    assert "`find`" not in guide
    assert "use `rg`" in guide


def test_guide_keeps_stage_4a_command_execution_with_fast() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")

    assert (
        "FAST must run `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py "
        "<thread_dir>` before handing off to Stage 4.A."
    ) in guide
    assert (
        "Run `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py "
        "<thread_dir>`"
    ) not in guide


def test_guide_stops_before_execute_sync_when_discuss_paths_exist() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")

    assert (
        "If `prep_manifest.json.discuss_paths` is non-empty, STOP before "
        "`execute_sync.py`."
    ) in guide


def test_guide_and_plan_stop_before_execute_sync_when_blocker_paths_exist() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")
    plan = Path("kamma/upstream_sync/templates/sync_thread_plan.md").read_text(
        encoding="utf-8"
    )

    required = (
        "If `prep_manifest.json.blocker_paths` is non-empty, STOP before "
        "`execute_sync.py`."
    )
    assert required in guide
    assert required in plan


def test_stage_five_finalization_is_fast_mechanical_handoff() -> None:
    plan = Path("kamma/upstream_sync/templates/sync_thread_plan.md").read_text(
        encoding="utf-8"
    )
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")
    command = "uv run python3 kamma/upstream_sync/scripts/finalize_accepted_sync.py <thread_dir>"

    assert f"If accepted, run `{command}`." not in plan
    assert (
        f"If accepted, write exact FAST handoff instructions to run `{command}`."
        in plan
    )
    assert (
        f"If accepted, write exact FAST handoff instructions to run `{command}`."
        in guide
    )


def test_stage_1_requires_api_health_check() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")
    plan = Path("kamma/upstream_sync/templates/sync_thread_plan.md").read_text(
        encoding="utf-8"
    )
    command = (
        "uv run ruff check tools/ scripts/ db/ exporter/ --select F821,E999 --quiet"
    )

    assert command in guide
    assert command in plan


def test_smd_coverage_wording_matches_checker_scope() -> None:
    readme = Path("kamma/upstream_sync/README.md").read_text(encoding="utf-8")
    checker = Path("kamma/upstream_sync/scripts/verify_smd_coverage.py").read_text(
        encoding="utf-8"
    )

    assert "every sync-relevant registry entry" in readme
    assert "Verify sync-relevant registry entries" in checker
    assert "every registry entry has" not in readme


def test_unique_paths_are_documented_as_cleanup_inventory_not_sync_targets() -> None:
    readme = Path("kamma/upstream_sync/README.md").read_text(encoding="utf-8")
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")

    expected = "cleanup inventory, not sync targets"
    assert expected in guide
    assert expected not in readme
    assert "guide.md#registry-categories" in readme


def test_reviewed_shadow_noop_ledger_is_documented() -> None:
    readme = Path("kamma/upstream_sync/README.md").read_text(encoding="utf-8")
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")
    plan = Path("kamma/upstream_sync/templates/sync_thread_plan.md").read_text(
        encoding="utf-8"
    )
    ledger = Path("kamma/upstream_sync/reviewed_shadow_noops.json")

    assert ledger.exists()
    assert "reviewed_shadow_noops.json" in readme
    assert "reviewed_shadow_noops.json" in guide
    assert "reviewed_shadow_noops.json" in plan


def test_reviewed_shadow_noop_default_user_reason_is_documented() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")
    plan = Path("kamma/upstream_sync/templates/sync_thread_plan.md").read_text(
        encoding="utf-8"
    )
    reason = (
        "User reviewed and confirmed this upstream change does not need to be ported "
        "to the shadow."
    )

    assert reason in guide
    assert reason in plan


def test_archive_scope_note_supersedes_stale_docs_exclusion() -> None:
    archive = Path("kamma/upstream_sync/archive_improvements.md").read_text(
        encoding="utf-8"
    )

    assert "`gui/` and `docs/` are permanently out of sync scope" not in archive
    assert (
        "Superseded scope note: `gui/` remains out of sync scope; `docs/` is "
        "upstream-owned and accepted verbatim, while `docs_rus/` is handled by "
        "Stage 4 Docs Translation Parity."
    ) in archive


def test_archive_improvements_is_marked_historical_only() -> None:
    archive = Path("kamma/upstream_sync/archive_improvements.md").read_text(
        encoding="utf-8"
    )

    assert "Historical record only." in archive
    assert "Current canonical instructions live in `guide.md`" in archive


def test_empty_suggestions_file_is_not_kept() -> None:
    assert not Path("kamma/upstream_sync/suggestions.md").exists()


def test_docs_define_single_category_dps_shadow_policy() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")
    readme = Path("kamma/upstream_sync/README.md").read_text(encoding="utf-8")

    required = "`dps_copies` is the single category for mixed/shared fork shadows"
    assert required in guide
    assert required not in readme
    assert "guide.md#registry-categories" in readme


def test_agents_requires_shadow_documentation_gate() -> None:
    agents = Path("AGENTS.md").read_text(encoding="utf-8")

    assert "Shadow Documentation Gate" in agents
    assert (
        "registry.json and the matching `kamma/upstream_sync/smd/*.md` entry" in agents
    )
    assert "one local path may appear in exactly one registry category" in agents


def test_only_dpd_kamma_sync_remains_as_sync_bash_entrypoint() -> None:
    wrapper = Path("scripts/cl_dps/dpd-kamma-sync").read_text(encoding="utf-8")

    assert "kamma/upstream_sync/scripts/init_sync_thread.py" in wrapper
    assert "scripts/bash/dpd_init_sync.py" not in wrapper

    obsolete_paths = [
        Path("scripts/cl_dps/dpd-sync-folders"),
        Path("scripts/bash/full_sync.sh"),
        Path("scripts/bash/dpd-sync-assertions.sh"),
        Path("scripts/bash/test_dpd_sync_assertions.sh"),
        Path("scripts/bash/dpd_init_sync.py"),
    ]
    assert [str(path) for path in obsolete_paths if path.exists()] == []


def test_commit_policy_is_inherited_from_global_rules() -> None:
    agents = Path("AGENTS.md").read_text(encoding="utf-8")
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")
    readme = Path("kamma/upstream_sync/README.md").read_text(encoding="utf-8")
    wrapper = Path("scripts/cl_dps/dpd-kamma-sync").read_text(encoding="utf-8")
    python_sync_scripts = [
        path.read_text(encoding="utf-8")
        for path in Path("kamma/upstream_sync/scripts").glob("*.py")
    ]

    expected = "Git commit/push policy is inherited from the global rules."
    assert "Local Commit Exception" not in agents
    assert "Only human-run Bash scripts under `scripts/cl_dps/`" not in agents
    assert expected in guide
    assert expected in readme
    assert 'git commit -m "$BACKUP_COMMIT_MESSAGE"' in wrapper
    assert all("git commit" not in script for script in python_sync_scripts)


def test_dpd_kamma_sync_checks_branch_before_backup_commit() -> None:
    wrapper = Path("scripts/cl_dps/dpd-kamma-sync").read_text(encoding="utf-8")

    assert 'CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"' in wrapper
    assert 'if [ "$CURRENT_BRANCH" != "sbs-ru" ]; then' in wrapper
    assert "Wrong branch" in wrapper
    assert wrapper.index('CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"') < (
        wrapper.index('uv run python3 "$BACKUP_SCRIPT"')
    )


def test_init_sync_thread_prints_exact_stage_one_restart_prompt() -> None:
    init_script = Path("kamma/upstream_sync/scripts/init_sync_thread.py").read_text(
        encoding="utf-8"
    )
    legacy_index = "kamma/" + "threads" + ".md"

    assert "Dispatch Stage 1 to the sync-fast subagent" in init_script
    assert "Run `/kamma:2-do` to start the sync." not in init_script
    assert legacy_index not in init_script
    assert "THREADS_FILE" not in init_script


def test_prep_analyzer_has_single_rename_expansion_path() -> None:
    source = Path("kamma/upstream_sync/scripts/prep_analyzer.py").read_text(
        encoding="utf-8"
    )

    assert "def expand_git_change(" not in source
    assert "for expanded_change in expand_git_change" not in source


def test_registry_docs_rus_description_matches_translation_parity_policy() -> None:
    registry = Path("kamma/upstream_sync/registry.json").read_text(encoding="utf-8")
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")

    assert "not a translation of upstream docs" not in registry
    assert "Stage 4: Docs Translation Parity" in guide
    assert "Maintained Russian translation of upstream docs/" in registry


def test_execute_sync_documents_manual_staging_by_default() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")
    plan = Path("kamma/upstream_sync/templates/sync_thread_plan.md").read_text(
        encoding="utf-8"
    )

    assert "`execute_sync.py <thread_dir>` leaves changes unstaged by default" in guide
    assert "`--stage`" in guide
    assert "`execute_sync.py <thread_dir>` leaves changes unstaged by default" in plan


def test_docs_translation_stage_uses_strict_parity_check() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")
    plan = Path("kamma/upstream_sync/templates/sync_thread_plan.md").read_text(
        encoding="utf-8"
    )
    command = (
        "uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py "
        "<thread_dir> --strict"
    )

    assert command in guide
    assert command in plan


def test_execute_sync_assertions_are_python_owned() -> None:
    source = Path("kamma/upstream_sync/scripts/execute_sync.py").read_text(
        encoding="utf-8"
    )

    assert "def run_sync_assertions(" in source
    assert "dpd-sync-assertions.sh" not in source
    assert '["bash"' not in source


def test_sync_docs_document_single_bash_wrapper() -> None:
    readme = Path("kamma/upstream_sync/README.md").read_text(encoding="utf-8")
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")
    product_guidelines = Path("conductor/product-guidelines.md").read_text(
        encoding="utf-8"
    )

    wrapper = "scripts/cl_dps/dpd-kamma-sync"
    assert wrapper in readme
    assert wrapper in guide
    assert wrapper in product_guidelines
    assert "scripts/cl/dpd-sync-folders" not in product_guidelines


def test_sync_docs_use_only_no_translate_redirect_policy() -> None:
    docs = [
        Path("AGENTS.md"),
        Path("kamma/upstream_sync/guide.md"),
        Path("kamma/upstream_sync/scripts/check_docs_parity.py"),
    ]
    forbidden_word = "sym" + "link"

    offenders = [
        str(path)
        for path in docs
        if forbidden_word in path.read_text(encoding="utf-8").lower()
    ]

    assert offenders == []


def test_sync_helper_scripts_use_printer_not_print() -> None:
    scripts = [
        Path("kamma/upstream_sync/scripts/init_sync_thread.py"),
        Path("tests/check_shadow_modifications.py"),
    ]

    for script in scripts:
        source = script.read_text(encoding="utf-8")
        assert "from tools.printer import printer as pr" in source
        assert "print(" not in source
