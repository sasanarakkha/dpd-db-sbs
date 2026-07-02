"""Verify sync_status.derive_stage reports the correct stage and next command per thread artifacts."""

import json
import re
from pathlib import Path

from kamma.upstream_sync.scripts.sync_status import (
    StageDescriptor,
    derive_stage,
    extract_guide_section,
    print_stage_instructions,
)

GUIDE_PATH = (
    Path(__file__).resolve().parent.parent / "kamma" / "upstream_sync" / "guide.md"
)

STAGE_HEADER_PATTERN = re.compile(
    r"^(?:#{1,6}\s*|\*\*)Stage (\d+(?:\.[A-Za-z])?)", re.MULTILINE
)
STAGE_TOKEN_PATTERN = re.compile(r"Stage (\d+(?:\.[A-Za-z])?)")
COMMIT_LIST_PATTERN = re.compile(r"Commit ([\d,\s]+(?:or\s+\d+)?)")
COMMIT_TOKEN_PATTERN = re.compile(r"Commit (\d+)")


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
    descriptor = derive_stage(tmp_path)
    assert descriptor.stage == "Stage 1: Prep"
    assert "stage1.py" in descriptor.next_command


def test_localized_noop_manifest_is_fast_path(tmp_path: Path) -> None:
    _write_manifest(tmp_path, localized=True)
    descriptor = derive_stage(tmp_path)
    assert descriptor.stage.startswith("Fast-path")
    assert "execute_sync.py" in descriptor.next_command


def test_docs_only_manifest_is_fast_path(tmp_path: Path) -> None:
    _write_manifest(tmp_path, localized=True, docs=True)
    descriptor = derive_stage(tmp_path)
    assert descriptor.stage.startswith("Fast-path")
    assert "execute_sync.py" in descriptor.next_command


def test_localized_noop_after_execute_sync_is_fast_path_stage_4(
    tmp_path: Path,
) -> None:
    _write_manifest(tmp_path, localized=True)
    (tmp_path / "execute_sync_done.json").write_text(
        json.dumps(
            {"to_upstream_sha": "1" * 40, "executed_at": "2026-07-02T00:00:00+00:00"}
        ),
        encoding="utf-8",
    )
    descriptor = derive_stage(tmp_path)
    assert descriptor.stage.startswith("Fast-path")
    assert "Stage 4" in descriptor.stage
    assert "finalize_accepted_sync.py" in descriptor.next_command
    assert "execute_sync.py" not in descriptor.next_command


def test_shadow_touching_manifest_without_plan_is_stage_2(tmp_path: Path) -> None:
    _write_manifest(tmp_path, localized=False)
    descriptor = derive_stage(tmp_path)
    assert descriptor.stage == "Stage 2: Analysis"


def test_dynamic_plan_present_is_stage_3(tmp_path: Path) -> None:
    _write_manifest(tmp_path, localized=False)
    (tmp_path / "dynamic_plan.md").write_text("plan", encoding="utf-8")
    descriptor = derive_stage(tmp_path)
    assert descriptor.stage == "Stage 3: Execution & Verification"


def test_docs_paths_with_dynamic_plan_is_stage_3_not_docs_analysis(
    tmp_path: Path,
) -> None:
    _write_manifest(tmp_path, localized=False, docs=True)
    (tmp_path / "dynamic_plan.md").write_text("plan", encoding="utf-8")
    descriptor = derive_stage(tmp_path)
    assert descriptor.stage == "Stage 3: Execution & Verification"


def test_docs_translation_plan_presence_has_no_effect_on_routing(
    tmp_path: Path,
) -> None:
    _write_manifest(tmp_path, localized=False, docs=True)
    (tmp_path / "dynamic_plan.md").write_text("plan", encoding="utf-8")
    (tmp_path / "docs_translation_plan.md").write_text("plan", encoding="utf-8")
    descriptor = derive_stage(tmp_path)
    assert descriptor.stage == "Stage 3: Execution & Verification"


def test_retrospective_present_is_stage_4_finalize(tmp_path: Path) -> None:
    _write_manifest(tmp_path, localized=False)
    (tmp_path / "dynamic_plan.md").write_text("plan", encoding="utf-8")
    (tmp_path / "retrospective.md").write_text("retro", encoding="utf-8")
    descriptor = derive_stage(tmp_path)
    assert descriptor.stage.startswith("Stage 4")
    assert "finalize_accepted_sync.py" in descriptor.next_command


def _all_descriptors(tmp_path: Path) -> list[StageDescriptor]:
    """Drive derive_stage() through every branch by incrementally building thread artifacts."""
    descriptors = [derive_stage(tmp_path)]  # Stage 1: empty thread dir

    _write_manifest(tmp_path, localized=True)
    descriptors.append(derive_stage(tmp_path))  # Fast-path

    (tmp_path / "execute_sync_done.json").write_text(
        json.dumps(
            {"to_upstream_sha": "1" * 40, "executed_at": "2026-07-02T00:00:00+00:00"}
        ),
        encoding="utf-8",
    )
    descriptors.append(derive_stage(tmp_path))  # Fast-path (Stage 4)
    (tmp_path / "execute_sync_done.json").unlink()

    _write_manifest(tmp_path, localized=False)
    descriptors.append(derive_stage(tmp_path))  # Stage 2

    (tmp_path / "dynamic_plan.md").write_text("plan", encoding="utf-8")
    descriptors.append(derive_stage(tmp_path))  # Stage 3

    (tmp_path / "retrospective.md").write_text("retro", encoding="utf-8")
    descriptors.append(derive_stage(tmp_path))  # Stage 4 (finalize)

    return descriptors


