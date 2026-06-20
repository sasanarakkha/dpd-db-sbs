"""Verify sync_status.derive_stage reports the correct stage and next command per thread artifacts."""

import json
from pathlib import Path

from kamma.upstream_sync.scripts.sync_status import derive_stage


def _write_manifest(thread_dir: Path, *, localized: bool, docs: bool = False) -> None:
    manifest: dict[str, object] = {
        "from_upstream_sha": "0" * 40,
        "to_upstream_sha": "1" * 40,
        "target_upstream_ref": "upstream/main",
        "generated_at": "2026-06-20T00:00:00+08:00",
        "changed_upstream_paths": ["docs/changelog.md"]
        if docs
        else [".github/workflows/ci.yml"],
        "deleted_upstream_paths": [],
        "blocker_paths": [],
        "discuss_paths": [],
        "needs_classification_paths": [],
        "unregistered_local_paths": [],
        "upstream_deleted_orphans": [],
        "mapped_actions": {}
        if localized
        else {
            "db/some_file.py": [
                {"category": "dps_copies", "local_path": "db/some_file_dps.py"}
            ]
        },
    }
    (thread_dir / "prep_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )


def test_empty_thread_dir_is_stage_1(tmp_path: Path) -> None:
    stage, command = derive_stage(tmp_path)
    assert stage == "Stage 1: Prep"
    assert "prep_analyzer.py" in command


def test_localized_noop_manifest_is_fast_path(tmp_path: Path) -> None:
    _write_manifest(tmp_path, localized=True)
    stage, command = derive_stage(tmp_path)
    assert stage.startswith("Fast-path")
    assert "execute_sync.py" in command


def test_shadow_touching_manifest_without_plan_is_stage_2(tmp_path: Path) -> None:
    _write_manifest(tmp_path, localized=False)
    stage, _command = derive_stage(tmp_path)
    assert stage == "Stage 2: Analysis"


def test_dynamic_plan_present_is_stage_3(tmp_path: Path) -> None:
    _write_manifest(tmp_path, localized=False)
    (tmp_path / "dynamic_plan.md").write_text("plan", encoding="utf-8")
    stage, _command = derive_stage(tmp_path)
    assert stage == "Stage 3: Execution & Verification"


def test_docs_translation_plan_present_is_stage_4(tmp_path: Path) -> None:
    _write_manifest(tmp_path, localized=False, docs=True)
    (tmp_path / "dynamic_plan.md").write_text("plan", encoding="utf-8")
    (tmp_path / "docs_translation_plan.md").write_text("plan", encoding="utf-8")
    stage, _command = derive_stage(tmp_path)
    assert stage == "Stage 4.B: Docs Translation"


def test_queued_docs_without_translation_plan_is_stage_4a(tmp_path: Path) -> None:
    _write_manifest(tmp_path, localized=False, docs=True)
    (tmp_path / "dynamic_plan.md").write_text("plan", encoding="utf-8")
    stage, command = derive_stage(tmp_path)
    assert stage == "Stage 4.A: Docs Analysis"
    assert "check_docs_parity.py" in command


def test_retrospective_present_is_stage_5_finalize(tmp_path: Path) -> None:
    _write_manifest(tmp_path, localized=False)
    (tmp_path / "dynamic_plan.md").write_text("plan", encoding="utf-8")
    (tmp_path / "retrospective.md").write_text("retro", encoding="utf-8")
    stage, command = derive_stage(tmp_path)
    assert stage.startswith("Stage 5")
    assert "finalize_accepted_sync.py" in command
