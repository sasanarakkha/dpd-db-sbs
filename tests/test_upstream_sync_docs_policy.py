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
    prep_stage = Path("kamma/upstream_sync/stages/prep.md").read_text(encoding="utf-8")
    command = (
        "uv run ruff check tools/ scripts/ db/ exporter/ --select F821,E999 --quiet"
    )

    assert command in guide
    assert command in plan
    assert command in prep_stage


def test_smd_coverage_wording_matches_checker_scope() -> None:
    readme = Path("kamma/upstream_sync/README.md").read_text(encoding="utf-8")
    infrastructure = Path("kamma/upstream_sync/infrastructure.md").read_text(
        encoding="utf-8"
    )
    checker = Path("kamma/upstream_sync/scripts/verify_smd_coverage.py").read_text(
        encoding="utf-8"
    )

    assert "every sync-relevant registry entry" in readme
    assert "every sync-relevant registry entry" in infrastructure
    assert "Verify sync-relevant registry entries" in checker
    assert "every registry entry has" not in readme
    assert "every registry entry has" not in infrastructure


def test_unique_paths_are_documented_as_cleanup_inventory_not_sync_targets() -> None:
    readme = Path("kamma/upstream_sync/README.md").read_text(encoding="utf-8")
    infrastructure = Path("kamma/upstream_sync/infrastructure.md").read_text(
        encoding="utf-8"
    )
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")

    expected = "cleanup inventory, not sync targets"
    assert expected in readme
    assert expected in infrastructure
    assert expected in guide


def test_reviewed_shadow_noop_ledger_is_documented() -> None:
    readme = Path("kamma/upstream_sync/README.md").read_text(encoding="utf-8")
    infrastructure = Path("kamma/upstream_sync/infrastructure.md").read_text(
        encoding="utf-8"
    )
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")
    plan = Path("kamma/upstream_sync/templates/sync_thread_plan.md").read_text(
        encoding="utf-8"
    )
    ledger = Path("kamma/upstream_sync/reviewed_shadow_noops.json")

    assert ledger.exists()
    assert "reviewed_shadow_noops.json" in readme
    assert "reviewed_shadow_noops.json" in infrastructure
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


def test_infrastructure_marks_stage_docs_as_legacy_reference() -> None:
    infrastructure = Path("kamma/upstream_sync/infrastructure.md").read_text(
        encoding="utf-8"
    )

    assert (
        "Legacy Stage 1-3 reference checklists; `guide.md` and `templates/` "
        "are canonical for current 5-stage syncs"
    ) in infrastructure


def test_empty_suggestions_file_is_not_kept() -> None:
    assert not Path("kamma/upstream_sync/suggestions.md").exists()


def test_docs_define_single_category_dps_shadow_policy() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")
    readme = Path("kamma/upstream_sync/README.md").read_text(encoding="utf-8")
    infrastructure = Path("kamma/upstream_sync/infrastructure.md").read_text(
        encoding="utf-8"
    )

    required = "`dps_copies` is the single category for mixed/shared fork shadows"
    assert required in guide
    assert required in readme
    assert required in infrastructure


def test_agents_requires_shadow_documentation_gate() -> None:
    agents = Path("AGENTS.md").read_text(encoding="utf-8")

    assert "Shadow Documentation Gate" in agents
    assert (
        "registry.json and the matching `kamma/upstream_sync/smd/*.md` entry" in agents
    )
    assert "one local path may appear in exactly one registry category" in agents