def _guide_stage_numbers() -> set[str]:
    text = GUIDE_PATH.read_text(encoding="utf-8")
    return set(STAGE_HEADER_PATTERN.findall(text))


def _guide_commit_numbers() -> set[str]:
    text = GUIDE_PATH.read_text(encoding="utf-8")
    match = COMMIT_LIST_PATTERN.search(text)
    assert match is not None, (
        "guide.md must document a 'Commit 1, 2, 3, or docs' style list "
        "for the drift-guard test to validate against"
    )
    return set(re.findall(r"\d+", match.group(1)))


def test_stage_names_match_guide_headers(tmp_path: Path) -> None:
    """Drift guard: every StageDescriptor.stage must reference a Stage number documented in guide.md."""
    guide_stages = _guide_stage_numbers()
    assert guide_stages, "no 'Stage N' headers found in guide.md"

    for descriptor in _all_descriptors(tmp_path):
        match = STAGE_TOKEN_PATTERN.search(descriptor.stage)
        assert match is not None, f"no 'Stage N' token found in {descriptor.stage!r}"
        assert match.group(1) in guide_stages, (
            f"StageDescriptor.stage {descriptor.stage!r} references Stage "
            f"{match.group(1)!r}, which has no matching header in guide.md "
            f"(known stages: {sorted(guide_stages)})"
        )


def test_commit_gates_match_guide_commit_list(tmp_path: Path) -> None:
    """Drift guard: every Commit-N gate referenced by a StageDescriptor must be documented in guide.md."""
    guide_commits = _guide_commit_numbers()
    assert guide_commits, "no 'Commit N' list found in guide.md"

    for descriptor in _all_descriptors(tmp_path):
        for gate in (descriptor.gate_before, descriptor.gate_after):
            if gate is None:
                continue
            match = COMMIT_TOKEN_PATTERN.search(gate)
            if match is None:
                continue
            assert match.group(1) in guide_commits, (
                f"gate {gate!r} references Commit {match.group(1)!r}, which is "
                f"not in guide.md's documented Commit list (known: {sorted(guide_commits)})"
            )


def test_every_descriptor_guide_anchor_resolves_to_nonempty_section(
    tmp_path: Path,
) -> None:
    """Drift guard: every StageDescriptor.guide_anchor must resolve to a real, non-empty guide.md section."""
    guide_text = GUIDE_PATH.read_text(encoding="utf-8")

    for descriptor in _all_descriptors(tmp_path):
        section = extract_guide_section(guide_text, descriptor.guide_anchor)
        assert section.strip(), (
            f"guide_anchor {descriptor.guide_anchor!r} for stage "
            f"{descriptor.stage!r} resolved to an empty section"
        )
        assert descriptor.guide_anchor in section


def test_extract_guide_section_stops_at_next_same_or_higher_heading() -> None:
    guide_text = (
        "## Section One\n"
        "line a\n"
        "line b\n"
        "### Subsection\n"
        "line c\n"
        "## Section Two\n"
        "line d\n"
    )

    section = extract_guide_section(guide_text, "## Section One")

    assert "line a" in section
    assert "line c" in section
    assert "Section Two" not in section
    assert "line d" not in section


def test_extract_guide_section_unknown_anchor_raises() -> None:
    guide_text = "## Section One\nline a\n"

    try:
        extract_guide_section(guide_text, "## Does Not Exist")
        raise AssertionError("expected ValueError for unknown anchor")
    except ValueError as exc:
        assert "Does Not Exist" in str(exc)


def test_print_stage_instructions_prints_nonempty_section_for_every_branch(
    tmp_path: Path, capsys
) -> None:
    for descriptor in _all_descriptors(tmp_path):
        exit_code = print_stage_instructions(descriptor, GUIDE_PATH)
        captured = capsys.readouterr()

        assert exit_code == 0
        assert captured.out.strip()


def test_print_stage_instructions_unknown_anchor_returns_clear_error(
    tmp_path: Path, capsys
) -> None:
    guide_path = tmp_path / "guide.md"
    guide_path.write_text("## Section One\nline a\n", encoding="utf-8")
    bad_descriptor = StageDescriptor(
        stage="Stage 1: Prep",
        next_command="n/a",
        owner="FAST",
        dispatch="sync-fast",
        gate_before=None,
        gate_after=None,
        reads=[],
        produces=[],
        stop_condition="n/a",
        guide_anchor="## Does Not Exist",
    )

    exit_code = print_stage_instructions(bad_descriptor, guide_path)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Does Not Exist" in captured.out or "Does Not Exist" in captured.err
