"""Verify the Stage 1 chainer short-circuits on failure and runs steps in order."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from kamma.upstream_sync.scripts.stage1 import (
    Stage1Step,
    build_default_steps,
    run_prep_analyzer,
    run_registry_validation,
    run_stage1,
    run_subprocess_step,
    run_triage_and_status,
)


def make_step(name: str, success: bool, calls: list[str]) -> Stage1Step:
    def run() -> tuple[bool, str]:
        calls.append(name)
        return success, f"{name} output"

    return Stage1Step(name=name, remediation=f"fix {name}", run=run)


def test_run_stage1_happy_path_runs_all_steps_in_order() -> None:
    calls: list[str] = []
    steps = [
        make_step("one", True, calls),
        make_step("two", True, calls),
        make_step("three", True, calls),
    ]

    result = run_stage1(Path("unused"), steps=steps)

    assert result == 0
    assert calls == ["one", "two", "three"]


def test_run_stage1_short_circuits_on_first_failure() -> None:
    calls: list[str] = []
    steps = [
        make_step("one", True, calls),
        make_step("two", False, calls),
        make_step("three", True, calls),
    ]

    result = run_stage1(Path("unused"), steps=steps)

    assert result == 1
    assert calls == ["one", "two"]


def test_run_stage1_prints_step_output_and_remediation_on_failure(
    capsys,
) -> None:
    calls: list[str] = []
    steps = [make_step("shadow health check", False, calls)]

    run_stage1(Path("unused"), steps=steps)

    captured = capsys.readouterr()
    assert "shadow health check output" in captured.out
    assert "fix shadow health check" in captured.out


def test_build_default_steps_returns_six_steps_in_spec_order(tmp_path: Path) -> None:
    steps = build_default_steps(tmp_path)

    assert [step.name for step in steps] == [
        "shadow health check",
        "lint gate (F821,E999)",
        "registry validation",
        "git fetch upstream",
        "prep analyzer",
        "triage + stage verdict",
    ]


@patch("kamma.upstream_sync.scripts.stage1.subprocess.run")
def test_run_subprocess_step_success(mock_run: MagicMock) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=["echo"], returncode=0, stdout="ok\n", stderr=""
    )

    success, output = run_subprocess_step(["echo", "ok"])

    assert success is True
    assert "ok" in output


@patch("kamma.upstream_sync.scripts.stage1.subprocess.run")
def test_run_subprocess_step_failure(mock_run: MagicMock) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=["false"], returncode=1, stdout="", stderr="boom\n"
    )

    success, output = run_subprocess_step(["false"])

    assert success is False
    assert "boom" in output


def test_run_registry_validation_success(monkeypatch, tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.json"
    registry_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "kamma.upstream_sync.scripts.stage1.get_registry_path", lambda: registry_path
    )
    monkeypatch.setattr(
        "kamma.upstream_sync.scripts.stage1.validate_registry_core",
        lambda data, repo_root=None: [],
    )

    success, _output = run_registry_validation()

    assert success is True


def test_run_registry_validation_failure_reports_errors(
    monkeypatch, tmp_path: Path
) -> None:
    registry_path = tmp_path / "registry.json"
    registry_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "kamma.upstream_sync.scripts.stage1.get_registry_path", lambda: registry_path
    )
    monkeypatch.setattr(
        "kamma.upstream_sync.scripts.stage1.validate_registry_core",
        lambda data, repo_root=None: ["bad thing"],
    )

    success, output = run_registry_validation()

    assert success is False
    assert "bad thing" in output


def test_run_prep_analyzer_wraps_exception_as_failure(
    monkeypatch, tmp_path: Path
) -> None:
    class ExplodingAnalyzer:
        def __init__(self, thread_dir: Path) -> None:
            pass

        def run(self) -> None:
            raise ValueError("accepted sync state is not bootstrapped")

    monkeypatch.setattr(
        "kamma.upstream_sync.scripts.stage1.PrepAnalyzer", ExplodingAnalyzer
    )

    success, output = run_prep_analyzer(tmp_path)

    assert success is False
    assert "bootstrapped" in output


def test_run_prep_analyzer_success(monkeypatch, tmp_path: Path) -> None:
    class FakeAnalyzer:
        def __init__(self, thread_dir: Path) -> None:
            self.thread_dir = thread_dir

        def run(self) -> None:
            pass

    monkeypatch.setattr("kamma.upstream_sync.scripts.stage1.PrepAnalyzer", FakeAnalyzer)

    success, _output = run_prep_analyzer(tmp_path)

    assert success is True


def test_run_triage_and_status_passes_on_clean_manifest(tmp_path: Path) -> None:
    (tmp_path / "prep_manifest.json").write_text(
        json.dumps(
            {
                "mapped_actions": {},
                "blocker_paths": [],
                "discuss_paths": [],
                "needs_classification_paths": [],
                "unregistered_local_paths": [],
                "upstream_deleted_orphans": [],
            }
        ),
        encoding="utf-8",
    )

    success, output = run_triage_and_status(tmp_path)

    assert success is True
    assert "Fast-path" in output


def test_run_triage_and_status_fails_when_blockers_present(tmp_path: Path) -> None:
    (tmp_path / "prep_manifest.json").write_text(
        json.dumps(
            {
                "mapped_actions": {},
                "blocker_paths": ["db/some_file.py"],
                "discuss_paths": [],
                "needs_classification_paths": [],
                "unregistered_local_paths": [],
                "upstream_deleted_orphans": [],
            }
        ),
        encoding="utf-8",
    )

    success, output = run_triage_and_status(tmp_path)

    assert success is False
    assert "db/some_file.py" in output


def test_run_triage_and_status_fails_when_discuss_paths_present(tmp_path: Path) -> None:
    (tmp_path / "prep_manifest.json").write_text(
        json.dumps(
            {
                "mapped_actions": {},
                "blocker_paths": [],
                "discuss_paths": ["db/discuss_me.py"],
                "needs_classification_paths": [],
                "unregistered_local_paths": [],
                "upstream_deleted_orphans": [],
            }
        ),
        encoding="utf-8",
    )

    success, output = run_triage_and_status(tmp_path)

    assert success is False
    assert "db/discuss_me.py" in output


def test_run_triage_and_status_passes_when_all_blockers_acknowledged(
    tmp_path: Path,
) -> None:
    (tmp_path / "prep_manifest.json").write_text(
        json.dumps(
            {
                "mapped_actions": {},
                "blocker_paths": ["x/y.py"],
                "discuss_paths": [],
                "needs_classification_paths": [],
                "unregistered_local_paths": [],
                "upstream_deleted_orphans": [],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "run_acknowledged_blockers.txt").write_text(
        "x/y.py\n", encoding="utf-8"
    )

    success, _output = run_triage_and_status(tmp_path)

    assert success is True


def test_run_triage_and_status_fails_when_ack_file_lists_different_path(
    tmp_path: Path,
) -> None:
    (tmp_path / "prep_manifest.json").write_text(
        json.dumps(
            {
                "mapped_actions": {},
                "blocker_paths": ["x/y.py"],
                "discuss_paths": [],
                "needs_classification_paths": [],
                "unregistered_local_paths": [],
                "upstream_deleted_orphans": [],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "run_acknowledged_blockers.txt").write_text(
        "some/other.py\n", encoding="utf-8"
    )

    success, output = run_triage_and_status(tmp_path)

    assert success is False
    assert "x/y.py" in output


def test_run_triage_and_status_fails_when_discuss_path_present_despite_ack(
    tmp_path: Path,
) -> None:
    (tmp_path / "prep_manifest.json").write_text(
        json.dumps(
            {
                "mapped_actions": {},
                "blocker_paths": ["x/y.py"],
                "discuss_paths": ["db/discuss_me.py"],
                "needs_classification_paths": [],
                "unregistered_local_paths": [],
                "upstream_deleted_orphans": [],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "run_acknowledged_blockers.txt").write_text(
        "x/y.py\n", encoding="utf-8"
    )

    success, output = run_triage_and_status(tmp_path)

    assert success is False
    assert "db/discuss_me.py" in output
